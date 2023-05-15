create table if not exists murdermotel.player (
    name text unique not null,
    roomid bigint,
    turn bigint,
    moves bigint,
    bodycount bigint,
    points bigint,
    memberid bigint constraint fk_mm_player_memberid references engine.__member(id) on update cascade on delete set null,
    datelastplayed timestamptz
);
