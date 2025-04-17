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

    assert any(mix.potion_type == [0, 100, 0, 0] for mix in result) or any(
        mix.potion_type == [0, 0, 100, 0] for mix in result
    )


def test_respect_max_capacity() -> None:
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


def test_checkout_creates_order(client, setup_inventory):
    cart_id = 1
    response = client.post(f"/carts/{cart_id}/items/RED_POTION_0", json={"quantity": 2})
    assert response.status_code == 204

    response = client.post(f"/carts/{cart_id}/items/GREEN_POTION_0", json={"quantity": 3})
    assert response.status_code == 204

    response = client.post(f"/carts/{cart_id}/checkout", json={"payment": "credit_card"})
    assert response.status_code == 200
    data = response.json()
    order_id = data['order_id']
    assert order_id is not None

    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT * FROM orders WHERE order_id = :order_id
            """),
            {"order_id": order_id}
        ).fetchone()
        assert result is not None
        assert result['total_gold_paid'] == 250


def test_audit_log_for_checkout(client, setup_inventory):
    cart_id = 2
    response = client.post(f"/carts/{cart_id}/items/RED_POTION_0", json={"quantity": 5})
    assert response.status_code == 204

    response = client.post(f"/carts/{cart_id}/checkout", json={"payment": "credit_card"})
    assert response.status_code == 200

    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT * FROM audit_log WHERE cart_id = :cart_id
            """),
            {"cart_id": cart_id}
        ).fetchone()
        assert result is not None
        assert result['action'] == 'checkout'
        assert result['timestamp'] <= datetime.utcnow() 