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

# keeping track of cart_ids in use and carts
running_cart_id = 1
carts = {}

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
    print(f"setting cart quantity: cart_id: {cart_id} item_sku: + {item_sku} quantity: {cart_item.quantity}")
    # update carts table with new quantity
    carts[cart_id] = Cart(cart_item.quantity, item_sku)
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # obtaining item quantity and expected payment
    total_potions_bought = carts[cart_id].quantity
    total_gold_paid = total_potions_bought * 50
    with db.engine.begin() as connection:
        # obtaining gold and num_potions in global_inventory
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        new_global_inventory_gold = first_row.gold + total_gold_paid
        new_global_inventory_num_potions = first_row.num_red_potions - total_potions_bought
        print(f"checking out cart quantity: cart_id: {cart_id} | item_sku: RED_POTION_0 | quantity: {total_potions_bought} | global_inventory_gold_before_checkout: {first_row.gold} | global_inventory_potions_before_checkout: {first_row.num_red_potions}")
        # updating global_inventory with new amounts
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {new_global_inventory_gold}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {new_global_inventory_num_potions}"))
        print(f"checking out cart quantity: cart_id: {cart_id} | new_global_inventory_gold = {new_global_inventory_gold} | new_global_inventory_num_potions = {new_global_inventory_num_potions}")
        # removing cart from table
        carts.pop(cart_id)
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
