"""Batch CMP-05: the more-screens door with every built screen, and the server that starts it.

Inputs: a control panel config and the screen modules already built.
Outputs: a handlers dictionary holding toolbox and logs, and a local server that answers for both.
Errors: ValueError whose message starts with an MS_ code of the door.
"""

from __future__ import annotations

import inspect
import threading
from http.server import ThreadingHTTPServer

import apccs2_control_panel as panel
import apccs2_log_viewer as log_viewer
import apccs2_more_screens as more


def build_all_more_handlers() -> dict:
    """CMP-05-05: the door's handlers plus the logs screen, in a new dictionary.

    Inputs: none.
    Outputs: a new dictionary holding what more.build_more_handlers() gives, plus "logs": log_viewer.handle_screen_request.
    Errors: MS_BAD_SCREEN when log_viewer.SCREEN_ID is not "logs", when log_viewer.handle_screen_request is not a
    function, or when the door's own handlers already hold "logs".
    """
    handlers = dict(more.build_more_handlers())
    if log_viewer.SCREEN_ID != "logs" or not inspect.isfunction(log_viewer.handle_screen_request):
        raise ValueError("MS_BAD_SCREEN: apccs2_log_viewer must define SCREEN_ID logs and handle_screen_request")
    if "logs" in handlers:
        raise ValueError("MS_BAD_SCREEN: the door already holds a logs screen")
    handlers["logs"] = log_viewer.handle_screen_request
    return handlers


def run_all_more_server(config: dict, host: str = "127.0.0.1", port: int = panel.DEFAULT_PORT,
                        ready_event: threading.Event | None = None) -> None:
    """CMP-05-05: run the control panel, the toolbox and the logs screen on one local port, until shutdown.

    Inputs: the config (see more.handle_more_request), a host (only 127.0.0.1 or localhost), a port (0 picks a free
    one) and an optional Event.
    Outputs: none. config["port"] is set to the port really used. Before serving, the Event gets the attributes
    server_port and server (so a caller can call server.shutdown()) and is then set.
    Errors: MS_HOST_REFUSED, MS_BAD_PORT or MS_BAD_CONFIG, raised before any socket is opened.
    """
    if host not in panel.ALLOWED_HOSTS:
        raise ValueError("MS_HOST_REFUSED: the server only listens on 127.0.0.1 or localhost")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("MS_BAD_PORT: port must be a whole number from 0 to 65535")
    problem = more._config_problem(config)
    if problem:
        raise ValueError("MS_BAD_CONFIG: " + str(problem))
    handler_class = more._make_handler(config, panel.build_panel_handlers(), build_all_more_handlers())
    server = ThreadingHTTPServer((host, port), handler_class)
    server.daemon_threads = True
    config["port"] = server.server_address[1]
    try:
        if ready_event is not None:
            ready_event.server_port = server.server_address[1]  # type: ignore[attr-defined]
            ready_event.server = server  # type: ignore[attr-defined]
            ready_event.set()
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
