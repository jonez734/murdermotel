create table murdermotel.npc (
    name   citext unique not null,
    module text,
    title  text,
    roomid bigint,
    state  jsonb
);
