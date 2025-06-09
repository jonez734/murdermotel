--\echo defense
create table if not exists (
    defenseid bigint unique not null,
    name text,
    description text
);

grant all on murdermotel.defense to web, term, sysop;
