"""Student entry point: uv run python -m gridworld --render terminal|pygame."""
import argparse


from gridworld.engine import Engine
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level

from gridworld.controllers.terminal_input import TerminalInput
from gridworld.controllers.pygame_input import PygameInput
from gridworld.views.bash_render import BashRender 
from gridworld.views.pygame_render import PygameRender


def main() -> None:
    parser = argparse.ArgumentParser(description="Grid-world — application assembly to implement in S0")
    parser.add_argument("--render", choices=["terminal", "pygame"], default="terminal",
                        help="display mode (default: terminal)")
    parser.add_argument("--level", default="levels/n0.json",
                        help="JSON map path (default: levels/n0.json)")
    args = parser.parse_args()
    # TODO: load Level, select InputSource and Renderer, then create Controller and Engine.
    # Start the renderer, call engine.run(), and close it in a finally block.
    
    level = Level.load(args.level)
    if args.render == "pygame":
        renderer = PygameRender()
        input_source = PygameInput(renderer) 
    else :
        renderer = BashRender()
        input_source = TerminalInput()

    controller=Controller(input_source)
    engine=Engine(level,controller,renderer)

    renderer.start()
    try:
        engine.run()
    finally :
        renderer.close()
    
    raise NotImplementedError(
        f"assemble the game ({args.render}, {args.level}). "
        "To check the supplied files: uv run python -m gridworld.views.pygame_render"
    )


if __name__ == "__main__":
    main()
