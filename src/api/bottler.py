from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import List
from src.api import auth
from src import database as db
import sqlalchemy


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


class PotionMixes(BaseModel):
    potion_type: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d]",
    )
    quantity: int = Field(
        ..., ge=1, le=10000, description="Quantity must be between 1 and 10,000"
    )

    @field_validator("potion_type")
    @classmethod
    def validate_potion_type(cls, potion_type: List[int]) -> List[int]:
        if sum(potion_type) != 100:
            raise ValueError("Sum of potion_type values must be exactly 100")
        return potion_type


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_deliver_bottles(potions_delivered: List[PotionMixes], order_id: int):
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    red_used = green_used = blue_used = dark_used = 0

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            qty = potion.quantity
            pt = potion.potion_type

            red_used += qty * pt[0]
            green_used += qty * pt[1]
            blue_used += qty * pt[2]
            dark_used += qty * pt[3]

            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO potion_inventory (red, green, blue, dark, quantity)
                    VALUES (:r, :g, :b, :d, :q)
                """
                ),
                {
                    "r": pt[0],
                    "g": pt[1],
                    "b": pt[2],
                    "d": pt[3],
                    "q": qty,
                },
            )

            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO potion_ledger (sku, quantity)
                    VALUES (:sku, :quantity)
                    """
                ),
                {
                    "sku": "_".join(map(str, pt)),
                    "quantity": qty,
                },
            )

        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                    red_ml = red_ml - :red,
                    green_ml = green_ml - :green,
                    blue_ml = blue_ml - :blue,
                    dark_ml = dark_ml - :dark
            """
            ),
            {
                "red": red_used,
                "green": green_used,
                "blue": blue_used,
                "dark": dark_used,
            },
        )

        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ml_ledger (red_ml, green_ml, blue_ml, dark_ml)
                VALUES (:r, :g, :b, :d)
                """
            ),
            {
                "r": -red_used,
                "g": -green_used,
                "b": -blue_used,
                "d": -dark_used,
            },
        )



def create_bottle_plan(
    red_ml: int,
    green_ml: int,
    blue_ml: int,
    dark_ml: int,
    maximum_potion_capacity: int,
    current_potion_inventory: List[PotionMixes],
) -> List[PotionMixes]:
    import random

    plan = []
    ml_list = [red_ml, green_ml, blue_ml, dark_ml]

    while sum(ml_list) >= 100 and len(plan) + len(current_potion_inventory) < maximum_potion_capacity:
        potion = [0, 0, 0, 0]
        while sum(potion) != 100:
            i = random.randint(0, 3)
            if ml_list[i] > potion[i]:
                potion[i] += 1

        for i in range(4):
            ml_list[i] -= potion[i]

        for existing in plan:
            if existing.potion_type == potion:
                existing.quantity += 1
                break
        else:
            plan.append(PotionMixes(potion_type=potion, quantity=1))

    return plan

    # return [
    #     PotionMixes(
    #         potion_type=[100, 0, 0, 0],
    #         quantity=5,
    #     )
    # ]


@router.post("/plan", response_model=List[PotionMixes])
def get_bottle_plan():
    """
    Gets the plan for bottling potions.
    Each bottle has a quantity of what proportion of red, green, blue, and dark potions to add.
    Colors are expressed in integers from 0 to 100 that must sum up to exactly 100.
    """

    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
                """
                SELECT red_ml, green_ml, blue_ml
                FROM global_inventory
                """
            )
        ).one()

    red_ml, green_ml, blue_ml = result

    # Maximum potion capacity could also be dynamically fetched from a config or a database if required
    maximum_potion_capacity = 50

    return create_bottle_plan(
        red_ml=red_ml,
        green_ml=green_ml,
        blue_ml=blue_ml,
        maximum_potion_capacity=maximum_potion_capacity,
        current_potion_inventory=[],
    )




if __name__ == "__main__":

    print(get_bottle_plan())