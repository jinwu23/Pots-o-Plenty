from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        # check if customer has already created a cart
        result = connection.execute(sqlalchemy.text(
            "SELECT count(*) FROM carts WHERE customer_name = :customer_name"
            ),
            [{"customer_name": new_cart.customer}])
        # customer has no entry in the carts table
        if(result.scalar_one() == 0):
            # add new row into carts table and get generated id
            result = connection.execute(sqlalchemy.text(
                "INSERT INTO carts (customer_name) VALUES (:customer_name) RETURNING id"
                ),
                [{"customer_name": new_cart.customer}])
            id = result.scalar_one()
        # customer has entry in the carts table
        else:
            result = connection.execute(sqlalchemy.text(
                "SELECT id FROM carts WHERE customer_name = :customer_name"
                ),
                [{"customer_name": new_cart.customer}])
            id = result.scalar_one()
    return {"cart_id": id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print(f"setting cart quantity: cart_id: {cart_id} item_sku: + {item_sku} quantity: {cart_item.quantity}")
    # check if row with cart_id and item_sku already exist in table
    with db.engine.begin() as connection:
        # check if row exists in cart_items table
        result = connection.execute(sqlalchemy.text(
            """
            SELECT COUNT(*)
            FROM cart_items
            WHERE cart_id = :cart_id and potion_id = (
            SELECT id
            FROM potions
            WHERE sku = :item_sku
            )     
            """),
        [{"cart_id": cart_id, "item_sku": item_sku}])
        count = result.scalar()
        if count != 0:
            # update cart_items table with new item and quantity
            connection.execute(sqlalchemy.text(
                """
                UPDATE cart_items
                SET quantity = :quantity
                WHERE cart_id = :cart_id and potion_id = (SELECT id FROM potions WHERE sku = :item_sku)
                """),
                [{"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity}])
        else:
            # create a new entry for specific cart quantity and sku
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO cart_items
                (cart_id, potion_id, quantity)
                VALUES
                (:cart_id, (SELECT id FROM potions WHERE sku = :item_sku), :quantity)          
                """),
                [{"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity}])
        
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    gold_ledger_entities = []
    potion_ledger_entities = []
    total_potions_bought = 0
    total_gold_paid = 0
    with db.engine.begin() as connection:
        # check if checkout is already happening 
        result = connection.execute(sqlalchemy.text(
        """
        SELECT in_checkout
        FROM carts
        WHERE id = :cart_id
        """), [{"cart_id": cart_id}])
        in_checkout = result.first().in_checkout
        if(in_checkout == False):
            # set in_checkout to true
            result = connection.execute(sqlalchemy.text(
            """
            UPDATE carts
            SET in_checkout = true
            WHERE id = :cart_id
            """), [{"cart_id": cart_id}])
            # get all cart_items associated with cart_id
            result = connection.execute(sqlalchemy.text(
                """
                SELECT cart_id, potion_id, cart_items.quantity, price
                FROM cart_items
                JOIN potions ON cart_items.potion_id = potions.id
                WHERE cart_id = :cart_id
                """),
                [{"cart_id": cart_id}])
            # create ledger entity for each cart_item
            for row in result:
                gold_paid = row.quantity * row.price
                potions_bought = row.quantity
                total_gold_paid += gold_paid
                total_potions_bought += potions_bought
                gold_ledger_entities.append({"gold_paid": gold_paid, "cart_id": cart_id, "potion_id": row.potion_id, "potions_bought": potions_bought})
                potion_ledger_entities.append({"potions_bought": -potions_bought, "potion_id": row.potion_id, "cart_id": cart_id})
            
            # insert all gold ledger entities
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO gold_ledger_entities
                (gold_change, description)
                VALUES
                (:gold_paid, 'cart checkout id =:cart_id potion_type = :potion_id potions_bought = :potions_bought')          
                """), gold_ledger_entities)
            # insert all potion ledger entities
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO potion_ledger_entities
                (potion_change, potion_id, description)
                VALUES
                (:potions_bought,:potion_id,'cart checkout id = :cart_id')          
                """), potion_ledger_entities)
            # removing cart_items
            connection.execute(sqlalchemy.text(
                """
                DELETE FROM cart_items
                WHERE cart_id = :cart_id
                """),
                [{"cart_id": cart_id}])
            # set in_checkout to false
            connection.execute(sqlalchemy.text(
            """
            UPDATE carts
            SET in_checkout = false
            WHERE id = :cart_id
            """), [{"cart_id": cart_id}])
            print(f"checkout, cart_id: {cart_id}")

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
