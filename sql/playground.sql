\echo playground
create table if not exists murdermotel.playground (
    roomid bigint unique not null primary key,
    shortname text unique,
    title text unique not null,
    description text,
    east bigint, --constraint fk_playground_east references murdermotel.playground(roomid) on update cascade on delete set null,
    north bigint, --constraint fk_playground_north references murdermotel.playground(roomid) on update cascade on delete set null,
    west bigint, --constraint fk_playground_west references murdermotel.playground(roomid) on update cascade on delete set null,
    south bigint, --constraint fk_playground_south references murdermotel.playground(roomid) on update cascade on delete set null,
    up bigint, --constraint fk_playground_up references murdermotel.playground(roomid) on update cascade on delete set null,
    down bigint --constraint fk_playground_down references murdermotel.playground(roomid) on update cascade on delete set null
);
