from __future__ import annotations


class RulesExtension:
    key: str = ""
    rule: dict | None = None

    def __init__(self, ruleset):
        self.rs = ruleset
        self.enabled = self.rule is None

    def set_enabled(self, on: bool) -> bool:
        self.enabled = bool(on)
        return self.enabled

    def init_profile(self, sheet: dict, selections: dict) -> None:
        pass

    def init_creature(self, sheet: dict, *, name: str, creature_type: str, mindless: bool) -> None:
        pass

    def ensure_profile(self, actor) -> None:
        pass

    def on_gender_change(self, actor, before: str, after: str) -> None:
        pass

    def on_long_rest(self, actor) -> dict:
        return {}

    def skill_names(self) -> list:
        return []

    def skill_ability(self, skill: str) -> str | None:
        return None

    def skill_modifier(self, actor, skill: str) -> int | None:
        return None

    def mental_abilities(self) -> set:
        return set()

    def difficulty_delta(self, actor, skill: str) -> int:
        return 0

    def save_disadvantage(self, actor, ability: str) -> bool:
        return False

    def speed_modifier(self, actor) -> int:
        return 0

    def use_item(self, actor, item_key: str, info, *, presenter=None) -> dict | None:
        return None

    def haggle_approaches(self) -> list:
        return []

    def haggle_cues(self) -> list:
        return []

    def haggle_terms(self, actor, approach: str) -> dict | None:
        return None

    def narration_register(self, skill: str, actor, approach: str = "") -> str:
        return ""

    def register_for_text(self, text: str, actor=None) -> str:
        return ""

    def briefing_lines(self, actor) -> list:
        return []

    def on_scene_built(self, key: str, scene) -> None:
        pass
