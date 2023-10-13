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
    red_ml_delivered = 0
    green_ml_delivered = 0
    blue_ml_delivered = 0
    gold_spent = 0
    total_ml_delivered = 0
    for barrel in barrels_delivered:
        if(barrel.sku == "SMALL_RED_BARREL"):
            red_ml_delivered += barrel.ml_per_barrel * barrel.quantity
        if(barrel.sku == "SMALL_GREEN_BARREL"):
            green_ml_delivered += barrel.ml_per_barrel * barrel.quantity    
        if(barrel.sku == "SMALL_BLUE_BARREL"):
            blue_ml_delivered += barrel.ml_per_barrel * barrel.quantity
        gold_spent += barrel.price * barrel.quantity
        total_ml_delivered += barrel.ml_per_barrel * barrel.quantity
    # add current ml with ml_delivered
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("""
                UPDATE global_inventory SET 
                gold = gold - :gold_spent,
                total_ml = total_ml + :total_ml_delivered,
                red_ml = red_ml + :red_ml_delivered,
                green_ml = green_ml + :green_ml_delivered,
                blue_ml = blue_ml + :blue_ml_delivered
            """), 
            [{"gold_spent": gold_spent, "red_ml_delivered": red_ml_delivered, "green_ml_delivered": green_ml_delivered, "blue_ml_delivered": blue_ml_delivered, "total_ml_delivered": total_ml_delivered}])
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