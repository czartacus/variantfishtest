"""
Roguelike run structure.

A Run is a sequence of Encounters.  The player fights one per floor.
After each battle, rewards are applied (gold + XP) and the run advances.

Run ends when:
    - player.lives reaches 0  (defeat)
    - floor exceeds total_floors  (victory)

Every SHOP_INTERVAL floors the player enters a shop phase where they can
spend gold to add pieces from a randomly generated offer to their roster.

Typical usage:
    config = RunConfig(total_floors=10, shop_interval=3)
    run = Run.new(player, config)

    while not run.over:
        enc  = run.current_encounter()
        result = battle_runner.run(...)   # you drive this
        run.resolve(result)
        if run.in_shop:
            # show shop, call run.buy() / run.skip_shop()
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

from .encounter import Encounter, generate_encounter
from .piece_definition import PieceDefinition
from .piece_instance import PieceInstance
from .player import Player
from .rewards import RewardSummary, apply_rewards


class RunPhase(Enum):
    BATTLE  = auto()
    SHOP    = auto()
    VICTORY = auto()
    DEFEAT  = auto()


@dataclass
class ShopOffer:
    """A single item in the floor shop."""
    definition: PieceDefinition
    cost: int
    tier: int


@dataclass
class RunConfig:
    total_floors: int = 10
    shop_interval: int = 3   # shop appears after floor 3, 6, 9 …
    shop_offer_count: int = 3
    shop_base_cost: int = 50
    shop_cost_per_tier: int = 30


@dataclass
class Run:
    """
    Tracks one complete roguelike run.

    Do not instantiate directly — use Run.new().
    """
    player: Player
    config: RunConfig
    floor: int = 1
    phase: RunPhase = RunPhase.BATTLE
    history: List[Tuple[int, str]] = field(default_factory=list)  # (floor, result)
    _encounter: Optional[Encounter] = field(default=None, repr=False)
    _shop_offers: List[ShopOffer] = field(default_factory=list, repr=False)
    _rng_seed: Optional[int] = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def new(
        cls,
        player: Player,
        config: RunConfig = None,
        seed: int = None,
    ) -> "Run":
        config = config or RunConfig()
        run = cls(player=player, config=config, _rng_seed=seed)
        run._encounter = generate_encounter(1, seed=seed)
        return run

    # ------------------------------------------------------------------
    # State accessors
    # ------------------------------------------------------------------

    @property
    def over(self) -> bool:
        return self.phase in (RunPhase.VICTORY, RunPhase.DEFEAT)

    @property
    def in_shop(self) -> bool:
        return self.phase == RunPhase.SHOP

    @property
    def in_battle(self) -> bool:
        return self.phase == RunPhase.BATTLE

    def current_encounter(self) -> Optional[Encounter]:
        return self._encounter if self.phase == RunPhase.BATTLE else None

    def shop_offers(self) -> List[ShopOffer]:
        return list(self._shop_offers)

    # ------------------------------------------------------------------
    # Battle resolution
    # ------------------------------------------------------------------

    def resolve(self, result) -> RewardSummary:
        """
        Apply battle result, award rewards, advance the run.

        result — ai.BattleResult

        Returns a RewardSummary for display.  After calling this, check
        run.phase to determine next step (SHOP, BATTLE, VICTORY, DEFEAT).
        """
        if self.phase != RunPhase.BATTLE:
            raise RuntimeError(f"resolve() called in phase {self.phase}")

        summary = apply_rewards(self.player, result, self.floor)
        self.history.append((self.floor, result.result))

        if self.player.lives <= 0:
            self.phase = RunPhase.DEFEAT
            return summary

        if self.floor >= self.config.total_floors:
            self.phase = RunPhase.VICTORY
            return summary

        # Advance floor
        self.floor += 1

        if self.floor % self.config.shop_interval == 1 and self.floor > 1:
            # e.g. floors 4, 7, 10 trigger a shop
            self._open_shop()
        else:
            self._next_encounter()

        return summary

    # ------------------------------------------------------------------
    # Shop
    # ------------------------------------------------------------------

    def _open_shop(self) -> None:
        from data.piece_pool import PIECE_POOL
        rng = random.Random(
            (self._rng_seed or 0) + self.floor * 1000
        )
        max_tier = 1 + (self.floor - 1) // 3
        pool = [(d, p, t) for d, p, t in PIECE_POOL if t <= max_tier]
        rng.shuffle(pool)
        offers = []
        for defn, _, tier in pool[: self.config.shop_offer_count]:
            cost = self.config.shop_base_cost + tier * self.config.shop_cost_per_tier
            offers.append(ShopOffer(definition=defn, cost=cost, tier=tier))
        self._shop_offers = offers
        self.phase = RunPhase.SHOP

    def buy(self, offer_idx: int) -> bool:
        """
        Purchase a shop offer.  Returns True if the player had enough gold.
        Does NOT close the shop — call skip_shop() when done shopping.
        """
        if not self.in_shop:
            raise RuntimeError("Not in shop phase")
        if not 0 <= offer_idx < len(self._shop_offers):
            raise IndexError(f"Offer index {offer_idx} out of range")
        offer = self._shop_offers[offer_idx]
        if self.player.spend(offer.cost):
            self.player.add_to_roster(offer.definition)
            self._shop_offers.pop(offer_idx)
            return True
        return False

    def skip_shop(self) -> None:
        """Close the shop and advance to the next battle."""
        if not self.in_shop:
            raise RuntimeError("Not in shop phase")
        self._shop_offers = []
        self._next_encounter()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _next_encounter(self) -> None:
        seed = (self._rng_seed or 0) + self.floor if self._rng_seed is not None else None
        self._encounter = generate_encounter(self.floor, seed=seed)
        self.phase = RunPhase.BATTLE

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    @property
    def wins(self) -> int:
        from ai import WHITE_WINS
        return sum(1 for _, r in self.history if r == WHITE_WINS)

    @property
    def losses(self) -> int:
        from ai import BLACK_WINS
        return sum(1 for _, r in self.history if r == BLACK_WINS)

    @property
    def draws(self) -> int:
        from ai import DRAW
        return sum(1 for _, r in self.history if r == DRAW)

    def __repr__(self) -> str:
        return (
            f"Run(floor={self.floor}/{self.config.total_floors}, "
            f"phase={self.phase.name}, "
            f"W/D/L={self.wins}/{self.draws}/{self.losses}, "
            f"lives={self.player.lives})"
        )
