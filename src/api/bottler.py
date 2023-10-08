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
    current_green_potions = 0
    current_green_ml = 0
    current_blue_potions = 0
    current_blue_ml = 0
    #update table with potions delivered
    with db.engine.begin() as connection:
        # get current number of potions and ml in table
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        current_red_potions = first_row.num_red_potions
        current_red_ml = first_row.num_red_ml
        current_green_potions = first_row.num_green_potions
        current_green_ml = first_row.num_green_ml
        current_blue_potions = first_row.num_blue_potions
        current_blue_ml = first_row.num_blue_ml
        total_red_potions = 0
        total_green_potions = 0
        total_blue_potions = 0
        total_red_ml = 0
        total_green_ml = 0
        total_blue_ml = 0
        # update table with sum of potions and ml
        for potion in potions_delivered:
            if(potion.potion_type == [100, 0, 0, 0]):
                total_red_potions = int(current_red_potions + potion.quantity)
                total_red_ml = int(current_red_ml - (potion.quantity * 100))
            if(potion.potion_type == [0, 100, 0, 0]):
                total_green_potions = int(current_green_potions + potion.quantity)
                total_green_ml = int(current_green_ml - (potion.quantity * 100))
            if(potion.potion_type == [0, 0, 100, 0]):
                total_blue_potions = int(current_blue_potions + potion.quantity)
                total_blue_ml = int(current_blue_ml - (potion.quantity * 100))
        current_total_potions = total_red_potions + total_green_potions + total_blue_potions
        current_total_ml = total_red_ml + total_green_ml + total_blue_ml
        # updating values in database
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {total_red_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {total_green_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))        
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = {total_blue_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {total_blue_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET total_potions = {current_total_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET total_ml = {current_total_ml}"))

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
        green_ml = first_row.num_green_ml
        blue_ml = first_row.num_blue_ml
        red_potions_to_brew = math.floor(red_ml / 100)
        green_potions_to_brew = math.floor(green_ml / 100)
        blue_potions_to_brew = math.floor(blue_ml / 100)
    ret_arr = []
    if red_potions_to_brew > 0:
        ret_arr.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": red_potions_to_brew,
                })
    if green_potions_to_brew > 0:
        ret_arr.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green_potions_to_brew,
                })
    if blue_potions_to_brew > 0:
        ret_arr.append(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": blue_potions_to_brew,
                })
    return ret_arr
