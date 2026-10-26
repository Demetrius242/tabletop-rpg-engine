import sys, pathlib, json, os, socket, struct, threading, time

_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine import events as E
from engine.dice import ScriptedDice
from web import catalog as C
from web.bridge import Session, serialize_event, WebFakeClient
from web.server import serve
from web.wsproto import recv_message, accept_key


def test_catalog_lists_dnd_and_cascades():
    rks = C.list_rulesets()
    assert any(r["key"] == "dnd" and r["wired"] for r in rks)
    settings = C.settings_for("dnd")
    assert any(s["key"] == "forgotten_realms" for s in settings)
    stories = C.stories_for("dnd", "forgotten_realms")
    assert stories[0]["key"] == "__free__"
    assert any(s["key"] == "watchers_barrow" for s in stories)


def test_build_story_session_has_party_and_scene():
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "watchers_barrow")
    assert state.pc.name == "Aria" and [c.name for c in comps] == ["Bertram"]
    assert scene is not None and scene.key == "watchers_barrow"
    assert any(p.follows_pc for p in scene.presences.values())


def test_character_view_has_mods_skills_and_decoration():
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "watchers_barrow")
    v = C.character_view(rs, state.pc)
    assert v["klass"] == "Rogue" and v["alignment_key"] == "cn"
    assert len(v["abilities"]) == 6 and len(v["skills"]) == 18
    assert any(s["proficient"] for s in v["skills"])
    assert v["decoration"]["accent"].startswith("#") and v["decoration"]["class_glyph"]
    assert v["inventory"] and v["inventory"][0]["color"].startswith("#")


def test_config_stats_counts_items_and_npcs():
    rs = C.build_ruleset("dnd")
    st = C.config_stats(rs, "forgotten_realms")
    assert st["items_total"] >= 40 and "items_by_rarity" in st
    assert st["npcs"] >= 1 and st["locations"] >= 1 and st["scenes"] >= 1


def test_optional_rules_come_from_the_ruleset():
    rs = C.build_ruleset("dnd")
    rules = C.optional_rules("dnd", rs)
    assert [o["key"] for o in rules] == [r["key"] for r in rs.optional_rules()]
    for o in rules:
        assert o["name"] and o["implemented"] is True and o["on"] is False


def test_character_view_has_gender_and_sections():
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "watchers_barrow")
    v = C.character_view(rs, state.pc)
    assert "gender" in v
    assert isinstance(v["sections"], list)
    assert all(sec.get("kind") for sec in v["sections"])


def test_two_file_save_round_trip(tmp_slot="__pytest_slot__"):
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "watchers_barrow")
    scene.move_pc("antechamber")
    state.pc.sheet["hp"] = 5
    res = C.save_session(tmp_slot, ruleset_key="dnd", setting_key="forgotten_realms",
                         story_key="watchers_barrow", state=state, scene=scene, companions=comps)
    d = C.SAVES_DIR / res["slot"]
    assert (d / "pc.json").exists() and (d / "world.json").exists()
    rk, sk, stk, rs2, state2, scene2, comps2 = C.load_saved(res["slot"])
    assert state2.pc.sheet["hp"] == 5 and scene2.pc_zone == "antechamber"
    assert [c.name for c in comps2] == ["Bertram"]
    import shutil
    shutil.rmtree(d, ignore_errors=True)


def test_serialize_styles_for_damage_heal_item_crit():
    party = {"Aria", "Bertram"}
    dmg = serialize_event(E.AttackResolved("Goblin", "Aria", True, False, "success", 6, "hurt", False), party)
    assert dmg["style"] == "damage"
    foe = serialize_event(E.AttackResolved("Aria", "Goblin", True, False, "success", 7, "hurt", True), party)
    assert foe["style"] == "attack-hit" and foe["defeated"]
    heal = serialize_event(E.Healed("Aria", amount=8, source="Potion of Healing"), party)
    assert heal["style"] == "heal" and "8" in heal["text"]
    item = serialize_event(E.ItemGained("Aria", "scroll_of_revivify", "Scroll of Revivify", "rare"), party)
    assert item["style"] == "item rarity-rare"
    crit = serialize_event(E.CheckResolved("stealth", "critical", True), party)
    assert crit["style"] == "crit-success"
    botch = serialize_event(E.CheckResolved("stealth", "botch", False), party)
    assert botch["style"] == "crit-fail"


