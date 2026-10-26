from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from engine import addons as _addons
from engine.state import Combatant, GameState
from engine.scene import Presence, Scene

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAVES_DIR = ROOT / "web" / "saves"
CONFIG_PATH = ROOT / "web" / "web_config.json"

SKILL_ABILITY = {
    "acrobatics": "dex", "animal_handling": "wis", "arcana": "int", "athletics": "str",
    "deception": "cha", "history": "int", "insight": "wis", "intimidation": "cha",
    "investigation": "int", "medicine": "wis", "nature": "int", "perception": "wis",
    "performance": "cha", "persuasion": "cha", "religion": "int", "sleight_of_hand": "dex",
    "stealth": "dex", "survival": "wis",
}
ABILITY_ORDER = ("str", "dex", "con", "int", "wis", "cha")
ABILITY_LABEL = {"str": "Strength", "dex": "Dexterity", "con": "Constitution",
                 "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"}

RARITY_COLORS = {
    "common": "#b9c2cc", "uncommon": "#4cd07d", "rare": "#4ea3ff",
    "very_rare": "#b069ff", "legendary": "#ffac33", "artifact": "#ff5d5d",
}

_ALIGN_THEME = {
    "lg": ("#e8c45a", "Honor is the shield of the innocent.", "☀"),
    "ng": ("#7fd0a8", "Goodness asks no leave.", "❀"),
    "cg": ("#6fd0d8", "A free heart, a kind hand.", "✦"),
    "ln": ("#c9b79a", "Order endures where passion fails.", "⚖"),
    "tn": ("#bcae93", "Balance in all things.", "☯"),
    "cn": ("#cf9be0", "I answer to myself alone.", "✧"),
    "le": ("#c4506a", "Order through dominion.", "♛"),
    "ne": ("#9aa0a6", "Whatever it takes.", "☠"),
    "ce": ("#e0603a", "Burn it all and laugh.", "✺"),
}
_CLASS_GLYPH = {
    "barbarian": "⚔", "bard": "♪", "cleric": "✝", "druid": "❦", "fighter": "⚔",
    "monk": "✊", "paladin": "♛", "ranger": "➶", "rogue": "⚑", "sorcerer": "✶",
    "warlock": "☾", "wizard": "✸",
}


def _dnd():
    from rulesets.dnd.core.dnd import DnDRuleset
    return DnDRuleset()


def build_ruleset(key: str):
    if key == "storyteller":
        from rulesets.storyteller.core.storyteller import StorytellerRuleset
        return StorytellerRuleset()
    return _dnd()


def _version_of(key: str) -> dict:
    mod = "rulesets.dnd.version" if key == "dnd" else "rulesets.storyteller.version"
    import importlib
    v = importlib.import_module(mod)
    return {"name": getattr(v, "NAME", key), "version": getattr(v, "VERSION", "?"),
            "status": getattr(v, "STATUS", "")}


RULESET_CATEGORY = {"dnd": "d20 / D&D-based", "storyteller": "Storyteller (revised)"}


def list_rulesets() -> list:
    out = []
    for key in ("dnd", "storyteller"):
        v = _version_of(key)
        out.append({"key": key, "name": v["name"], "version": v["version"], "status": v["status"],
                    "wired": key == "dnd", "category": RULESET_CATEGORY.get(key, "Other"),
                    "blurb": ("A d20 system: races, classes, alignments, leveling, spells, items, "
                              "trade, and structured exploration scenes."
                              if key == "dnd" else
                              "Vampire: the Masquerade -- blood, Humanity, frenzy, Disciplines and "
                              "rituals. (Listed; full web wiring pending.)")})
    return out


def settings_for(ruleset_key: str) -> list:
    if ruleset_key != "dnd":
        return [{"key": "default", "name": "Default", "tone": ""}]
    rs = _dnd()
    out = []
    for key in rs.list_settings():
        s = rs.setting_info(key)
        out.append({"key": key, "name": getattr(s, "name", key),
                    "tone": getattr(s, "tone", ""),
                    "blurb": (getattr(s, "narration_brief", lambda: "")() or "")[:240]})
    return out


STORY_CATEGORIES = [("adventure", "Adventures"), ("free", "Free Exploration"), ("test", "Test scenes")]
_SCENE_TITLES = {"watchers_barrow": ("The Watcher's Barrow",
                                     "Sneak a cult-haunted Sword Coast barrow, sense what waits below, "
                                     "and choose your moment to strike. Begins with Aria (rogue) and "
                                     "Bertram (cleric).")}


def stories_for(ruleset_key: str, setting_key: str) -> list:
    out = [{"key": "__free__", "name": "Free Exploration", "category": "free",
            "blurb": "Begin with a ready adventurer in the chosen world and wander where you will."}]
    if ruleset_key != "dnd":
        return out
    rs = _dnd()
    if setting_key:
        rs.use_setting(setting_key)
    for adv in rs.list_adventures():
        out.append({"key": adv["key"], "name": adv["name"], "blurb": adv.get("blurb", ""),
                    "campaign": True, "category": "adventure", "detail": True})
    for key in rs.list_scenes():
        name, blurb = _SCENE_TITLES.get(key, (key.replace("_", " ").title(), "An authored scene."))
        out.append({"key": key, "name": name, "blurb": blurb, "category": "test"})
    return out


