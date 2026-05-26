import argparse

from murdermotel import lib

def main():
    parser = lib.buildargs()
    args = parser.parse_args()

    try:
        lib.runmodule(args, "main", "lobby")
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass

if __name__ == "__main__":
    main()