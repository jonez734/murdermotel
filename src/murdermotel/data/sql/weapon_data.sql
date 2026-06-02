-- weapon_data.sql
-- Seed data for murdermotel.weapon_recipe
-- count controls rarity: 6=common, 3=uncommon, 1=rare, 0=disabled

delete from murdermotel.weapon_recipe;

insert into murdermotel.weapon_recipe (name, title, component1, component2, count, usemessages, state) values
    ('axe',
     'Axe',
     'axeblade',
     'axehandle',
     6,
     array[
         'You swing the axe with all your might and slaughter',
         'THUCK! WHACK! THUCK! You hack away and finish',
         'You butcher'
     ],
     '{"damage_min": 15, "damage_max": 30, "type": "melee", "power": "high"}'),

    ('pistol',
     'Pistol',
     'pistol',
     'bullets',
     6,
     array[
         'You take aim.. pull the trigger.. and waste',
         'BANG! BANG! You gun down the vermin called',
         'You take aim and shoot'
     ],
     '{"damage_min": 10, "damage_max": 20, "type": "ranged", "ammo": 6, "ammo_max": 6}'),

    ('chlorine',
     'Chlorine',
     'chlorinegas',
     'gassprayer',
     6,
     array[
         'The noxious fumes spread from the sprayer and poison',
         'The chlorine spews out and asphyxiates your mortal enemy',
         'You gas'
     ],
     '{"damage_min": 5, "damage_max": 25, "type": "area", "radius": 1}'),

    ('fire',
     'Fire',
     'lighterfluid',
     'flamethrower',
     6,
     array[
         'You barbecue',
         'You pull out your flame thrower and fry',
         'Heat and light burst from the flame gun as you cook'
     ],
     '{"damage_min": 20, "damage_max": 40, "type": "burn", "area": false}'),

    ('acid',
     'Acid',
     'industrialacid',
     'acidsprayer',
     6,
     array[
         'You boil away',
         'You pump the acid sprayer furiously and disolve',
         'The acid hisses from the nozzle of your sprayer. It liquifies'
     ],
     '{"damage_min": 12, "damage_max": 35, "type": "corrosive", "uses": 3, "uses_max": 3}')
on conflict (name) do update set
    title = excluded.title,
    component1 = excluded.component1,
    component2 = excluded.component2,
    count = excluded.count,
    usemessages = excluded.usemessages,
    state = excluded.state;