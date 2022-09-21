\echo item
create table if not exists murdermotel.item (
    "type" text not null,
    "name" text unique not null primary key,
    "title" text,
    "description" text,
    "usemessages" text[]
);

create table if not exists murdermotel.map_item_player (
    itemid bigint,
    playername text constraint fk_map_item_player references murdermotel.player(name) on update cascade on delete cascade
);

create unique index idx_map_item_player on murdermotel.map_item_player(itemid, playername);

create table if not exists murdermotel.map_item_room (
    itemid bigint constraint fk_map_item_room references murdermotel.item(itemid) on update cascade on delete cascade,
    roomid bigint constraint fk_map_item_player references murdermotel.playground(roomid) on update cascade on delete cascade
);

create unique index idx_map_item_room on murdermotel.map_item_player(itemid, playername);