def _iter_conditions(cond):
    if isinstance(cond, dict):
        yield cond
        for v in cond.values():
            yield from _iter_conditions(v)
    elif isinstance(cond, (list, tuple)):
        for v in cond:
            yield from _iter_conditions(v)


def story_detail(ruleset_key: str, setting_key: str, story_key: str) -> dict:
    if not story_key or story_key == "__free__":
        return {"key": "__free__", "name": "Free Exploration", "kind": "free",
                "description": ("No authored plot -- you start with a ready party in the chosen world "
                                "and go wherever you like. The narrator improvises around your choices."),
                "chapters": [], "stats": []}
    rs = build_ruleset(ruleset_key)
    if ruleset_key == "dnd" and setting_key:
        rs.use_setting(setting_key)
    adv = rs.build_adventure(story_key) if hasattr(rs, "build_adventure") else None
    if adv is None:
        name, blurb = _SCENE_TITLES.get(story_key, (story_key.replace("_", " ").title(), ""))
        return {"key": story_key, "name": name, "kind": "test",
                "description": blurb or "A single authored exploration scene for quick testing.",
                "chapters": [], "stats": [{"label": "Type", "value": "single scene"}]}
    md = adv.metadata or {}
    events = list(adv.events.values())
    quests = sum(1 for e in events for t in e.tasks if not getattr(t, "hidden", False))
    npc_goals = sum(len(e.npc_tasks) for e in events)
    scene_keys = {e.scene_key for e in events if e.scene_key}
    items = set()
    for e in events:
        for t in e.tasks:
            for oc in t.outcomes:
                for c in _iter_conditions(oc.when):
                    if isinstance(c, dict) and c.get("has_item"):
                        items.add(c["has_item"])
    chapters = list(md.get("chapters") or [])
    done = sum(1 for c in chapters if c.get("implemented"))
    stats = [
        {"label": "Story beats", "value": len(events)},
        {"label": "Quests", "value": quests},
        {"label": "NPC goals", "value": npc_goals},
        {"label": "Scenes", "value": len(scene_keys)},
        {"label": "Party", "value": len(adv.party)},
    ]
    if items:
        stats.append({"label": "Key items", "value": len(items)})
    if chapters:
        stats.insert(0, {"label": "Chapters", "value": f"{done}/{len(chapters)} implemented"})
    return {"key": story_key, "name": adv.title, "kind": "adventure",
            "description": md.get("description") or md.get("blurb", ""),
            "tone": md.get("tone", ""), "chapters": chapters, "stats": stats,
            "party": [_party_brief(rs, spec) for spec in adv.party]}


def _party_brief(rs, spec: dict) -> dict:
    try:
        member = build_party_member(rs, spec, is_pc=True)
        sh = member.sheet
        return {"name": member.name, "race": sh.get("race", ""), "klass": sh.get("class", ""),
                "level": sh.get("level", 1)}
    except Exception:
        return {"name": spec.get("pregen", "?"), "race": "", "klass": "", "level": 1}


def _starter_pc(rs, spec, *, inventory=(), tools=()):
    pc = rs.build_pc(spec)
    pc.sheet.setdefault("inventory", [])
    for t in tools:
        if t not in pc.sheet.get("proficiencies", []):
            pc.sheet.setdefault("proficiencies", []).append(t)
    for k in inventory:
        rs.grant_item(pc, k)
    grant_starting_inventory(rs, pc)
    return pc


_FREE_PC = {"name": "Wren", "race": "half_elf", "class": "fighter", "background": "soldier",
            "alignment": "lg",
            "abilities": {"str": 15, "dex": 13, "con": 14, "int": 10, "wis": 12, "cha": 8},
            "skills": ["athletics", "perception"]}

_BARROW_PC = {"name": "Aria", "race": "elf", "class": "rogue", "background": "criminal",
              "alignment": "cn",
              "abilities": {"str": 8, "dex": 15, "con": 13, "wis": 12, "int": 14, "cha": 10},
              "skills": ["stealth", "perception", "investigation", "acrobatics"]}

_BARROW_ALLY = {"name": "Bertram", "race": "human", "class": "cleric", "background": "acolyte",
                "alignment": "lg",
                "abilities": {"str": 12, "dex": 10, "con": 13, "wis": 15, "int": 11, "cha": 14},
                "skills": ["medicine", "religion"]}


def is_adventure(ruleset_key: str, setting_key: str, story_key: str) -> bool:
    if not story_key or story_key == "__free__":
        return False
    rs = build_ruleset(ruleset_key)
    if ruleset_key == "dnd" and setting_key:
        rs.use_setting(setting_key)
    return hasattr(rs, "build_adventure") and rs.build_adventure(story_key) is not None


