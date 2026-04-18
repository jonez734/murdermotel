--\echo defense
create table if not exists murdermotel.defense (
    name citext not null,
    serial int not null default 0,
    description text,
    unique (name, serial)
);

grant select on murdermotel.defense to web, term;
grant all on murdermotel.defense to sysop;
