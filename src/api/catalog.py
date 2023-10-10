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
    ret_arr = []
    with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
            for row in result:
                 if row.quantity > 0:
                    ret_arr.append(
                            {
                                "sku": row.sku,
                                "name": row.name,
                                "quantity": row.quantity,
                                "price": row.price,
                                "potion_type": [row.red, row.green, row.blue, row.dark]
                            })
    print(f"Catalog: {ret_arr}")
    return ret_arr
