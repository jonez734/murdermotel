--\echo weapon_recipe
create table if not exists murdermotel.weapon_recipe (
    name        citext primary key,
    title       text,
    component1  citext not null,
    component2  citext not null,
    count       int not null default 6,
    usemessages text[],
    state       jsonb
);

grant select on murdermotel.weapon_recipe to web, term;
grant all on murdermotel.weapon_recipe to sysop;