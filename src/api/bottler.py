from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import math


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)
    #initializing variables
    current_red_potions = 0
    current_red_ml = 0
    #update table with potions delivered
    with db.engine.begin() as connection:
        # get current number of red potions and red_ml in table
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        current_red_potions = first_row.num_red_potions
        current_red_ml = first_row.num_red_ml
        # update table with sum of red potions and red_ml
        total_red_potions = int(current_red_potions + potions_delivered[0].quantity)
        total_red_ml = int(current_red_ml - (potions_delivered[0].quantity * 100))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {total_red_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    # get amount of red_ml i have
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        red_ml = first_row.num_red_ml
        potions_to_brew = math.floor(red_ml / 100)

    if potions_to_brew > 0:
        return [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": potions_to_brew,
                }
            ]
    else:
        return []