def test_web_fake_client_parses_commands():
    cl = WebFakeClient()
    cl.last_user = "attack the goblin"
    g = cl.complete("...EXACTLY one intent...", None, grammar=True)
    assert "combat_start" in g.text
    cl.last_user = "I flee for the door"
    combat_prompt = "the player's COMBAT action\nEnemies: Goblin, Orc.\nAdjacent zones: gate."
    out = cl.complete(combat_prompt, None, grammar=True)
    assert json.loads(out.text)["action"] == "flee"
    cl.last_user = "move to the gate"
    out = cl.complete(combat_prompt, None, grammar=True)
    assert json.loads(out.text) == {"action": "move", "zone": "gate"}


class _FakeWS:
    def __init__(self):
        self.sent = []
    def send_text(self, t):
        self.sent.append(json.loads(t)); return True
    def close(self):
        pass


def _drive(ws, sess, commands, settle=0.12):
    sess.start(); time.sleep(0.12)
    for c in commands:
        sess.submit(c); time.sleep(settle)
    time.sleep(0.4)
    sess.stop(); time.sleep(0.15)


def test_session_exploration_emits_items_and_checks():
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "watchers_barrow")
    rs.dice = ScriptedDice(default=17)
    ws = _FakeWS()
    sess = Session(ws, ruleset_key="dnd", setting_key="forgotten_realms", story_key="watchers_barrow",
                   rs=rs, state=state, scene=scene, companions=comps)
    _drive(ws, sess, ["go to the antechamber", "search", "go to the gallery", "take the reliquary"])
    cats = {m.get("cat") for m in ws.sent if m.get("kind") == "log"}
    assert "item" in cats and "check" in cats
    assert any(m.get("kind") == "narration" for m in ws.sent)
    assert any(m.get("style", "").startswith("item rarity-") for m in ws.sent)


def test_session_combat_handoff_shows_damage_and_defeat():
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "watchers_barrow")
    rs.dice = ScriptedDice(default=16)
    state.pc.sheet["hp"] = 40; state.pc.sheet["max_hp"] = 40
    ws = _FakeWS()
    sess = Session(ws, ruleset_key="dnd", setting_key="forgotten_realms", story_key="watchers_barrow",
                   rs=rs, state=state, scene=scene, companions=comps)
    cmds = ["go to the antechamber", "go to the gallery", "attack a cultist"] + \
           ["attack a chanting cultist"] * 12
    _drive(ws, sess, cmds, settle=0.1)
    assert any(m.get("cat") == "combat" for m in ws.sent)
    assert any(m.get("style") == "damage" for m in ws.sent)
    assert any(m.get("defeated") for m in ws.sent)


def test_levelup_messages_stage_choose_and_apply_on_long_rest():
    from web.server import App
    app = App(_FakeWS(), fake=True)
    app.handle({"type": "begin", "ruleset": "dnd", "setting": "forgotten_realms", "story": "__free__"})
    try:
        app.ws.sent.clear()
        app.handle({"type": "levelUp"})
        lu = [m for m in app.ws.sent if m["type"] == "levelUp"][-1]
        assert lu["party"] and lu["roadmaps"]
        pc = lu["party"][0]
        assert pc["available"] is False and len(pc["slots"]) == 0
        app.ws.sent.clear(); app.handle({"type": "levelAward", "member": pc["name"]})
        card = [m for m in app.ws.sent if m["type"] == "levelUp"][-1]["party"][0]
        assert card["available"] and card["target_level"] == 2
        before_level = card["level"]
        assert card["level"] == before_level
        app.ws.sent.clear(); app.handle({"type": "longRest"})
        sent = app.ws.sent
        assert any(m.get("type") == "restResult" and m.get("longRest") for m in sent)
        after = [m for m in sent if m["type"] == "levelUp"][-1]["party"][0]
        assert after["level"] == before_level + 1 and after["available"] is False
    finally:
        if app.session:
            app.session.stop()


