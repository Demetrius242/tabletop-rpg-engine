from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Line:
    name: str
    ok: bool
    required: bool
    detail: str


@dataclass
class Report:
    ready: bool
    lines: list


def probe(ruleset) -> Report:
    from engine.difficulty import DifficultyBand
    lines: list[Line] = []
    state = {"pc": None}

    def check(name, required, fn):
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        lines.append(Line(name, bool(ok), required, str(detail)))

    def skills():
        s = ruleset.skill_names()
        return len(s) > 0, f"{len(s)} skills defined"

    def diffmap():
        bands = list(DifficultyBand)
        for b in bands:
            ruleset.difficulty_for_band(b)
        return True, f"all {len(bands)} difficulty bands map to a Difficulty"

    def pc_factory():
        pc = ruleset.make_pc("Probe")
        state["pc"] = pc
        ok = pc is not None and bool(getattr(pc, "sheet", None))
        return ok, f"make_pc -> sheet with {len(pc.sheet)} keys"

    def resolution():
        pc = state["pc"]
        skill = ruleset.skill_names()[0]
        diff = ruleset.difficulty_for_band(DifficultyBand.MEDIUM)
        out = ruleset.resolve_check(pc, skill, diff)
        return out.band is not None, f"resolve_check('{skill}') -> {out.band.value}"

    def health():
        pc = state["pc"]
        d, f, k = ruleset.health_descriptor(pc), ruleset.health_fraction(pc), ruleset.is_defeated(pc)
        ok = isinstance(d, str) and 0.0 <= f <= 1.0 and isinstance(k, bool)
        return ok, f"descriptor '{d}', fraction {f:.2f}, defeated={k}"

    def combat():
        pc = state["pc"]
        tm = ruleset.turn_model()
        make_enemy = getattr(ruleset, "make_enemy", None)
        foe = make_enemy("Sparring Foe") if make_enemy else ruleset.make_pc("Foe")
        res = tm.resolve_attack(pc, foe)
        return hasattr(res, "hit"), f"turn model resolves an attack (hit={res.hit})"

    def creation():
        spec = ruleset.creation_spec()
        return True, (f"{len(spec)} creation steps" if spec else "no creation wizard (optional)")

    def features():
        from engine.ruleset import Ruleset
        feats = []
        if ruleset.morality() is not None:
            feats.append("morality/degeneration")
        if type(ruleset).try_special_action is not Ruleset.try_special_action:
            feats.append("explicit invocation (powers/rituals)")
        if type(ruleset).available_combat_powers is not Ruleset.available_combat_powers:
            feats.append("combat powers")
        return True, ", ".join(feats) or "none beyond the core"

    check("skill catalog", True, skills)
    check("difficulty mapping", True, diffmap)
    check("PC factory", True, pc_factory)
    check("check resolution", True, resolution)
    check("health track", True, health)
    check("combat resolution", True, combat)
    check("creation wizard", False, creation)
    check("flavor systems", False, features)

    ready = all(l.ok for l in lines if l.required)
    return Report(ready=ready, lines=lines)


def render(report: Report, version=None) -> None:
    if version is not None:
        print(f"{getattr(version, 'NAME', 'Ruleset')}  v{getattr(version, 'VERSION', '?')}"
              f"  [{getattr(version, 'STATUS', 'unknown')}]")
        if getattr(version, "SUMMARY", ""):
            print(f"  {version.SUMMARY}")
        print("-" * 64)
    req = [l for l in report.lines if l.required]
    passed = sum(1 for l in req if l.ok)
    for l in report.lines:
        mark = "PASS" if l.ok else "FAIL"
        tag = "required" if l.required else "optional"
        print(f"  [{mark}] {l.name:<22} ({tag})  {l.detail}")
    print("-" * 64)
    verdict = "READY" if report.ready else "UNFINISHED"
    print(f"{verdict}   ({passed}/{len(req)} required checks passed)")
