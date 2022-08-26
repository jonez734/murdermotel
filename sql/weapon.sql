\echo weapon
create table if not exists murdermotel.weapon (
    weaponid bigint unique not null,
    name text unique not null,
    pair bigint constraint fk_weapon_pairid references murdermotel.weapon(weaponid) on update cascade on delete cascade
);