def test_levelup_subclass_choice_is_revisable_before_rest():
    from web.server import App
    app = App(_FakeWS(), fake=True)
    app.handle({"type": "begin", "ruleset": "dnd", "setting": "forgotten_realms", "story": "__free__"})
    try:
        pc = app.session.state.pc
        app.session.rs.advance_to_level(pc, 2)
        app.handle({"type": "levelAward", "member": pc.name})
        app.ws.sent.clear(); app.handle({"type": "levelUp"})
        card = [m for m in app.ws.sent if m["type"] == "levelUp"][-1]["party"][0]
        sub_slot = next((s for s in card["slots"] if s["key"] == "subclass"), None)
        assert sub_slot is not None and len(sub_slot["options"]) >= 2
        first, second = sub_slot["options"][0]["id"], sub_slot["options"][1]["id"]
        app.handle({"type": "levelChoose", "member": pc.name, "slot": "subclass", "value": first})
        app.handle({"type": "levelChoose", "member": pc.name, "slot": "subclass", "value": second})
        app.ws.sent.clear(); app.handle({"type": "levelUp"})
        card = [m for m in app.ws.sent if m["type"] == "levelUp"][-1]["party"][0]
        assert card["choices"]["subclass"] == second
        app.handle({"type": "longRest"})
        assert pc.sheet.get("subclass") == second
    finally:
        if app.session:
            app.session.stop()


