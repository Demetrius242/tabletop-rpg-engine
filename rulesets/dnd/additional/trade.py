from __future__ import annotations

import random

from rulesets.dnd.additional import items as _items

RARITY_WEIGHT = {"common": 100, "uncommon": 38, "rare": 11, "very_rare": 3, "legendary": 1, "artifact": 0}
RARITY_RETENTION = {"common": 0.20, "uncommon": 0.40, "rare": 0.65, "very_rare": 0.85,
                    "legendary": 0.95, "artifact": 1.0}
_RANK = {r: i for i, r in enumerate(_items.RARITY_ORDER)}


def price_to_buy(item, markup: float = 1.0) -> int:
    return max(1, round(item.value * markup))


def price_to_sell(item, sell_rate: float = 0.5) -> int:
    return max(0, round(item.value * sell_rate))


def _max_rank(max_rarity: str) -> int:
    return _RANK.get(max_rarity, _RANK["rare"])


def eligible_items(tradesman, pool=None) -> list:
    pool = pool if pool is not None else _items.tradeable()
    cats = set(getattr(tradesman, "categories", ()) or ())
    region = (getattr(tradesman, "region", "") or "").lower()
    ceiling = _max_rank(getattr(tradesman, "max_rarity", "rare"))
    floor = _RANK.get(getattr(tradesman, "min_rarity", "common"), 0)
    out = []
    for it in pool:
        if it.plot:
            continue
        if cats and it.category not in cats:
            continue
        if not (floor <= _RANK.get(it.rarity, 0) <= ceiling):
            continue
        if it.regions and region and region not in it.regions:
            continue
        if it.regions and not region:
            continue
        out.append(it)
    return out


def _weight(item, rarity_bias: float) -> float:
    base = RARITY_WEIGHT.get(item.rarity, 0)
    return base * (rarity_bias ** _RANK.get(item.rarity, 0))


def _weighted_sample(candidates, weights, k, rng) -> list:
    chosen, pool, wts = [], list(candidates), list(weights)
    k = min(k, len(pool))
    for _ in range(k):
        total = sum(wts)
        if total <= 0:
            break
        idx = rng.choices(range(len(pool)), weights=wts, k=1)[0]
        chosen.append(pool.pop(idx))
        wts.pop(idx)
    return chosen


def generate_stock(tradesman, pool=None, rng=None) -> list:
    rng = rng or random.Random()
    cand = eligible_items(tradesman, pool)
    if not cand:
        return []
    bias = float(getattr(tradesman, "rarity_bias", 1.0) or 1.0)
    weights = [_weight(it, bias) for it in cand]
    size = int(getattr(tradesman, "stock_size", 6) or 6)
    return [it.key for it in _weighted_sample(cand, weights, size, rng)]


def restock(current_keys, tradesman, pool=None, rng=None) -> list:
    rng = rng or random.Random()
    kept = []
    for key in (current_keys or []):
        it = _items.get(key)
        if it is None or it.plot:
            continue
        if rng.random() < RARITY_RETENTION.get(it.rarity, 0.3):
            kept.append(key)
    size = int(getattr(tradesman, "stock_size", 6) or 6)
    if len(kept) >= size:
        return kept[:size]
    cand = [it for it in eligible_items(tradesman, pool) if it.key not in kept]
    bias = float(getattr(tradesman, "rarity_bias", 1.0) or 1.0)
    weights = [_weight(it, bias) for it in cand]
    fresh = _weighted_sample(cand, weights, size - len(kept), rng)
    return kept + [it.key for it in fresh]
