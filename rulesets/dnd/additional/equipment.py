from __future__ import annotations

SLOTS = ["main_hand", "off_hand", "armor", "helm", "cloak", "gloves", "boots", "amulet", "ring_1", "ring_2"]
SLOT_LABEL = {"main_hand": "Main hand", "off_hand": "Off hand", "armor": "Body", "helm": "Head",
              "cloak": "Cloak", "gloves": "Hands", "boots": "Feet", "amulet": "Amulet",
              "ring_1": "Ring", "ring_2": "Ring"}
SLOT_GROUP = {"main_hand": "weapon", "off_hand": "weapon", "armor": "armor", "helm": "armor",
              "cloak": "armor", "gloves": "armor", "boots": "armor", "amulet": "jewelry",
              "ring_1": "jewelry", "ring_2": "jewelry"}

ARMOR_PROF = {
    "barbarian": {"light", "medium", "shield"}, "bard": {"light"},
    "cleric": {"light", "medium", "shield"}, "druid": {"light", "medium", "shield"},
    "fighter": {"light", "medium", "heavy", "shield"}, "monk": set(),
    "paladin": {"light", "medium", "heavy", "shield"}, "ranger": {"light", "medium", "shield"},
    "rogue": {"light"}, "sorcerer": set(), "warlock": {"light"}, "wizard": set(),
}
WEAPON_PROF = {
    "barbarian": {"simple", "martial"}, "fighter": {"simple", "martial"},
    "paladin": {"simple", "martial"}, "ranger": {"simple", "martial"},
    "rogue": {"simple", "finesse"}, "bard": {"simple", "finesse"}, "monk": {"simple", "finesse"},
    "cleric": {"simple"}, "druid": {"simple"}, "sorcerer": {"simple"},
    "warlock": {"simple"}, "wizard": {"simple"},
}
ENC_LIGHT, ENC_HEAVY = 5, 10
_DEFAULT_WEIGHT = {"weapon": 3, "armor": 20, "shield": 6, "ring": 0, "wondrous": 1, "rod": 4,
                   "staff": 4, "wand": 1, "potion": 0.5, "scroll": 0, "gear": 1, "tool": 5, "ammunition": 1}


def _g(item, key, default=None):
    return getattr(item, key, default) if item is not None else default


def item_slot(item) -> str:
    s = _g(item, "slot", "") or ""
    if s:
        return s
    cat = _g(item, "category", "")
    if cat == "weapon":
        return "main_hand"
    if cat == "armor":
        return "armor"
    if cat == "shield":
        return "off_hand"
    if cat == "ring":
        return "ring_1"
    if cat == "wondrous":
        name = (_g(item, "name", "") or "").lower()
        return "cloak" if ("cloak" in name or "cape" in name) else "amulet"
    return ""


def is_equippable(item) -> bool:
    return bool(item_slot(item))


def item_weight(item) -> float:
    w = _g(item, "weight", 0) or 0
    if w:
        return float(w)
    return float(_DEFAULT_WEIGHT.get(_g(item, "category", ""), 1))


def item_grants(item) -> dict:
    out: dict = {}
    for g in (_g(item, "grants", ()) or ()):
        if ":" in g:
            k, v = g.split(":", 1)
            try:
                out[k.strip().lower()] = int(v.replace("+", ""))
            except ValueError:
                pass
    if out or _g(item, "armor_type", "") or _g(item, "category", "") == "weapon":
        return out
    import re
    for b in (_g(item, "bonuses", ()) or ()):
        m = re.match(r"\s*\+(\d+)\s*([A-Za-z ]*)", str(b))
        if m:
            amt = int(m.group(1)); what = m.group(2).strip().lower()
            if "ac" in what or what == "":
                out["ac" if "ac" in what else "weapon"] = amt
            else:
                out[what.split()[0]] = amt
    return out


def _class_key(sheet) -> str:
    return (sheet.get("class_key") or "").lower()


def proficient_with(sheet, item) -> bool:
    ck = _class_key(sheet)
    at = _g(item, "armor_type", "")
    if at:
        return at in ARMOR_PROF.get(ck, set())
    if _g(item, "category", "") == "weapon" or item_slot(item) in ("main_hand", "off_hand") and _g(item, "category") == "weapon":
        kind = _g(item, "weapon_kind", "") or "simple"
        profs = WEAPON_PROF.get(ck, {"simple"})
        if kind == "simple":
            return "simple" in profs
        return "martial" in profs or (_g(item, "finesse", False) and "finesse" in profs)
    return True


