from dataclasses import dataclass, field
from typing import List, Optional

from .army import Army
from .piece_definition import PieceDefinition
from .piece_instance import PieceInstance

# Default back-rank chars used when a lineup slot is left empty
_DEFAULT_BACK_RANK = ["r", "n", "b", "q", "k", "b", "n", "r"]


@dataclass
class Player:
    """
    Persistent player state for an RPG run.

    roster   — all PieceInstances the player owns.
    lineup   — 8 back-rank slots (a-file … h-file), each is an index into
               roster or None (None falls back to the standard chess piece
               for that slot: R N B Q K B N R).
    gold     — currency spent in the shop.
    lives    — remaining losses before the run ends.
    """

    name: str
    gold: int = 100
    lives: int = 3
    roster: List[PieceInstance] = field(default_factory=list)
    lineup: List[Optional[int]] = field(default_factory=lambda: [None] * 8)

    # ------------------------------------------------------------------
    # Roster management
    # ------------------------------------------------------------------

    def add_to_roster(self, definition: PieceDefinition, level: int = 1) -> PieceInstance:
        """Create a new PieceInstance and add it to the roster."""
        inst = PieceInstance(definition=definition, level=level)
        self.roster.append(inst)
        return inst

    def remove_from_roster(self, idx: int) -> PieceInstance:
        """Remove and return the piece at roster index idx.  Clears lineup slots that referenced it."""
        inst = self.roster.pop(idx)
        self.lineup = [
            None if slot == idx else (slot - 1 if slot is not None and slot > idx else slot)
            for slot in self.lineup
        ]
        return inst

    # ------------------------------------------------------------------
    # Lineup management
    # ------------------------------------------------------------------

    def set_slot(self, slot: int, roster_idx: Optional[int]) -> None:
        """Assign a roster piece to back-rank slot 0–7.  Pass None to clear."""
        if not 0 <= slot <= 7:
            raise ValueError(f"Slot must be 0–7, got {slot}")
        self.lineup[slot] = roster_idx

    def piece_at_slot(self, slot: int) -> Optional[PieceInstance]:
        idx = self.lineup[slot]
        if idx is not None and 0 <= idx < len(self.roster):
            return self.roster[idx]
        return None

    # ------------------------------------------------------------------
    # Army construction
    # ------------------------------------------------------------------

    def current_army(self, pawn: Optional[PieceDefinition] = None) -> Army:
        """
        Build an Army from the current lineup.

        Slots with no assigned piece fall back to the standard chess piece
        for that position so the army is always valid.
        """
        from data.pieces import BY_CHAR

        back_rank = []
        for slot, idx in enumerate(self.lineup):
            if idx is not None and 0 <= idx < len(self.roster):
                back_rank.append(self.roster[idx].to_definition())
            else:
                back_rank.append(BY_CHAR[_DEFAULT_BACK_RANK[slot]])
        return Army(name=self.name, back_rank=back_rank, pawn=pawn)

    # ------------------------------------------------------------------
    # Gold
    # ------------------------------------------------------------------

    def spend(self, amount: int) -> bool:
        """Deduct gold.  Returns True if successful, False if insufficient funds."""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def earn(self, amount: int) -> None:
        self.gold += amount

    def __repr__(self) -> str:
        return (
            f"Player({self.name!r}, gold={self.gold}, lives={self.lives}, "
            f"roster={len(self.roster)} pieces)"
        )
