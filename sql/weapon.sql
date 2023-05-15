\echo weapon
create table if not exists murdermotel.weapon (
    weaponid bigint unique not null,
    name text unique not null,
    component1 bigint constraint fk_weapon_component1 references murdermotel.component(componentid) on update cascade on delete cascade,
    component2 bigint constraint fk_weapon_component1 references murdermotel.component(componentid) on update cascade on delete cascade
);

create table if not exists murdermotel.component (
    componentid bigint,
    name text
);

create table if not exists murdermotel.map_weaponcomponent_player (
    componentid bigint constraint fk_map_component_id references murdermotel.component(componentid) on update cascade on delete cascade,
    playername text constraint fk_map_component_player references murdermotel.player(name) on update cascade on delete cascade
);

--create table if not exists murdermotel.map_
