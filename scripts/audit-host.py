#!/usr/bin/env python3
"""Read-only audit of the known classroom host and its two Compose projects.

Run on the host: sudo python3 audit-host.py > protected-audit.json
Review output before sharing: it contains hostnames, usernames and infrastructure paths.
Environment values are allowlisted. Compose commands, labels, APT source files and
SSH configuration are copied from the known deployment; review those before running
on a different host, where inline credentials or different services may exist.
No configuration, package, service, container, firewall or account is changed.
"""
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from datetime import datetime, timezone


def command(args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=25)
        return {"exit_code": p.returncode, "output": p.stdout.strip(),
                "error": p.stderr.strip()[:1000]}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"error": type(e).__name__}


def metadata(path):
    p = Path(path)
    try:
        s = p.stat()
        return {"path": str(p), "mode": stat.filemode(s.st_mode), "uid": s.st_uid,
                "gid": s.st_gid, "bytes": s.st_size,
                "modified": datetime.fromtimestamp(s.st_mtime, timezone.utc).isoformat()}
    except OSError:
        return {"path": str(p), "exists": False}


def read(path):
    try:
        return Path(path).read_text()
    except (OSError, UnicodeError):
        return ""


PUBLIC_ENV = {"APP_ENV", "APP_HOST", "TRAEFIK_NETWORK", "DEV_PORT", "PROD_IMAGE",
              "WUD_WATCHER_LOCAL_WATCHBYDEFAULT", "WUD_WATCHER_LOCAL_WATCHDIGESTDEFAULT",
              "WUD_WATCHER_LOCAL_CRON", "WUD_WATCHER_LOCAL_JITTER",
              "WUD_TRIGGER_DOCKER_PRODUCTION_AUTO", "WUD_TRIGGER_DOCKER_PRODUCTION_PRUNE",
              "WUD_TRIGGER_DOCKER_PRODUCTION_DRYRUN"}


def env_summary(items):
    if isinstance(items, dict):
        data = items
    else:
        data = dict(x.split("=", 1) for x in items if "=" in x)
    return {"names": sorted(data), "public_values": {k: v for k, v in data.items()
                                                    if k in PUBLIC_ENV}}


