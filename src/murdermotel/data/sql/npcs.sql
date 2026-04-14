-- npcs.sql
-- Seed data for murdermotel.npc table
insert into murdermotel.npc (name, kind, title, modulepath, state) values
    ('thief',     'thief', 'The Sneaky Thief', 'thief',     '{}'),
    ('rabidwolf', 'wolf',  'Rabid Wolf',        'rabidwolf', '{}')
on conflict (name) do nothing;
