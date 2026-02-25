create table murdermotel.npc (
    name   citext unique not null,
    module text,
    title  text,
    roomid bigint constraint fk_map_item_player references murdermotel.playground(id) on update cascade on delete cascade,
    state  jsonb
);
