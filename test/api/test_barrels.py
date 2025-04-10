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
        Barrel(sku="SMALL_RED_BARREL", ml_per_barrel=1000, potion_type=[1.0, 0, 0, 0], price=100, quantity=10),
        Barrel(sku="SMALL_GREEN_BARREL", ml_per_barrel=1000, potion_type=[0, 1.0, 0, 0], price=150, quantity=5),
        Barrel(sku="SMALL_BLUE_BARREL", ml_per_barrel=1000, potion_type=[0, 0, 1.0, 0], price=500, quantity=2),
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
        Barrel(sku="SMALL_RED_BARREL", ml_per_barrel=1000, potion_type=[1.0, 0, 0, 0], price=100, quantity=10),
        Barrel(sku="SMALL_GREEN_BARREL", ml_per_barrel=1000, potion_type=[0, 1.0, 0, 0], price=150, quantity=5),
        Barrel(sku="SMALL_BLUE_BARREL", ml_per_barrel=1000, potion_type=[0, 0, 1.0, 0], price=500, quantity=2),
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
        Barrel(sku="SMALL_RED_BARREL", ml_per_barrel=1000, potion_type=[1.0, 0, 0, 0], price=100, quantity=10),
    ]

    gold = 1000
    max_barrel_capacity = 5000  # Already at max capacity
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
        Barrel(sku="CHEAP_GREEN", ml_per_barrel=1000, potion_type=[0, 1.0, 0, 0], price=100, quantity=1),
        Barrel(sku="EXPENSIVE_GREEN", ml_per_barrel=1000, potion_type=[0, 1.0, 0, 0], price=300, quantity=1),
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