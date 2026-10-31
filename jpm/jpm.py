#!/usr/bin/env python3
"""
jpm — JapyScript package manager.

Manages a project's `japy.json` manifest, resolves dependencies, fetches
`.jpkg` archives from the registry, and writes lockfiles for reproducible
builds.

    jpm init                  create japy.json
    jpm install [pkg[@ver]]   install a package or all dependencies
    jpm list                  list installed packages
    jpm publish               publish the current project
"""

from __future__ import annotations
import json
import os
import sys
import hashlib
import urllib.request
import urllib.error

REGISTRY   = "https://registry.japyscript.dev"
MANIFEST   = "japy.json"
LOCKFILE   = "japy.lock"
MODULES    = "japy_modules"


def load_manifest() -> dict:
    if not os.path.exists(MANIFEST):
        raise SystemExit(f"error: {MANIFEST} not found. run `jpm init`.")
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def cmd_init(args) -> int:
    if os.path.exists(MANIFEST):
        print(f"error: {MANIFEST} already exists")
        return 1
    name = input("package name: ").strip() or "my-package"
    version = input("version [0.1.0]: ").strip() or "0.1.0"
    manifest = {
        "name": name,
        "version": version,
        "description": "",
        "entry": "main.jpy",
        "dependencies": {},
    }
    save_manifest(manifest)
    print(f"wrote {MANIFEST}")
    return 0


def _fetch_pkg(name: str, version: str):
    url = f"{REGISTRY}/packages/{name}/{version}.jpkg"
    os.makedirs(MODULES, exist_ok=True)
    dest_dir = os.path.join(MODULES, name)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"{version}.jpkg")
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        sha = hashlib.sha256(data).hexdigest()
        print(f"  [{name}@{version}] {len(data)} bytes  sha256={sha[:16]}...")
        return {"name": name, "version": version, "sha256": sha, "path": dest}
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"  [x] {name}@{version}  {e}")
        return None


def cmd_install(args) -> int:
    manifest = load_manifest()
    deps = dict(manifest.get("dependencies", {}))

    if args.package:
        if "@" in args.package:
            name, version = args.package.split("@", 1)
        else:
            name, version = args.package, "latest"
        deps[name] = version

    if not deps:
        print("nothing to install")
        return 0

    installed = []
    for name, version in deps.items():
        print(f"installing {name}@{version}")
        entry = _fetch_pkg(name, version)
        if entry:
            installed.append(entry)

    manifest["dependencies"] = deps
    save_manifest(manifest)

    with open(LOCKFILE, "w", encoding="utf-8") as f:
        json.dump({"locked": installed}, f, indent=2)
    print(f"lockfile written: {LOCKFILE}")
    return 0


def cmd_list(args) -> int:
    manifest = load_manifest()
    deps = manifest.get("dependencies", {})
    if not deps:
        print("no dependencies declared")
        return 0
    print(f"{manifest.get('name')}@{manifest.get('version')}")
    for name, version in deps.items():
        print(f"  - {name}@{version}")
    return 0


def cmd_publish(args) -> int:
    manifest = load_manifest()
    print(f"publishing {manifest.get('name')}@{manifest.get('version')}")
    print("  (registry publishing uses an auth token; set JPY_TOKEN)")
    token = os.environ.get("JPY_TOKEN")
    if not token:
        print("error: JPY_TOKEN not set")
        return 1
    print("  publish not yet accepted by registry — batch 3 enables it")
    return 0


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="jpm", description="JapyScript package manager")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("init", help="create japy.json").set_defaults(func=cmd_init)

    p_ins = sub.add_parser("install", help="install packages")
    p_ins.add_argument("package", nargs="?")
    p_ins.set_defaults(func=cmd_install)

    sub.add_parser("list", help="list installed packages").set_defaults(func=cmd_list)
    sub.add_parser("publish", help="publish current project").set_defaults(func=cmd_publish)

    args = ap.parse_args(argv)
    if not hasattr(args, "func"):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
