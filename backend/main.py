"""FastAPI ASGI entrypoint for the Textile Production Management System.

Exposes ``app`` as the ASGI application, declared as
``backend.main:app`` for ``fastapi dev`` / ``fastapi run``. The
application is created at import time with a ``.env`` file path
relative to this module.
"""

from pathlib import Path

from bootstrap.http_application import create_app

app = create_app(settings_env_file=Path(__file__).resolve().with_name(".env"))