def build_session(ruleset_key: str, setting_key: str, story_key: str, party=None):
    rs = build_ruleset(ruleset_key)
    if ruleset_key == "dnd" and setting_key:
        rs.use_setting(setting_key)
    companions = []
    scene = None
    adv = rs.build_adventure(story_key) if hasattr(rs, "build_adventure") else None
    roster = [s for s in (party or []) if s] or (list(adv.party) if adv is not None else [])
    if adv is not None and roster:
        pc = build_party_member(rs, roster[0], is_pc=True)
        for spec in roster[1:]:
            companions.append(build_party_member(rs, spec, is_pc=False))
        start_ev = adv.events.get(adv.start_event)
        scene = rs.build_scene(start_ev.scene_key) if start_ev and start_ev.scene_key else None
        if scene is not None:
            for c in companions:
                key = c.name.split()[0].lower()
                scene.presences[key] = Presence(key, c.name, scene.pc_zone, kind="npc",
                                                disposition="friendly", combatant=c, follows_pc=True,
                                                note=f"{c.name}, at your side.")
            location = scene.zones[scene.pc_zone].name
        else:
            location = rs.setting_info(setting_key).name if setting_key else "the Underdark"
        state = GameState(pc=pc, location=location)
        if companions:
            state.flags["party"] = [c.name for c in companions]
        return rs, state, scene, companions
    if ruleset_key == "dnd" and story_key and story_key != "__free__":
        pc = _starter_pc(rs, _BARROW_PC, inventory=["potion_of_healing"], tools=["thieves_tools"])
        ally = _starter_pc(rs, _BARROW_ALLY, inventory=["potion_of_healing"])
        ally.is_pc = False
        companions = [ally]
        scene = rs.build_scene(story_key)
        if scene is not None:
            scene.presences["bertram"] = Presence(
                "bertram", "Bertram", scene.pc_zone, kind="npc", disposition="friendly",
                combatant=ally, follows_pc=True, note="A cleric of Tymora at your side.")
            location = scene.zones[scene.pc_zone].name
        else:
            location = rs.setting_info(setting_key).name if setting_key else "the wilds"
    else:
        pc = _starter_pc(rs, _FREE_PC, inventory=["potion_of_healing"])
        brief = ""
        try:
            loc = rs.location("roadside_tavern")
            location = getattr(loc, "name", None) or "a roadside tavern on the Sword Coast"
        except Exception:
            location = "a roadside tavern on the Sword Coast"
    state = GameState(pc=pc, location=location)
    if companions:
        state.flags["party"] = [c.name for c in companions]
    return rs, state, scene, companions


def _ability_mod(score: int) -> int:
    return (int(score) - 10) // 2


def _sign(n: int) -> str:
    return f"{n:+d}"


def character_view(rs, c: Combatant, *, is_party_leader=False) -> dict:
    sh = c.sheet
    ab = sh.get("abilities", {})
    pb = sh.get("proficiency_bonus", 2)
    profs = set(sh.get("proficiencies", []))
    saves_prof = set(sh.get("save_proficiencies", []))
    abilities = [{"key": a, "label": ABILITY_LABEL[a], "score": ab.get(a, 10),
                  "mod": _sign(_ability_mod(ab.get(a, 10)))} for a in ABILITY_ORDER]
    saves = [{"key": a, "label": ABILITY_LABEL[a][:3],
              "mod": _sign(_ability_mod(ab.get(a, 10)) + (pb if a in saves_prof else 0)),
              "proficient": a in saves_prof} for a in ABILITY_ORDER]
    skills = []
    for sk in sorted(SKILL_ABILITY):
        a = SKILL_ABILITY[sk]
        prof = sk in profs
        skills.append({"key": sk, "label": sk.replace("_", " ").title(),
                       "ability": a.upper(), "proficient": prof,
                       "mod": _sign(_ability_mod(ab.get(a, 10)) + (pb if prof else 0))})
    dex_mod = _ability_mod(ab.get("dex", 10))
    rp = sh.get("roleplay", {}) or {}
    chosen = rp.get("chosen", {}) if isinstance(rp, dict) else {}
    align_key = sh.get("alignment_key", "") or _infer_align_key(sh.get("alignment", ""))
    accent, motto, sigil = _ALIGN_THEME.get(align_key, ("#c9b79a", "", "✦"))
    inv = []
    for k in sh.get("inventory", []):
        info = rs.item_info(k) if hasattr(rs, "item_info") else None
        rarity = getattr(info, "rarity", "common") if info else "common"
        inv.append({"key": k, "name": info.name if info else k.replace("_", " ").title(),
                    "rarity": rarity, "color": RARITY_COLORS.get(rarity, "#b9c2cc")})
    view = {
        "name": c.name, "is_pc": c.is_pc,
        "race": sh.get("race", ""), "klass": sh.get("class", ""), "level": sh.get("level", 1),
        "background": sh.get("background", ""),
        "alignment": sh.get("alignment", ""), "alignment_key": align_key,
        "hp": sh.get("hp", 0), "max_hp": sh.get("max_hp", sh.get("hp", 0)),
        "ac": sh.get("ac", 10), "speed": sh.get("speed", 30),
        "initiative": _sign(dex_mod), "proficiency_bonus": _sign(pb),
        "condition": rs.health_descriptor(c) if hasattr(rs, "health_descriptor") else "",
        "abilities": abilities, "saves": saves, "skills": skills,
        "race_traits": sh.get("race_traits", []), "class_features": sh.get("class_features", []),
        "languages": sh.get("languages", []), "resistances": sh.get("resistances", []),
        "attacks": sh.get("attacks", []), "inventory": inv,
        "hit_dice": {"remaining": int(sh.get("hit_dice_remaining", sh.get("level", 1))),
                     "total": int(sh.get("hit_dice_total", sh.get("level", 1))),
                     "die": sh.get("hit_die", 8)},
        "encumbrance": (rs.encumbrance_status(c) if hasattr(rs, "encumbrance_status") else {}),
        "narrative": {
            "trait": chosen.get("trait", ""), "ideal": chosen.get("ideal", ""),
            "bond": chosen.get("bond", ""), "flaw": chosen.get("flaw", ""),
            "feature": (sh.get("background_feature") or {}).get("name", ""),
        },
        "decoration": {"accent": accent, "motto": motto, "align_sigil": sigil,
                       "class_glyph": _CLASS_GLYPH.get(sh.get("class_key", ""), "✦"),
                       "banner": f"{sh.get('race','')} {sh.get('class','')}".strip()},
    }
    if "gender_current" in sh:
        view["gender"] = {"initial": sh.get("gender_initial", ""), "current": sh.get("gender_current", ""),
                          "dissonant": int(sh.get("gender_dissonance", 0)) > 0,
                          "dissonance_rests": int(sh.get("gender_dissonance", 0))}
    view["sections"] = [sec for fn in _addons.registered("web.sheet_section")
                        if (sec := fn(rs, c))]
    return view


