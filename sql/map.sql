\echo map
create table if not exists homicidehotel.map (
    id bigint unique not null,
    shortname text unique not null primary key,
    description text,
    east text constraint fk_map_east references homicidehotel.map(shortname) on update cascade on delete set null,
    north text constraint fk_map_north references homicidehotel.map(shortname) on update cascade on delete set null,
    west text constraint fk_map_west references homicidehotel.map(shortname) on update cascade on delete set null,
    south text constraint fk_map_south references homicidehotel.map(shortname) on update cascade on delete set null,
    up text constraint fk_map_up references homicidehotel.map(shortname) on update cascade on delete set null,
    down text constraint fk_map_down references homicidehotel.map(shortname) on update cascade on delete set null
);


    