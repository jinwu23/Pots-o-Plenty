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
# carts is a dictionary from cart_id to dictionary of item_sku to quantity
carts = {}

class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    # set customer cart_id and increment running_cart_id
    global running_cart_id
    cart_id = running_cart_id
    running_cart_id += 1
    carts[cart_id] = {}
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
    carts[cart_id].update({item_sku : cart_item.quantity})
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # obtaining sku of item bought
    with db.engine.begin() as connection:
        for checkout_sku in carts[cart_id].keys():
            # obtain quantity of potion
            result = connection.execute(sqlalchemy.text(f"SELECT * FROM potions WHERE sku = {checkout_sku}"))
            first_row = result.first()
            potion_quantity = first_row.quantity
            # updating potion count in potions table
            connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity = {potion_quantity - carts[cart_id][checkout_sku]} WHERE sku = {checkout_sku}"))
            if checkout_sku == "RED_POTION_100":
                total_red_potions_bought = carts[cart_id][checkout_sku]
            if checkout_sku == "GREEN_POTION_100":
                total_green_potions_bought = carts[cart_id][checkout_sku]
            if checkout_sku == "BLUE_POTION_100":
                total_blue_potions_bought = carts[cart_id][checkout_sku]
            if checkout_sku == "PURPLE_POTION_50_50":
                total_purple_potions_bought = carts[cart_id][checkout_sku]
        total_potions_bought = total_red_potions_bought + total_green_potions_bought + total_blue_potions_bought + total_purple_potions_bought
        total_gold_paid = total_potions_bought * 50
        # obtaining gold and num_potions in global_inventory
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        new_gold = first_row.gold + total_gold_paid
        new_num_potions = first_row.total_potions - total_potions_bought
        print(f"checking out cart quantity: cart_id: {cart_id} | total_quantity: {total_potions_bought} | global_inventory_gold_before_checkout: {first_row.gold} | global_inventory_potions_before_checkout: {first_row.total_potions}")
        # updating global_inventory with new amounts
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {new_gold}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET total_potions = {new_num_potions}"))
        print(f"checking out cart quantity: cart_id: {cart_id} | new_global_inventory_gold = {new_gold} | new_global_inventory_num_potions = {new_num_potions}")
        # removing cart from table
        carts.pop(cart_id)
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
