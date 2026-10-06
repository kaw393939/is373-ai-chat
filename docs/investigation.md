# Investigation — October 6, 2026

## Scope and method

Read-only SSH inspection, including sudo-assisted container/network/firewall checks, of the authorized droplet, local clones of three public repositories, GitHub workflow/secret-name metadata, DNS resolution, and trusted HTTPS requests. No application services, firewall settings, users, credentials, or DNS records were changed. Secret values and production .env files were not read.

GitHub account: `kaw393939`. HTTPS Git cloning works. GitHub SSH authentication from this workstation failed, while droplet SSH authentication succeeded. GitHub CLI is authenticated and can access repository APIs. These are separate credentials.

## Observed host

| Item | Observation |
|---|---|
| Hostname | ubuntu-s-1vcpu-2gb-nyc1 |
| OS | Ubuntu 24.04.5 LTS, x86_64 |
| Memory | About 1.9 GiB total; about 1.2 GiB available at inspection |
| Swap | None |
| Root disk | 48 GB total; about 44 GB available |
| Docker CLI | 29.8.1 |
| Compose CLI | v5.5.1 |
| Services | Docker and SSH active |
| TCP listeners | Public 22, 80, 443; loopback 8090, 8091; local DNS |
| Hosting checkout | /opt/373_hosting |
| Application checkout | /opt/is373_ci_cd |
| Shared proxy stack | /opt/webserver/compose.yaml |
| SSH user | kwilliams, member of sudo; not in docker group |
| CPU | 1 vCPU, verified with nproc |
| Firewall | UFW active; deny incoming by default; allow SSH/80/443 for IPv4 and IPv6 |
| Runtime | 8 running containers; calculator, WUD, Traefik reported healthy |

`docker ps` initially failed because the SSH user cannot access the Docker socket directly. After the owner provided sudo access, privileged read-only inspection verified running containers, the `web` network, UFW rules, and port bindings. No credentials were written to repository files or reports. Root-owned Git checkout inspection hit Git's ownership protection; no global safe-directory exception was added.

The host exposes one CPU, confirmed with `nproc`. The available RAM is a point-in-time measurement, not a capacity guarantee. This is suitable for a small hosted-LLM teaching deployment after load testing, not local model inference or an assumed production scale. Build images and browser tests on GitHub runners. Consider more RAM or managed PostgreSQL as usage grows; prices were not evaluated.

## Existing routing

The readable proxy configuration uses Traefik `v3.7.13`, HTTP-to-HTTPS redirection, Let's Encrypt HTTP-01, and Docker network `web`. Ports 80/443 are already allocated. Add this app with its own router and existing network; do not start a second proxy on this server.

Live `web` network inspection confirmed that Traefik, all five Apache sites, and calculator production share the proxy network. WUD is not on that public routing network. Docker reported loopback-only published ports for the calculator and WUD, and public 80/443 for Traefik.

A one-time `docker stats` sample showed about 40 MiB for calculator production, 93 MiB for WUD, 34 MiB for Traefik, and 6–10 MiB per Apache container. The displayed limits match total host memory, so these services do not appear to have tighter per-container memory limits. This sample does not establish performance under load.

The proxy has a Docker socket mount. The calculator updater also uses Docker control. A socket mount marked read-only does not restrict the Docker API to read-only requests. Keep these privileges outside the application and reconsider socket access protection when hardening the hosting stack.

The dashboard returned HTTP 200 at `/dashboard/` without credentials; host documentation and configuration describe disabled authentication. This verifies dashboard HTML availability, not the authorization behavior of every API endpoint. Protect administrative metadata before treating the host as a long-lived production deployment.

`calc.mywebclass.org`, `traefik.firehose360.com`, and the candidate `chat.mywebclass.org` resolved to the inspected droplet. Candidate chat DNS resolution does not establish that a chat route, certificate, or application exists.

## Application release evidence

`https://calc.mywebclass.org/health` returned trusted HTTPS, HTTP 200, and:

```json
{
  "status": "ok",
  "environment": "production",
  "commit": "4600202bad42da0c5ffb11d83ce8364671293d3d",
  "built_at": "2026-10-01T18:06:20Z"
}
```

This matches the cloned calculator repository HEAD. It is public application-reported identity, not direct inspection of its container digest. The October 1 main CI/CD runs succeeded; recent deployed-image security runs also succeeded. Those scans use a report-only vulnerability policy, so success does not imply zero findings.

## Repository background

| Repository | Examined commit | Relevant patterns |
|---|---|---|
| is373_ci_cd | 4600202bad42da0c5ffb11d83ce8364671293d3d | FastAPI, uv lock, pytest, Playwright, native amd64/arm64 image tests, publish saved tested artifacts, security scans, runtime restrictions, health release identity |
| 373_hosting | 9d828ad1cf3b72d3c6379e074474683eae0cdd8f | Beginner-oriented hosting textbook, Docker installation, TLS, routing overlays, verification scripts, operational exercises |
| is373_fall2026 | 2138fda1d7e6154fef3af8ffc415956f7236a40e | Next.js/React, TypeScript, Tailwind, Radix-based UI, Docker, Playwright, accessibility tooling, discovery lessons |

The calculator publishes to Docker Hub using the existing `DOCKER_API_KEY` secret and WUD polls its `prod` tag. No repository variables or deployment environments were returned by the inspected API calls. Secret values cannot be retrieved and were not requested.

Preserve build-once/test/publish discipline, immutable digest selection, visible release identity, and student explanations. Extend deployment with migration ordering and readiness gates. Independent WUD updates are a poor fit for releases that couple schema changes to application changes.

## Remaining evidence to collect during installation

DigitalOcean cloud firewall, backup and monitoring status; detailed runtime restart/resource policy inspection and exact image digest verification; chosen hostname/TLS behavior; resource limits under streaming load; permitted registry pulls; database backup destination and restore exercise; dedicated deployment identity. No DigitalOcean control-plane access was available in this investigation.
