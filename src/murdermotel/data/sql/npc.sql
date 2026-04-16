create table murdermotel.npc (
    name   citext unique not null,
    kind   text not null,
    modulepath text,
    title  text,
    roomid bigint constraint fk_map_item_player references murdermotel.playground(id) on update cascade on delete cascade,
    state  jsonb,
    is_bot boolean DEFAULT false,
    target text,
    targetedby text,
    is_alive boolean DEFAULT true
);

-- Migrate: rename old 'module' column to 'modulepath' if it exists
do $$
begin
    if exists (
        select 1 from information_schema.columns
        where table_schema='murdermotel' and table_name='npc' and column_name='module'
    ) then
        alter table murdermotel.npc rename column module to modulepath;
    end if;
end$$;
alter table if exists murdermotel.npc add column if not exists modulepath text;

-- Migrate: add bot-related columns if they don't exist
alter table if exists murdermotel.npc add column if not exists is_bot boolean DEFAULT false;
alter table if exists murdermotel.npc add column if not exists target text;
alter table if exists murdermotel.npc add column if not exists targetedby text;
alter table if exists murdermotel.npc add column if not exists is_alive boolean DEFAULT true;
