#!/usr/bin/env python3
"""Host-only collector. Publish aggregate data, never Docker environments or logs."""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

root = Path("/var/lib/chat-metrics")
root.mkdir(mode=0o755, exist_ok=True)
path = root / "host.json"
try:
    previous = json.loads(path.read_text())
except (OSError, ValueError):
    previous = {"samples": [], "cpu": [0, 0]}
fields = list(map(int, Path("/proc/stat").read_text().splitlines()[0].split()[1:]))
total, idle = sum(fields[:8]), fields[3] + fields[4]
old_total, old_idle = previous.get("cpu", [0, 0])
cpu = 100 * (1 - (idle - old_idle) / max(1, total - old_total))
mem = {
    line.split(":")[0]: int(line.split()[1]) * 1024
    for line in Path("/proc/meminfo").read_text().splitlines()
}
disk = shutil.disk_usage("/")
r = subprocess.run(
    ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
    capture_output=True,
    text=True,
    timeout=15,
    check=True,
)
statuses = subprocess.run(
    ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
    capture_output=True,
    text=True,
    timeout=10,
    check=True,
)
status = dict(line.split("\t", 1) for line in statuses.stdout.splitlines())
containers = []
for line in r.stdout.splitlines():
    item = json.loads(line)
    if item["Name"].startswith("is373-ai-chat-"):
        containers.append(
            {
                "name": item["Name"],
                "cpu": item["CPUPerc"],
                "memory": item["MemUsage"],
                "status": status.get(item["Name"], "unknown"),
            }
        )
sample = {
    "at": time.time(),
    "cpu_percent": round(max(0, min(cpu, 100)), 2),
    "memory_total": mem["MemTotal"],
    "memory_used": mem["MemTotal"] - mem["MemAvailable"],
    "disk_total": disk.total,
    "disk_used": disk.used,
    "containers": containers,
}
output = {"status": "ok", "cpu": [total, idle], "samples": (previous["samples"] + [sample])[-60:]}
tmp = root / "host.json.tmp"
tmp.write_text(json.dumps(output))
os.chmod(tmp, 0o644)
tmp.replace(path)
