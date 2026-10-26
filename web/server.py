from __future__ import annotations

import json
import pathlib
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from engine import addons as _addons
from web import catalog as C
from web.bridge import Session
from web.wsproto import WebSocket, handshake_response, recv_message

STATIC = pathlib.Path(__file__).resolve().parent / "static"
_MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml",
         ".png": "image/png", ".ico": "image/x-icon"}


def _chosen_rules(msg: dict) -> set:
    return {str(k) for k, on in (msg.get("rules") or {}).items() if on}


class App:

    def __init__(self, ws: WebSocket, *, fake=True, server_url=None):
        self.ws = ws
        self.fake = fake
        self.server_url = server_url
        self.session: Session | None = None
        self._shop = None

    def _current_connection(self) -> dict:
        if C.has_saved_connection():
            return C.load_connection()
        if not self.fake and self.server_url:
            base = self.server_url.rstrip("/").removesuffix("/completion")
            return {"kind": "llama-cpp", "base_url": base, "endpoint": "completions",
                    "api_key": "", "model": ""}
        return dict(C.DEFAULT_CONNECTION)

    def _restrictions(self, conn: dict, client=None) -> dict:
        r = C.connection_restrictions(conn)
        live = client if client is not None else getattr(self.session, "client", None)
        forced = getattr(live, "forced", None)
        dropped = getattr(live, "dropped", None)
        if isinstance(forced, dict):
            r["pinned"] = {**r.get("pinned", {}), **forced}
        if dropped:
            r["locked"] = list(dict.fromkeys(list(r.get("locked", [])) + list(dropped)))
        return r

    def _send(self, obj) -> None:
        self.ws.send_text(json.dumps(obj))

    def handle(self, msg: dict) -> None:
        t = msg.get("type")
        if t == "catalog":
            cfg = C.load_config()
            conn = self._current_connection()
            self._send({"type": "catalog", "rulesets": C.list_rulesets(),
                        "settings": C.settings_for(cfg.get("ruleset", "dnd")),
                        "stories": C.stories_for(cfg.get("ruleset", "dnd"), cfg.get("setting", "")),
                        "connection": conn, "backend": C.backend_label(conn), "last": cfg})
        elif t == "settings":
            rk = msg.get("ruleset", "dnd")
            self._send({"type": "settings", "ruleset": rk, "settings": C.settings_for(rk),
                        "stories": C.stories_for(rk, "")})
        elif t == "stories":
            rk, sk = msg.get("ruleset", "dnd"), msg.get("setting", "")
            self._send({"type": "stories", "ruleset": rk, "setting": sk,
                        "stories": C.stories_for(rk, sk)})
        elif t == "storyDetail":
            rk, sk, stk = msg.get("ruleset", "dnd"), msg.get("setting", ""), msg.get("story", "")
            self._send({"type": "storyDetail", "story": stk,
                        "detail": C.story_detail(rk, sk, stk)})
        elif t == "begin":
            self._begin(msg.get("ruleset", "dnd"), msg.get("setting", ""), msg.get("story", "__free__"))
        elif t == "creationOptions":
            rs = C.build_ruleset(msg.get("ruleset", "dnd"))
            self._send({"type": "creationOptions",
                        "options": C.creation_options(rs, rules=_chosen_rules(msg))})
        elif t == "rollAbilities":
            self._send({"type": "abilities",
                        "abilities": C.roll_ability_scores(abilities=msg.get("abilities"))})
        elif t == "createParty":
            self._create_party(msg)
        elif t == "itemDetail":
            rs = self.session.rs if self.session else C.build_ruleset(msg.get("ruleset", "dnd"))
            self._send({"type": "itemDetail", "item": C.item_detail(rs, msg.get("key", ""))})
        elif t == "spellbook":
            self._send_spellbook()
        elif t in ("prepareSpells", "setKnown", "setCantrips"):
            self._allocate_spells(t, msg.get("member", ""), msg.get("keys", []))
        elif t == "equipment":
            self._send_equipment(msg.get("member", ""))
        elif t == "equip":
            self._equip(msg.get("member", ""), msg.get("key", ""), msg.get("slot", ""))
        elif t == "unequip":
            self._unequip(msg.get("member", ""), msg.get("slot", ""))
        elif t == "shortRest":
            self._short_rest(msg.get("member", ""), int(msg.get("dice", 0)))
        elif t == "longRest":
            self._long_rest()
        elif t == "levelUp":
            self._send_levelup()
        elif t == "levelAward":
            self._level_award(msg.get("member", ""))
        elif t == "levelChoose":
            self._level_choose(msg.get("member", ""), msg.get("slot", ""), msg.get("value"))
        elif t == "levelCancel":
            self._level_cancel(msg.get("member", ""))
        elif t == "action":
            if self.session and self._shop and self._shop_chat(str(msg.get("text", ""))):
                pass
            elif self.session:
                self.session.submit(str(msg.get("text", "")))
        elif t == "openShop":
            self._open_shop(msg.get("tradesman", ""))
        elif t == "closeShop":
            self._shop = None
            self._send({"type": "shopClosed"})
        elif t == "shopHaggle":
            self._shop_haggle(msg.get("approach", "persuasion"), msg.get("item", ""))
        elif t == "tradeDeal":
            self._trade_deal(msg.get("take", []), msg.get("give", []))
        elif t == "sheet":
            if self.session:
                self._send({"type": "party", "party": self.session.party_views()})
        elif t == "info":
            self._send_info()
        elif t == "setRule":
            self._set_rule(msg.get("key"), bool(msg.get("on")))
        elif t == "save":
            self._save(msg.get("slot", "save"))
        elif t == "listSaves":
            self._send({"type": "saves", "saves": C.list_saves()})
        elif t == "load":
            self._load(msg.get("slot", ""))
        elif t == "getJournal":
            self._send({"type": "journal",
                        "journal": self.session.journal() if self.session else {}})
        elif t == "getLlamaSettings":
            self._send_llama_settings()
        elif t == "saveLlamaSettings":
            self._save_llama_settings(msg.get("settings") or {})
        elif t == "saveConnection":
            self._save_connection(msg.get("connection") or {})
        elif t == "testConnection":
            self._test_connection(msg.get("connection") or {})
        elif t == "listLlmConfigs":
            self._list_llm_configs()
        elif t == "saveLlmConfig":
            self._save_llm_config(msg.get("name", ""), msg.get("settings") or {})
        elif t == "loadLlmConfig":
            self._load_llm_config(msg.get("name", ""))
        elif t == "ping":
            self._send({"type": "pong"})

    def _begin(self, rk, sk, stk) -> None:
        C.update_config(ruleset=rk, setting=sk, story=stk)
        if self.session:
            self.session.stop()
        rs, state, scene, comps = C.build_session(rk, sk, stk)
        self.session = Session(self.ws, ruleset_key=rk, setting_key=sk, story_key=stk, rs=rs,
                               state=state, scene=scene, companions=comps,
                               connection=self._current_connection())
        self._send({"type": "began", "ruleset": rk, "setting": sk, "story": stk,
                    "party": self.session.party_views(),
                    "versions": C.versions(rk, sk, stk)})
        self.session.start()

    def _create_party(self, msg) -> None:
        rk, sk = msg.get("ruleset", "dnd"), msg.get("setting", "")
        pc_spec = msg.get("pc") or {}
        allies = msg.get("allies")
        if allies is None:
            a = msg.get("ally")
            allies = [a] if a else []
        allies = [a for a in allies if a]
        story = msg.get("story") or "__free__"
        adventure = C.is_adventure(rk, sk, story)
        try:
            if adventure:
                rs, state, scene, comps = C.build_session(rk, sk, story, party=[pc_spec] + allies)
            else:
                story = "__free__"
                rs, state, scene, comps = C.build_custom_session(rk, sk, pc_spec, allies)
        except Exception as exc:
            self._send({"type": "createError", "error": str(exc)})
            return
        for key in _chosen_rules(msg):
            rs.set_rule(key, True)
        C.update_config(ruleset=rk, setting=sk, story=story)
        if self.session:
            self.session.stop()
        self.session = Session(self.ws, ruleset_key=rk, setting_key=sk, story_key=story, rs=rs,
                               state=state, scene=scene, companions=comps,
                               connection=self._current_connection())
        self._send({"type": "began", "ruleset": rk, "setting": sk, "story": story,
                    "party": self.session.party_views(), "versions": C.versions(rk, sk, story)})
        self.session.start()

    def _members(self):
        if not self.session:
            return []
        return [self.session.state.pc] + list(self.session.companions)

    def _member(self, name):
        return next((m for m in self._members() if m.name == name), None)

    def _send_spellbook(self) -> None:
        if not self.session:
            self._send({"type": "spellbook", "casters": [], "books": {}})
            return
        rs = self.session.rs
        casters = C.party_casters(rs, self._members())
        books = {m.name: C.spellbook_view(rs, m) for m in self._members() if m.sheet.get("spellcasting")}
        self._send({"type": "spellbook", "casters": casters, "books": books})

    def _allocate_spells(self, kind, name, keys) -> None:
        m = self._member(name)
        if m is None or not self.session:
            return
        rs = self.session.rs
        if kind == "prepareSpells":
            rs.prepare_spells(m, keys)
        elif kind == "setKnown":
            rs.set_known_spells(m, keys)
        elif kind == "setCantrips":
            rs.set_cantrips(m, keys)
        self._send({"type": "spellAllocated", "member": name, "book": C.spellbook_view(rs, m)})

    def _equip_target(self, name):
        return self._member(name) or (self.session.state.pc if self.session else None)

    def _inventory_briefs(self, member):
        rs = self.session.rs
        out = []
        for key in member.sheet.get("inventory", []):
            it = rs.item_info(key)
            rar = getattr(it, "rarity", "common") if it else "common"
            out.append({"key": key, "name": getattr(it, "name", key) if it else key,
                        "rarity": rar, "color": C.RARITY_COLORS.get(rar, "#b9c2cc"),
                        "equippable": bool(rs._equipment and rs._equipment.is_equippable(it)) if it else False,
                        "slot": (rs._equipment.item_slot(it) if (it and rs._equipment) else "")})
        return out

    def _send_equipment(self, name) -> None:
        if not self.session:
            self._send({"type": "equipment", "member": name, "view": {}, "inventory": []})
            return
        m = self._equip_target(name)
        rs = self.session.rs
        self._send({"type": "equipment", "member": m.name, "view": rs.equipment_view(m),
                    "inventory": self._inventory_briefs(m)})

    def _equip(self, name, key, slot) -> None:
        m = self._equip_target(name)
        if m is None or not self.session:
            return
        res = self.session.rs.equip_item(m, key, slot, in_combat=False)
        if not res.get("ok"):
            self._send({"type": "equipResult", "ok": False, "message": res.get("message", "Can't equip that.")})
        self._send_equipment(m.name)
        self._send({"type": "party", "party": self.session.party_views()})

    def _unequip(self, name, slot) -> None:
        m = self._equip_target(name)
        if m is None or not self.session:
            return
        self.session.rs.unequip_item(m, slot)
        self._send_equipment(m.name)
        self._send({"type": "party", "party": self.session.party_views()})

    def _short_rest(self, name, dice) -> None:
        m = self._equip_target(name)
        if m is None or not self.session:
            return
        res = self.session.rs.short_rest(m, spend_hit_dice=max(0, dice))
        self._send({"type": "restResult", "member": m.name, "message": res.get("message", ""),
                    "healed": res.get("healed", 0), "hit_dice_remaining": res.get("hit_dice_remaining", 0)})
        self._send({"type": "party", "party": self.session.party_views()})

    _CLASS_COLORS = {
        "barbarian": "#b5482f", "bard": "#c46aa6", "cleric": "#d8c373", "druid": "#5e9a52",
        "fighter": "#9a8c7a", "monk": "#5fa6a0", "paladin": "#cbb24a", "ranger": "#6f9a4f",
        "rogue": "#7a6f86", "sorcerer": "#c8553a", "warlock": "#7d4fa6", "wizard": "#4f73b6",
    }

    def _class_color(self, ck: str) -> str:
        return self._CLASS_COLORS.get(ck, "#b07a2c")

    def _class_glyph(self, ck: str) -> str:
        return C._CLASS_GLYPH.get(ck, (ck[:1].upper() if ck else "?"))

    def _levelup_card(self, m) -> dict:
        st = self.session.rs.level_up_state(m)
        pck = st.get("class_key", "")
        st["color"] = self._class_color(pck)
        st["glyph"] = self._class_glyph(pck)
        for c in st.get("classes", []):
            c["color"] = self._class_color(c.get("class_key", ""))
            c["glyph"] = self._class_glyph(c.get("class_key", ""))
        return st

    def _roadmap_for(self, rs, ck: str) -> dict:
        cls = rs.classes.get(ck)
        subclasses = {}
        if rs._subclasses is not None:
            for sk, sv in rs.list_subclasses(ck).items():
                feats = {str(lvl): [n for n, _ in fl]
                         for lvl, fl in rs._subclasses.subclass_feature_table(ck, sk).items()}
                subclasses[sk] = {"label": sv.get("label", sk.title()),
                                  "blurb": sv.get("blurb", ""), "features": feats}
        return {
            "label": getattr(cls, "label", ck.title()),
            "color": self._class_color(ck),
            "glyph": self._class_glyph(ck),
            "subclass_level": rs.subclass_choice_level(ck),
            "subclass_noun": (rs._subclasses.subclass_noun(ck) if rs._subclasses is not None
                              else "subclass"),
            "rows": rs.class_progression(ck),
            "subclasses": subclasses,
        }

    def _send_levelup(self) -> None:
        if not self.session:
            self._send({"type": "levelUp", "party": [], "roadmaps": {}}); return
        rs = self.session.rs
        cards = [self._levelup_card(m) for m in self._members()]
        roadmaps = {}
        for c in cards:
            for cl in c.get("classes", []):
                ck = cl.get("class_key", "")
                if ck and ck not in roadmaps and rs.classes.get(ck) is not None:
                    roadmaps[ck] = self._roadmap_for(rs, ck)
            cc = c.get("chosen_class")
            if c.get("available") and c.get("is_new_class") and cc and cc not in roadmaps \
                    and rs.classes.get(cc) is not None:
                roadmaps[cc] = self._roadmap_for(rs, cc)
        self._send({"type": "levelUp", "party": cards, "roadmaps": roadmaps,
                    "available": sum(1 for c in cards if c.get("available"))})

    def _level_award(self, name) -> None:
        m = self._member(name)
        if m is None or not self.session:
            return
        self.session.rs.award_level_up(m)
        self._send_levelup()

    def _level_choose(self, name, slot, value) -> None:
        m = self._member(name)
        if m is None or not self.session:
            return
        self.session.rs.set_level_choice(m, slot, value)
        self._send_levelup()

    def _level_cancel(self, name) -> None:
        m = self._member(name)
        if m is None or not self.session:
            return
        self.session.rs.cancel_level_up(m)
        self._send_levelup()

    def _send_llama_settings(self) -> None:
        llama = C.load_llama()
        conn = self._current_connection()
        self._send({"type": "llamaSettings", "settings": llama, "models": C.list_models(),
                    "connection": conn,
                    "runtime": {"fake": conn.get("kind") == "canned", "connection": conn,
                                "backend": C.backend_label(conn),
                                "restrictions": self._restrictions(conn)}})

    def _save_connection(self, conn: dict) -> None:
        saved = C.save_connection(conn)
        applied = False
        if self.session is not None:
            self.session.reconnect(saved)
            applied = True
        self._send({"type": "connectionSaved", "ok": True, "connection": saved,
                    "backend": C.backend_label(saved), "applied_live": applied,
                    "restrictions": self._restrictions(saved)})

    def _test_connection(self, conn: dict) -> None:
        from engine.llm import client_from_connection, Sampling, LLMUnavailable
        kind = conn.get("kind", "canned")
        if kind == "canned":
            self._send({"type": "connectionTest", "ok": True,
                        "message": "Canned narrator — no model needed.",
                        "restrictions": self._restrictions(conn)})
            return
        try:
            client = client_from_connection(conn)
            if hasattr(client, "timeout"):
                client.timeout = 20.0
            out = client.complete("<|im_start|>user\nReply with the single word: pong<|im_end|>\n"
                                  "<|im_start|>assistant\n",
                                  Sampling(temperature=0.7, top_p=1.0, max_tokens=256))
            reply = (out.text or "").strip()
            ok = bool(reply)
            msg = (f"Model replied: “{reply[:60]}”." if ok
                   else "Reached the backend, but the model returned an empty reply.")
            self._send({"type": "connectionTest", "ok": ok, "message": msg,
                        "backend": C.backend_label(conn),
                        "restrictions": self._restrictions(conn, client)})
        except LLMUnavailable as exc:
            self._send({"type": "connectionTest", "ok": False, "message": str(exc)})
        except Exception as exc:
            self._send({"type": "connectionTest", "ok": False, "message": f"{type(exc).__name__}: {exc}"})

    def _save_llama_settings(self, settings: dict) -> None:
        llama = C.save_llama(settings)
        self._apply_llama_live()
        self._send({"type": "llamaSettingsSaved", "ok": True, "settings": llama,
                    "models": C.list_models(), "applied_live": self.session is not None})

    def _apply_llama_live(self) -> bool:
        from web.bridge import apply_saved_sampling, _saved_system_prompt
        if self.session is None:
            return False
        client = getattr(self.session, "client", None)
        if client is not None:
            apply_saved_sampling(client)
        if getattr(self.session, "engine", None) is not None:
            self.session.engine.narrator_override = _saved_system_prompt()
        return True

    def _list_llm_configs(self) -> None:
        self._send({"type": "llmConfigs", "configs": C.list_llm_configs()})

    def _save_llm_config(self, name: str, settings: dict) -> None:
        saved = C.save_llm_config(name, settings or {})
        self._send({"type": "llmConfigSaved", "ok": True, "name": saved,
                    "configs": C.list_llm_configs()})

    def _load_llm_config(self, name: str) -> None:
        cfg = C.load_llm_config(name)
        C.save_llama(cfg)
        self._apply_llama_live()
        self._send_llama_settings()

    def _long_rest(self) -> None:
        if not self.session:
            return
        rs = self.session.rs
        msgs, leveled = [], []
        for m in self._members():
            res = rs.long_rest(m)
            msgs.append(res.get("message", ""))
            if res.get("leveled_up"):
                leveled.append(res["leveled_up"])
        self._send({"type": "restResult", "member": "", "longRest": True,
                    "message": "  ".join(x for x in msgs if x), "leveled": leveled})
        self._send({"type": "party", "party": self.session.party_views()})
        self._send_levelup()

    def _shop_view(self):
        rs = self.session.rs; pc = self.session.state.pc
        tk = self._shop["tradesman"]; disc = self._shop.get("discount", 0.0)
        t = rs.tradesman_info(tk)
        def brief(key, price):
            it = rs.item_info(key); rar = getattr(it, "rarity", "common") if it else "common"
            return {"key": key, "name": getattr(it, "name", key) if it else key, "price": price,
                    "rarity": rar, "color": C.RARITY_COLORS.get(rar, "#b9c2cc")}
        trader = []
        for key in rs.shop_stock(tk):
            if rs.item_info(key) is None:
                continue
            base = rs.price_quote(key, tk, selling=False) or 0
            trader.append(brief(key, int(round(base * (1 - disc)))))
        player = []
        for key in pc.sheet.get("inventory", []):
            it = rs.item_info(key)
            if it is None or getattr(it, "plot", False):
                continue
            player.append(brief(key, rs.price_quote(key, tk, selling=True) or 0))
        return {"tradesman": {"key": tk, "name": getattr(t, "name", tk)}, "gold": pc.sheet.get("gold", 0),
                "discount": int(round(disc * 100)), "trader_items": trader, "player_items": player,
                "approaches": rs.haggle_approaches()}

    def _open_shop(self, tradesman):
        if not self.session:
            self._send({"type": "shop", "view": None}); return
        rs = self.session.rs
        tk = tradesman or self._pick_tradesman(rs)
        if not tk or rs.tradesman_info(tk) is None:
            self._send({"type": "shopError", "error": "There's no merchant to trade with here."}); return
        self._shop = {"tradesman": tk, "discount": 0.0}
        self._send({"type": "shop", "view": self._shop_view()})

    def _pick_tradesman(self, rs) -> str:
        keys = rs.list_tradesmen()
        if not keys:
            return ""
        declared = self._scene_merchants()
        valid_declared = [k for k in declared if rs.tradesman_info(k) is not None]
        if valid_declared:
            return valid_declared[0]
        ctx = " ".join(filter(None, [str(getattr(self.session.state, "location", "") or ""),
                                     self._scene_context()])).lower()
        ctx_words = {w for w in re.findall(r"[a-z]+", ctx) if len(w) >= 4}
        best, best_score = keys[0], 0
        for k in keys:
            t = rs.tradesman_info(k)
            hay = f"{getattr(t, 'region', '')} {getattr(t, 'location', '')}".lower()
            score = len(ctx_words & {w for w in re.findall(r"[a-z]+", hay) if len(w) >= 4})
            if score > best_score:
                best, best_score = k, score
        return best

    def _scene_merchants(self) -> list:
        sc = getattr(self.session, "scene", None)
        if sc is None or not hasattr(sc, "merchants_here"):
            return []
        try:
            return list(sc.merchants_here() or [])
        except Exception:
            return []

    def _scene_context(self) -> str:
        sc = getattr(self.session, "scene", None)
        if sc is None:
            return ""
        try:
            z = sc.here()
            return (z.name if z is not None else "") or ""
        except Exception:
            return ""

    def _shop_chat(self, text):
        low = text.strip().lower()
        if any(k in low for k in ("haggle", "barter", "persuade", "negotiate", "talk down", "intimidat")):
            self._shop_haggle("intimidation" if "intimidat" in low else "persuasion", ""); return True
        rs = self.session.rs
        for approach, cues in (rs.haggle_cues() if hasattr(rs, "haggle_cues") else []):
            if any(k in low for k in cues):
                self._shop_haggle(approach, ""); return True
        return False

    def _shop_haggle(self, approach, item):
        if not (self.session and self._shop):
            return
        rs = self.session.rs; pc = self.session.state.pc; tk = self._shop["tradesman"]
        item = item or (rs.shop_stock(tk)[0] if rs.shop_stock(tk) else "")
        if not item:
            return
        res = rs.haggle(pc, item, tk, approach=approach)
        if res.get("ok"):
            disc = res.get("discount_pct", 0) / 100.0
            if res.get("waived"):
                disc = max(disc, 0.99)
            self._shop["discount"] = max(self._shop.get("discount", 0.0), disc)
            style = res.get("style", "check")
            self._send({"type": "log", "cat": style, "style": style,
                        "text": f"[{res['approach']}] {res['roll']} vs DC {res['dc']} → {res['discount_pct']}% off"
                                + (" — the merchant waives the price!" if res.get("waived") else "")})
        self._send({"type": "shop", "view": self._shop_view()})

    def _trade_deal(self, take, give):
        if not (self.session and self._shop):
            return
        rs = self.session.rs; pc = self.session.state.pc; tk = self._shop["tradesman"]
        disc = self._shop.get("discount", 0.0)
        stock = rs.shop_stock(tk); inv = pc.sheet.setdefault("inventory", [])
        take = [k for k in take if k in stock]
        give = [k for k in give if k in inv and not getattr(rs.item_info(k), "plot", False)]
        cost = sum(int(round((rs.price_quote(k, tk, selling=False) or 0) * (1 - disc))) for k in take)
        revenue = sum(rs.price_quote(k, tk, selling=True) or 0 for k in give)
        net = cost - revenue
        gold = pc.sheet.get("gold", 0)
        if net > 0 and gold < net:
            self._send({"type": "dealResult", "ok": False,
                        "message": f"You can't afford this deal (needs {net} gp; you have {gold})."})
            self._send({"type": "shop", "view": self._shop_view()}); return
        for k in take:
            stock.remove(k); inv.append(k)
        for k in give:
            inv.remove(k)
            if k not in stock:
                stock.append(k)
        pc.sheet["gold"] = gold - net
        msg = ("Paid {} gp".format(net) if net > 0 else
               ("Received {} gp".format(-net) if net < 0 else "An even trade"))
        self._send({"type": "dealResult", "ok": True, "net": net, "take": take, "give": give,
                    "gold": pc.sheet["gold"], "message": msg + "."})
        self._send({"type": "shop", "view": self._shop_view()})
        self._send({"type": "party", "party": self.session.party_views()})

    def _send_info(self) -> None:
        s = self.session
        rk = s.ruleset_key if s else "dnd"
        sk = s.setting_key if s else "forgotten_realms"
        stk = s.story_key if s else "__free__"
        rs = s.rs if s else C.build_ruleset(rk)
        self._send({"type": "info", "versions": C.versions(rk, sk, stk),
                    "rules": C.rules_in_use(rk), "optional": C.optional_rules(rk, rs),
                    "stats": C.config_stats(rs, sk)})

    def _set_rule(self, key, on) -> None:
        applied = on
        if self.session is not None:
            applied = self.session.rs.set_rule(key, on)
        self._send({"type": "ruleSet", "key": key, "on": applied})
        if self.session is not None:
            self._send({"type": "party", "party": self.session.party_views()})
            self._send_info()

    def _save(self, slot) -> None:
        if not self.session:
            self._send({"type": "saved", "ok": False, "error": "No game in progress."})
            return
        s = self.session
        try:
            res = C.save_session(slot, ruleset_key=s.ruleset_key, setting_key=s.setting_key,
                                 story_key=s.story_key, state=s.state, scene=s.scene,
                                 companions=s.companions)
            self._send({"type": "saved", "ok": True, **res, "saves": C.list_saves()})
        except Exception as exc:
            self._send({"type": "saved", "ok": False, "error": str(exc)})

    def _load(self, slot) -> None:
        try:
            rk, sk, stk, rs, state, scene, comps = C.load_saved(slot)
        except Exception as exc:
            self._send({"type": "loaded", "ok": False, "error": str(exc)})
            return
        if self.session:
            self.session.stop()
        self.session = Session(self.ws, ruleset_key=rk, setting_key=sk, story_key=stk, rs=rs,
                               state=state, scene=scene, companions=comps,
                               connection=self._current_connection())
        self._send({"type": "loaded", "ok": True, "ruleset": rk, "setting": sk, "story": stk,
                    "party": self.session.party_views(), "versions": C.versions(rk, sk, stk),
                    "location": state.location})
        self.session.start()

    def close(self) -> None:
        if self.session:
            self.session.stop()


