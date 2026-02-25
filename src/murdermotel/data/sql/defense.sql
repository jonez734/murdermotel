--\echo defense
create table if not exists murdermotel.defense (
--    defenseid bigint unique not null,
--    module text,
--    state jsonb,
--    name citext,
    description text
);

grant select on murdermotel.defense to web, term;
grant all on murdermotel.defense to sysop;
