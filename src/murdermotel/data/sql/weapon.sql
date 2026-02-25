--\echo weapon
create table if not exists murdermotel.component (
    componentid bigint unique,
    name citext
);

create table if not exists murdermotel.weapon (
--    weaponid bigint unique not null,
--    name citext unique not null,
--    module text,
--    state jsonb,
    component1 bigint constraint fk_weapon_component1 references murdermotel.component(componentid) on update cascade on delete cascade,
    component2 bigint constraint fk_weapon_component2 references murdermotel.component(componentid) on update cascade on delete cascade
) inherits (murdermotel.item);

create table if not exists murdermotel.map_weaponcomponent_player (
    componentid bigint constraint fk_map_component_id references murdermotel.component(componentid) on update cascade on delete cascade,
    playermoniker citext constraint fk_map_component_player references murdermotel.player(moniker) on update cascade on delete cascade
);

grant all on murdermotel.map_weaponcomponent_player to term, sysop;
