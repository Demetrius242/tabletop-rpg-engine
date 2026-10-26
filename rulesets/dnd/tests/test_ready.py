import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.readiness import probe
from rulesets.dnd.core.dnd import DnDRuleset
from rulesets.dnd import version


def test_ruleset_reports_ready():
    report = probe(DnDRuleset())
    failed = [l.name for l in report.lines if l.required and not l.ok]
    assert report.ready, f"UNFINISHED -- failing required checks: {failed}"


def test_version_metadata_present():
    assert version.NAME and version.VERSION and version.STATUS
    assert isinstance(version.DECLARES, dict)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