def _infer_align_key(label: str) -> str:
    if not label:
        return ""
    s = label.lower()
    law = "l" if "lawful" in s else ("c" if "chaotic" in s else "n")
    moral = "g" if "good" in s else ("e" if "evil" in s else "n")
    key = (law + moral)
    if key == "nn":
        return "tn"
    return key


def config_stats(rs, setting_key: str) -> dict:
    out = {}
    rules = rs.enabled_rules() if hasattr(rs, "enabled_rules") else set()
    try:
        from rulesets.dnd.additional import items as _items
        alli = _items.all_items(rules=rules)
        by_rarity = {}
        for it in alli:
            by_rarity[it.rarity] = by_rarity.get(it.rarity, 0) + 1
        out["items_total"] = len(alli)
        out["items_tradeable"] = len(_items.tradeable(rules=rules))
        out["items_by_rarity"] = by_rarity
    except Exception:
        pass
    for fn in _addons.registered("web.stats"):
        fn(rs, out)
    try:
        out["npcs"] = len(rs.list_npcs())
        out["locations"] = len(rs.list_locations())
        out["tradesmen"] = len(rs.list_tradesmen())
        out["scenes"] = len(rs.list_scenes())
        out["settings"] = len(rs.list_settings())
    except Exception:
        pass
    try:
        from rulesets.dnd.additional import spells as _spells
    except Exception:
        pass
    return out


def rules_in_use(ruleset_key: str) -> list:
    if ruleset_key != "dnd":
        return [{"name": "Storyteller core", "on": True, "locked": True}]
    return [
        {"name": "Ability checks, AC & hit points", "on": True, "locked": True},
        {"name": "Nine races, twelve classes (level 1-20)", "on": True, "locked": True},
        {"name": "Backgrounds, alignments & proficiencies", "on": True, "locked": True},
        {"name": "Spell preparation & slot/resource expenditure", "on": True, "locked": True},
        {"name": "Items, 5e trade & restocking shops", "on": True, "locked": True},
        {"name": "Encumbrance & equipment slots (class proficiency)", "on": True, "locked": True},
        {"name": "Hit-dice short-rest healing", "on": True, "locked": True},
        {"name": "Surprise round from stealth", "on": True, "locked": True},
        {"name": "Haggling (Persuasion-modified prices)", "on": True, "locked": True},
        {"name": "City long-rest rule (rent a room or face the Watch)", "on": True, "locked": True},
        {"name": "Structured exploration scenes", "on": True, "locked": True},
    ]


def optional_rules(ruleset_key: str, rs=None) -> list:
    rs = rs if rs is not None else build_ruleset(ruleset_key)
    rules = rs.optional_rules() if hasattr(rs, "optional_rules") else []
    return [dict(r, implemented=True) for r in rules]


def versions(ruleset_key: str, setting_key: str, story_key: str) -> dict:
    rv = _version_of(ruleset_key)
    out = {"ruleset": rv}
    if ruleset_key == "dnd":
        try:
            import importlib
            ev = importlib.import_module("rulesets.dnd.version")
        except Exception:
            pass
        if setting_key:
            s = _dnd().setting_info(setting_key)
            out["setting"] = {"name": getattr(s, "name", setting_key), "tone": getattr(s, "tone", "")}
        if story_key and story_key != "__free__":
            name = story_key.replace("_", " ").title()
            try:
                _rs = _dnd()
                if setting_key:
                    _rs.use_setting(setting_key)
                name = next((a["name"] for a in _rs.list_adventures() if a["key"] == story_key),
                            _SCENE_TITLES.get(story_key, (name,))[0])
            except Exception:
                pass
            out["story"] = {"name": name, "key": story_key}
        else:
            out["story"] = {"name": "Free Exploration", "key": "__free__"}
    try:
        import importlib
        top = (ROOT / "VERSION").read_text(encoding="utf-8").splitlines()
        out["engine"] = next((ln.split()[-1] for ln in top if ln.lower().startswith("engine")), "?")
    except Exception:
        out["engine"] = "?"
    return out


