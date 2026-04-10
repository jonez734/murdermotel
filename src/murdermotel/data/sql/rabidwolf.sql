create table if not exists murdermotel.rabidwolf (
    name citext unique not null,
    strength bigint,
    roomid bigint,
    healthpoints bigint default 35,
    constraint fk_rabidwolf_npc foreign key (name) references murdermotel.npc(name) on update cascade on delete cascade
);

grant all on murdermotel.rabidwolf to term, web, sysop;
