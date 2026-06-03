from bbsengine6 import database, io

from murdermotel import lib


def main():
    parser = lib.buildargs()
    args = parser.parse_args()

    try:
        with database.getpool(args) as pool:
            lib.runmodule(args, "main", "lobby", pool=pool)
    except KeyboardInterrupt:
        io.echo(f"{{/all}}**INTR**")
    except EOFError:
        io.echo(f"{{/all}}**EOF**")
    finally:
        io.echo(
            f"{{savecursor}}{{curpos:{io.terminal.height()},0}}{{el}}{{reset}}{{restorecursor}}"
        )



if __name__ == "__main__":
    main()
