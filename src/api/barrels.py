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
    # get total number of red_ml we purchased and gold spent
    total_red_ml_delivered = 0
    total_gold_spent = 0
    for barrel in barrels_delivered:
        total_red_ml_delivered += barrel.ml_per_barrel
        total_gold_spent += barrel.price
    # add current num_red_ml with red_ml_delivered
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        total_red_ml = total_red_ml_delivered + first_row.num_red_ml
        total_gold = first_row.gold - total_gold_spent
    # update num_red_ml in DB
        result = connection.execute(sqlalchemy.text("UPDATE * SET num_red_ml = " + total_red_ml))
    # update gold in DB
        result = connection.execute(sqlalchemy.text("UPDATE * SET gold = " + total_gold))
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    # Checking gold in global_inventory
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        curr_gold = first_row.gold
    # Checking price and quantity of SMALL_RED_BARREL
    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            small_red_barrel_price = barrel.price
            small_red_barrel_quantity = barrel.quantity
    # Checking how many small red barrels I can buy
    purchasable_barrels = curr_gold / small_red_barrel_price
    # Check if we can buy entire stock
    if purchasable_barrels > small_red_barrel_quantity:
        purchasable_barrels = small_red_barrels_quantity
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": purchasable_barrels,
        }
    ]
