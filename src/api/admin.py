from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.delete(db.cart_items),
            sqlalchemy.delete(db.gold_ledger_entities),
            sqlalchemy.delete(db.ml_ledger_entities),
            sqlalchemy.delete(db.potion_ledger_entities),
            )
        connection.execute(
            sqlalchemy.insert(db.gold_ledger_entities).values(gold_change = 100, description = "intitial population")
        )
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potions o' Plenty",
        "shop_owner": "Jin Wu",
    }

