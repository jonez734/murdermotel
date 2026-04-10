create table if not exists murdermotel.boobytrap (
    name citext unique not null,
    running bool,
    timer bigint,
    constraint fk_boobytrap_item foreign key (name) references murdermotel.item(name) on update cascade on delete cascade
);
