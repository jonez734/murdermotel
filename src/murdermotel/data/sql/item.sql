--\echo item
create table if not exists murdermotel.item (
    "name" citext not null,
    "kind" text not null check (kind in ('component', 'defense', 'boobytrap', 'item', 'weapon')),
    "serial" int not null default 0,
    "title" text,
    "modulepath" text,
    "state" jsonb,
    "usemessages" text[]
);

create index idx_item_name on murdermotel.item(name);
create unique index idx_item_name_serial on murdermotel.item(name, serial);

--\echo map_item_player
create table if not exists murdermotel.map_item_player (
    itemname citext,
    serial int not null default 0,
    playermoniker citext constraint fk_map_item_player references murdermotel.player(moniker) on update cascade on delete cascade
);

create unique index idx_map_item_player on murdermotel.map_item_player(itemname, serial, playermoniker);

--\echo map_item_room
create table if not exists murdermotel.map_item_room (
    itemname citext,
    serial int not null default 0,
    roomid bigint constraint fk_map_item_player references murdermotel.playground(id) on update cascade on delete cascade
);

create unique index idx_map_item_room on murdermotel.map_item_room(itemname, serial, roomid);
