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

# keeping track of cart_ids in use
running_cart_id = 1

# class to keep quantity and item_sku of carts together
class Cart:
    def __init__(self, quantity, item_sku):
        self.quantity = quantity
        self.item_sku = item_sku

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    # set customer cart_id and increment running_cart_id
    global running_cart_id
    cart_id = running_cart_id
    running_cart_id += 1
    # create a new row on carts table with the cart
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO carts (id, item_sku, quantity) VALUES ("+ str(cart_id) +", 'RED_POTION_0', 0)"))
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print("setting cart quantity: cart_id: " + str(cart_id) + " item_sku: + " + str(item_sku) + " quantity: " + str(cart_item.quantity))

    # update carts table with new quantity
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE carts SET quantity = "+ str(cart_item.quantity) +" WHERE id = " + str(cart_id)))
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # obtaining item quantity and expected payment
    total_potions_bought = 0
    total_gold_paid = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM carts WHERE id = " + str(cart_id)))
        first_row = result.first()
        customer_quantity = first_row.quantity
        expected_payment = customer_quantity * 50
        total_potions_bought = customer_quantity
        total_gold_paid = expected_payment
        # obtaining gold and num_potions in global_inventory
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        global_inventory_gold = first_row.gold
        global_inventory_num_potions = first_row.num_red_potions
        new_global_inventory_gold = global_inventory_gold + total_gold_paid
        new_global_inventory_num_potions = global_inventory_num_potions - total_potions_bought
        print("checking out cart quantity: cart_id: " + str(cart_id) + " | item_sku: RED_POTION_0 | quantity: " + str(customer_quantity) + " | global_inventory_gold_before_checkout: " + str(global_inventory_gold) + " | global_inventory_potions_before_checkout: " + str(global_inventory_num_potions))
        # updating global_inventory with new amounts
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(new_global_inventory_gold)))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = " + str(new_global_inventory_num_potions)))
        print("checking out cart quantity: cart_id: " + str(cart_id) + " | new_global_inventory_gold = "+ str(new_global_inventory_gold)+ "| new_global_inventory_num_potions = "+ str(new_global_inventory_num_potions) )
        # removing the cart from the table
        connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = " + str(cart_id)))
        
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
