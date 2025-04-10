from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Annotated
from src import database as db
import sqlalchemy



router = APIRouter()


class CatalogItem(BaseModel):
    sku: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]{1,20}$")]
    name: str
    quantity: Annotated[int, Field(ge=1, le=10000)]
    price: Annotated[int, Field(ge=1, le=500)]
    potion_type: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d]",
    )


# Placeholder function, you will replace this with a database call
def create_catalog() -> List[CatalogItem]:
    catalog = []

    with db.engine.begin() as connection:
        red = connection.execute(
            sqlalchemy.text("""
                SELECT COALESCE(SUM(quantity), 0) AS qty FROM potion_inventory
                WHERE red = 100 AND green = 0 AND blue = 0 AND dark = 0
            """)
        ).scalar_one()

        if red > 0:
            catalog.append(CatalogItem(
                sku="RED_POTION_0",
                name="red potion",
                quantity=red,
                price=50,
                potion_type=[100, 0, 0, 0]
            ))

        green = connection.execute(
            sqlalchemy.text("""
                SELECT COALESCE(SUM(quantity), 0) AS qty FROM potion_inventory
                WHERE green = 100 AND red = 0 AND blue = 0 AND dark = 0
            """)
        ).scalar_one()

        if green > 0:
            catalog.append(CatalogItem(
                sku="GREEN_POTION_0",
                name="green potion",
                quantity=green,
                price=50,
                potion_type=[0, 100, 0, 0]
            ))

        blue = connection.execute(
            sqlalchemy.text("""
                SELECT COALESCE(SUM(quantity), 0) AS qty FROM potion_inventory
                WHERE blue = 100 AND red = 0 AND green = 0 AND dark = 0
            """)
        ).scalar_one()

        if blue > 0:
            catalog.append(CatalogItem(
                sku="BLUE_POTION_0",
                name="blue potion",
                quantity=blue,
                price=50,
                potion_type=[0, 0, 100, 0]
            ))

    return catalog
    # return [
    #     CatalogItem(
    #         sku="RED_POTION_0",
    #         name="red potion",
    #         quantity=1,
    #         price=50,
    #         potion_type=[100, 0, 0, 0],
    #     )
    # ]


@router.get("/catalog/", tags=["catalog"], response_model=List[CatalogItem])
def get_catalog() -> List[CatalogItem]:
    """
    Retrieves the catalog of items. Each unique item combination should have only a single price.
    You can have at most 6 potion SKUs offered in your catalog at one time.
    """
    return create_catalog()
