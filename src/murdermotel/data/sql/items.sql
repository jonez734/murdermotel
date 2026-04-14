-- items.sql
-- Seed data for murdermotel.item table
insert into murdermotel.item (name, kind, title, modulepath, usemessages, state) values
    ('axeblade',        'component', 'axe blade',         null, array['You swing the axe with all your might and slaughter', 'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], '{}'),
    ('pistol',          'component', 'pistol',             null, array['You take aim.. pull the trigger.. and waste', 'BANG! BANG! You gun down the vermin called', 'You take aim and shoot'], '{}'),
    ('chlorinegas',     'component', 'chlorine gas',       null, array['The noxious fumes spread from the sprayer and poison', 'The chlorine spews out and asphyxiates your mortal enemy', 'You gas'], '{}'),
    ('flamethrower',    'component', 'flame thrower',      null, array['You barbecue', 'You pull out your flame thrower and fry', 'Heat and light burst from the flame gun as you cook'], '{}'),
    ('industrialacid',  'component', 'industrial acid',    null, array['You boil away', 'You pump the acid sprayer furiously and disolve', 'The acid hisses from the nozzle of your sprayer. It liquifies'], '{}'),
    ('axehandle',       'component', 'axe handle',         null, null, '{}'),
    ('bullets',         'component', 'bullets',            null, null, '{}'),
    ('gassprayer',      'component', 'gas sprayer',        null, null, '{}'),
    ('lighterfluid',    'component', 'lighter fluid',      null, null, '{}'),
    ('acidsprayer',     'component', 'acid sprayer',       null, null, '{}'),
    ('riotshield',      'defense',   'riot shield',        null, null, '{}'),
    ('flakjacket',      'defense',   'flak jacket',        null, null, '{}'),
    ('gasmask',         'defense',   'gas mask',           null, null, '{}'),
    ('fireextinguisher','defense',   'fire extinguisher',  null, null, '{}'),
    ('lye',             'defense',   'lye',                null, null, '{}'),
    ('boobytrap',       'boobytrap', 'booby trap',         'boobytrap', null, '{}')
on conflict (name) do nothing;
