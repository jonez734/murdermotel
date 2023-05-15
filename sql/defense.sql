\echo defense
create table if not exists (
    defenseid bigint unique not null,
    name text,
    description text
);
