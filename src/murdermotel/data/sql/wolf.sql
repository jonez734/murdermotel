create table if not exists murdermotel.wolf (
    name citext unique not null,
    strength bigint,
    roomid bigint,
    healthpoints bigint default 35,
    constraint fk_wolf_npc foreign key (name) references murdermotel.npc(name) on update cascade on delete cascade
);

grant all on murdermotel.wolf to term, web, sysop;
