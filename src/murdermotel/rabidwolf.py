import random

from bbsengine6 import io

from . import lib

def init(args, **kw):
    return True

def access(args, op, **kw):
    return True

def buildargs(args=None, **kw):
    return None

# @since 20230304
def help(**kw):
    player = kw["player"] if "player" in kw else None

    if player is None:
        io.echo("You do not exist! Go Away!", level="error")
        return False

    if len(player.weapons()) > 0:
        io.echo("{f6}{var:optioncolor}[A]{var:labelcolor}ttack")
    io.echo("{var:optioncolor}[I]{var:labelcolor}gnore{f6}{var:optioncolor}[F]{var:labelcolor}lee room{f6}")
    return

def attack(args, player, weapons, wolf):
    io.echo(f"weapons={weapons!r}", level="debug")
    weapon = None
    if len(weapons) == 1:
        io.echo(f"you only have 1 weapon: {weapons[0]}")
        weapon = weapons[0]
    else:
        key = 0
        buf = []
        options = ""
        for w in weapons:
            buf.append(f"{chr(ord('1')+key)}) {w}")
            options += chr(ord("1")+key)
            key += 1
        ch = io.inputchar(f"{{var:promptcolor}}kill with? {' '.join(buf)} {{var:inputcolor}}", options, "")
        # ttyio.echo("kill with which? 1) axe 2) pistol 3) chlorine 4) fire 5) acid")
        weapon = weapons[ord(ch) - ord("1")]
        io.echo(f"{ch} {{var:sepcolor}}- {{var:labelcolor}}{weapon}")

    io.echo(f"{wolf=}", level="debug")
    damage = bbsengine.diceroll(1, 6)*5
    io.echo(f"You remove {damage}% of the {wolf.short()}'s strength!")
    player.moves += 5
    wolf.healthpoints -= damage
    if wolf.healthpoints < 1:
        wolf.healthpoints = 0
        wolf.roomid = 0
        io.echo(f"You killed the {wolf.short()}!")
        player.moves += 500
        bbsengine.logentry(f"{player.name} killed the {wolf.short()}!")


    if player.moves < 1:
        io.echo("You have died.")
        player.save()
        return
    
    player.save()

    damage = 0
    if bbsengine.diceroll(1, 10) < 6:
        damage = random.randint(1, 10)+10
        io.echo(f"damage={damage}", level="debug")
        io.echo("The {} claws you for {}".format(wolf.short(), bbsengine.pluralize(damage, "move", "moves")))
        player.moves -= damage
        if player.moves < 0:
            player.moves = 0
            io.echo("You are out of moves. You are dead.")

    player.save()
    
def flee(args, player, exits):
    # tries several times, up to the number of exits (6)
    io.echo(f"total exits: {len(exits)}", level="debug")
    k = []
    for e in exits.keys():
        k.append(e)

    for t in range(0, len(exits)):
        e = random.choice(k)
        io.echo(f"t={t!r} e={e!r}", level="debug")
        if exits[e] is not None:
            io.echo(f"selected {e!r} exit")
            player.roomid = exits[e]
            player.save()
            break
        io.echo(f"skipped invalid exit {e!r}", level="debug")
    return

def main(args, **kw):
    player = kw["player"] if "player" in kw else None
    if player is None:
        io.echo("You do not exist! Go Away!")
        return False
    wolf = kw["wolf"] if "wolf" in kw else None
    if wolf is None:
        io.echo("The wolf does not exist!")
        return False

    room = kw["room"] if "room" in kw else None
    if room is None:
        io.echo("The room you are in does not exist!")
        return False

    done = False
    while not done:
        lib.setarea(args, player, "playground: rabid wolf")

        io.echo(f"{{var:labelcolor}}There is a {wolf.short()} snarling at you.{{f6}}")

        weapons = player.weapons()
        options = "IF?"
        if len(weapons) > 0:
            options += "A"
        options = "".join(sorted(options))
        ch = io.inputchar(f"{{var:promptcolor}}Make selection {{var:optioncolor}}[{options}]{{var:promptcolor}}: {{var:inputcolor}}", options, "", help=help, player=player)
        if ch == "A":
            io.echo(f"Attack {wolf.short()}")
            attack(args, player, weapons, wolf)
            if wolf.roomid == 0:
                break
        elif ch == "I":
            io.echo("Ignore")
            break
        elif ch == "F":
            io.echo("Flee")
            flee(args, player, room.exits)
            roomchange = True
            break
    return True
