from src.api.bottler import PotionMixes, create_bottle_plan


from typing import List


def test_bottle_red_potions() -> None:
    red_ml: int = 100
    green_ml: int = 0
    blue_ml: int = 0
    dark_ml: int = 0
    maximum_potion_capacity: int = 1000
    current_potion_inventory: List[PotionMixes] = []

    result = create_bottle_plan(
        red_ml=red_ml,
        green_ml=green_ml,
        blue_ml=blue_ml,
        dark_ml=dark_ml,
        maximum_potion_capacity=maximum_potion_capacity,
        current_potion_inventory=current_potion_inventory,
    )

    assert len(result) == 1
    assert result[0].potion_type == [100, 0, 0, 0]
    assert result[0].quantity == 5

def test_bottle_green_potions() -> None:
    result = create_bottle_plan(
        red_ml=0,
        green_ml=250,
        blue_ml=0,
        dark_ml=0,
        maximum_potion_capacity=1000,
        current_potion_inventory=[],
    )

    assert len(result) == 1
    assert result[0].potion_type == [0, 100, 0, 0]
    assert result[0].quantity == 5


def test_bottle_blue_and_green_combo() -> None:
    result = create_bottle_plan(
        red_ml=0,
        green_ml=100,
        blue_ml=100,
        dark_ml=0,
        maximum_potion_capacity=1000,
        current_potion_inventory=[],
    )

    assert any(mix.potion_type == [0, 100, 0, 0] for mix in result) or \
           any(mix.potion_type == [0, 0, 100, 0] for mix in result)


def test_respect_max_capacity() -> None:
    # Already 995 potions in inventory, only 5 more can be added
    result = create_bottle_plan(
        red_ml=1000,
        green_ml=0,
        blue_ml=0,
        dark_ml=0,
        maximum_potion_capacity=1000,
        current_potion_inventory=[
            PotionMixes(potion_type=[100, 0, 0, 0], quantity=995)
        ],
    )

    assert len(result) == 1
    assert result[0].quantity == 5


def test_no_mix_when_capacity_reached() -> None:
    result = create_bottle_plan(
        red_ml=500,
        green_ml=500,
        blue_ml=500,
        dark_ml=500,
        maximum_potion_capacity=1000,
        current_potion_inventory=[
            PotionMixes(potion_type=[100, 0, 0, 0], quantity=1000)
        ],
    )

    assert result == []
