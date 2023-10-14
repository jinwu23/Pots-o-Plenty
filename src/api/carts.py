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
    # add new row into carts table and get generated id
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "INSERT INTO carts (customer_name) VALUES (:customer_name) RETURNING id"
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
    total_potions_bought = 0
    total_gold_paid = 0
    with db.engine.begin() as connection:
        # get all cart_items associated with cart_id
        result = connection.execute(sqlalchemy.text(
            """
            SELECT cart_id, potion_id, cart_items.quantity, price
            FROM cart_items
            JOIN potions ON cart_items.potion_id = potions.id
            WHERE cart_id = :cart_id
            """),
            [{"cart_id": cart_id}])
        # perform operations based on each item
        for row in result:
            # update gold_paid and potions_bought
            gold_paid = row.quantity * row.price
            potions_bought = row.quantity
            total_gold_paid += gold_paid
            total_potions_bought += potions_bought
            # update global_inventory with new gold and total_potions
            connection.execute(sqlalchemy.text(
                """
                UPDATE global_inventory
                SET 
                gold = gold + :gold_paid,
                total_potions = total_potions - :potions_bought
                """),
                [{"gold_paid": gold_paid, "potions_bought": potions_bought}])
            # update potion inventory with new potion quantities
            connection.execute(sqlalchemy.text(
                """
                UPDATE potions
                SET quantity = quantity - :potions_bought
                WHERE id = :potion_id
                """),
                [{"potions_bought": potions_bought, "potion_id": row.potion_id}])
            # removing cart from carts and cart_items
            connection.execute(sqlalchemy.text(
                """
                DELETE FROM cart_items
                WHERE cart_id = :cart_id
                """),
                [{"cart_id": cart_id}])
            connection.execute(sqlalchemy.text(
                """
                DELETE FROM carts
                WHERE id = :cart_id
                """),
                [{"cart_id": cart_id}])
            print(f"checkout, cart_id: {cart_id}, potion_id = {row.potion_id}")

    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}
