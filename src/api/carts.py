from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from sqlalchemy import desc
from sqlalchemy import asc
from sqlalchemy import func
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    results = []
    previous = ""
    next = ""
    with db.engine.begin() as connection:
        # get all orders with Customer, Quantity, Item SKU, Time
        search_query = (sqlalchemy.select(
                db.cart_items.c.id,
                db.cart_items.c.timestamp,
                db.cart_items.c.quantity,
                db.carts.c.customer_name,
                db.potions.c.sku,
                (db.cart_items.c.quantity * db.potions.c.price).label('gold_paid'),
            ).select_from(db.cart_items)
        .join(db.carts, db.cart_items.c.cart_id == db.carts.c.id)
        .join(db.potions, db.cart_items.c.potion_id == db.potions.c.id)
        .where(db.cart_items.c.checked_out == True)
        )

        # determine sorting based on order by
        if sort_order == search_sort_order.asc:
            search_query = search_query.order_by(asc(sort_col))
        if sort_order == search_sort_order.desc:
            search_query = search_query.order_by(desc(sort_col))

        # determine sorting based on name and sku
        if customer_name != "":
            search_query = search_query.where(db.carts.c.customer_name.ilike(f"%{customer_name}%"))

        if potion_sku != "":
            search_query = search_query.where(db.potions.c.sku.ilike(f"%{potion_sku}%"))

        # get the result
        result = connection.execute(search_query)
        rows = result.fetchall()
        print(rows[0].sku)
        print(rows[1].sku)

        num_rows = len(rows)
        print(num_rows)

        # find our index on the table
        index = 0
        if search_page != "":
            index = int(search_page)
                    
        # see if we have a previous 
        if index >= 5:
            previous = str(index - 5)

        # see if we have more rows to display
        if num_rows > index + 5:
            next = str(index + 5)
            # we can display 5 rows 
            for i in range(index, index + 5):
                print(i)
                curr_row = rows[i]
                if curr_row is not None:
                    results.append({
                        "line_item_id": curr_row.id,
                        "item_sku": curr_row.sku,
                        "customer_name": curr_row.customer_name,
                        "line_item_total": curr_row.gold_paid,
                        "timestamp": curr_row.timestamp,
                    })
        else:
            # figure out how many rows we can display and add all to results
            displayable_rows = num_rows - index
            for i in range(index, index + displayable_rows):
                print(i)
                curr_row = rows[i]
                if curr_row is not None:
                    results.append({
                        "line_item_id": curr_row.id,
                        "item_sku": curr_row.sku,
                        "customer_name": curr_row.customer_name,
                        "line_item_total": curr_row.gold_paid,
                        "timestamp": curr_row.timestamp,
                    })
        
    return {
        "previous": previous,
        "next": next,
        "results": results,
    }


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
                WHERE cart_id = :cart_id AND checked_out = false
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
            # set checked_out to true for cart_items
            connection.execute(sqlalchemy.text(
                """
                UPDATE cart_items
                SET checked_out = true
                WHERE cart_id = :cart_id
                """),
                [{"cart_id": cart_id}])
            # set in_checkout to false for cart_items
            connection.execute(sqlalchemy.text(
            """
            UPDATE carts
            SET in_checkout = false
            WHERE id = :cart_id
            """), [{"cart_id": cart_id}])
            print(f"checkout, cart_id: {cart_id}")

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
