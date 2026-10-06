# 2 · Environment before code

[Compose](../compose.yaml) runs PostgreSQL and the app. The database exposes only a loopback development port. The app image builds its React bundle in a Node stage and installs locked Python dependencies in another stage. Runtime contains the compiled UI and API, not Node or development source mounts.

Copy [.env.example](../.env.example) to ignored .env. Environment values describe a deployment; code describes behavior. Never commit real passwords or API keys. [.dockerignore](../.dockerignore) also excludes them from image build context. Production [configuration validation](../app/config.py) requires HTTPS, PostgreSQL, and a sufficiently long signing key.

Two ways to develop:

1. Use Docker for the complete local stack as shown in the README.
2. Start only the Compose database; run Python locally with uv and a Vite frontend server. Vite proxies `/api` to FastAPI. Set BASE_URL to the browser origin, such as http://localhost:5173, so cookie-authenticated requests pass Origin checks.

JWT access stays in memory. Refresh uses an HttpOnly cookie. Refreshing the page therefore restores a session through the API rather than reading a token from localStorage.

The CLI admin bootstrap is a one-off process using the same environment/models as the web service. Registration is approval-based, so the first admin must exist before approving students.

**Exercise:** change a development port and explain why BASE_URL must change too. Then deliberately use a different origin and observe the refresh rejection.
