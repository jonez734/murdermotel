--\echo item
create table if not exists murdermotel.item (
    "name" citext unique not null primary key,
    "kind" text not null check (kind in ('component', 'defense', 'boobytrap', 'item')),
    "title" text,
    "module" text,
    "state" jsonb,
    "usemessages" text[]
);

--\echo map_item_player
create table if not exists murdermotel.map_item_player (
    itemname citext,
    playermoniker citext constraint fk_map_item_player references murdermotel.player(moniker) on update cascade on delete cascade
);

create unique index idx_map_item_player on murdermotel.map_item_player(itemname, playermoniker);

--\echo map_item_room
create table if not exists murdermotel.map_item_room (
    itemname citext, -- constraint fk_map_item_room references murdermotel.item(name) on update cascade on delete cascade,
    roomid bigint constraint fk_map_item_player references murdermotel.playground(id) on update cascade on delete cascade
);

create unique index idx_map_item_room on murdermotel.map_item_player(itemname, playermoniker);
