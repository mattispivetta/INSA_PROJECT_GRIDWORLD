"""Launch the game with terminal or Pygame rendering."""
import argparse

from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.engine import Engine
from gridworld.models.level import Level
from gridworld.views.bash_render import BashRender


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Gridworld")
    parser.add_argument("--render", choices=["terminal", "pygame"], default="terminal",
                        help="display mode (default: terminal)")
    parser.add_argument("--level", default="levels/n0.json",
                        help="JSON map path (default: levels/n0.json)")
    args = parser.parse_args()
    level = Level.load(args.level)
    if args.render == "pygame":
        from gridworld.controllers.pygame_input import PygameInput
        from gridworld.views.pygame_render import PygameRender

        renderer = PygameRender()
        input_source = PygameInput(renderer)
    else:
        renderer = BashRender()
        input_source = TerminalInput()
    controller = Controller(input_source)
    engine = Engine(level, controller, renderer)
    try:
        renderer.start()
        engine.run()
    finally:
        renderer.close()


if __name__ == "__main__":
    main()
