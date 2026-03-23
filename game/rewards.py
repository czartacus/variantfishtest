"""
Reward calculation after a battle.

Rewards are applied directly to a Player object based on the BattleResult
outcome and the current floor number.

Gold rewards:
    win   → WIN_GOLD  + floor bonus
    draw  → DRAW_GOLD + floor bonus (halved)
    loss  → LOSS_GOLD (consolation; no floor bonus)

XP rewards:
    win   → XP_WIN  distributed across all roster pieces in the lineup
    draw  → XP_DRAW distributed across all roster pieces in the lineup
    loss  → no XP
"""

from dataclasses import dataclass
from typing import List, Optional

WIN_GOLD  = 40
DRAW_GOLD = 15
LOSS_GOLD = 5
GOLD_FLOOR_BONUS = 5   # extra gold per floor on a win
DRAW_FLOOR_DIVISOR = 2  # floor bonus is halved on a draw

XP_WIN  = 2
XP_DRAW = 1


@dataclass
class RewardSummary:
    """Human-readable summary of what was awarded after a battle."""
    gold_earned: int
    xp_per_piece: int
    leveled_up: List[str]   # display names of pieces that leveled up
    life_lost: bool


def apply_rewards(player, result, floor: int) -> RewardSummary:
    """
    Apply gold, XP, and life penalties to player based on battle result.

    player — game.player.Player
    result — ai.BattleResult  (WHITE_WINS / BLACK_WINS / DRAW)
    floor  — current floor number (1-indexed)

    Returns a RewardSummary for display in the UI.
    """
    from ai import WHITE_WINS, DRAW

    outcome = result.result
    life_lost = False

    if outcome == WHITE_WINS:
        gold = WIN_GOLD + floor * GOLD_FLOOR_BONUS
        xp   = XP_WIN
    elif outcome == DRAW:
        gold = DRAW_GOLD + (floor * GOLD_FLOOR_BONUS) // DRAW_FLOOR_DIVISOR
        xp   = XP_DRAW
    else:  # BLACK_WINS (player loses)
        gold = LOSS_GOLD
        xp   = 0
        player.lives -= 1
        life_lost = True

    player.earn(gold)

    leveled_up = []
    for slot_idx in range(8):
        inst = player.piece_at_slot(slot_idx)
        if inst is not None and xp > 0:
            did_level = inst.grant_xp(xp)
            if did_level:
                leveled_up.append(inst.display_name)

    return RewardSummary(
        gold_earned=gold,
        xp_per_piece=xp,
        leveled_up=leveled_up,
        life_lost=life_lost,
    )