def main():
    out = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "effective_uid": os.geteuid()}
    checks = {
        "os": ["cat", "/etc/os-release"], "kernel": ["uname", "-a"],
        "cpu": ["lscpu"], "memory": ["free", "-h"], "disk": ["df", "-hT"],
        "block_devices": ["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINTS"],
        "uptime": ["uptime"], "docker_version": ["docker", "version", "--format", "{{json .}}"],
        "compose_version": ["docker", "compose", "version"],
        "enabled_units": ["systemctl", "list-unit-files", "--state=enabled", "--no-pager"],
        "running_services": ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager"],
        "failed_units": ["systemctl", "--failed", "--no-pager"],
        "timers": ["systemctl", "list-timers", "--all", "--no-pager"],
        "docker_unit": ["systemctl", "cat", "docker"],
        "containerd_unit": ["systemctl", "cat", "containerd"],
        "ssh_effective": ["sshd", "-T"], "sudo_policy": ["sudo", "-l", "-U", "kwilliams"],
        "listeners": ["ss", "-lntup"], "ufw": ["ufw", "status", "verbose"],
        "iptables_filter": ["iptables", "-S"], "iptables_nat": ["iptables", "-t", "nat", "-S"],
        "ipv6_filter": ["ip6tables", "-S"],
        "docker_projects": ["docker", "compose", "ls", "--format", "json"],
        "docker_storage": ["docker", "system", "df"],
        "docker_stats": ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
        "packages": ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"],
        "manual_packages": ["apt-mark", "showmanual"],
        "pending_updates": ["apt", "list", "--upgradable"],
        "fstab": ["cat", "/etc/fstab"],
        "forwarding": ["sysctl", "net.ipv4.ip_forward", "net.ipv6.conf.all.forwarding"],
    }
    out["system"] = {name: command(args) for name, args in checks.items()}
    out["reboot_required"] = Path("/var/run/reboot-required").exists()
    out["users"] = [line for line in read("/etc/passwd").splitlines()
                    if line.split(":")[0] == "root" or int(line.split(":")[2]) >= 1000]
    out["groups"] = [line for line in read("/etc/group").splitlines()
                     if line.split(":")[0] in {"sudo", "docker", "kwilliams"}]
    config_paths = ["/etc/docker/daemon.json", "/etc/ssh/sshd_config",
                    *glob.glob("/etc/ssh/sshd_config.d/*"), "/etc/apt/sources.list.d/docker.sources",
                    "/etc/apt/sources.list.d/docker.list", "/etc/apt/apt.conf.d/20auto-upgrades",
                    "/etc/apt/apt.conf.d/50unattended-upgrades"]
    out["host_config"] = {p: read(p) for p in config_paths if Path(p).is_file()}
    out["apt_sources"] = [{**metadata(p), "content": read(p)} for p in glob.glob("/etc/apt/sources.list.d/*")]
    out["scheduled_file_inventory"] = [metadata(p) for pattern in
                                      ["/etc/cron*/*", "/var/spool/cron/crontabs/*", "/etc/systemd/system/*"]
                                      for p in glob.glob(pattern)]
    # Commands in cron/history may contain inline credentials: inventory only.
    out["history_inventory"] = [metadata(p) for p in
                                ["/root/.bash_history", "/home/kwilliams/.bash_history"]]
    out["ssh_inventory"] = []
    for base in ["/root/.ssh", "/home/kwilliams/.ssh"]:
        for p in glob.glob(base + "/*"):
            item = metadata(p)
            if p.endswith("authorized_keys") or p.endswith(".pub"):
                item["fingerprints"] = command(["ssh-keygen", "-lf", p])
            out["ssh_inventory"].append(item)
    ids = command(["docker", "ps", "-aq"]).get("output", "").split()
    inspected = command(["docker", "inspect", *ids]) if ids else {}
    containers = json.loads(inspected.get("output", "[]"))
    out["containers"] = []
    for c in containers:
        cfg, host = c["Config"], c["HostConfig"]
        labels = cfg.get("Labels") or {}
        labels = {k: ("[REDACTED]" if any(x in k.lower() for x in ["password", "token", "auth", "secret"])
                      else v) for k, v in labels.items()}
        out["containers"].append({
            "name": c["Name"].lstrip("/"), "id": c["Id"], "image_id": c["Image"],
            "requested_image": cfg["Image"], "created": c["Created"],
            "state": {k: v for k, v in c["State"].items() if k not in {"Health", "Error"}},
            "health_status": c["State"].get("Health", {}).get("Status"),
            "user": cfg.get("User"), "working_directory": cfg.get("WorkingDir"),
            "environment": env_summary(cfg.get("Env") or []), "labels": labels,
            "restart_policy": host.get("RestartPolicy"), "read_only": host.get("ReadonlyRootfs"),
            "privileged": host.get("Privileged"), "cap_add": host.get("CapAdd"),
            "cap_drop": host.get("CapDrop"), "security_opt": host.get("SecurityOpt"),
            "memory_limit": host.get("Memory"), "nano_cpus": host.get("NanoCpus"),
            "pids_limit": host.get("PidsLimit"), "log_config": host.get("LogConfig"),
            "tmpfs": host.get("Tmpfs"), "mounts": c.get("Mounts"),
            "ports": c["NetworkSettings"].get("Ports"),
            "networks": {k: {a: v for a, v in n.items() if a in {"IPAddress", "Aliases", "NetworkID"}}
                         for k, n in c["NetworkSettings"]["Networks"].items()},
        })
    out["images"] = []
    for image_id in sorted({c["Image"] for c in containers}):
        data = json.loads(command(["docker", "image", "inspect", image_id]).get("output", "[]"))
        for d in data:
            out["images"].append({k: d.get(k) for k in
                                 ["Id", "RepoTags", "RepoDigests", "Created", "Architecture", "Os", "Size"]})
    out["networks"] = json.loads(command(["docker", "network", "inspect", *command(
        ["docker", "network", "ls", "-q"]).get("output", "").split()]).get("output", "[]"))
    volume_names = command(["docker", "volume", "ls", "-q"]).get("output", "").split()
    out["volumes"] = json.loads(command(["docker", "volume", "inspect", *volume_names]).get("output", "[]")) if volume_names else []
    out["compose_models"] = {}
    for path in ["/opt/webserver", "/opt/is373_ci_cd"]:
        model_result = command(["docker", "compose", "--project-directory", path, "config", "--format", "json"])
        if model_result.get("exit_code") == 0:
            model = json.loads(model_result["output"])
            for svc in model.get("services", {}).values():
                svc["environment"] = env_summary(svc.get("environment") or {})
                if "healthcheck" in svc:
                    svc["healthcheck"].pop("test", None)
                # Labels/commands in these known stacks have no inline provider credentials.
                for key in list(svc.get("labels", {})):
                    if any(x in key.lower() for x in ["auth", "password", "secret", "token"]):
                        svc["labels"][key] = "[REDACTED]"
            out["compose_models"][path] = model
        else:
            out["compose_models"][path] = {"exit_code": model_result.get("exit_code"), "error": "render failed"}
    out["project_files"] = []
    for base in ["/opt/webserver", "/opt/is373_ci_cd", "/opt/373_hosting"]:
        for p in Path(base).rglob("*"):
            if ".git" in p.parts or len(p.relative_to(base).parts) > 3 or not p.is_file():
                continue
            item = metadata(p)
            if p.name.startswith(".env") or p.suffix == ".env":
                item["environment"] = env_summary([line for line in read(p).splitlines()
                                                   if "=" in line and not line.startswith("#")])
            if "letsencrypt" not in p.parts and "secrets" not in p.parts and p.suffix not in {".env", ".key"} and not p.name.startswith(".env"):
                item["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
            out["project_files"].append(item)
    out["git_checkouts"] = {}
    for base in ["/opt/is373_ci_cd", "/opt/373_hosting"]:
        out["git_checkouts"][base] = {"head": command(["git", "-C", base, "rev-parse", "HEAD"]),
                                     "status": command(["git", "-C", base, "status", "--short"]),
                                     "tracked": command(["git", "-C", base, "ls-files"])}
    out["certificate_store"] = metadata("/opt/webserver/letsencrypt/acme.json")
    try:
        acme = json.loads(read("/opt/webserver/letsencrypt/acme.json"))
        out["certificate_store"]["domains"] = [c.get("domain") for resolver in acme.values()
                                               for c in resolver.get("Certificates", [])]
    except (ValueError, AttributeError):
        pass
    out["registry_auth_inventory"] = []
    for p in ["/root/.docker/config.json", "/home/kwilliams/.docker/config.json"]:
        item = metadata(p)
        try:
            config = json.loads(read(p))
            item["registry_names"] = sorted(config.get("auths", {}))
            item["credential_store"] = config.get("credsStore")
        except ValueError:
            pass
        out["registry_auth_inventory"].append(item)
    print("AUDIT_JSON_BEGIN")
    print(json.dumps(out, indent=2))
    print("AUDIT_JSON_END")


if __name__ == "__main__":
    main()
