CREATE TABLE global_inventory (
    gold int,
    total_potions int,
    total_ml int,
    num_red_ml int,
    num_green_ml int,
    num_blue_ml int,
    num_red_potions int,
    num_green_potions int,
    num_blue_potions int
);

INSERT INTO global_inventory (
    gold,
    total_potions,
    total_ml,
    num_red_ml,
    num_green_ml,
    num_blue_ml,
    num_red_potions,
    num_green_potions,
    num_blue_potions) 
VALUES (100, 0, 0, 0, 0, 0, 0, 0, 0);

CREATE TABLE potions(
    sku: text,
    name: text,
    quantity: int,
    price: int,
    red: int,
    green: int,
    blue: int,
    dark: int
);

INSERT INTO potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
VALUES ("RED_POTION_100", "red potion", 0, 100, 100, 0, 0, 0);

INSERT INTO potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
VALUES ("GREEN_POTION_100", "green potion", 0, 100, 0, 100, 0, 0);

INSERT INTO potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
VALUES ("BLUE_POTION_100", "blue potion", 0, 100, 0, 0, 100, 0);

INSERT INTO potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
VALUES ("PURPLE_POTION_50_50", "blue potion", 0, 100, 50, 0, 50, 0);