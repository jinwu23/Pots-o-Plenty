from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)
    # get total number of ml we purchased and gold spent
    total_red_ml_delivered = 0
    total_green_ml_delivered = 0
    total_blue_ml_delivered = 0
    total_gold_spent = 0
    for barrel in barrels_delivered:
        if(barrel.sku == "SMALL_RED_BARREL"):
            total_red_ml_delivered += barrel.ml_per_barrel * barrel.quantity
            total_gold_spent += barrel.price * barrel.quantity
        if(barrel.sku == "SMALL_GREEN_BARREL"):
            total_green_ml_delivered += barrel.ml_per_barrel * barrel.quantity
            total_gold_spent += barrel.price * barrel.quantity
        if(barrel.sku == "SMALL_BLUE_BARREL"):
            total_blue_ml_delivered += barrel.ml_per_barrel * barrel.quantity
            total_gold_spent += barrel.price * barrel.quantity
    # add current ml with ml_delivered
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        total_red_ml = int(total_red_ml_delivered + first_row.num_red_ml)
        total_green_ml = int(total_green_ml_delivered + first_row.num_green_ml)
        total_blue_ml = int(total_blue_ml_delivered + first_row.num_blue_ml)
        total_gold = int(first_row.gold - total_gold_spent)
    # update num_red_ml in DB
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {total_red_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {total_green_ml}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = {total_blue_ml}"))
    # update gold in DB
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {total_gold}"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    #initializing variables
    curr_gold = 0
    small_red_barrel_price = 0
    small_green_barrel_price = 0
    small_blue_barrel_price = 0
    # Checking gold in global_inventory
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        curr_gold = first_row.gold
    # Checking price and quantity of SMALL_RED|GREEN|BLUE_BARREL
    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            small_red_barrel_price = barrel.price
        elif barrel.sku == "SMALL_GREEN_BARREL":
            small_green_barrel_price = barrel.price
        elif barrel.sku == "SMALL_BLUE_BARREL":
            small_blue_barrel_price = barrel.price
    # Checking how many small red barrels I can buy
    # logic being: try to purchase one of each barrel, red -> green -> blue
    ret_arr = []
    if curr_gold >= small_red_barrel_price:
        ret_arr.append(
                {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
                })
    if curr_gold >= small_red_barrel_price + small_green_barrel_price:
        ret_arr.append(
                {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            })
    if curr_gold >= small_red_barrel_price + small_green_barrel_price + small_blue_barrel_price:
        ret_arr.append(
                {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
            })
    return ret_arr