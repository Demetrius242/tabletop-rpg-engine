import sys
import pathlib
import types

_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine import narration as N


def test_genre_for_tone_maps_known_labels():
    assert N.genre_for_tone("a tale of dread and nightmare") == "horror"
    assert N.genre_for_tone("grimdark and brutal") == "grimdark"
    assert N.genre_for_tone("heroic high fantasy with frontier grit") == "heroic"
    assert N.genre_for_tone("sword and sorcery, pulpy") == "sword_and_sorcery"
    assert N.genre_for_tone("noir investigation") == "mystery"
    assert N.genre_for_tone("") == N.DEFAULT_GENRE
    assert N.genre_for_tone("something unmappable") == N.DEFAULT_GENRE


def test_style_block_includes_genre_and_mode():
    block = N.style_block(genre_key="horror", mode_key="exploration")
    assert "How to narrate this beat:" in block
    assert N.GENRES["horror"].label in block and "STYLE" in block
    assert N.MODES["exploration"].label in block and "NARRATION MODE" in block
    assert "Cold mineral air" in block


def test_each_mode_has_a_worked_example():
    for key in ("exploration", "dialogue", "combat"):
        assert N.MODES[key].example.strip(), f"{key} mode should ship an example"


def test_genre_examples_present_and_vivid():
    for g in N.GENRES.values():
        assert g.example.strip()
        assert len(g.example) >= 80


def _test_register():
    reg = N.Register("solemn_test", "Solemn (test)", "Measured, grave, ceremonial.",
                     {"opening": "The bells fall silent one by one.", "unused": ""},
                     heading="TEST REGISTER")
    N.add_register(reg, aliases=("grave_test",))
    return reg


def test_register_overlay_block_and_aliases():
    reg = _test_register()
    assert N.register("solemn_test") is reg and N.register("GRAVE_TEST") is reg
    assert N.register("nonsense") is None
    block = N.style_block(genre_key="horror", mode_key="dialogue", register_key="solemn_test")
    assert "TEST REGISTER" in block and "Solemn (test)" in block
    assert "[opening]" in block and "The bells fall silent" in block
    assert "[unused]" not in block
    plain = N.style_block(genre_key="horror", mode_key="dialogue")
    assert "TEST REGISTER" not in plain


def test_unknown_register_key_is_ignored():
    block = N.style_block(genre_key="horror", mode_key="dialogue", register_key="no_such_register")
    assert block == N.style_block(genre_key="horror", mode_key="dialogue")


def _card(**kw):
    base = dict(name="Brannor", role="blacksmith", description="A singed-bearded dwarf.",
                demeanor="Gruff but honest.", voice="Blunt and clipped.",
                mannerisms="Tests every edge with a thumb.",
                dialogue_examples=("Daggerford pays its debts.", "Coin's coin."))
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_speaking_brief_uses_voice_mannerisms_and_examples():
    brief = N.speaking_brief(_card())
    assert "Now voicing Brannor" in brief and "blacksmith" in brief
    assert "Blunt and clipped" in brief and "Tests every edge" in brief
    assert "Daggerford pays its debts." in brief
    assert "do NOT reuse" in brief.lower() or "not reuse" in brief.lower()


def test_speaking_brief_skips_missing_fields():
    brief = N.speaking_brief(types.SimpleNamespace(name="Stranger", role="", description="",
                                                   demeanor="", voice="", mannerisms="",
                                                   dialogue_examples=()))
    assert "Now voicing Stranger" in brief
    assert "Mannerisms" not in brief and "Sample lines" not in brief


def test_differentiate_is_deterministic_and_distinct():
    names = ["Guard", "Guard", "Guard", "Guard"]
    a = N.differentiate(names, seed=7)
    b = N.differentiate(names, seed=7)
    assert a == b
    looks = [r["appearance"] for r in a]
    manners = [r["manner"] for r in a]
    assert len(set(looks)) == len(looks)
    assert len(set(manners)) == len(manners)
    assert N.differentiate(names, seed=8) != a


def test_differentiate_accepts_objects_with_name():
    rows = N.differentiate([types.SimpleNamespace(name="Cultist") for _ in range(3)], seed=1)
    assert [r["name"] for r in rows] == ["Cultist", "Cultist", "Cultist"]
    assert all(r["appearance"] and r["manner"] for r in rows)


def test_group_brief_names_each_figure():
    text = N.group_brief(["Muk", "Grish", "Tev"], role="cultists", seed=3)
    assert "cultists" in text
    for n in ("Muk", "Grish", "Tev"):
        assert n in text


def test_engine_attaches_register_overlay_by_key():
    from engine.engine import ExplorationEngine
    from engine.llm import FakeLLMClient
    from engine.state import GameState
    from rulesets.dnd.core.dnd import DnDRuleset

    _test_register()
    rs = DnDRuleset(); rs.use_setting("forgotten_realms")
    pc = rs.build_pc({"name": "Lyra", "race": "human", "class": "bard", "background": "charlatan",
                      "alignment": "cn",
                      "abilities": {"str": 10, "dex": 12, "con": 12, "int": 10, "wis": 10, "cha": 16},
                      "skills": ["persuasion"]})

    class _P:
        def emit(self, e): pass
        def read_action(self): raise EOFError

    eng = ExplorationEngine(client=FakeLLMClient(), presenter=_P(),
                            state=GameState(pc=pc, location="Triboar"), ruleset=rs, scene=None)
    plain = eng._narrator_system("exploration")
    overlaid = eng._narrator_system("dialogue", "solemn_test")
    assert "TEST REGISTER" not in plain
    assert "TEST REGISTER" in overlaid and "The bells fall silent" in overlaid
    assert "heroic" in overlaid.lower()


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
