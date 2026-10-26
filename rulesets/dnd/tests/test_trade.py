import sys, pathlib, random
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.additional import items, trade
from rulesets.dnd.core.dnd import DnDRuleset
from rulesets.dnd.settings.forgotten_realms.tradesmen import TRADESMEN


def test_pricing_follows_value_markup_and_sell_rate():
    it = items.get("flame_tongue")
    assert trade.price_to_buy(it, 1.2) == 6000
    assert trade.price_to_sell(it, 0.5) == 2500
    assert trade.price_to_buy(it, 1.0) >= trade.price_to_sell(it, 0.5)


def test_village_stock_is_cheap_common_consumables():
    t = TRADESMEN["old_wenna"]
    stock = trade.generate_stock(t, rng=random.Random(1))
    assert stock and all(items.get(k).rarity == "common" for k in stock)
    assert all(items.get(k).category in t.categories for k in stock)


def test_elite_stock_is_restricted_to_rare_and_better():
    t = TRADESMEN["xanthros"]
    rank = {r: i for i, r in enumerate(items.RARITY_ORDER)}
    seen = set()
    for seed in range(10):
        for k in trade.generate_stock(t, rng=random.Random(seed)):
            seen.add(items.get(k).rarity)
            assert rank[items.get(k).rarity] >= rank["rare"]
    assert any(r in seen for r in ("rare", "very_rare", "legendary"))


def test_plot_items_never_generate():
    t = TRADESMEN["quillan_myr"]
    for seed in range(40):
        for k in trade.generate_stock(t, rng=random.Random(seed)):
            assert not items.get(k).plot


def test_region_locked_items_only_appear_for_local_tradesmen():
    drow = TRADESMEN["shyntra_drow"]
    eligible_keys = {it.key for it in trade.eligible_items(drow)}
    waterdeep = TRADESMEN["jessa_quickfingers"]
    wd_keys = {it.key for it in trade.eligible_items(waterdeep)}
    assert "drow_blade" in eligible_keys and "drow_blade" not in wd_keys


def test_rarity_bias_tilts_the_odds():
    base = type(TRADESMEN["xanthros"])
    plain = base("a", "A", "loc", "waterdeep", categories=("wondrous", "ring", "staff", "wand"),
                 max_rarity="legendary", min_rarity="uncommon", stock_size=6, rarity_bias=1.0)
    tilted = base("b", "B", "loc", "waterdeep", categories=("wondrous", "ring", "staff", "wand"),
                  max_rarity="legendary", min_rarity="uncommon", stock_size=6, rarity_bias=3.0)
    rank = {r: i for i, r in enumerate(items.RARITY_ORDER)}

    def avg_rank(t):
        total = 0
        for seed in range(60):
            ks = trade.generate_stock(t, rng=random.Random(seed))
            total += sum(rank[items.get(k).rarity] for k in ks) / max(1, len(ks))
        return total / 60
    assert avg_rank(tilted) > avg_rank(plain)


def test_restock_keeps_rarer_items_longer():
    t = TRADESMEN["xanthros"]
    stock = ["potion_of_healing", "plus_one_weapon", "flame_tongue", "staff_of_power"]
    kept = {k: 0 for k in stock}
    for seed in range(300):
        new = trade.restock(stock, t, rng=random.Random(seed))
        for k in stock:
            if k in new:
                kept[k] += 1
    assert kept["potion_of_healing"] < kept["plus_one_weapon"] < kept["flame_tongue"] < kept["staff_of_power"]


def test_tradesman_roster_spans_tiers_and_places():
    from collections import Counter
    tiers = Counter(t.tier for t in TRADESMEN.values())
    assert len(TRADESMEN) >= 10
    assert tiers["village"] >= 1 and tiers["elite"] >= 1 and tiers["city"] >= 1
    regions = {t.region for t in TRADESMEN.values()}
    assert {"waterdeep", "underdark", "high_forest"} <= regions
    for t in TRADESMEN.values():
        assert t.card and t.card.name and t.card.voice and t.card.hook


def test_unique_assortment_means_unique_npc():
    assert TRADESMEN["old_wenna"].card.race == "human" and TRADESMEN["old_wenna"].tier == "village"
    assert TRADESMEN["jessa_quickfingers"].card.race == "tiefling" and TRADESMEN["jessa_quickfingers"].tier == "city"
    assert TRADESMEN["xanthros"].card.race == "fiend" and TRADESMEN["xanthros"].tier == "elite"


def test_buy_and_sell_move_gold_and_items():
    rs = DnDRuleset()
    pc = rs.build_pc({"name": "Roan", "race": "human", "class": "fighter", "background": "soldier",
                      "alignment": "ln",
                      "abilities": {"str": 15, "con": 14, "dex": 13, "int": 12, "wis": 10, "cha": 8},
                      "skills": ["athletics", "perception"]})
    rs.shops["brannor_stonehand"] = ["longsword", "plus_one_weapon"]
    gold0 = pc.sheet["gold"]
    out = rs.buy(pc, "longsword", "brannor_stonehand")
    assert out["ok"] and "longsword" in pc.sheet["inventory"]
    assert pc.sheet["gold"] == gold0 - out["price"]
    assert "longsword" not in rs.shop_stock("brannor_stonehand")
    assert rs.buy(pc, "plus_one_weapon", "brannor_stonehand")["ok"] is False
    sale = rs.sell(pc, "longsword", "brannor_stonehand")
    assert sale["ok"] and sale["price"] < out["price"]
    assert "longsword" not in pc.sheet["inventory"]


def test_cannot_sell_plot_items():
    rs = DnDRuleset()
    pc = rs.build_pc({"name": "P", "race": "human", "class": "fighter", "background": "soldier",
                      "alignment": "ln",
                      "abilities": {"str": 15, "con": 14, "dex": 13, "int": 12, "wis": 10, "cha": 8},
                      "skills": ["athletics", "perception"]})
    pc.sheet["inventory"].append("whisperfang")
    out = rs.sell(pc, "whisperfang", "jessa_quickfingers")
    assert out["ok"] is False and "whisperfang" in pc.sheet["inventory"]


def test_shops_restock_as_long_rests_pass():
    rs = DnDRuleset()
    rs.open_shops(seed=5)
    pc = rs.build_pc({"name": "C", "race": "human", "class": "cleric", "background": "acolyte",
                      "alignment": "lg",
                      "abilities": {"wis": 15, "con": 14, "str": 13, "cha": 12, "dex": 10, "int": 8},
                      "skills": ["medicine", "persuasion"]})
    t = rs.tradesman_info("halgrim_pawn")
    rs.shops["halgrim_pawn"] = ["potion_of_healing", "dagger"]
    before = list(rs.shop_stock("halgrim_pawn"))
    for _ in range(t.restock_interval):
        rs.long_rest(pc)
    assert rs._rest_count == t.restock_interval
    assert len(rs.shop_stock("halgrim_pawn")) == t.stock_size


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for t in ALL:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(ALL) - failed}/{len(ALL)} passed")
    raise SystemExit(1 if failed else 0)