def _ws_connect(host, port):
    s = socket.create_connection((host, port), timeout=5)
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    s.sendall((f"GET /ws HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
               f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(1024)
    assert b" 101 " in buf and accept_key(key).encode() in buf
    s.settimeout(5)
    return s


def _ws_send(s, obj):
    payload = json.dumps(obj).encode()
    mask = os.urandom(4)
    out = bytearray([0x81])
    n = len(payload)
    if n < 126:
        out.append(0x80 | n)
    elif n < 65536:
        out.append(0x80 | 126); out += struct.pack(">H", n)
    else:
        out.append(0x80 | 127); out += struct.pack(">Q", n)
    out += mask
    out += bytes(payload[i] ^ mask[i & 3] for i in range(n))
    s.sendall(bytes(out))


def _read_until(rfile, pred, limit=60):
    for _ in range(limit):
        kind, data = recv_message(rfile)
        if kind != "text":
            continue
        msg = json.loads(data)
        if pred(msg):
            return msg
    raise AssertionError("expected message not received")


def test_end_to_end_websocket_session():
    httpd = serve("127.0.0.1", 0, fake=True)
    port = httpd.socket.getsockname()[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        s = _ws_connect("127.0.0.1", port)
        rfile = s.makefile("rb")
        _ws_send(s, {"type": "catalog"})
        cat = _read_until(rfile, lambda m: m.get("type") == "catalog")
        assert any(r["key"] == "dnd" for r in cat["rulesets"])

        _ws_send(s, {"type": "begin", "ruleset": "dnd", "setting": "forgotten_realms", "story": "watchers_barrow"})
        began = _read_until(rfile, lambda m: m.get("type") == "began")
        assert began["party"][0]["name"] == "Aria"
        _read_until(rfile, lambda m: m.get("kind") == "narration")

        _ws_send(s, {"type": "action", "text": "go to the antechamber"})
        _read_until(rfile, lambda m: m.get("kind") == "narration")

        _ws_send(s, {"type": "info"})
        info = _read_until(rfile, lambda m: m.get("type") == "info")
        assert info["stats"]["items_total"] >= 40
        assert isinstance(info["optional"], list)

        _ws_send(s, {"type": "save", "slot": "__e2e__"})
        saved = _read_until(rfile, lambda m: m.get("type") == "saved")
        assert saved["ok"] and set(saved["files"]) == {"pc.json", "world.json"}
        import shutil
        shutil.rmtree(C.SAVES_DIR / "__e2e__", ignore_errors=True)
        s.close()
    finally:
        httpd.shutdown()


def test_creation_options_and_point_buy():
    rs = C.build_ruleset("dnd")
    opt = C.creation_options(rs)
    assert len(opt["races"]) >= 5 and len(opt["classes"]) >= 10 and opt["point_buy"]["budget"] == 27
    assert opt["point_buy"]["abilities"] == ["str", "dex", "con", "int", "wis", "cha"]
    assert opt["genders"]
    assert C.point_buy_spent({"str": 15, "dex": 14, "con": 13, "int": 12, "wis": 10, "cha": 8}) == 27
    assert C.point_buy_spent({"str": 16}) is None


def test_build_custom_pc_gets_gear_and_spellbook():
    rs = C.build_ruleset("dnd")
    pc = C.build_custom_pc(rs, {"name": "Lyra", "race": "elf", "class": "wizard", "background": "sage",
                                "alignment": "tn", "abilities": {"str": 8, "dex": 14, "con": 13, "int": 15, "wis": 12, "cha": 10},
                                "skills": ["arcana", "investigation"]})
    assert pc.sheet["inventory"]
    sb = C.spellbook_view(rs, pc)
    assert sb["caster"] and sb["cantrips"] and sb["prepared"] and "1" in sb["repertoire"]


def test_item_detail_hides_hidden_flags():
    rs = C.build_ruleset("dnd")
    d = C.item_detail(rs, "potion_of_healing")
    assert d["found"] and d["value"] > 0 and "plot" not in d and "requires_rule" not in d


def test_end_to_end_create_party_and_spellbook():
    httpd = serve("127.0.0.1", 0, fake=True)
    port = httpd.socket.getsockname()[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        s = _ws_connect("127.0.0.1", port)
        rfile = s.makefile("rb")
        _ws_send(s, {"type": "creationOptions", "ruleset": "dnd"})
        opt = _read_until(rfile, lambda m: m.get("type") == "creationOptions")["options"]
        assert opt["point_buy"]["budget"] == 27

        _ws_send(s, {"type": "createParty", "ruleset": "dnd", "setting": "forgotten_realms",
                     "pc": {"form": {"name": "Lyra", "race": "elf", "class": "wizard", "background": "sage",
                                     "alignment": "tn", "abilities": {"str": 8, "dex": 14, "con": 13, "int": 15, "wis": 12, "cha": 10},
                                     "skills": ["arcana", "investigation"], "gender": "female"}},
                     "ally": {"pregen": "bertram"}})
        began = _read_until(rfile, lambda m: m.get("type") == "began")
        assert [p["name"] for p in began["party"]] == ["Lyra", "Bertram"]
        assert began["party"][0]["gender"] and began["party"][0]["inventory"]
        _read_until(rfile, lambda m: m.get("kind") == "narration")

        _ws_send(s, {"type": "spellbook"})
        sb = _read_until(rfile, lambda m: m.get("type") == "spellbook")
        assert "Lyra" in sb["casters"] and "Bertram" in sb["casters"]
        first_two = [sp["key"] for sp in sb["books"]["Lyra"]["repertoire"]["1"]][:2]

        _ws_send(s, {"type": "prepareSpells", "member": "Lyra", "keys": first_two})
        alloc = _read_until(rfile, lambda m: m.get("type") == "spellAllocated")
        assert alloc["book"]["prepared"] == first_two

        _ws_send(s, {"type": "itemDetail", "key": "spellbook"})
        it = _read_until(rfile, lambda m: m.get("type") == "itemDetail")["item"]
        assert it["found"] and "plot" not in it and "requires_rule" not in it
        s.close()
    finally:
        httpd.shutdown()


def test_end_to_end_equipment_and_short_rest():
    httpd = serve("127.0.0.1", 0, fake=True)
    port = httpd.socket.getsockname()[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        s = _ws_connect("127.0.0.1", port)
        rfile = s.makefile("rb")
        _ws_send(s, {"type": "createParty", "ruleset": "dnd", "setting": "forgotten_realms",
                     "pc": {"form": {"name": "Bron", "race": "human", "class": "fighter",
                                     "background": "soldier", "alignment": "ln",
                                     "abilities": {"str": 15, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
                                     "skills": ["athletics"]}}})
        _read_until(rfile, lambda m: m.get("type") == "began")
        _read_until(rfile, lambda m: m.get("kind") == "narration")

        _ws_send(s, {"type": "equipment", "member": "Bron"})
        eq = _read_until(rfile, lambda m: m.get("type") == "equipment")
        assert len(eq["view"]["slots"]) == 10 and "status" in eq["view"]["encumbrance"]
        main = next(sl for sl in eq["view"]["slots"] if sl["slot"] == "main_hand")
        assert main["item"] is not None and eq["view"]["ac"] >= 16

        _ws_send(s, {"type": "unequip", "member": "Bron", "slot": "main_hand"})
        eq2 = _read_until(rfile, lambda m: m.get("type") == "equipment")
        assert next(sl for sl in eq2["view"]["slots"] if sl["slot"] == "main_hand")["item"] is None
        weap = next(it["key"] for it in eq2["inventory"] if it["equippable"] and it["slot"] == "main_hand")
        _ws_send(s, {"type": "equip", "member": "Bron", "key": weap, "slot": "main_hand"})
        eq3 = _read_until(rfile, lambda m: m.get("type") == "equipment")
        assert next(sl for sl in eq3["view"]["slots"] if sl["slot"] == "main_hand")["item"]["key"] == weap

        _ws_send(s, {"type": "shortRest", "member": "Bron", "dice": 1})
        rest = _read_until(rfile, lambda m: m.get("type") == "restResult")
        assert "message" in rest and rest["hit_dice_remaining"] <= 1
        s.close()
    finally:
        httpd.shutdown()


def test_end_to_end_shop_and_barter():
    httpd = serve("127.0.0.1", 0, fake=True)
    port = httpd.socket.getsockname()[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        s = _ws_connect("127.0.0.1", port)
        rfile = s.makefile("rb")
        _ws_send(s, {"type": "createParty", "ruleset": "dnd", "setting": "forgotten_realms",
                     "pc": {"form": {"name": "Sable", "race": "human", "class": "fighter",
                                     "background": "soldier", "alignment": "ln",
                                     "abilities": {"str": 15, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
                                     "skills": ["athletics"]}}})
        _read_until(rfile, lambda m: m.get("type") == "began")
        _read_until(rfile, lambda m: m.get("kind") == "narration")

        _ws_send(s, {"type": "openShop"})
        shop = _read_until(rfile, lambda m: m.get("type") == "shop")
        v = shop["view"]
        assert v and v["trader_items"] and "gold" in v
        gold0 = v["gold"]
        sellable = [it["key"] for it in v["player_items"]]
        assert "potion_of_healing" in sellable
        price = next(it["price"] for it in v["player_items"] if it["key"] == "potion_of_healing")

        _ws_send(s, {"type": "tradeDeal", "take": [], "give": ["potion_of_healing"]})
        deal = _read_until(rfile, lambda m: m.get("type") == "dealResult")
        assert deal["ok"] and deal["net"] == -price
        after = _read_until(rfile, lambda m: m.get("type") == "shop")["view"]
        assert after["gold"] == gold0 + price
        assert "potion_of_healing" not in [it["key"] for it in after["player_items"]]
        assert "potion_of_healing" in [it["key"] for it in after["trader_items"]]

        cheapest = min(after["trader_items"], key=lambda it: it["price"])
        _ws_send(s, {"type": "tradeDeal", "take": [cheapest["key"]], "give": []})
        d2 = _read_until(rfile, lambda m: m.get("type") == "dealResult")
        assert d2["ok"] and d2["net"] == cheapest["price"]

        _ws_send(s, {"type": "shopHaggle", "approach": "persuasion"})
        hv = _read_until(rfile, lambda m: m.get("type") == "shop")["view"]
        assert isinstance(hv["discount"], int) and 0 <= hv["discount"] <= 100

        _ws_send(s, {"type": "closeShop"})
        assert _read_until(rfile, lambda m: m.get("type") == "shopClosed")
        s.close()
    finally:
        httpd.shutdown()


def test_ready_signal_marks_idle_between_turns():
    httpd = serve("127.0.0.1", 0, fake=True)
    port = httpd.socket.getsockname()[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        s = _ws_connect("127.0.0.1", port)
        rfile = s.makefile("rb")
        _ws_send(s, {"type": "createParty", "ruleset": "dnd", "setting": "forgotten_realms",
                     "pc": {"form": {"name": "Pip", "race": "human", "class": "fighter",
                                     "background": "soldier", "alignment": "ln",
                                     "abilities": {"str": 14, "dex": 12, "con": 13, "int": 10, "wis": 10, "cha": 10},
                                     "skills": ["athletics"]}}})
        _read_until(rfile, lambda m: m.get("type") == "began")
        assert _read_until(rfile, lambda m: m.get("type") == "ready")
        _ws_send(s, {"type": "action", "text": "look around"})
        assert _read_until(rfile, lambda m: m.get("type") == "ready")
        s.close()
    finally:
        httpd.shutdown()


def test_levelup_exposes_classes_and_multiclass_choice():
    from web.server import App
    app = App(_FakeWS(), fake=True)
    app.handle({"type": "begin", "ruleset": "dnd", "setting": "forgotten_realms", "story": "__free__"})
    try:
        app.ws.sent.clear(); app.handle({"type": "levelUp"})
        card = [m for m in app.ws.sent if m["type"] == "levelUp"][-1]["party"][0]
        assert card["classes"] and card["classes"][0]["level"] == 1
        assert "color" in card["classes"][0] and "glyph" in card["classes"][0]
        name = card["name"]
        app.handle({"type": "levelAward", "member": name})
        app.ws.sent.clear(); app.handle({"type": "levelUp"})
        card = [m for m in app.ws.sent if m["type"] == "levelUp"][-1]["party"][0]
        class_slot = next((s for s in card["slots"] if s["key"] == "class"), None)
        assert class_slot is not None
        new_ids = [o["id"] for o in class_slot["options"] if o["id"].startswith("new:")]
        assert new_ids and any(o["id"].startswith("advance:") for o in class_slot["options"])
        pick = next(i for i in new_ids if i.endswith("wizard"))
        app.handle({"type": "levelChoose", "member": name, "slot": "class", "value": pick})
        app.handle({"type": "longRest"})
        app.ws.sent.clear(); app.handle({"type": "levelUp"})
        last = [m for m in app.ws.sent if m["type"] == "levelUp"][-1]
        card = last["party"][0]
        keys = {c["class_key"] for c in card["classes"]}
        assert "wizard" in keys and card["level"] == 2
        assert "wizard" in last["roadmaps"]
    finally:
        if app.session:
            app.session.stop()


def test_llama_settings_round_trip():
    from web.server import App
    p = C.CONFIG_PATH
    orig = p.read_text("utf-8") if p.exists() else None
    app = App(_FakeWS(), fake=True)
    try:
        C.save_connection({"kind": "canned"})
        app.handle({"type": "getLlamaSettings"})
        got = [m for m in app.ws.sent if m["type"] == "llamaSettings"][-1]
        assert "settings" in got and "models" in got and "runtime" in got
        assert got["runtime"]["fake"] is True
        assert got["runtime"]["restrictions"] == {"locked": [], "pinned": {}}
        for k in ("top_k", "min_p", "repeat_penalty", "frequency_penalty", "presence_penalty",
                  "seed", "system_prompt"):
            assert k in got["settings"], f"missing sampler key {k!r}"
        app.ws.sent.clear()
        app.handle({"type": "saveLlamaSettings",
                    "settings": {"temperature": 1.1, "top_p": 0.88, "max_tokens": 321,
                                 "top_k": 55, "min_p": 0.1, "repeat_penalty": 1.2,
                                 "frequency_penalty": 0.3, "presence_penalty": -0.4, "seed": 7,
                                 "system_prompt": "Be terse.",
                                 "context_size": 2048, "gpu_layers": 12, "model": "z.gguf",
                                 "server_url": "http://127.0.0.1:9999/completion"}})
        saved = [m for m in app.ws.sent if m["type"] == "llamaSettingsSaved"][-1]
        assert saved["ok"] and saved["settings"]["temperature"] == 1.1
        assert saved["settings"]["top_k"] == 55 and saved["settings"]["seed"] == 7
        assert saved["settings"]["system_prompt"] == "Be terse."
        assert saved["applied_live"] is False
        assert C.save_llama({"frequency_penalty": -9})["frequency_penalty"] == -2.0
        assert C.load_llama()["context_size"] == 2048
        assert "ruleset" in C.load_config()
    finally:
        if orig is not None:
            p.write_text(orig, "utf-8")


def test_connection_restrictions_for_backends():
    assert C.connection_restrictions({"kind": "canned"}) == {"locked": [], "pinned": {}}
    assert C.connection_restrictions({"kind": "llama-cpp"}) == {"locked": [], "pinned": {}}
    local = C.connection_restrictions({"kind": "openai", "base_url": "http://127.0.0.1:5000"})
    assert set(local["locked"]) == {"top_k", "min_p", "repeat_penalty"} and local["pinned"] == {}
    kimi = C.connection_restrictions({"kind": "openai", "base_url": "https://api.kimi.com/coding"})
    assert {"frequency_penalty", "presence_penalty", "seed"} <= set(kimi["locked"])
    assert kimi["pinned"] == {"temperature": 1.0, "top_p": 0.95}


def test_llama_settings_surface_restrictions_for_hosted_backend():
    from web.server import App
    p = C.CONFIG_PATH
    orig = p.read_text("utf-8") if p.exists() else None
    app = App(_FakeWS(), fake=True)
    try:
        C.save_connection({"kind": "openai", "base_url": "https://api.kimi.com/coding",
                           "endpoint": "chat", "model": "kimi"})
        app.handle({"type": "getLlamaSettings"})
        got = [m for m in app.ws.sent if m["type"] == "llamaSettings"][-1]
        restr = got["runtime"]["restrictions"]
        assert {"frequency_penalty", "presence_penalty", "seed"} <= set(restr["locked"])
        assert restr["pinned"]["top_p"] == 0.95
    finally:
        if orig is not None:
            p.write_text(orig, "utf-8")


def test_llm_config_save_load_round_trip():
    from web.server import App
    p = C.CONFIG_PATH
    orig = p.read_text("utf-8") if p.exists() else None
    made = C.LLM_CONFIGS_DIR / "pytest_profile.json"
    app = App(_FakeWS(), fake=True)
    try:
        app.handle({"type": "listLlmConfigs"})
        cfgs = [m for m in app.ws.sent if m["type"] == "llmConfigs"][-1]["configs"]
        assert "default" in cfgs
        app.ws.sent.clear()
        app.handle({"type": "saveLlmConfig", "name": "pytest profile",
                    "settings": {"temperature": 1.4, "top_k": 12, "system_prompt": "vivid",
                                 "model": "should_be_ignored.gguf"}})
        savedmsg = [m for m in app.ws.sent if m["type"] == "llmConfigSaved"][-1]
        assert savedmsg["ok"] and savedmsg["name"] == "pytest_profile"
        assert "pytest_profile" in savedmsg["configs"]
        cfg = C.load_llm_config("pytest_profile")
        assert cfg["temperature"] == 1.4 and cfg["top_k"] == 12 and cfg["system_prompt"] == "vivid"
        assert "model" not in cfg
        app.ws.sent.clear()
        app.handle({"type": "loadLlmConfig", "name": "pytest_profile"})
        ls = [m for m in app.ws.sent if m["type"] == "llamaSettings"][-1]
        assert ls["settings"]["temperature"] == 1.4 and ls["settings"]["system_prompt"] == "vivid"
        assert C.load_llama()["temperature"] == 1.4
    finally:
        if made.exists():
            made.unlink()
        if orig is not None:
            p.write_text(orig, "utf-8")


def test_connection_round_trip_and_live_reconnect():
    from web.server import App
    p = C.CONFIG_PATH
    orig = p.read_text("utf-8") if p.exists() else None
    app = App(_FakeWS(), fake=True)
    try:
        C.save_connection({"kind": "canned"})
        app.handle({"type": "catalog"})
        cat = [m for m in app.ws.sent if m["type"] == "catalog"][-1]
        assert cat["connection"]["kind"] == "canned" and "backend" in cat

        app.ws.sent.clear()
        app.handle({"type": "saveConnection", "connection": {
            "kind": "openai", "base_url": "http://127.0.0.1:5000/v1", "endpoint": "chat",
            "model": "eva-qwen", "api_key": "sk-x", "timeout": "900"}})
        saved = [m for m in app.ws.sent if m["type"] == "connectionSaved"][-1]
        assert saved["ok"] and saved["applied_live"] is False
        assert C.load_connection()["kind"] == "openai"
        assert C.load_connection()["base_url"] == "http://127.0.0.1:5000/v1"
        assert C.load_connection()["timeout"] == 900

        app.handle({"type": "begin", "ruleset": "dnd", "setting": "forgotten_realms", "story": "__free__"})
        from engine.llm import OpenAIClient
        assert isinstance(app.session.client, OpenAIClient)
        assert app.session.client.endpoint == "chat" and app.session.client.base_url == "http://127.0.0.1:5000"
        assert app.session.client.timeout == 900

        app.ws.sent.clear()
        app.handle({"type": "saveConnection", "connection": {"kind": "canned"}})
        saved2 = [m for m in app.ws.sent if m["type"] == "connectionSaved"][-1]
        assert saved2["applied_live"] is True
        assert not isinstance(app.session.client, OpenAIClient)
        assert app.session.engine.client is app.session.client

        app.ws.sent.clear()
        app.handle({"type": "testConnection", "connection": {"kind": "canned"}})
        t = [m for m in app.ws.sent if m["type"] == "connectionTest"][-1]
        assert t["ok"] is True
    finally:
        if app.session:
            app.session.stop()
        if orig is not None:
            p.write_text(orig, "utf-8")


def test_oota_campaign_lists_and_journal_round_trip():
    from web.server import App
    stories = C.stories_for("dnd", "forgotten_realms")
    oota = next((s for s in stories if s["key"] == "oota_ch1"), None)
    assert oota is not None and oota.get("campaign") is True
    app = App(_FakeWS(), fake=True)
    app.handle({"type": "begin", "ruleset": "dnd", "setting": "forgotten_realms", "story": "oota_ch1"})
    try:
        began = [m for m in app.ws.sent if m["type"] == "began"][-1]
        names = [p["name"] for p in began["party"]]
        assert names and names[0].startswith("Sarith")
        assert any(n == "Ront" for n in names) and any(n == "Pog" for n in names)
        app.ws.sent.clear()
        app.handle({"type": "getJournal"})
        j = [m for m in app.ws.sent if m["type"] == "journal"][-1]["journal"]
        assert j["event"] == "velkynvelve_escape"
        assert j["chapter"] and any("prisoner" in o["text"].lower() for o in j["objectives"])
    finally:
        if app.session:
            app.session.stop()


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
if __name__ == "__main__":
    import inspect
    failed = 0
    for t in ALL:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1; print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            import traceback
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc()
    print(f"\n{len(ALL) - failed}/{len(ALL)} passed")
    raise SystemExit(1 if failed else 0)
