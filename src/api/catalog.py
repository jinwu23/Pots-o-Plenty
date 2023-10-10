from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    # figure out how many red_potions table has 

    with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
            first_row = result.first()
            total_red_potions = int(first_row.num_red_potions)
            total_green_potions = int(first_row.num_green_potions)
            total_blue_potions = int(first_row.num_blue_potions)
    ret_arr = []
    if total_red_potions > 0:
        ret_arr.append(
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": total_red_potions,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                })
    if total_green_potions > 0:
        ret_arr.append(
                {
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    "quantity": total_green_potions,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                })
    if total_blue_potions > 0:
        ret_arr.append(
                {
                    "sku": "BLUE_POTION_0",
                    "name": "blue potion",
                    "quantity": total_blue_potions,
                    "price": 50,
                    "potion_type": [0, 0, 100, 0],
                })
    print(ret_arr)
    return ret_arr
