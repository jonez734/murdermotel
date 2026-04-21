create table if not exists murdermotel.boobytrap (
    name citext not null,
    serial int not null default 1,
    running bool,
    timer bigint,
    constraint fk_boobytrap_item foreign key (name, serial) references murdermotel.item(name, serial) on update cascade on delete cascade,
    constraint pk_boobytrap primary key (name, serial)
);

create unique index idx_boobytrap_name on murdermotel.boobytrap(name);
