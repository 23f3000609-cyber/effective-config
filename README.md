# Layered Configuration FastAPI

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/effective-config`.

Try query overrides:

`http://127.0.0.1:8000/effective-config?set=port=9000&set=debug=true&set=workers=2`

## Configuration precedence

Defaults -> `config.<APP_ENV>.yaml` -> `.env` -> OS `APP_*` environment variables -> repeated `set` query parameters.

`APP_ENV` selects the YAML file and defaults to `development`. The `.env` file is read explicitly. OS variables override `.env`. `NUM_WORKERS` in `.env` aliases to `workers`; `APP_WORKERS` maps to the same key and wins at the OS layer. `api_key` is always masked in the response.

## Deploy on Railway

1. Push this project to a GitHub repository.
2. In Railway, create a new project and deploy the repository.
3. Railway should detect Python. The included `Procfile` starts Uvicorn on the platform-provided `PORT`.
4. Generate a public domain in the service's Settings / Networking.
5. Submit the public URL ending in `/effective-config`.
