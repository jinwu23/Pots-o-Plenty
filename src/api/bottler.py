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
    #update table with potions delivered
    with db.engine.begin() as connection:
        # update table with sum of potions and ml
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))   
        # loop through each potion in potions table         
        for potion_row in result:
            # loop through potions delivered and find corresponding potion
            for potions in potions_delivered:
                if (potions.potion_type[0] == potion_row.red and 
                   potions.potion_type[1] == potion_row.green and
                   potions.potion_type[2] == potion_row.blue and
                   potions.potion_type[3] == potion_row.dark):
                    # get ml spent for each type
                    red_ml_spent = potion_row.red * potions.quantity
                    green_ml_spent = potion_row.green * potions.quantity
                    blue_ml_spent = potion_row.blue * potions.quantity
                    total_ml_spent = red_ml_spent + green_ml_spent + blue_ml_spent
                    # update values in database
                    connection.execute(
                        sqlalchemy.text("""
                            UPDATE potions SET
                            quantity = quantity + :potions_delivered WHERE sku = :sku
                        """),
                    [{"potions_delivered": potions.quantity,
                      "sku": potion_row.sku,
                    }])
                    connection.execute(
                        sqlalchemy.text("""
                            UPDATE global_inventory SET
                            total_potions = total_potions + :potions_delivered,
                            total_ml = total_ml - :total_ml_spent,
                            red_ml = red_ml - :red_ml_spent,
                            green_ml = green_ml - :green_ml_spent,
                            blue_ml = blue_ml - :blue_ml_spent
                        """),
                    [{"potions_delivered": potions.quantity,
                       "sku": potion_row.sku,
                       "total_ml_spent": total_ml_spent,
                        "red_ml_spent": red_ml_spent,
                        "green_ml_spent": green_ml_spent,
                        "blue_ml_spent": blue_ml_spent
                    }])

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

    # dictionary of item SKU to number of potions to brew
    potions_to_brew = {}
    ret_arr = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        red_potions_to_brew = math.floor((first_row.red_ml / 100) / 2)
        green_potions_to_brew = math.floor(first_row.green_ml / 100)
        blue_potions_to_brew = math.floor((first_row.blue_ml / 100) / 2)
        purple_potions_to_brew = min(math.floor((first_row.red_ml / 100)), math.floor((first_row.blue_ml / 100)))
        potions_to_brew
        potions_to_brew["RED_POTION_100"] = red_potions_to_brew
        potions_to_brew["GREEN_POTION_100"] = green_potions_to_brew
        potions_to_brew["BLUE_POTION_100"] = blue_potions_to_brew
        potions_to_brew["PURPLE_POTION_50_50"] = purple_potions_to_brew
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for row in result:
            if potions_to_brew[row.sku] != 0:
                ret_arr.append(
                    {
                        "potion_type": [row.red, row.green, row.blue, row.dark],
                        "quantity": potions_to_brew[row.sku],
                    })
    return ret_arr
