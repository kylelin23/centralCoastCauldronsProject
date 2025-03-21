from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, conint
from src.api import auth

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

class InventoryAudit(BaseModel):
    number_of_potions: int
    ml_in_barrels: int
    gold: int


class CapacityPlan(BaseModel):
    potion_capacity: conint(ge=0, le=10)
    ml_capacity: conint(ge=0, le=10)


@router.get("/audit", response_model=InventoryAudit)
def get_inventory():
    """
    Returns an audit of the current inventory. Any discrepencies between
    what is reported here and my source of trusth will be posted
    as errors on potion exchange.
    """
    return InventoryAudit(number_of_potions=0, ml_in_barrels=0, gold=0)


@router.post("/plan", response_model=CapacityPlan)
def get_capacity_plan():
    """
    Provides a daily capacity purchase plan.

    Start with 1 capacity for 50 potions and 1 capacity for 10,000 ml of potion.
    Each additional capacity unit costs 1000 gold.
    """
    return CapacityPlan(potion_capacity=0, ml_capacity=0)


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def deliver_capacity_plan(capacity_purchase: CapacityPlan, order_id: int):
    """
    Processes the delivery of the planned capacity purchase.

    Start with 1 capacity for 50 potions and 1 capacity for 10,000 ml of potion.
    Each additional capacity unit costs 1000 gold.
    """
    print(f"capacity delivered: {capacity_purchase} order_id: {order_id}")

    pass