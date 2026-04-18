-- npc_player_items.sql
-- Items carried by bot NPCs

create table murdermotel.npc_player_items (
    npcmoniker citext not null references murdermotel.npc(name) on delete cascade,
    itemname   citext not null,
    primary key (npcmoniker, itemname)
);