
import argparse
from threading import Lock
from uuid import uuid4
import json

from flask import Flask, Response, request

from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.engine import Engine
from gridworld.models.level import Level
from gridworld.views.bash_render import BashRender


def json_response(data: dict, status: int = 200) -> Response:
    """Encode JSON and disable caching."""
    dumped = json.dumps(data, allow_nan=False)
    resp = Response(dumped, status=status, mimetype="application/json")
    resp.headers["Cache-Control"] = "no-store"
    return resp


def error_response(status: int, code: str, message: str) -> Response:
    return json_response(
        {"error": {"code": code, "message": message}},
        status,
    )


def create_app(engine: Engine | None) -> Flask:
    """Build an HTTP application around one shared game."""
    app = Flask(__name__)

    lock = Lock()
    session_id = uuid4().hex
    revision = 0
    running = engine is not None

    def state_frame() -> dict:
        """Build the StateFrame. Call while holding the lock."""
        if engine is None:
            return {}

        state = engine.get_state()

        return {
            "state": state,
            "running": running,
            "session_id": session_id,
            "revision": revision,
            "protocol_version": 1,
        }

    @app.get("/api/state")
    def get_state() -> Response:
        with lock:
            if engine is None:
                return error_response(
                    503,
                    "engine_unavailable",
                    "The game engine is unavailable",
                )

            return json_response(state_frame())

    @app.post("/api/actions")
    def post_action() -> Response:
        nonlocal revision, running

        # 1. Check Content-Type
        if not request.is_json:
            return error_response(
                415,
                "unsupported_media_type",
                "Content-Type must be application/json",
            )

        # 2. Read JSON
        body = request.get_json(silent=True)

        if not isinstance(body, dict):
            return error_response(
                400,
                "bad_request",
                "Request body must be a JSON object",
            )

        # 3. Check the exact body structure
        if set(body.keys()) != {"action"}:
            return error_response(
                422,
                "invalid_action",
                "Request must contain exactly one action field",
            )

        action = body["action"]

        # 4. Check action type
        if not isinstance(action, str):
            return error_response(
                422,
                "invalid_action",
                "Action must be a string",
            )

        # 5. Check allowed actions
        allowed_actions = {
            "north",
            "south",
            "east",
            "west",
            "wait",
            "quit",
        }

        if action not in allowed_actions:
            return error_response(
                422,
                "invalid_action",
                "Unknown action",
            )

        # 6. All game operations are protected by the lock
        with lock:
            if engine is None:
                return error_response(
                    503,
                    "engine_unavailable",
                    "The game engine is unavailable",
                )

            if not running:
                return error_response(
                    409,
                    "conflict",
                    "The game is no longer running",
                )

            state_before = engine.get_state()

            # Check whether the engine has already ended the game
            if state_before.get("status") in ("won", "lost", "quit"):
                running = False
                revision += 1
                return error_response(
                    409,
                    "conflict",
                    "The game is already over",
                )

            # Explicit quit: no game turn is consumed
            if action == "quit":
                running = False
                revision += 1
                return json_response(state_frame())

            # Normal action
            engine.apply_action(action)

            state_after = engine.get_state()

            # The game stops after victory or defeat
            if state_after.get("status") in ("won", "lost", "quit"):
                running = False

            revision += 1

            return json_response(state_frame())

    @app.errorhandler(500)
    def internal_error(error) -> Response:
        return error_response(
            500,
            "internal_error",
            "The server could not process the request",
        )

    return app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the Gridworld HTTP API"
    )
    parser.add_argument("--level", default="levels/n0.json")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    level = Level.load(args.level)

    engine = Engine(
        level,
        Controller(TerminalInput()),
        BashRender(),
    )

    app = create_app(engine)

    app.run(
        host="127.0.0.1",
        port=args.port,
        debug=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()
