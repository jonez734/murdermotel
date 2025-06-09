--\echo item
create table if not exists murdermotel.item (
    "type" text not null,
    "name" text unique not null primary key,
    "title" text,
    "usemessages" text[]
);

\echo map_item_player
create table if not exists murdermotel.map_item_player (
    itemname text,
    playermoniker text constraint fk_map_item_player references murdermotel.player(moniker) on update cascade on delete cascade
);

create unique index idx_map_item_player on murdermotel.map_item_player(itemname, playermoniker);

\echo map_item_room
create table if not exists murdermotel.map_item_room (
    itemname text, -- constraint fk_map_item_room references murdermotel.item(name) on update cascade on delete cascade,
    roomid bigint constraint fk_map_item_player references murdermotel.playground(roomid) on update cascade on delete cascade
);

create unique index idx_map_item_room on murdermotel.map_item_player(itemname, playermoniker);
