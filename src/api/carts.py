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

# dictionary to store each cart to cart_id
total_carts = {}
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
    global running_cart_id
    cart_id = running_cart_id
    running_cart_id += 1
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
    global total_carts
    total_carts.update({cart_id : Cart(cart_item.quantity, item_sku)})
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    global total_carts
    # obtaining item quantity, item_sku and expected payment
    item_quantity = total_carts[cart_id].quantity
    item_sku = total_carts[cart_id].item_sku
    expected_payment = item_quantity * 50
    # checking for red potion purchase
    if item_sku == "RED_POTION_0":
        with db.engine.begin() as connection:
            # figuring out new gold and red potion count
            result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
            first_row = result.first()
            total_gold = first_row.gold + expected_payment
            total_red_potions =  first_row.num_red_potions - item_quantity
            # update gold and potion count in DB
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(int(total_gold))))
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = " + str(int(total_red_potions))))
    # deleting cart from dictionary
    total_carts.pop(cart_id)

    return {"total_potions_bought": int(item_quantity), "total_gold_paid": int(expected_payment)}
