import argparse
from copy import deepcopy
import json
from threading import Lock
from uuid import uuid4

from flask import Flask, Response, request

from gridworld.controllers.controller import Controller
from gridworld.controllers.terminal_input import TerminalInput
from gridworld.engine import Engine
from gridworld.models.level import Level
from gridworld.views.bash_render import BashRender


def json_response(data: dict, status: int = 200) -> Response:
    """Encode ordinary JSON and set Content-Type and Cache-Control headers."""
    dumped = json.dumps(data, allow_nan=False)
    resp = Response(dumped, status=status, mimetype="application/json")
    resp.headers["Cache-Control"] = "no-store"
    return resp

def error_response(status: int, code: str, message: str) -> Response:
    """Supplied helper: keep the same error envelope for every route."""
    return json_response({"error": {"code": code, "message": message}}, status)


def create_app(engine: Engine | None) -> Flask:
    """Build an HTTP application around one shared game."""
    app = Flask(__name__)
    lock = Lock()
    session_id = uuid4().hex
    revision = 0

    def state_frame() -> dict:
        """Build the five-field StateFrame; call while holding the lock."""
        if engine is None:
            return {}
        state = engine.get_state()
        running = state.get("status") not in ("won", "lost", "quit")
        return {
            "protocol_version": 1,
            "session_id": session_id,
            "revision": revision,
            "running": running,
            "state": state,
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
        nonlocal revision
        
        # Validate Content-Type
        if not request.is_json:
            return error_response(415, "unsupported_media_type", "Content-Type must be application/json")

        try:
            body = request.get_json(silent=True)
        except Exception:
            return error_response(400, "bad_request", "Malformed JSON body")

        if not isinstance(body, dict):
            return error_response(400, "bad_request", "Request body must be a JSON object")

        # Check allowed fields (only 'action' should be present)
        keys = list(body.keys())
        if keys != ["action"]:
            return error_response(400, "bad_request", "Request must contain exactly one 'action' field")

        action = body.get("action")
        if not isinstance(action, str):
            return error_response(422, "unprocessable_entity", "Action must be a string")

        allowed_actions = {"north", "south", "east", "west", "wait", "quit"}
        if action not in allowed_actions:
            return error_response(422, "unprocessable_entity", f"Unknown action: {action}")

        with lock:
            if engine is None:
                return error_response(503, "service_unavailable", "Engine is not available")

            state_before = engine.get_state()
            is_running = state_before.get("status") not in ("won", "lost", "quit")

            if not is_running:
                return error_response(409, "conflict", "Game is already over or quit")

            # Handle explicit quit action
            if action == "quit":
                # Mark status as quit if engine supports it, or handle via internal flag/state update
                if hasattr(engine, "quit"):
                    engine.quit()
                elif "status" in state_before:
                    state_before["status"] = "quit"
                revision += 1
                return json_response(state_frame(), 200)

            # Check if game is already won/lost before moving
            if state_before.get("status") in ("won", "lost"):
                return error_response(409, "conflict", "Game is already won or lost")

            # Apply action and get new state
            engine.apply_action(action)
            revision += 1
            return json_response(state_frame(), 200)

    @app.errorhandler(500)
    def internal_error(error) -> Response:
        return error_response(500, "internal_error", "The server could not process the request")

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Gridworld HTTP API")
    parser.add_argument("--level", default="levels/n0.json")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    # TODO: load args.level, construct your Engine, then create the application.
    # Existing Controller, TerminalInput and BashRender satisfy its constructor.
    # Start the HTTP server on 127.0.0.1 with args.port.
    # Do not call Engine.run(), read keys or start a local display loop.
    raise NotImplementedError("Complete web-mode startup")


if __name__ == "__main__":
    main()