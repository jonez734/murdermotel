create table if not exists murdermotel.player (
    moniker citext unique not null,
    roomid bigint,
    turn bigint,
    moves bigint,
    bodycount bigint,
    points bigint,
    died bigint,
    modulepath text,
    membermoniker citext constraint fk_mm_player_membermoniker references engine.__member(moniker) on update cascade on delete set null,
    datelastplayed timestamptz,
    datecreated timestamptz,
    target text,
    targetedby text
);

grant all on murdermotel.player to term, web, sysop;

-- Migrate: add target columns if they don't exist
alter table if exists murdermotel.player add column if not exists target text;
alter table if exists murdermotel.player add column if not exists targetedby text;