def carry_capacity(sheet) -> float:
    return sheet.get("abilities", {}).get("str", 10) * 15.0


def carried_weight(sheet, lookup) -> float:
    total = 0.0
    for key in list(sheet.get("inventory", [])) + list(sheet.get("equipped", {}).values()):
        total += item_weight(lookup(key))
    return round(total, 1)


def encumbrance(sheet, lookup) -> dict:
    cap = carry_capacity(sheet)
    w = carried_weight(sheet, lookup)
    str_score = sheet.get("abilities", {}).get("str", 10)
    if w > str_score * ENC_HEAVY:
        status, speed = "heavily encumbered", -20
    elif w > str_score * ENC_LIGHT:
        status, speed = "encumbered", -10
    else:
        status, speed = "unencumbered", 0
    return {"weight": w, "capacity": cap, "status": status, "speed_penalty": speed,
            "over": w > cap}


def _slot_ok_for_item(item, slot) -> bool:
    nat = item_slot(item)
    grp = SLOT_GROUP.get(slot)
    if SLOT_GROUP.get(nat) != grp:
        return False
    if grp == "weapon":
        if _g(item, "category") == "shield":
            return slot == "off_hand"
        if slot == "off_hand" and _g(item, "hands", 1) >= 2:
            return False
        return True
    if grp == "jewelry":
        if _g(item, "category") == "ring":
            return slot in ("ring_1", "ring_2")
        return slot == nat or (nat == "amulet" and slot == "amulet") or (nat == "cloak" and slot == "cloak")
    return slot == nat


def can_equip(actor, item, slot, *, in_combat=False, lookup=None) -> dict:
    sheet = actor.sheet
    if in_combat:
        return {"ok": False, "reason": "You can't change gear in the middle of a fight."}
    if item is None or not is_equippable(item):
        return {"ok": False, "reason": "That can't be equipped."}
    if slot not in SLOTS:
        return {"ok": False, "reason": "No such slot."}
    if not _slot_ok_for_item(item, slot):
        return {"ok": False, "reason": f"{_g(item,'name','That')} doesn't go in the {SLOT_LABEL.get(slot, slot)} slot."}
    if not proficient_with(sheet, item):
        return {"ok": False, "reason": f"Your class isn't proficient with {_g(item,'name','that')}."}
    equipped = sheet.get("equipped", {})
    if slot == "main_hand" and _g(item, "hands", 1) >= 2 and equipped.get("off_hand"):
        return {"ok": False, "reason": "A two-handed weapon needs the off hand free."}
    if slot == "off_hand":
        mh_key = equipped.get("main_hand")
        if mh_key is not None and lookup is not None and _g(lookup(mh_key), "hands", 1) >= 2:
            return {"ok": False, "reason": "Your main weapon is two-handed; the off hand can't be used."}
    return {"ok": True, "reason": ""}


def equip(rs, actor, item_key, slot, *, in_combat=False) -> dict:
    item = rs.item_info(item_key) if hasattr(rs, "item_info") else None
    chk = can_equip(actor, item, slot, in_combat=in_combat, lookup=lambda k: rs.item_info(k))
    if not chk["ok"]:
        return {"ok": False, "message": chk["reason"]}
    sheet = actor.sheet
    inv = sheet.setdefault("inventory", [])
    equipped = sheet.setdefault("equipped", {})
    if item_key not in inv and item_key not in equipped.values():
        return {"ok": False, "message": "You aren't carrying that."}
    if item_key in inv:
        inv.remove(item_key)
    if equipped.get(slot):
        inv.append(equipped[slot])
    if slot == "main_hand" and _g(item, "hands", 1) >= 2 and equipped.get("off_hand"):
        inv.append(equipped.pop("off_hand"))
    equipped[slot] = item_key
    recompute(rs, actor)
    return {"ok": True, "message": f"Equipped {_g(item,'name',item_key)}.", "slot": slot}


