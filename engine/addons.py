from __future__ import annotations

import importlib
import os
import pathlib
import sys
import types

CORE_DIR = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = "addon.json"
_PACKAGE = "addons"

_loaded: list | None = None
_registry: dict[str, list] = {}


def search_dirs() -> list[pathlib.Path]:
    dirs = [CORE_DIR.parent]
    for extra in (os.environ.get("RPG_ADDONS_PATH") or "").split(os.pathsep):
        if extra.strip():
            dirs.append(pathlib.Path(extra.strip()).resolve())
    out = []
    for d in dirs:
        if d.is_dir() and d not in out:
            out.append(d)
    return out


def discover(dirs=None) -> list[pathlib.Path]:
    found: dict[str, pathlib.Path] = {}
    for d in (search_dirs() if dirs is None else dirs):
        for sub in sorted(pathlib.Path(d).iterdir()):
            if (sub.is_dir() and sub.resolve() != CORE_DIR and sub.name.isidentifier()
                    and (sub / "__init__.py").is_file() and (sub / MANIFEST).is_file()):
                found.setdefault(sub.name, sub)
    return [found[k] for k in sorted(found)]


def _namespace(paths) -> types.ModuleType:
    pkg = sys.modules.get(_PACKAGE)
    if pkg is None:
        pkg = types.ModuleType(_PACKAGE)
        pkg.__doc__ = "Optional add-ons, discovered by engine.addons."
        pkg.__path__ = []
        sys.modules[_PACKAGE] = pkg
    for p in paths:
        if str(p) not in pkg.__path__:
            pkg.__path__.append(str(p))
    return pkg


def load_all() -> list:
    global _loaded
    if _loaded is not None:
        return _loaded
    _loaded = []
    folders = discover()
    _namespace(sorted({f.parent for f in folders}, key=str))
    for folder in folders:
        mod = importlib.import_module(f"{_PACKAGE}.{folder.name}")
        install = getattr(mod, "install", None)
        if callable(install):
            install()
        _loaded.append(mod)
    return _loaded


def loaded() -> list:
    return [m.__name__.rsplit(".", 1)[-1] for m in (_loaded or [])]


def register(kind: str, obj) -> None:
    _registry.setdefault(kind, []).append(obj)


def registered(kind: str) -> list:
    return list(_registry.get(kind, ()))


def extend_ruleset(ruleset_key: str, factory) -> None:
    register(f"ruleset:{ruleset_key}", factory)


def ruleset_extensions(ruleset_key: str) -> list:
    return registered(f"ruleset:{ruleset_key}")
