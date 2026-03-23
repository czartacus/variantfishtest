"""
Enemy army generator for RPG encounters.

Difficulty scales with floor number.  The generator:
  1. Unlocks higher-tier pieces as the floor increases.
  2. Assigns a total power budget that grows with floor.
  3. Fills 8 back-rank slots greedily from the available pool,
     always reserving slot 4 (e-file) for the king.

Floor tiers:
    floors 1-3  → tier 1 pieces only
    floors 4-6  → tiers 1-2
    floors 7+   → tiers 1-3
"""

import random
from dataclasses import dataclass
from typing import List, Tuple

from .army import Army
from .piece_definition import PieceDefinition

# King is always present; excluded from budget pieces.
_KING = PieceDefinition("king", "k", predefined="king")

# (base_budget, budget_per_floor) — total power rating for 7 non-king slots
_BUDGET_BASE = 1800
_BUDGET_PER_FLOOR = 150


def _max_tier(floor: int) -> int:
    if floor <= 3:
        return 1
    if floor <= 6:
        return 2
    return 3


def _available_pool(floor: int) -> List[Tuple[PieceDefinition, int]]:
    """Return (definition, power) pairs available at this floor."""
    from data.piece_pool import PIECE_POOL
    max_t = _max_tier(floor)
    return [(defn, power) for defn, power, tier in PIECE_POOL if tier <= max_t]


@dataclass
class Encounter:
    """
    A single enemy encounter.

    floor    — 1-indexed floor number (affects difficulty).
    enemy    — the generated enemy Army.
    variant  — name of the chess variant to play (default "chess").
    """
    floor: int
    enemy: Army
    variant: str = "chess"


def generate_encounter(floor: int, seed: int = None, variant: str = "chess") -> Encounter:
    """
    Generate an Encounter for the given floor.

    seed — optional random seed for reproducible encounters.
    """
    rng = random.Random(seed)
    pool = _available_pool(floor)
    budget = _BUDGET_BASE + floor * _BUDGET_PER_FLOOR

    back_rank: List[PieceDefinition] = [None] * 8
    back_rank[4] = _KING  # king always on e-file

    remaining = budget
    slots = [0, 1, 2, 3, 5, 6, 7]  # everything except the king slot
    rng.shuffle(slots)

    for slot in slots:
        affordable = [(d, p) for d, p in pool if p <= remaining]
        if not affordable:
            # Fall back to the cheapest available piece regardless of budget
            defn, power = min(pool, key=lambda x: x[1])
        else:
            defn, power = rng.choice(affordable)
        back_rank[slot] = defn
        remaining -= power

    name = f"Floor {floor} Enemy"
    army = Army(name=name, back_rank=back_rank)
    return Encounter(floor=floor, enemy=army, variant=variant)
