from dataclasses import dataclass
from .piece_definition import PieceDefinition


@dataclass
class PieceInstance:
    """
    A piece owned by the player, carrying RPG progression stats.

    Wraps a PieceDefinition and adds level + XP.  Higher levels scale
    value_mg/value_eg overrides fed to Fairy-Stockfish, making the piece
    genuinely stronger in the engine's evaluation.

    Constants (class-level, not dataclass fields):
        XP_PER_LEVEL        — XP needed to advance one level
        MAX_LEVEL           — cap; grant_xp is a no-op above this
        VALUE_BONUS_PER_LEVEL — internal Fairy-SF value units added per level
                               above 1 (reference: rook ≈ 1276 mg / 1380 eg)
    """

    definition: PieceDefinition
    level: int = 1
    xp: int = 0

    XP_PER_LEVEL = 3
    MAX_LEVEL = 5
    VALUE_BONUS_PER_LEVEL = 120  # ~10 % of a rook per level

    def grant_xp(self, amount: int = 1) -> bool:
        """Add XP. Returns True if the piece leveled up."""
        if self.level >= self.MAX_LEVEL:
            return False
        self.xp += amount
        if self.xp >= self.XP_PER_LEVEL:
            self.xp -= self.XP_PER_LEVEL
            self.level = min(self.level + 1, self.MAX_LEVEL)
            return True
        return False

    def to_definition(self) -> PieceDefinition:
        """
        Return a PieceDefinition whose value overrides reflect the current
        level.  Only applies if the base definition already has values set;
        pieces without overrides keep None (engine uses its own defaults).
        """
        base = self.definition
        bonus = (self.level - 1) * self.VALUE_BONUS_PER_LEVEL
        mg = (base.value_mg + bonus) if base.value_mg is not None else None
        eg = (base.value_eg + bonus) if base.value_eg is not None else None
        return PieceDefinition(
            name=base.name,
            char=base.char,
            predefined=base.predefined,
            betza=base.betza,
            value_mg=mg,
            value_eg=eg,
        )

    @property
    def display_name(self) -> str:
        suffixes = ["", " II", " III", " IV", " V"]
        return self.definition.name.capitalize() + suffixes[self.level - 1]

    @property
    def xp_to_next(self) -> int:
        """XP still needed to reach the next level (0 if at MAX_LEVEL)."""
        if self.level >= self.MAX_LEVEL:
            return 0
        return self.XP_PER_LEVEL - self.xp

    def __repr__(self) -> str:
        return (
            f"PieceInstance({self.display_name!r}, "
            f"lv={self.level}, xp={self.xp}/{self.XP_PER_LEVEL})"
        )
