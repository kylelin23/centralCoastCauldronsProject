from dataclasses import dataclass
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import List
import random

import sqlalchemy
from src.api import auth
from src import database as db



router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int = Field(gt=0, description="Must be greater than 0")
    potion_type: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d] that sum to 1.0",
    )
    price: int = Field(ge=0, description="Price must be non-negative")
    quantity: int = Field(ge=0, description="Quantity must be non-negative")

    @field_validator("potion_type")
    @classmethod
    def validate_potion_type(cls, potion_type: List[float]) -> List[float]:
        if len(potion_type) != 4:
            raise ValueError("potion_type must have exactly 4 elements: [r, g, b, d]")
        if not abs(sum(potion_type) - 1.0) < 1e-6:
            raise ValueError("Sum of potion_type values must be exactly 1.0")
        return potion_type


class BarrelOrder(BaseModel):
    sku: str
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


@dataclass
class BarrelSummary:
    gold_paid: int


def calculate_barrel_summary(barrels: List[Barrel]) -> BarrelSummary:
    return BarrelSummary(gold_paid=sum(b.price * b.quantity for b in barrels))


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_deliver_barrels(barrels_delivered: List[Barrel], order_id: int):
    """
    Processes barrels delivered based on the provided order_id. order_id is a unique value representing
    a single delivery; the call is idempotent based on the order_id.
    """
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    delivery = calculate_barrel_summary(barrels_delivered)

    red_ml = 0
    green_ml = 0
    blue_ml = 0

    for barrel in barrels_delivered:
        total_ml = barrel.ml_per_barrel * barrel.quantity
        red_ml += total_ml * barrel.potion_type[0]
        green_ml += total_ml * barrel.potion_type[1]
        blue_ml += total_ml * barrel.potion_type[2]

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                gold = gold - :gold_paid
                """
            ),
            [{"gold_paid": delivery.gold_paid,
                "red_ml": int(red_ml),
                "green_ml": int(green_ml),
                "blue_ml": int(blue_ml),
            }]
        )

    pass


def create_barrel_plan(
    gold: int,
    max_barrel_capacity: int,
    current_red_ml: int,
    current_green_ml: int,
    current_blue_ml: int,
    current_dark_ml: int,
    wholesale_catalog: List[Barrel],
) -> List[BarrelOrder]:
    print(
        f"gold: {gold}, max_barrel_capacity: {max_barrel_capacity}, current_red_ml: {current_red_ml}, current_green_ml: {current_green_ml}, current_blue_ml: {current_blue_ml}, wholesale_catalog: {wholesale_catalog}"
    )

    colors = ["red", "blue", "green"]
    color = random.choice(colors)

    dict = {
        "red": {"index": 0, "current_ml": current_red_ml},
        "green": {"index": 1, "current_ml": current_green_ml},
        "blue": {"index": 2, "current_ml": current_blue_ml},
    }

    index = dict[color]["index"]
    currentMl = dict[color]["current_ml"]

    if currentMl < 5000:

        candidateBarrel = None
        min_price = float('inf')
        # Find the cheapest small barrel
        for barrel in wholesale_catalog:
            if barrel.potion_type[index] == 1.0 and barrel.price < min_price:
                candidateBarrel = barrel
                min_price = barrel.price
    if candidateBarrel and candidateBarrel.price <= gold:
        return [BarrelOrder(sku=candidateBarrel.sku, quantity=1)]




    # find cheapest red barrel
    red_barrel = min(
        (barrel for barrel in wholesale_catalog if barrel.potion_type[0] == 1),
        key=lambda b: b.price,
        default=None,
    )

    # make sure we can afford it
    if red_barrel and red_barrel.price <= gold:
        return [BarrelOrder(sku=red_barrel.sku, quantity=1)]

    # return an empty list if no affordable red barrel is found
    return []


@router.post("/plan", response_model=List[BarrelOrder])
def get_wholesale_purchase_plan(wholesale_catalog: List[Barrel]):
    """
    Gets the plan for purchasing wholesale barrels. The call passes in a catalog of available barrels
    and the shop returns back which barrels they'd like to purchase and how many.
    """
    print(f"barrel catalog: {wholesale_catalog}")

    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT gold
                FROM global_inventory
                """
            )
        ).one()

        gold = row.gold

    # TODO: fill in values correctly based on what is in your database
    return create_barrel_plan(
        gold=gold,
        max_barrel_capacity=10000,
        current_red_ml=row.red_ml,
        current_green_ml=row.green_ml,
        current_blue_ml=row.blue_ml,
        current_dark_ml=0,
        wholesale_catalog=wholesale_catalog,
    )
