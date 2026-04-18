-- item_data.sql
-- Seed data for murdermotel.item table: 6 of each component and defense
delete from murdermotel.item where kind in ('component', 'defense');

insert into murdermotel.item (name, kind, serial, title, modulepath, usemessages, state) values
-- 10 components x 6 each = 60
    ('axeblade',        'component', 1, 'axe blade',         null, array['You swing the axe with all your might and slaughter', 'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], '{}'),
    ('axeblade',        'component', 2, 'axe blade',         null, array['You swing the axe with all your might and slaughter', 'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], '{}'),
    ('axeblade',        'component', 3, 'axe blade',         null, array['You swing the axe with all your might and slaughter', 'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], '{}'),
    ('axeblade',        'component', 4, 'axe blade',         null, array['You swing the axe with all your might and slaughter', 'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], '{}'),
    ('axeblade',        'component', 5, 'axe blade',         null, array['You swing the axe with all your might and slaughter', 'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], '{}'),
    ('axeblade',        'component', 6, 'axe blade',         null, array['You swing the axe with all your might and slaughter', 'THUCK! WHACK! THUCK! You hack away and finish', 'You butcher'], '{}'),

    ('pistol',          'component', 1, 'pistol',             null, array['You take aim.. pull the trigger.. and waste', 'BANG! BANG! You gun down the vermin called', 'You take aim and shoot'], '{}'),
    ('pistol',          'component', 2, 'pistol',             null, array['You take aim.. pull the trigger.. and waste', 'BANG! BANG! You gun down the vermin called', 'You take aim and shoot'], '{}'),
    ('pistol',          'component', 3, 'pistol',             null, array['You take aim.. pull the trigger.. and waste', 'BANG! BANG! You gun down the vermin called', 'You take aim and shoot'], '{}'),
    ('pistol',          'component', 4, 'pistol',             null, array['You take aim.. pull the trigger.. and waste', 'BANG! BANG! You gun down the vermin called', 'You take aim and shoot'], '{}'),
    ('pistol',          'component', 5, 'pistol',             null, array['You take aim.. pull the trigger.. and waste', 'BANG! BANG! You gun down the vermin called', 'You take aim and shoot'], '{}'),
    ('pistol',          'component', 6, 'pistol',             null, array['You take aim.. pull the trigger.. and waste', 'BANG! BANG! You gun down the vermin called', 'You take aim and shoot'], '{}'),

    ('chlorinegas',     'component', 1, 'chlorine gas',       null, array['The noxious fumes spread from the sprayer and poison', 'The chlorine spews out and asphyxiates your mortal enemy', 'You gas'], '{}'),
    ('chlorinegas',     'component', 2, 'chlorine gas',       null, array['The noxious fumes spread from the sprayer and poison', 'The chlorine spews out and asphyxiates your mortal enemy', 'You gas'], '{}'),
    ('chlorinegas',     'component', 3, 'chlorine gas',       null, array['The noxious fumes spread from the sprayer and poison', 'The chlorine spews out and asphyxiates your mortal enemy', 'You gas'], '{}'),
    ('chlorinegas',     'component', 4, 'chlorine gas',       null, array['The noxious fumes spread from the sprayer and poison', 'The chlorine spews out and asphyxiates your mortal enemy', 'You gas'], '{}'),
    ('chlorinegas',     'component', 5, 'chlorine gas',       null, array['The noxious fumes spread from the sprayer and poison', 'The chlorine spews out and asphyxiates your mortal enemy', 'You gas'], '{}'),
    ('chlorinegas',     'component', 6, 'chlorine gas',       null, array['The noxious fumes spread from the sprayer and poison', 'The chlorine spews out and asphyxiates your mortal enemy', 'You gas'], '{}'),

    ('flamethrower',    'component', 1, 'flame thrower',      null, array['You barbecue', 'You pull out your flame thrower and fry', 'Heat and light burst from the flame gun as you cook'], '{}'),
    ('flamethrower',    'component', 2, 'flame thrower',      null, array['You barbecue', 'You pull out your flame thrower and fry', 'Heat and light burst from the flame gun as you cook'], '{}'),
    ('flamethrower',    'component', 3, 'flame thrower',      null, array['You barbecue', 'You pull out your flame thrower and fry', 'Heat and light burst from the flame gun as you cook'], '{}'),
    ('flamethrower',    'component', 4, 'flame thrower',      null, array['You barbecue', 'You pull out your flame thrower and fry', 'Heat and light burst from the flame gun as you cook'], '{}'),
    ('flamethrower',    'component', 5, 'flame thrower',      null, array['You barbecue', 'You pull out your flame thrower and fry', 'Heat and light burst from the flame gun as you cook'], '{}'),
    ('flamethrower',    'component', 6, 'flame thrower',      null, array['You barbecue', 'You pull out your flame thrower and fry', 'Heat and light burst from the flame gun as you cook'], '{}'),

    ('industrialacid',  'component', 1, 'industrial acid',    null, array['You boil away', 'You pump the acid sprayer furiously and disolve', 'The acid hisses from the nozzle of your sprayer. It liquifies'], '{}'),
    ('industrialacid',  'component', 2, 'industrial acid',    null, array['You boil away', 'You pump the acid sprayer furiously and disolve', 'The acid hisses from the nozzle of your sprayer. It liquifies'], '{}'),
    ('industrialacid',  'component', 3, 'industrial acid',    null, array['You boil away', 'You pump the acid sprayer furiously and disolve', 'The acid hisses from the nozzle of your sprayer. It liquifies'], '{}'),
    ('industrialacid',  'component', 4, 'industrial acid',    null, array['You boil away', 'You pump the acid sprayer furiously and disolve', 'The acid hisses from the nozzle of your sprayer. It liquifies'], '{}'),
    ('industrialacid',  'component', 5, 'industrial acid',    null, array['You boil away', 'You pump the acid sprayer furiously and disolve', 'The acid hisses from the nozzle of your sprayer. It liquifies'], '{}'),
    ('industrialacid',  'component', 6, 'industrial acid',    null, array['You boil away', 'You pump the acid sprayer furiously and disolve', 'The acid hisses from the nozzle of your sprayer. It liquifies'], '{}'),

    ('axehandle',       'component', 1, 'axe handle',         null, null, '{}'),
    ('axehandle',       'component', 2, 'axe handle',         null, null, '{}'),
    ('axehandle',       'component', 3, 'axe handle',         null, null, '{}'),
    ('axehandle',       'component', 4, 'axe handle',         null, null, '{}'),
    ('axehandle',       'component', 5, 'axe handle',         null, null, '{}'),
    ('axehandle',       'component', 6, 'axe handle',         null, null, '{}'),

    ('bullets',         'component', 1, 'bullets',            null, null, '{}'),
    ('bullets',         'component', 2, 'bullets',            null, null, '{}'),
    ('bullets',         'component', 3, 'bullets',            null, null, '{}'),
    ('bullets',         'component', 4, 'bullets',            null, null, '{}'),
    ('bullets',         'component', 5, 'bullets',            null, null, '{}'),
    ('bullets',         'component', 6, 'bullets',            null, null, '{}'),

    ('gassprayer',      'component', 1, 'gas sprayer',        null, null, '{}'),
    ('gassprayer',      'component', 2, 'gas sprayer',        null, null, '{}'),
    ('gassprayer',      'component', 3, 'gas sprayer',        null, null, '{}'),
    ('gassprayer',      'component', 4, 'gas sprayer',        null, null, '{}'),
    ('gassprayer',      'component', 5, 'gas sprayer',        null, null, '{}'),
    ('gassprayer',      'component', 6, 'gas sprayer',        null, null, '{}'),

    ('lighterfluid',    'component', 1, 'lighter fluid',      null, null, '{}'),
    ('lighterfluid',    'component', 2, 'lighter fluid',      null, null, '{}'),
    ('lighterfluid',    'component', 3, 'lighter fluid',      null, null, '{}'),
    ('lighterfluid',    'component', 4, 'lighter fluid',      null, null, '{}'),
    ('lighterfluid',    'component', 5, 'lighter fluid',      null, null, '{}'),
    ('lighterfluid',    'component', 6, 'lighter fluid',      null, null, '{}'),

    ('acidsprayer',     'component', 1, 'acid sprayer',       null, null, '{}'),
    ('acidsprayer',     'component', 2, 'acid sprayer',       null, null, '{}'),
    ('acidsprayer',     'component', 3, 'acid sprayer',       null, null, '{}'),
    ('acidsprayer',     'component', 4, 'acid sprayer',       null, null, '{}'),
    ('acidsprayer',     'component', 5, 'acid sprayer',       null, null, '{}'),
    ('acidsprayer',     'component', 6, 'acid sprayer',       null, null, '{}'),

-- 5 defenses x 6 each = 30
    ('riotshield',      'defense',   1, 'riot shield',        null, null, '{}'),
    ('riotshield',      'defense',   2, 'riot shield',        null, null, '{}'),
    ('riotshield',      'defense',   3, 'riot shield',        null, null, '{}'),
    ('riotshield',      'defense',   4, 'riot shield',        null, null, '{}'),
    ('riotshield',      'defense',   5, 'riot shield',        null, null, '{}'),
    ('riotshield',      'defense',   6, 'riot shield',        null, null, '{}'),

    ('flakjacket',      'defense',   1, 'flak jacket',        null, null, '{}'),
    ('flakjacket',      'defense',   2, 'flak jacket',        null, null, '{}'),
    ('flakjacket',      'defense',   3, 'flak jacket',        null, null, '{}'),
    ('flakjacket',      'defense',   4, 'flak jacket',        null, null, '{}'),
    ('flakjacket',      'defense',   5, 'flak jacket',        null, null, '{}'),
    ('flakjacket',      'defense',   6, 'flak jacket',        null, null, '{}'),

    ('gasmask',         'defense',   1, 'gas mask',           null, null, '{}'),
    ('gasmask',         'defense',   2, 'gas mask',           null, null, '{}'),
    ('gasmask',         'defense',   3, 'gas mask',           null, null, '{}'),
    ('gasmask',         'defense',   4, 'gas mask',           null, null, '{}'),
    ('gasmask',         'defense',   5, 'gas mask',           null, null, '{}'),
    ('gasmask',         'defense',   6, 'gas mask',           null, null, '{}'),

    ('fireextinguisher','defense',   1, 'fire extinguisher',  null, null, '{}'),
    ('fireextinguisher','defense',   2, 'fire extinguisher',  null, null, '{}'),
    ('fireextinguisher','defense',   3, 'fire extinguisher',  null, null, '{}'),
    ('fireextinguisher','defense',   4, 'fire extinguisher',  null, null, '{}'),
    ('fireextinguisher','defense',   5, 'fire extinguisher',  null, null, '{}'),
    ('fireextinguisher','defense',   6, 'fire extinguisher',  null, null, '{}'),

    ('lye',             'defense',   1, 'lye',                null, null, '{}'),
    ('lye',             'defense',   2, 'lye',                null, null, '{}'),
    ('lye',             'defense',   3, 'lye',                null, null, '{}'),
    ('lye',             'defense',   4, 'lye',                null, null, '{}'),
    ('lye',             'defense',   5, 'lye',                null, null, '{}'),
    ('lye',             'defense',   6, 'lye',                null, null, '{}'),

    ('boobytrap',       'boobytrap', 0, 'booby trap',         'boobytrap', null, '{}')
on conflict (name, serial) do nothing;
