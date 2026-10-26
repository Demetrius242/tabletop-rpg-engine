import sys
import pathlib
import tempfile

_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine import addons as A


def _make(base, name, *, init=True, manifest=True):
    d = pathlib.Path(base) / name
    d.mkdir()
    if init:
        (d / "__init__.py").write_text("def install():\n    pass\n", encoding="utf-8")
    if manifest:
        (d / A.MANIFEST).write_text('{"name": "%s"}' % name, encoding="utf-8")
    return d


def test_discover_needs_init_and_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        _make(tmp, "beta")
        _make(tmp, "alpha")
        _make(tmp, "no_manifest", manifest=False)
        _make(tmp, "no_init", init=False)
        _make(tmp, "not-an-identifier")
        assert [d.name for d in A.discover([tmp])] == ["alpha", "beta"]


def test_first_folder_of_a_name_wins():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        first = _make(a, "dup")
        _make(b, "dup")
        assert A.discover([a, b]) == [first]


def test_core_folder_is_never_an_addon():
    assert (A.CORE_DIR / "engine").is_dir()
    assert A.CORE_DIR not in [d.resolve() for d in A.discover([A.CORE_DIR.parent])]


def test_search_dirs_start_next_to_core_and_read_env():
    import os
    old = os.environ.get("RPG_ADDONS_PATH")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.environ["RPG_ADDONS_PATH"] = tmp
            dirs = A.search_dirs()
            assert dirs[0] == A.CORE_DIR.parent
            assert pathlib.Path(tmp).resolve() in dirs
        finally:
            if old is None:
                os.environ.pop("RPG_ADDONS_PATH", None)
            else:
                os.environ["RPG_ADDONS_PATH"] = old


def test_registry_round_trip():
    A.register("test.kind", "x")
    assert "x" in A.registered("test.kind")
    assert A.registered("test.nothing") == []


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
if __name__ == "__main__":
    ok = 0
    for t in ALL:
        try:
            t(); ok += 1
        except Exception as exc:
            print(f"FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{ok}/{len(ALL)} passed")
    sys.exit(0 if ok == len(ALL) else 1)
