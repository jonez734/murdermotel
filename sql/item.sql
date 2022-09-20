\echo item
create table murdermotel.item if not exists (
    itemid bigint unique not null,
    type text not null,
    name text,
    description text,
    usemessage text
);

create table murdermotel.map_item_player (
    itemid bigint constraint fk_map_item_room references item(itemid) on update cascade on delete cascade,
    playername text constraint fk_map_item_player references player(name) on update cascade on delete cascade
);

create unique index idx_map_item_player on murdermotel.map_item_player(itemid, playername);

create table murdermotel.map_item_room (
    itemid bigint constraint fk_map_item_room references item(itemid) on update cascade on delete cascade,
    roomid bigint constraint fk_map_item_player references room(id) on update cascade on delete cascade
);

create unique index idx_map_item_room on murdermotel.map_item_player(itemid, roomid);
