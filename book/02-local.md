# Local development: reproduce the system before changing it

A teammate says, “It works on my machine.” Our first job is to turn that observation into a repeatable environment. We need to know which code runs, which configuration it reads, where data persists and how to recognize readiness. Installation is useful when those relationships become visible.

After this chapter, you should be able to start a local mock system, explain the different database addresses used by containers and host processes, diagnose a failed readiness check, and justify a development route. Entry skills are in the [reader's guide](start-here.md); practice is [Lab 02](labs/02-request-trace.md).

## Why package the environment?

A directly installed application can work well: install a runtime and libraries, configure a database and start a process. The difficulty is remembering and repeating every required step. An image captures part of that environment, and Compose declares the cooperating services. External data, configuration, the host kernel and container runtime remain dependencies. Read the [deployment history](12-history.md#from-configured-machines-to-packaged-processes) before concluding that packaging removes operations.

The [Dockerfile](../Dockerfile) builds the frontend in Node, installs Python dependencies with a frozen lock, and copies the results into a runtime image. That runtime serves compiled React and FastAPI. Node is a build tool here, not a production web server. [Compose](../compose.yaml) runs that app and PostgreSQL, with a persistent database volume.

## A worked first installation

Use a fresh learner-owned checkout and its repository root. You need Docker with Compose v2 for this route; host Python and Node are unnecessary for container-only startup. First record your source and confirm the tools:

```sh
git rev-parse HEAD
docker version
docker compose version
cp .env.example .env
```

Copying the example is a first-checkout step. If you already have local configuration, review it rather than overwrite it. Keep `APP_ENV=development`, `PROVIDER=mock`, `EMAIL_PROVIDER=disabled` and `REGISTRATION_POLICY=approval`. Generate two separate values with `openssl rand -hex 32` and privately replace `JWT_SECRET` and `POSTGRES_PASSWORD`. For the later host-process route, also replace the password in `DATABASE_URL`. Hex values avoid URL-encoding surprises in this example. Do not submit `.env` as lab evidence.

Build and initialize the services:

```sh
docker compose config --quiet
docker compose up -d --wait db
docker compose build app
docker compose run --rm app alembic upgrade head
docker compose run --rm app python -m app.cli seed
docker compose run --rm -it app python -m app.cli admin --email admin@example.org
docker compose up -d --wait app
curl -fsS http://localhost:8000/api/health
```

`config --quiet` validates the declaration without printing resolved secrets. Database readiness precedes schema migration. Migration creates the current schema; `seed` ensures role-budget rows exist. The one-off admin command prompts for a password of at least sixteen characters and creates an approved administrator if that email is absent. It does not reset an existing administrator's password. Starting the web process alone is therefore not the whole installation.

The health response should report `status: ok`, the current schema (`0002` in this case-study baseline), and `provider: mock`. A local Compose build normally reports `commit: development` because its build does not supply a Git SHA. Record the checkout separately; that string is not a verified release identity. Health establishes a database connection and migration-table read, not every user journey.

Open [localhost:8000](http://localhost:8000), sign in as the local administrator, register a synthetic ordinary user, approve it and sign in with that user. Send “Explain a transaction.” The deterministic adapter begins its response with `Workshop reply:`. You have observed the UI/API/database/provider path without paying for a model request. Lab 02 asks you to trace the evidence behind that observation.

## Two addresses, one local database

| Process | Database address | Why |
|---|---|---|
| App or one-off app command in Compose | `db:5432` | `db` is the Compose service name on its private network. |
| Python/uv running on your computer | `localhost:5432` | Compose maps the database port to the host's loopback interface. |

Compose explicitly supplies the app's internal `DATABASE_URL` and `BASE_URL=http://localhost:8000`. Those values override corresponding entries loaded through `env_file`. A `.env` file supplies values; it is not itself the process's final environment. Docker documents this [environment precedence](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/).

Changing only `.env`'s `BASE_URL` does not change this container route's hard-coded origin or port mapping. For a custom container port, review the mapping and origin together. Keep the documented defaults for the initial lab.

Database and app host ports bind to `127.0.0.1`. The named database volume preserves rows across app replacement. `docker compose stop` stops services without deleting their volume. Volume deletion is a separate destructive choice, not a routine fix for a failed startup.

## The source-development alternative

Choose this route when fast source reload matters. Install Python 3.14.7/uv and Node 24. Keep only the Compose database running; stop the Compose app if it occupies port 8000. In `.env`, use a loopback `DATABASE_URL` with your local database password and `BASE_URL=http://localhost:5173`.

```sh
uv sync --frozen
npm --prefix frontend ci
npm --prefix frontend run build
make migrate
make seed
uv run python -m app.cli admin --email admin@example.org
make dev
```

In a second terminal, run `npm --prefix frontend run dev` and open the origin Vite reports. The normal port is 5173; if it chooses another port, update `BASE_URL` to that browser origin and restart Python. The [Vite configuration](../frontend/vite.config.ts) proxies `/api` to port 8000. The browser therefore sees one origin even though two development processes participate.

The source route improves reload speed and debugging access but adds host-tool dependencies. The container route makes the packaged runtime visible but rebuilds after code changes. Neither replaces testing the release image; choose based on the investigation.

## Diagnose a controlled failure

In a disposable source-development environment, deliberately set `BASE_URL` to a different local origin, restart the API, and attempt a page reload/session refresh. Refresh should receive HTTP 403 because `same_origin` compares Origin with configured `BASE_URL`. Restore the matching value and restart. Observe the failing request before changing settings at random.

| Symptom | First observation | Reason to investigate |
|---|---|---|
| Database never becomes healthy | `docker compose ps` and database logs | Port conflict, persisted volume/configuration mismatch or startup failure. |
| App health fails | App logs and migration result | A responding process may still have no migrated database. |
| UI loads but refresh fails | Origin and status in Network panel | A correct bundle does not establish correct auth configuration. |
| Password changed in `.env`, old volume remains | Configuration and volume history | Initialization settings do not re-create an existing PostgreSQL database. |

Read logs locally and redact sensitive material from submitted excerpts. Fix the diagnosed cause. Do not disable origin validation or delete data to make a check green.

## Evidence and judgment

Record the checkout, startup steps, sanitized health response, one synthetic journey and a diagram showing both database addresses. Explain what remains unproved: real provider delivery, email, production DNS/TLS, sustained load and recovery need separate evidence. [Lab 02](labs/02-request-trace.md) separately traces an in-process ASGI request using temporary SQLite; it needs no Docker or browser and does not establish those network/runtime properties. Return to [one request](01-system.md) before changing schema or policy.
