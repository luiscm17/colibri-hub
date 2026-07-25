from pathlib import Path

from bootstrap.http_application import create_app

app = create_app(settings_env_file=Path(__file__).resolve().with_name(".env"))
