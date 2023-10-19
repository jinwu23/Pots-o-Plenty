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
    for barrel in barrels_delivered:
        potion_type = ""
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0
        if(barrel.potion_type == [1,0,0,0]):
            potion_type = 'red'
            red_ml = barrel.ml_per_barrel * barrel.quantity
        if(barrel.potion_type == [0,1,0,0]):
            potion_type = 'green'
            green_ml = barrel.ml_per_barrel * barrel.quantity
        if(barrel.potion_type == [0,0,1,0]):
            potion_type = 'blue'
            blue_ml = barrel.ml_per_barrel * barrel.quantity
        if(barrel.potion_type == [0,0,0,1]):
            potion_type = 'dark'
            dark_ml = barrel.ml_per_barrel * barrel.quantity
        # insert ml_ledger_entity
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO ml_ledger_entities
                (red_change, green_change, blue_change, dark_change, description)
                VALUES
                (:red_change, :green_change, :blue_change, :dark_change, 'barrel delivery: price = :price, quantity = :quantity')          
                """),
                [{"red_change": red_ml, "green_change": green_ml, "blue_change": blue_ml, "dark_change": dark_ml, "potion_type": potion_type, "price": barrel.price, "quantity": barrel.quantity}])
        # insert gold_ledger_entity
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO gold_ledger_entities
                (gold_change, description)
                VALUES
                (:gold_change, CONCAT('barrel delivery: potion_type = ', :potion_type, ', price = :price, quantity = :quantity'))          
                """),
                [{"gold_change": -(barrel.quantity * barrel.price), "potion_type": potion_type, "price": barrel.price, "quantity": barrel.quantity}])
        
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    ret_arr = []
    # Checking gold in global_inventory
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold_change),0) FROM gold_ledger_entities"))
        gold = result.scalar_one()
    # Checking price and quantity of BARRELS
    # buying one of each barrel
    for barrel in wholesale_catalog:
        if gold >= barrel.price:
            ret_arr.append(
                {
                "sku": barrel.sku,
                "quantity": 1,
                })
            gold = gold - barrel.price
    return ret_arr