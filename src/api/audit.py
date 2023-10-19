from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(gold_change),0) FROM gold_ledger_entities"))
        gold = result.scalar_one()
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(potion_change),0) FROM potion_ledger_entities"))
        potions = result.scalar_one()
        result = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(red_change + green_change + blue_change + dark_change),0) FROM ml_ledger_entities"))
        ml = result.scalar_one()
        
        print(f"audit_gold: {gold}, audit_potions: {potions}, audit_ml: {ml}")

    return {"number_of_potions": potions, "ml_in_barrels": ml, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