def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"ruleset": "dnd", "setting": "forgotten_realms", "story": "__free__"}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def update_config(**fields) -> dict:
    cfg = load_config()
    cfg.update(fields)
    save_config(cfg)
    return cfg


MODELS_DIR = ROOT / "llm" / "models"
DEFAULT_LLAMA = {
    "server_url": "http://127.0.0.1:8080/completion",
    "temperature": 0.85, "top_p": 0.95, "max_tokens": 512,
    "top_k": 40, "min_p": 0.05, "repeat_penalty": 1.1,
    "frequency_penalty": 0.0, "presence_penalty": 0.0, "seed": -1,
    "system_prompt": "",
    "model": "", "context_size": 8192, "gpu_layers": 999,
    "models_dir": "",
}
LLM_CONFIG_KEYS = ("temperature", "top_p", "max_tokens", "top_k", "min_p", "repeat_penalty",
                   "frequency_penalty", "presence_penalty", "seed", "system_prompt")


def models_dir() -> pathlib.Path:
    raw = str((load_config().get("llama", {}) or {}).get("models_dir", "") or "").strip()
    if raw:
        try:
            p = pathlib.Path(raw).expanduser()
            if p.is_dir():
                return p
        except Exception:
            pass
    return MODELS_DIR


def list_models() -> list:
    try:
        return sorted(p.name for p in models_dir().glob("*.gguf"))
    except Exception:
        return []


def load_llama() -> dict:
    llama = dict(DEFAULT_LLAMA)
    llama.update(load_config().get("llama", {}) or {})
    if not llama.get("model"):
        models = list_models()
        llama["model"] = models[0] if models else ""
    return llama


_UNSET = object()
_FLOAT_RANGES = {
    "temperature": (0.0, 2.0), "top_p": (0.0, 1.0), "min_p": (0.0, 1.0),
    "repeat_penalty": (0.0, 2.0), "frequency_penalty": (-2.0, 2.0), "presence_penalty": (-2.0, 2.0),
}
_INT_KEYS = ("max_tokens", "context_size", "gpu_layers", "top_k")


def _coerce_llama_value(key: str, v):
    if key in _FLOAT_RANGES:
        lo, hi = _FLOAT_RANGES[key]
        try:
            return max(lo, min(hi, float(v)))
        except (TypeError, ValueError):
            return _UNSET
    if key in _INT_KEYS:
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return _UNSET
    if key == "seed":
        try:
            s = int(v)
        except (TypeError, ValueError):
            return _UNSET
        return s if s >= 0 else -1
    return str(v)


def save_llama(partial: dict) -> dict:
    cur = load_llama()
    for k in DEFAULT_LLAMA:
        if k not in partial:
            continue
        v = _coerce_llama_value(k, partial[k])
        if v is not _UNSET:
            cur[k] = v
    update_config(llama=cur)
    return cur


LLM_CONFIGS_DIR = ROOT / "web" / "llm_configs"


def _sanitize_llm_config(settings: dict) -> dict:
    out = {}
    for k in LLM_CONFIG_KEYS:
        if k in (settings or {}):
            v = _coerce_llama_value(k, settings[k])
            out[k] = DEFAULT_LLAMA[k] if v is _UNSET else v
        else:
            out[k] = DEFAULT_LLAMA[k]
    return out


def ensure_default_llm_config() -> None:
    LLM_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    p = LLM_CONFIGS_DIR / "default.json"
    if not p.exists():
        p.write_text(json.dumps(_sanitize_llm_config(DEFAULT_LLAMA), indent=2), encoding="utf-8")


def list_llm_configs() -> list:
    ensure_default_llm_config()
    try:
        names = sorted(p.stem for p in LLM_CONFIGS_DIR.glob("*.json"))
    except Exception:
        names = []
    if "default" in names:
        names = ["default"] + [n for n in names if n != "default"]
    return names


def save_llm_config(name: str, settings: dict) -> str:
    LLM_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    safe = _safe_slot(name)
    (LLM_CONFIGS_DIR / f"{safe}.json").write_text(
        json.dumps(_sanitize_llm_config(settings), indent=2), encoding="utf-8")
    return safe