def _addon_static_dirs() -> dict:
    return {a["name"]: pathlib.Path(a["dir"]) for a in _addons.registered("web.static")}


def _with_addon_assets(body: bytes) -> bytes:
    css, js = [], []
    for a in _addons.registered("web.static"):
        css += [f'<link rel="stylesheet" href="addons/{a["name"]}/{f}" />' for f in a.get("css", ())]
        js += [f'<script src="addons/{a["name"]}/{f}"></script>' for f in a.get("js", ())]
    html = body.decode("utf-8")
    html = html.replace("<!--addon-styles-->", "\n".join(css)).replace("<!--addon-scripts-->", "\n".join(js))
    return html.encode("utf-8")


def make_handler(*, fake=True, server_url=None):
    _addons.load_all()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def _serve_static(self):
            rel = self.path.split("?", 1)[0].lstrip("/") or "index.html"
            root = STATIC
            if rel.startswith("addons/"):
                parts = rel.split("/", 2)
                root = _addon_static_dirs().get(parts[1]) if len(parts) == 3 else None
                rel = parts[2] if len(parts) == 3 else ""
                if root is None or not rel:
                    self.send_error(404, "Not found")
                    return
            path = (root / rel).resolve()
            if not str(path).startswith(str(root.resolve())) or not path.is_file():
                self.send_error(404, "Not found")
                return
            body = path.read_bytes()
            if root is STATIC and rel == "index.html":
                body = _with_addon_assets(body)
            self.send_response(200)
            self.send_header("Content-Type", _MIME.get(path.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.split("?", 1)[0] == "/ws" and \
                    self.headers.get("Upgrade", "").lower() == "websocket":
                self._serve_ws()
                return
            self._serve_static()

        def _serve_ws(self):
            key = self.headers.get("Sec-WebSocket-Key", "")
            self.wfile.write(handshake_response(key))
            self.wfile.flush()
            self.close_connection = True
            ws = WebSocket(self.wfile)
            app = App(ws, fake=fake, server_url=server_url)
            try:
                while not ws.closed:
                    kind, data = recv_message(self.rfile)
                    if kind is None or kind == "close":
                        break
                    if kind == "ping":
                        ws.pong(data or b"")
                        continue
                    if kind != "text":
                        continue
                    try:
                        msg = json.loads(data)
                    except (ValueError, TypeError):
                        continue
                    try:
                        app.handle(msg)
                    except Exception as exc:
                        try:
                            ws.send_text(json.dumps({"type": "error", "error": str(exc)}))
                        except Exception:
                            break
            finally:
                app.close()
                ws.close()

    return Handler


def serve(host="127.0.0.1", port=8765, *, fake=True, server_url=None):
    httpd = ThreadingHTTPServer((host, port), make_handler(fake=fake, server_url=server_url))
    return httpd
