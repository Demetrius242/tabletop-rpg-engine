import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.additional import items


def test_every_item_is_well_formed():
    for it in items.all_items():
        assert it.key and it.name and it.category in items.CATEGORIES
        assert it.rarity in items.RARITY_ORDER
        assert isinstance(it.value, int) and it.value >= 0
        assert isinstance(it.attunement, bool) and isinstance(it.plot, bool)
        assert isinstance(it.regions, tuple)


def test_catalogue_spans_categories_and_rarities():
    rarities = {it.rarity for it in items.all_items()}
    cats = {it.category for it in items.all_items()}
    assert {"common", "uncommon", "rare", "very_rare", "legendary"} <= rarities
    assert {"weapon", "armor", "potion", "scroll", "wondrous"} <= cats


def test_plot_items_exist_and_are_excluded_from_trade():
    plot = [it for it in items.all_items() if it.plot]
    assert len(plot) >= 3
    for it in plot:
        assert it.special
    tradeable_keys = {it.key for it in items.tradeable()}
    assert all(it.key not in tradeable_keys for it in plot)


def test_special_details_cover_the_requested_kinds():
    specials = " ".join(it.special.lower() for it in items.all_items() if it.special)
    assert "cursed" in specials
    assert "alive" in specials and "talking" in specials
    assert "god" in specials
    dawn = items.get("dawnshard")
    assert dawn.plot and dawn.rarity == "uncommon" and "god" in dawn.special.lower()


def test_attunement_is_flagged():
    assert items.get("ring_of_protection").attunement is True
    assert items.get("bag_of_holding").attunement is False


def test_region_filtering():
    ft = items.get("flame_tongue")
    assert "baldurs_gate" in ft.regions
    bg = {it.key for it in items.in_region("baldurs_gate")}
    ud = {it.key for it in items.in_region("underdark")}
    assert "flame_tongue" in bg and "flame_tongue" not in ud
    assert "drow_blade" in ud and "drow_blade" not in bg
    assert "potion_of_healing" in bg and "potion_of_healing" in ud


def test_lore_is_richer_for_rarer_items():
    common_lore = items.get("torch").lore
    legend_lore = items.get("holy_avenger").lore
    assert len(legend_lore) > len(common_lore)


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
