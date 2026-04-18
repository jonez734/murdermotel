--\echo weapon
create table if not exists murdermotel.component (
    componentid bigint unique,
    name citext
);

create table if not exists murdermotel.weapon (
    name citext unique not null,
    component1 bigint,
    component1_serial int not null default 0,
    component2 bigint,
    component2_serial int not null default 0,
    constraint fk_weapon_component1 foreign key (component1, component1_serial) references murdermotel.item(name, serial) on update cascade on delete cascade,
    constraint fk_weapon_component2 foreign key (component2, component2_serial) references murdermotel.item(name, serial) on update cascade on delete cascade,
    constraint fk_weapon_item foreign key (name) references murdermotel.item(name, serial) on update cascade on delete cascade
);

create table if not exists murdermotel.map_weaponcomponent_player (
    componentid bigint,
    component_serial int not null default 0,
    playermoniker citext constraint fk_map_component_player references murdermotel.player(moniker) on update cascade on delete cascade
);

create unique index idx_map_weaponcomponent_player on murdermotel.map_weaponcomponent_player(componentid, component_serial, playermoniker);

grant all on murdermotel.map_weaponcomponent_player to term, sysop;
