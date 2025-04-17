from src.api.barrels import (
    calculate_barrel_summary,
    create_barrel_plan,
    Barrel,
    BarrelOrder,
)
from typing import List


def test_barrel_delivery() -> None:
    delivery: List[Barrel] = [
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=1000,
            potion_type=[1.0, 0, 0, 0],
            price=100,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_GREEN_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=150,
            quantity=5,
        ),
    ]

    delivery_summary = calculate_barrel_summary(delivery)

    assert delivery_summary.gold_paid == 1750


def test_buy_small_red_barrel_plan() -> None:
    wholesale_catalog: List[Barrel] = [
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=1000,
            potion_type=[1.0, 0, 0, 0],
            price=100,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_GREEN_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=150,
            quantity=5,
        ),
        Barrel(
            sku="SMALL_BLUE_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 0, 1.0, 0],
            price=500,
            quantity=2,
        ),
    ]

    gold = 100
    max_barrel_capacity = 10000
    current_red_ml = 0
    current_green_ml = 1000
    current_blue_ml = 1000
    current_dark_ml = 1000

    barrel_orders = create_barrel_plan(
        gold,
        max_barrel_capacity,
        current_red_ml,
        current_green_ml,
        current_blue_ml,
        current_dark_ml,
        wholesale_catalog,
    )

    assert isinstance(barrel_orders, list)
    assert all(isinstance(order, BarrelOrder) for order in barrel_orders)
    assert len(barrel_orders) > 0
    assert barrel_orders[0].sku == "SMALL_RED_BARREL"
    assert barrel_orders[0].quantity == 1


def test_cant_afford_barrel_plan() -> None:
    wholesale_catalog: List[Barrel] = [
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=1000,
            potion_type=[1.0, 0, 0, 0],
            price=100,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_GREEN_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=150,
            quantity=5,
        ),
        Barrel(
            sku="SMALL_BLUE_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 0, 1.0, 0],
            price=500,
            quantity=2,
        ),
    ]

    gold = 50
    max_barrel_capacity = 10000
    current_red_ml = 0
    current_green_ml = 1000
    current_blue_ml = 1000
    current_dark_ml = 1000

    barrel_orders = create_barrel_plan(
        gold,
        max_barrel_capacity,
        current_red_ml,
        current_green_ml,
        current_blue_ml,
        current_dark_ml,
        wholesale_catalog,
    )

    assert isinstance(barrel_orders, list)
    assert len(barrel_orders) == 0


def test_capacity_limit_blocks_purchase() -> None:
    wholesale_catalog = [
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=1000,
            potion_type=[1.0, 0, 0, 0],
            price=100,
            quantity=10,
        ),
    ]

    gold = 1000
    max_barrel_capacity = 5000  
    current_red_ml = 5000
    current_green_ml = 0
    current_blue_ml = 0
    current_dark_ml = 0

    barrel_orders = create_barrel_plan(
        gold,
        max_barrel_capacity,
        current_red_ml,
        current_green_ml,
        current_blue_ml,
        current_dark_ml,
        wholesale_catalog,
    )

    assert len(barrel_orders) == 0


def test_prefers_cheapest_available_barrel() -> None:
    wholesale_catalog = [
        Barrel(
            sku="CHEAP_GREEN",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=100,
            quantity=1,
        ),
        Barrel(
            sku="EXPENSIVE_GREEN",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=300,
            quantity=1,
        ),
    ]

    gold = 150
    max_barrel_capacity = 10000
    current_red_ml = 0
    current_green_ml = 0
    current_blue_ml = 0
    current_dark_ml = 0

    barrel_orders = create_barrel_plan(
        gold,
        max_barrel_capacity,
        current_red_ml,
        current_green_ml,
        current_blue_ml,
        current_dark_ml,
        wholesale_catalog,
    )

    assert len(barrel_orders) == 1
    assert barrel_orders[0].sku == "CHEAP_GREEN"
    assert barrel_orders[0].quantity == 1

@pytest.fixture(scope="module")
def setup_inventory():
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("""
                INSERT INTO potion_inventory (sku, red, green, blue, dark, quantity)
                VALUES ('RED_POTION_0', 100, 0, 0, 0, 10),
                       ('GREEN_POTION_0', 0, 100, 0, 0, 10),
                       ('BLUE_POTION_0', 0, 0, 100, 0, 10)
            """)
        )
    yield
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("""
                DELETE FROM potion_inventory WHERE sku IN ('RED_POTION_0', 'GREEN_POTION_0', 'BLUE_POTION_0')
            """)
        )


def test_cart_checkout_updates_inventory(client, setup_inventory):
    cart_id = 1
    response = client.post(f"/carts/{cart_id}/items/RED_POTION_0", json={"quantity": 2})
    assert response.status_code == 204

    response = client.post(f"/carts/{cart_id}/items/GREEN_POTION_0", json={"quantity": 3})
    assert response.status_code == 204

    response = client.post(f"/carts/{cart_id}/checkout", json={"payment": "credit_card"})
    assert response.status_code == 200
    assert "order_id" in response.json()

    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT quantity FROM potion_inventory WHERE sku = 'RED_POTION_0'
            """)
        ).fetchone()
        assert result['quantity'] == 8

        result = connection.execute(
            sqlalchemy.text("""
                SELECT quantity FROM potion_inventory WHERE sku = 'GREEN_POTION_0'
            """)
        ).fetchone()
        assert result['quantity'] == 7


def test_custom_potion_mixes(client, setup_inventory):
    cart_id = 2
    response = client.post(f"/carts/{cart_id}/items/RED_POTION_0", json={"quantity": 5})
    assert response.status_code == 204

    response = client.post(f"/carts/{cart_id}/checkout", json={"payment": "credit_card"})
    assert response.status_code == 200
    assert "order_id" in response.json()

    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT quantity FROM potion_inventory WHERE sku = 'RED_POTION_0'
            """)
        ).fetchone()
        assert result['quantity'] == 5