-- defense_data.sql
-- Seed data for murdermotel.defense table: 6 of each defense
delete from murdermotel.defense;

insert into murdermotel.defense (name, serial, description) values
    ('riotshield', 1, 'A sturdy plexiglass shield used by riot police. Provides excellent protection against thrown objects and close-quarters attacks.'),
    ('riotshield', 2, 'A sturdy plexiglass shield used by riot police. Provides excellent protection against thrown objects and close-quarters attacks.'),
    ('riotshield', 3, 'A sturdy plexiglass shield used by riot police. Provides excellent protection against thrown objects and close-quarters attacks.'),
    ('riotshield', 4, 'A sturdy plexiglass shield used by riot police. Provides excellent protection against thrown objects and close-quarters attacks.'),
    ('riotshield', 5, 'A sturdy plexiglass shield used by riot police. Provides excellent protection against thrown objects and close-quarters attacks.'),
    ('riotshield', 6, 'A sturdy plexiglass shield used by riot police. Provides excellent protection against thrown objects and close-quarters attacks.'),

    ('flakjacket', 1, 'A heavy bulletproof vest. Rated to stop most pistol rounds and fragmentation. Bulky but life-saving.'),
    ('flakjacket', 2, 'A heavy bulletproof vest. Rated to stop most pistol rounds and fragmentation. Bulky but life-saving.'),
    ('flakjacket', 3, 'A heavy bulletproof vest. Rated to stop most pistol rounds and fragmentation. Bulky but life-saving.'),
    ('flakjacket', 4, 'A heavy bulletproof vest. Rated to stop most pistol rounds and fragmentation. Bulky but life-saving.'),
    ('flakjacket', 5, 'A heavy bulletproof vest. Rated to stop most pistol rounds and fragmentation. Bulky but life-saving.'),
    ('flakjacket', 6, 'A heavy bulletproof vest. Rated to stop most pistol rounds and fragmentation. Bulky but life-saving.'),

    ('gasmask', 1, 'A military-grade gas mask with integral charcoal filter. Protects against chemical agents and toxic fumes.'),
    ('gasmask', 2, 'A military-grade gas mask with integral charcoal filter. Protects against chemical agents and toxic fumes.'),
    ('gasmask', 3, 'A military-grade gas mask with integral charcoal filter. Protects against chemical agents and toxic fumes.'),
    ('gasmask', 4, 'A military-grade gas mask with integral charcoal filter. Protects against chemical agents and toxic fumes.'),
    ('gasmask', 5, 'A military-grade gas mask with integral charcoal filter. Protects against chemical agents and toxic fumes.'),
    ('gasmask', 6, 'A military-grade gas mask with integral charcoal filter. Protects against chemical agents and toxic fumes.'),

    ('fireextinguisher', 1, 'A standard ABC dry chemical fire extinguisher. Effective against flammable liquids and electrical fires.'),
    ('fireextinguisher', 2, 'A standard ABC dry chemical fire extinguisher. Effective against flammable liquids and electrical fires.'),
    ('fireextinguisher', 3, 'A standard ABC dry chemical fire extinguisher. Effective against flammable liquids and electrical fires.'),
    ('fireextinguisher', 4, 'A standard ABC dry chemical fire extinguisher. Effective against flammable liquids and electrical fires.'),
    ('fireextinguisher', 5, 'A standard ABC dry chemical fire extinguisher. Effective against flammable liquids and electrical fires.'),
    ('fireextinguisher', 6, 'A standard ABC dry chemical fire extinguisher. Effective against flammable liquids and electrical fires.'),

    ('lye', 1, 'A bucket of granular lye (sodium hydroxide). Highly caustic and can cause severe chemical burns.'),
    ('lye', 2, 'A bucket of granular lye (sodium hydroxide). Highly caustic and can cause severe chemical burns.'),
    ('lye', 3, 'A bucket of granular lye (sodium hydroxide). Highly caustic and can cause severe chemical burns.'),
    ('lye', 4, 'A bucket of granular lye (sodium hydroxide). Highly caustic and can cause severe chemical burns.'),
    ('lye', 5, 'A bucket of granular lye (sodium hydroxide). Highly caustic and can cause severe chemical burns.'),
    ('lye', 6, 'A bucket of granular lye (sodium hydroxide). Highly caustic and can cause severe chemical burns.')
on conflict (name, serial) do nothing;