def load_llm_config(name: str) -> dict:
    safe = _safe_slot(name)
    try:
        raw = json.loads((LLM_CONFIGS_DIR / f"{safe}.json").read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    return _sanitize_llm_config(raw)


CONNECTION_KINDS = ("canned", "llama-cpp", "openai")
CONNECTION_ENDPOINTS = ("completions", "chat")
DEFAULT_CONNECTION = {
    "kind": "canned",
    "base_url": "http://127.0.0.1:8080",
    "endpoint": "completions",
    "api_key": "",
    "model": "",
    "timeout": 120,
}
CONNECTION_TIMEOUT_MIN = 5
CONNECTION_TIMEOUT_MAX = 3600


def _clean_timeout(val, fallback=120) -> int:
    try:
        secs = int(round(float(val)))
    except (TypeError, ValueError):
        return int(fallback)
    return max(CONNECTION_TIMEOUT_MIN, min(CONNECTION_TIMEOUT_MAX, secs))


def has_saved_connection() -> bool:
    return "connection" in load_config()


def load_connection() -> dict:
    conn = dict(DEFAULT_CONNECTION)
    conn.update(load_config().get("connection", {}) or {})
    if conn.get("kind") not in CONNECTION_KINDS:
        conn["kind"] = "canned"
    if conn.get("endpoint") not in CONNECTION_ENDPOINTS:
        conn["endpoint"] = "completions"
    conn["timeout"] = _clean_timeout(conn.get("timeout"))
    return conn


def save_connection(partial: dict) -> dict:
    cur = load_connection()
    if "kind" in partial:
        k = str(partial["kind"])
        cur["kind"] = k if k in CONNECTION_KINDS else cur["kind"]
    if "endpoint" in partial:
        e = str(partial["endpoint"])
        cur["endpoint"] = e if e in CONNECTION_ENDPOINTS else cur["endpoint"]
    for k in ("base_url", "api_key", "model"):
        if k in partial:
            cur[k] = str(partial[k] or "").strip()
    if "timeout" in partial:
        cur["timeout"] = _clean_timeout(partial["timeout"], cur.get("timeout", 120))
    update_config(connection=cur)
    return cur


_OPENAI_UNSENT = ("top_k", "min_p", "repeat_penalty")


def connection_restrictions(conn: dict) -> dict:
    from engine.llm import web_api_profile
    kind = (conn or {}).get("kind", "canned")
    if kind != "openai":
        return {"locked": [], "pinned": {}}
    locked = list(_OPENAI_UNSENT)
    pinned: dict = {}
    prof = web_api_profile(conn.get("base_url", ""))
    if prof:
        for f in prof.get("drop", ()):
            if f not in locked:
                locked.append(f)
        pinned = dict(prof.get("pin", {}))
    return {"locked": locked, "pinned": pinned}


def backend_label(conn: dict) -> str:
    kind = (conn or {}).get("kind", "canned")
    if kind == "canned":
        return "canned (no model)"
    if kind == "llama-cpp":
        return f"llama.cpp @ {conn.get('base_url') or '(unset)'}"
    if kind == "openai":
        style = "chat" if conn.get("endpoint") == "chat" else "completions"
        return f"OpenAI API ({style}) @ {conn.get('base_url') or '(unset)'}"
    return kind


def _safe_slot(slot: str) -> str:
    keep = "".join(ch for ch in (slot or "") if ch.isalnum() or ch in ("-", "_", " ")).strip()
    return (keep or "save").replace(" ", "_")[:48]


def list_saves() -> list:
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for d in sorted(SAVES_DIR.iterdir()):
        meta = d / "pc.json"
        if d.is_dir() and meta.exists():
            try:
                pc = json.loads(meta.read_text(encoding="utf-8"))
                world = json.loads((d / "world.json").read_text(encoding="utf-8")) if (d / "world.json").exists() else {}
                out.append({"slot": d.name, "pc_name": pc.get("name", "?"),
                            "location": world.get("location", ""),
                            "saved_at": world.get("saved_at", ""),
                            "ruleset": world.get("ruleset", ""), "story": world.get("story", "")})
            except Exception:
                continue
    return out


def save_session(slot: str, *, ruleset_key, setting_key, story_key, state: GameState,
                 scene: Scene | None, companions: list) -> dict:
    slot = _safe_slot(slot)
    d = SAVES_DIR / slot
    d.mkdir(parents=True, exist_ok=True)
    pc_doc = state.pc.to_dict()
    pc_doc["_meta"] = {"ruleset": ruleset_key, "setting": setting_key, "story": story_key}
    flags = {k: v for k, v in state.flags.items()
             if k not in ("present_enemies", "combat_arena", "party_companions")}
    world_doc = {
        "saved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "ruleset": ruleset_key, "setting": setting_key, "story": story_key,
        "location": state.location, "mode": state.mode, "flags": flags,
        "history": [{"role": t.role, "text": t.text} for t in state.history[-12:]],
        "companions": [c.to_dict() for c in companions],
        "scene": scene.to_dict() if scene is not None else None,
        "versions": versions(ruleset_key, setting_key, story_key),
    }
    (d / "pc.json").write_text(json.dumps(pc_doc, indent=2), encoding="utf-8")
    (d / "world.json").write_text(json.dumps(world_doc, indent=2), encoding="utf-8")
    return {"slot": slot, "files": ["pc.json", "world.json"], "saved_at": world_doc["saved_at"]}


def load_saved(slot: str):
    slot = _safe_slot(slot)
    d = SAVES_DIR / slot
    pc_doc = json.loads((d / "pc.json").read_text(encoding="utf-8"))
    world = json.loads((d / "world.json").read_text(encoding="utf-8"))
    meta = pc_doc.get("_meta", {})
    ruleset_key = world.get("ruleset") or meta.get("ruleset", "dnd")
    setting_key = world.get("setting") or meta.get("setting", "")
    story_key = world.get("story") or meta.get("story", "__free__")
    rs = build_ruleset(ruleset_key)
    if ruleset_key == "dnd" and setting_key:
        rs.use_setting(setting_key)
    pc_doc.pop("_meta", None)
    pc = Combatant.from_dict(pc_doc)
    state = GameState(pc=pc, location=world.get("location", ""), mode=world.get("mode", "exploration"),
                      flags=dict(world.get("flags", {})))
    from engine.state import Turn
    state.history = [Turn(t["role"], t["text"]) for t in world.get("history", [])]
    companions = [Combatant.from_dict(c) for c in world.get("companions", [])]
    scene = Scene.from_dict(world["scene"]) if world.get("scene") else None
    return ruleset_key, setting_key, story_key, rs, state, scene, companions


import random as _random

try:
    from rulesets.dnd.additional import items as _items_cat
except Exception:
    _items_cat = None
try:
    from rulesets.dnd.additional import spells as _spells_cat
except Exception:
    _spells_cat = None
try:
    from rulesets.dnd.additional.gender import GENDERS as _GENDERS
except Exception:
    _GENDERS = ("male", "female", "androgynous", "non_applicable")

_PB_COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
_PB_BUDGET = 27
_STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
_SCHOOL_ICON = {"abjuration": "🛡", "conjuration": "✦", "divination": "👁", "enchantment": "💗",
                "evocation": "🔥", "illusion": "🌀", "necromancy": "💀", "transmutation": "⚗"}


def _g(obj, key, default=None):
    if obj is None:
        return default
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def point_buy_config() -> dict:
    return {"budget": _PB_BUDGET, "min": 8, "max": 15,
            "cost": {str(k): v for k, v in _PB_COST.items()}, "abilities": list(ABILITY_ORDER),
            "standard_array": list(_STANDARD_ARRAY)}


def point_buy_spent(scores: dict) -> int | None:
    total = 0
    for v in scores.values():
        v = int(v)
        if v < 8 or v > 15:
            return None
        total += _PB_COST.get(v, 999)
    return total


def roll_ability_scores(abilities=None, seed=None) -> dict:
    rng = _random.Random(seed)
    abils = [str(a)[:16] for a in (abilities or ABILITY_ORDER)][:12]
    def roll4d6():
        d = sorted((rng.randint(1, 6) for _ in range(4)), reverse=True)
        return sum(d[:3])
    return {a: roll4d6() for a in abils}


def creation_options(rs, *, rules=()) -> dict:
    races = []
    for k in rs.list_races():
        info = rs.race_info(k)
        bonuses = _g(info, "ability_bonuses") or _g(info, "bonus", {}) or {}
        races.append({"key": k, "name": _g(info, "label", k.title()),
                      "blurb": (_g(info, "blurb", "") or "")[:140],
                      "bonuses": {a: bonuses.get(a, 0) for a in bonuses},
                      "skills": list(_g(info, "skills", ()) or ()),
                      "speed": _g(info, "speed", 30)})
    classes = []
    for k in rs.list_classes():
        info = rs.class_info(k)
        skill_list = _g(info, "skill_list", None) or _g(info, "skills", ()) or ()
        classes.append({"key": k, "name": _g(info, "label", k.title()),
                        "blurb": (_g(info, "blurb", "") or "")[:140],
                        "hit_die": _g(info, "hit_die", 8),
                        "skill_list": list(skill_list),
                        "skill_choices": int(_g(info, "skill_choices", len(skill_list) or 2)),
                        "saves": list(_g(info, "saving_throws", ()) or ()),
                        "caster": bool(_g(info, "spellcasting", None))})
    backgrounds = []
    for k in rs.list_backgrounds():
        info = rs.background_info(k)
        backgrounds.append({"key": k, "name": _g(info, "label", k.title()),
                            "skills": list(_g(info, "skills", ()) or ()),
                            "equipment": list(_g(info, "equipment", ()) or ()),
                            "feature": _g(_g(info, "feature", None), "name", "") if _g(info, "feature", None) else ""})
    aligns = []
    for k in rs.list_alignments():
        al = rs._align.get(k) if getattr(rs, "_align", None) else None
        aligns.append({"key": k, "label": _g(al, "label", k.upper())})
    out = {
        "abilities": [{"key": a, "label": ABILITY_LABEL[a]} for a in ABILITY_ORDER],
        "point_buy": point_buy_config(),
        "races": races, "classes": classes, "backgrounds": backgrounds, "alignments": aligns,
        "skills": [{"key": s, "label": s.replace("_", " ").title(), "ability": SKILL_ABILITY[s].upper()}
                   for s in sorted(SKILL_ABILITY)],
        "pregens": pregens(),
        "genders": list(_GENDERS),
    }
    for fn in _addons.registered("web.creation_options"):
        fn(rs, out, set(rules or ()))
    return out


def pregens() -> list:
    from rulesets.dnd.settings.forgotten_realms.pregens import PREGEN_META
    return list(PREGEN_META)


def _pregen_forms() -> dict:
    from rulesets.dnd.settings.forgotten_realms.pregens import PREGEN_FORMS
    return PREGEN_FORMS


def grant_starting_inventory(rs, actor) -> None:
    if _items_cat is None:
        return
    ck = actor.sheet.get("class_key", "")
    inv = actor.sheet.setdefault("inventory", [])
    for key in _items_cat.starting_kit(ck):
        if key not in inv:
            inv.append(key)
    if getattr(rs, "_equipment", None) is not None:
        rs._equipment.auto_equip_kit(rs, actor)


def _autofill_spells(rs, actor) -> None:
    sc = actor.sheet.get("spellcasting")
    if not sc or _spells_cat is None:
        return
    ck = actor.sheet.get("class_key", "")
    cantrips = _spells_cat.cantrip_keys_for_class(ck)[: sc.get("cantrips_known", 0)]
    rs.set_cantrips(actor, cantrips)
    pool = _spells_cat.spell_keys_for_class(ck, min_level=1)[: sc.get("spells_count", 0)]
    if sc.get("spells_method") == "known":
        rs.set_known_spells(actor, pool)
    else:
        rs.prepare_spells(actor, pool)


def build_custom_session(ruleset_key: str, setting_key: str, pc_spec: dict, allies=None):
    rs = build_ruleset(ruleset_key)
    if ruleset_key == "dnd" and setting_key:
        rs.use_setting(setting_key)
    pc = build_party_member(rs, pc_spec or {}, is_pc=True)
    if allies is None:
        ally_specs = []
    elif isinstance(allies, dict):
        ally_specs = [allies]
    else:
        ally_specs = list(allies)
    companions = [build_party_member(rs, spec, is_pc=False) for spec in ally_specs if spec]
    try:
        loc = rs.location("roadside_tavern")
        location = getattr(loc, "name", None) or "a roadside tavern on the Sword Coast"
    except Exception:
        location = rs.setting_info(setting_key).name if setting_key else "a roadside tavern"
    state = GameState(pc=pc, location=location)
    if companions:
        state.flags["party"] = [c.name for c in companions]
    return rs, state, None, companions


def build_custom_pc(rs, form: dict):
    sel = dict(form or {})
    pc = rs.build_pc(sel)
    grant_starting_inventory(rs, pc)
    _autofill_spells(rs, pc)
    return pc


def build_party_member(rs, spec: dict, *, is_pc=True):
    if spec.get("pregen"):
        form = _pregen_forms().get(spec["pregen"])
        if form is None:
            raise ValueError(f"unknown pregen {spec['pregen']!r}")
        member = build_custom_pc(rs, form)
    else:
        member = build_custom_pc(rs, spec.get("form", {}))
    if not is_pc:
        member.is_pc = False
    return member


def item_detail(rs, key: str) -> dict:
    info = rs.item_info(key) if hasattr(rs, "item_info") else None
    if info is None:
        return {"key": key, "name": key.replace("_", " ").title(), "found": False}
    rarity = _g(info, "rarity", "common")
    special = _g(info, "special", "")
    return {
        "key": key, "found": True, "name": _g(info, "name", key.title()),
        "category": _g(info, "category", "gear"), "rarity": rarity,
        "rarity_color": RARITY_COLORS.get(rarity, "#b9c2cc"),
        "value": _g(info, "value", 0), "attunement": bool(_g(info, "attunement", False)),
        "bonuses": list(_g(info, "bonuses", ()) or ()),
        "effects": _g(info, "effects", ""), "lore": _g(info, "lore", ""),
        "special": special if not _g(info, "plot", False) else "",
    }


def _spell_brief(rs, spell) -> dict:
    sp = (rs.spell_info(spell) if hasattr(rs, "spell_info") else None) if isinstance(spell, str) else spell
    key = spell if isinstance(spell, str) else _g(spell, "key", "")
    if sp is None:
        return {"key": key, "name": (key or "").replace("_", " ").title(), "level": 0,
                "school": "", "desc": "", "icon": "✦"}
    school = _g(sp, "school", "")
    return {"key": _g(sp, "key", key), "name": _g(sp, "name", (key or "").title()),
            "level": _g(sp, "level", 0), "school": school, "desc": _g(sp, "desc", ""),
            "icon": _SCHOOL_ICON.get(school, "✦")}


def spellbook_view(rs, actor) -> dict:
    sc = actor.sheet.get("spellcasting")
    if not sc:
        return {"name": actor.name, "caster": False}
    ck = actor.sheet.get("class_key", "")
    by_level = _spells_cat.by_level(ck) if _spells_cat else {}
    repertoire = {str(lvl): [_spell_brief(rs, k) for k in keys] for lvl, keys in by_level.items()}
    all_cantrips = [_spell_brief(rs, k) for k in (_spells_cat.cantrip_keys_for_class(ck) if _spells_cat else [])]
    slots = actor.sheet.get("spell_slots", {}) or {}
    remaining = actor.sheet.get("spell_slots_remaining", {}) or {}
    return {
        "name": actor.name, "caster": True, "class": actor.sheet.get("class", ""),
        "ability": sc.get("ability", "").upper(), "save_dc": sc.get("save_dc"),
        "attack_bonus": sc.get("attack_bonus"), "method": sc.get("spells_method", "prepared"),
        "cantrips_known": sc.get("cantrips_known", 0), "spells_count": sc.get("spells_count", 0),
        "slots": {str(k): v for k, v in slots.items()},
        "slots_remaining": {str(k): v for k, v in remaining.items()},
        "repertoire": repertoire, "all_cantrips": all_cantrips,
        "cantrips": list(sc.get("cantrips", [])),
        "known": list(sc.get("known", [])), "prepared": list(sc.get("prepared", [])),
    }


def party_casters(rs, members) -> list:
    return [m.name for m in members if m.sheet.get("spellcasting")]
