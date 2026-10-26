from __future__ import annotations

PB_BY_LEVEL = {**{l: 2 for l in range(1, 5)}, **{l: 3 for l in range(5, 9)},
               **{l: 4 for l in range(9, 13)}, **{l: 5 for l in range(13, 17)},
               **{l: 6 for l in range(17, 21)}}


def proficiency_bonus(level: int = 1) -> int:
    return PB_BY_LEVEL.get(max(1, min(20, level)), 2)


def ability_mod(score: int) -> int:
    return (score - 10) // 2


def resolve_skill_proficiencies(skill_list, skill_choices: int, chosen, race_skills=()) -> list:
    allowed = set(skill_list)
    seen, ordered = set(), []
    for s in (chosen or ()):
        s = s.lower()
        if s in allowed and s not in seen:
            seen.add(s)
            ordered.append(s)
    ordered = ordered[:skill_choices]
    seen = set(ordered)
    for s in skill_list:
        if len(ordered) >= skill_choices:
            break
        if s not in seen:
            seen.add(s)
            ordered.append(s)
    final = list(ordered)
    for s in race_skills or ():
        if s not in seen:
            seen.add(s)
            final.append(s)
    return final


def save_modifier(score: int, proficient: bool, level: int = 1) -> int:
    return ability_mod(score) + (proficiency_bonus(level) if proficient else 0)


def spell_stats(score: int, level: int = 1) -> dict:
    pb = proficiency_bonus(level)
    mod = ability_mod(score)
    return {"spell_save_dc": 8 + pb + mod, "spell_attack_bonus": pb + mod}
