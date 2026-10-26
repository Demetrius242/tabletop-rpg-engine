import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.readiness import probe, render
from rulesets.dnd import version
from rulesets.dnd.core.dnd import DnDRuleset

if __name__ == "__main__":
    report = probe(DnDRuleset())
    render(report, version)
    sys.exit(0 if report.ready else 1)
