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
    potion_ledger_entities = []
    ml_ledger_entities = []
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            # get specific potion_id
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT id FROM potions WHERE 
                    red = :potion_red and
                    green = :potion_green and
                    blue = :potion_blue and
                    dark = :potion_dark
                    """),
                    [{"potion_red": potion.potion_type[0], "potion_green": potion.potion_type[1], "potion_blue": potion.potion_type[2], "potion_dark": potion.potion_type[3]}])
            potion_id = result.scalar_one()
            # add to ledger entities
            potion_ledger_entities.append({"potion_id": potion_id, "potions_delivered": potion.quantity})
            ml_ledger_entities.append({
                "red_change": -(potion.potion_type[0] * potion.quantity), 
                "green_change": -(potion.potion_type[1] * potion.quantity), 
                "blue_change": -(potion.potion_type[2] * potion.quantity), 
                "dark_change": -(potion.potion_type[3] * potion.quantity), 
                "potion_type": potion_id, 
                "quantity": potion.quantity})
        # insert potion_ledger_entity
        connection.execute(sqlalchemy.text(
                """
                INSERT INTO potion_ledger_entities
                (potion_change, potion_id, description)
                VALUES
                (:potions_delivered, :potion_id, 'bottler delivery')          
                """), potion_ledger_entities)
            # insert ml potion_ledger_entity
        connection.execute(sqlalchemy.text(
                """
                INSERT INTO ml_ledger_entities
                (red_change, green_change, blue_change, dark_change, description)
                VALUES
                (:red_change, :green_change, :blue_change, :dark_change, 'bottler delivery: potion_type = :potion_type, quantity = :quantity')          
                """), ml_ledger_entities)
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

    ret_arr = []
    with db.engine.begin() as connection:
        # get total ml of every color
        result = connection.execute(sqlalchemy.text(
            """SELECT 
            COALESCE(SUM(red_change),0) AS red_ml,
            COALESCE(SUM(green_change),0) AS green_ml,
            COALESCE(SUM(blue_change),0) AS blue_ml,
            COALESCE(SUM(dark_change),0) AS dark_ml
            FROM ml_ledger_entities
            """))
        result = result.first()
        red_ml = result.red_ml
        green_ml = result.green_ml
        blue_ml = result.blue_ml
        dark_ml = result.dark_ml
        # get total potions in inventory
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(potion_change),0) from potion_ledger_entities"))
        total_potions_brewable = 300 - result.scalar_one()
        # divide total_potions_brewable by potion types
        result = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM potions"))
        total_potions_brewable = math.floor(total_potions_brewable / result.scalar_one())
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for row in result:
            potions_brewable = 0
            if(row.red == 100):
                potions_brewable = math.floor((red_ml/row.red)/2)
            if(row.green == 100):
                potions_brewable = math.floor((green_ml/row.green)/2)
            if(row.blue == 100):
                potions_brewable = math.floor((blue_ml/row.blue)/2)
            if(row.red == 50 and row.green == 50):
                potions_brewable = math.floor(min((red_ml/row.red)/4, (green_ml/row.green)/4))
            if(row.red == 50 and row.blue == 50):
                potions_brewable = math.floor(min((red_ml/row.red)/4, (blue_ml/row.blue)/4))
            if(row.green == 50 and row.blue == 50):
                potions_brewable = math.floor(min((green_ml/row.green)/4, (blue_ml/row.blue)/4))
            # check if we exceed capacity
            if(potions_brewable > total_potions_brewable):
                potions_brewable = total_potions_brewable
            if(potions_brewable > 0):
                ret_arr.append(
                {
                    "potion_type": [row.red, row.green, row.blue, row.dark],
                    "quantity": potions_brewable,
                })
            
    return ret_arr