def unequip(rs, actor, slot) -> dict:
    sheet = actor.sheet
    equipped = sheet.setdefault("equipped", {})
    key = equipped.pop(slot, None)
    if key is None:
        return {"ok": False, "message": "Nothing in that slot."}
    sheet.setdefault("inventory", []).append(key)
    recompute(rs, actor)
    return {"ok": True, "message": "Unequipped.", "slot": slot}


def recompute(rs, actor) -> None:
    sheet = actor.sheet
    lookup = (lambda k: rs.item_info(k)) if hasattr(rs, "item_info") else (lambda k: None)
    equipped = sheet.get("equipped", {})
    sheet.setdefault("base_attacks", [dict(a) for a in sheet.get("attacks", [])])
    dex = (sheet.get("abilities", {}).get("dex", 10) - 10) // 2
    base_ac = 10 + dex

    overlay: dict = {}
    for key in equipped.values():
        for stat, amt in item_grants(lookup(key)).items():
            overlay[stat] = overlay.get(stat, 0) + amt
    sheet["equip_bonuses"] = overlay

    body = lookup(equipped.get("armor")) if equipped.get("armor") else None
    if body is not None and _g(body, "ac", 0):
        ac = _g(body, "ac", 11) + min(dex, _g(body, "dex_cap", 99))
    else:
        ac = base_ac
    shield = lookup(equipped.get("off_hand")) if equipped.get("off_hand") else None
    if shield is not None and _g(shield, "armor_type") == "shield":
        ac += _g(shield, "ac", 2)
    ac += overlay.get("ac", 0)
    sheet["ac"] = ac

    weap = lookup(equipped.get("main_hand")) if equipped.get("main_hand") else None
    if weap is not None and _g(weap, "category") == "weapon":
        str_mod = (sheet.get("abilities", {}).get("str", 10) - 10) // 2
        use = max(str_mod, dex) if _g(weap, "finesse", False) or _g(weap, "ranged", False) else \
            (dex if _g(weap, "ranged", False) else str_mod)
        pb = sheet.get("proficiency_bonus", 2)
        magic = overlay.get("weapon", 0)
        die = next((b.split()[0] for b in (_g(weap, "bonuses", ()) or ()) if "d" in b.split()[0]), "1d6")
        bonus = use + pb + magic
        dmg = f"{die}{(use+magic):+d}" if (use + magic) else die
        sheet["attacks"] = [{"name": _g(weap, "name", "weapon"), "bonus": bonus, "damage": dmg,
                             "reach": "ranged" if _g(weap, "ranged", False) else "melee"}]
    else:
        sheet["attacks"] = [dict(a) for a in sheet.get("base_attacks", [])]


def auto_equip_kit(rs, actor) -> None:
    sheet = actor.sheet
    look = lambda k: rs.item_info(k)
    armors = sorted([k for k in list(sheet.get("inventory", [])) if _g(look(k), "slot") == "armor"],
                    key=lambda k: _g(look(k), "ac", 0), reverse=True)
    for k in armors:
        if equip(rs, actor, k, "armor").get("ok"):
            break
    weapons = sorted([k for k in list(sheet.get("inventory", [])) if _g(look(k), "category") == "weapon"],
                     key=lambda k: (_g(look(k), "hands", 1), -_g(look(k), "value", 0)))
    for k in weapons:
        if equip(rs, actor, k, "main_hand").get("ok"):
            break
    mh = sheet.get("equipped", {}).get("main_hand")
    if mh and _g(look(mh), "hands", 1) < 2:
        for k in list(sheet.get("inventory", [])):
            if _g(look(k), "category") == "shield" and equip(rs, actor, k, "off_hand").get("ok"):
                break


def equipment_view(rs, actor) -> dict:
    sheet = actor.sheet
    lookup = (lambda k: rs.item_info(k)) if hasattr(rs, "item_info") else (lambda k: None)
    equipped = sheet.get("equipped", {})
    slots = []
    for s in SLOTS:
        key = equipped.get(s)
        it = lookup(key) if key else None
        slots.append({"slot": s, "label": SLOT_LABEL[s], "group": SLOT_GROUP[s],
                      "item": None if it is None else {"key": key, "name": _g(it, "name", key)}})
    return {"slots": slots, "encumbrance": encumbrance(sheet, lookup),
            "ac": sheet.get("ac", 10), "bonuses": sheet.get("equip_bonuses", {})}
