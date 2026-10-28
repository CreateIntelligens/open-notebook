# Fail if the running deployment loses its patched production frontend.
import json
import re
import subprocess
from pathlib import Path


def verify():
    result = subprocess.run(
        ["nginx", "-v"], capture_output=True, text=True, check=True
    )
    version = tuple(map(int, re.search(
        r"nginx/(\d+)\.(\d+)\.(\d+)", result.stderr
    ).groups()))
    assert version >= (1, 31, 7) or (1, 30, 6) <= version < (1, 31, 0), version
    frontend = Path("/opt/frontend")
    package = json.loads((frontend / "node_modules/next/package.json").read_text())
    next_version = tuple(map(int, package["version"].split(".")))
    assert next_version >= (16, 1, 5), next_version
    assert (frontend / ".next/BUILD_ID").is_file(), "production build missing"
    servers = []
    for process in Path("/proc").glob("[0-9]*"):
        try:
            command = (process / "cmdline").read_bytes()
            if b"next-server" not in command:
                continue
            assert (process / "cwd").resolve() == frontend, command
            assert b"NODE_ENV=production" in (process / "environ").read_bytes().split(b"\0"), command
            servers.append(process.name)
        except (FileNotFoundError, ProcessLookupError):
            continue
    assert servers, "production Next.js process missing"
    subprocess.run(["nginx", "-t"], check=True)
    print(f"PASS nginx={version} next={package['version']} production_pids={servers}")


if __name__ == "__main__":
    verify()
