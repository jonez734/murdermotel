create table if not exists murdermotel.thief (
    name citext unique not null,
    bag citext[],
    roomid bigint,
    healthpoints bigint default 35,
    constraint fk_thief_npc foreign key (name) references murdermotel.npc(name) on update cascade on delete cascade
);

grant all on murdermotel.thief to term, web, sysop;

-- map items to thief (like map_item_player)
create table if not exists murdermotel.map_item_thief (
    itemname citext not null,
    thiefname citext not null default 'thief',
    constraint fk_map_item_thief foreign key (thiefname) references murdermotel.thief(name) on update cascade on delete cascade
);

create unique index idx_map_item_thief on murdermotel.map_item_thief(itemname, thiefname);
grant all on murdermotel.map_item_thief to term, web, sysop;
