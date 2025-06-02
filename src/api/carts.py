from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import sqlalchemy
from src.api import auth
from enum import Enum
from typing import List, Optional
from src import database as db
from datetime import datetime

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class SearchSortOptions(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"


class SearchSortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class LineItem(BaseModel):
    line_item_id: int
    item_sku: str
    customer_name: str
    line_item_total: int
    timestamp: str


class SearchResponse(BaseModel):
    previous: Optional[str] = None
    next: Optional[str] = None
    results: List[LineItem]


@router.get("/search/", response_model=SearchResponse, tags=["search"])
def search_orders(
    customerName: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: SearchSortOptions = SearchSortOptions.timestamp,
    sort_order: SearchSortOrder = SearchSortOrder.desc,
):
    itemMaximum = 5
    prev = None
    next = None

    with db.engine.begin() as connection:
        query = sqlalchemy.text("""
            SELECT
                cart_items.id AS line_item_id,
                potions.sku AS item_sku,
                carts.customer AS customerName,
                (cart_items.quantity * potions.price) AS line_item_total,
                carts.timestamp AS timestamp
            FROM carts
            JOIN cart_items ON carts.id = cart_items.cart_id
            JOIN potions ON cart_items.potion_id = potions.id
        """)
        results = connection.execute(query).mappings().all()

    if customer_name:
        filtered = []
    for r in results:
        customerLower = r["customerName"].lower()
        search_customer_lower = customerName.lower()
        if search_customer_lower in customerLower:
            filtered.append(r)
        results = filtered

    if potion_sku:
        filtered = []
        for r in results:
            sku_lower = r["item_sku"].lower()
            search_sku_lower = potion_sku.lower()
            if search_sku_lower in sku_lower:
                filtered.append(r)
        results = filtered

    reverse = sort_order == SearchSortOrder.desc
    results.sort(key=lambda x: x[sort_col.value], reverse=reverse)

    page = int(search_page) if search_page.isdigit() else 0
    start = page
    end = start + itemMaximum
    paged_results = results[start:end]

    if start - itemMaximum >= 0:
        prev = str(start - itemMaximum)
    if end < len(results):
        next = str(end)

    items = [LineItem(**item) for item in paged_results]

    return SearchResponse(prev=prev, next=next, results=items)

cart_id_counter = 1
carts: dict[int, dict[str, int]] = {}


class Customer(BaseModel):
    customer_id: str
    customer_name: str
    character_class: str
    level: int = Field(ge=1, le=20)


@router.post("/visits/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_visits(visit_id: int, customers: List[Customer]):
    """
    Shares the customers that visited the store on that tick.
    """
    print(customers)
    pass


class CartCreateResponse(BaseModel):
    cart_id: int


@router.post("/", response_model=CartCreateResponse)
def create_cart(new_cart: Customer):
    """
    Creates a new cart for a specific customer.
    """
    global cart_id_counter
    cart_id = cart_id_counter
    cart_id_counter += 1
    carts[cart_id] = {}
    return CartCreateResponse(cart_id=cart_id)


class CartItem(BaseModel):
    quantity: int = Field(ge=1, description="Quantity must be at least 1")


@router.post("/{cart_id}/items/{item_sku}", status_code=status.HTTP_204_NO_CONTENT)
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    print(
        f"cart_id: {cart_id}, item_sku: {item_sku}, cart_item: {cart_item}, carts: {carts}"
    )
    if cart_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")

    carts[cart_id][item_sku] = cart_item.quantity
    return status.HTTP_204_NO_CONTENT


class CheckoutResponse(BaseModel):
    total_potions_bought: int
    total_gold_paid: int


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout", response_model=CheckoutResponse)
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Handles the checkout process for a specific cart.
    """

    if cart_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart = carts[cart_id]
    total_potions_bought = 0
    total_gold_paid = 0
    order_id = None

    with db.engine.begin() as connection:
        order_id = connection.execute(
            sqlalchemy.text("""
                INSERT INTO orders (cart_id, total_gold_paid, created_at)
                VALUES (:cart_id, :total_gold_paid, :created_at)
                RETURNING order_id
            """),
            {
                "cart_id": cart_id,
                "total_gold_paid": total_gold_paid,
                "created_at": datetime.utcnow(),
            }
        ).fetchone()[0]

        for sku, quantity in cart.items():
            potion_inventory = connection.execute(
                sqlalchemy.text("""
                    SELECT sku, red, green, blue, dark, quantity
                    FROM potion_inventory
                    WHERE sku = :sku
                """),
                {"sku": sku}
            ).fetchone()

            if potion_inventory is None:
                raise HTTPException(status_code=400, detail=f"SKU {sku} not found in inventory")

            new_quantity = potion_inventory['quantity'] - quantity
            if new_quantity < 0:
                raise HTTPException(status_code=400, detail=f"Not enough stock for SKU: {sku}")

            connection.execute(
                sqlalchemy.text("""
                    UPDATE potion_inventory
                    SET quantity = :new_quantity
                    WHERE sku = :sku
                """),
                {"sku": sku, "new_quantity": new_quantity},
            )

            connection.execute(
                sqlalchemy.text("""
                    INSERT INTO order_items (order_id, sku, quantity, line_item_total)
                    VALUES (:order_id, :sku, :quantity, :line_item_total)
                """),
                {
                    "order_id": order_id,
                    "sku": sku,
                    "quantity": quantity,
                    "line_item_total": quantity * 50,
                },
            )

            total_potions_bought += quantity
            total_gold_paid += quantity * 50

        connection.execute(
            sqlalchemy.text("""
                UPDATE global_inventory
                SET gold = gold + :added_gold
            """),
            {"added_gold": total_gold_paid},
        )

    return CheckoutResponse(
        total_potions_bought=total_potions_bought,
        total_gold_paid=total_gold_paid,
        order_id=order_id,  # Return the created order's ID
    )