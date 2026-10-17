import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Layer 2: environment-specific YAML. APP_ENV defaults to development.
environment = os.getenv("APP_ENV", "development").strip().lower()
yaml_path = BASE_DIR / f"config.{environment}.yaml"
yaml_config = {}
if yaml_path.exists():
    with yaml_path.open("r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f) or {}

# Layer 3: .env file values (read explicitly; does not override OS variables here).
dotenv_config = dotenv_values(BASE_DIR / ".env")

# Convert external variable names to application config keys.
ENV_KEY_MAP = {
    "APP_PORT": "port",
    "APP_WORKERS": "workers",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
    "NUM_WORKERS": "workers",
}

def coerce(key: str, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "on"}
    return str(value)

def normalize_layer(layer: dict) -> dict:
    result = {}
    for raw_key, value in (layer or {}).items():
        if value is None:
            continue
        key = ENV_KEY_MAP.get(str(raw_key).upper(), str(raw_key).lower())
        result[key] = coerce(key, value)
    return result

def effective_config(cli_sets: list[str]) -> dict:
    config = dict(DEFAULTS)

    # Defaults -> environment-specific YAML -> .env
    config.update(normalize_layer(yaml_config))
    config.update(normalize_layer(dict(dotenv_config)))

    # OS environment variables have higher precedence than .env.
    # Only APP_* OS variables are used; APP_ENV is only the selector.
    os_layer = {
        key: value
        for key, value in os.environ.items()
        if key.startswith("APP_") and key != "APP_ENV"
    }
    config.update(normalize_layer(os_layer))

    # Query-string overrides are the highest-precedence layer.
    for item in cli_sets:
        if "=" not in item:
            continue
        raw_key, raw_value = item.split("=", 1)
        key = ENV_KEY_MAP.get(raw_key.strip().upper(), raw_key.strip().lower())
        config[key] = coerce(key, raw_value.strip())

    # Ensure the required response never reveals the configured secret.
    config["api_key"] = "****"
    return config

app = FastAPI(title="Layered Configuration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Configuration API is running", "endpoint": "/effective-config"}

@app.get("/effective-config")
def get_effective_config(set_values: Optional[list[str]] = Query(default=None, alias="set")):
    # The alias ensures repeated URL parameters named "set" are parsed exactly as required.
    return effective_config(set_values or [])
