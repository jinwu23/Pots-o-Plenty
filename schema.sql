create table
  public.global_inventory (
    gold integer generated by default as identity,
    red_ml integer null,
    green_ml bigint null,
    blue_ml bigint null,
    total_potions integer null,
    total_ml integer null,
    constraint global_inventory_pkey primary key (gold)
  ) tablespace pg_default;

insert into global_inventory (
    gold,
    total_potions,
    total_ml,
    num_red_ml,
    num_green_ml,
    num_blue_ml,
    num_red_potions,
    num_green_potions,
    num_blue_potions) 
values (100, 0, 0, 0, 0, 0, 0, 0, 0);

create table
  public.potions (
    id bigint generated by default as identity,
    sku text null,
    name text null,
    quantity integer null,
    price integer null,
    red integer null,
    green integer null,
    blue integer null,
    dark integer null,
    constraint potions_pkey primary key (id)
  ) tablespace pg_default;

insert into potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
values ("RED_POTION_100", "red potion", 0, 100, 100, 0, 0, 0);

insert into potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
values ("GREEN_POTION_100", "green potion", 0, 100, 0, 100, 0, 0);

insert into potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
values ("BLUE_POTION_100", "blue potion", 0, 100, 0, 0, 100, 0);

insert into potions (
    sku,
    name,
    quantity,
    price,
    red,
    green,
    blue,
    dark) 
values ("PURPLE_POTION_50_50", "blue potion", 0, 100, 50, 0, 50, 0);

create table
  public.carts (
    id bigint generated by default as identity,
    customer_name text null,
    constraint carts_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.cart_items (
    id bigint generated by default as identity,
    cart_id bigint null,
    sku text null,
    quantity integer null,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (id)
  ) tablespace pg_default;