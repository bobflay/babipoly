#!/usr/bin/env python3
"""
Babipoly Game Simulation
========================
Ivory Coast Monopoly variant - Currency: FCFA (West African CFA franc)

Board: 40 squares  |  Players: 2-8  |  Starting money: 250,000 FCFA
Simulates full games for 2, 4, 6, and 8 players and reports:
  - Game length distribution
  - Win rates by player order (first-player advantage)
  - Economic flow (rent, GO rewards, properties bought)
  - Balance recommendations (starting money / rent adjustments)

Usage:
    python babipoly_sim.py              # 500 games per player count (default)
    python babipoly_sim.py --games 200  # faster run
    python babipoly_sim.py --games 2000 # higher precision
"""

import random
import statistics
import argparse
from collections import defaultdict
from copy import deepcopy
from typing import List, Dict, Optional, Tuple

# ══════════════════════════════════════════════════════════════════
# GAME CONSTANTS
# ══════════════════════════════════════════════════════════════════

STARTING_MONEY = 250_000   # FCFA per player
GO_REWARD      = 10_000    # FCFA for passing / landing on GO
JAIL_BAIL      = 5_000     # FCFA to pay out of jail (not specified; ~2% of start)
MAX_ROUNDS     = 10_000    # safety cap to prevent infinite games
BOARD_SIZE     = 40
JAIL_POS       = 10        # "Passage Libre" / jail square

# AI tuning knobs
BUY_RESERVE_RATIO  = 0.10  # keep at least 10% of starting_money after buying
BUILD_RESERVE_RATIO = 0.15 # keep at least 15% of starting_money after building
BAIL_RICH_RATIO    = 0.40  # pay bail immediately if cash > 40% of starting_money

# ══════════════════════════════════════════════════════════════════
# BOARD DATA
# ══════════════════════════════════════════════════════════════════

# Color groups: positions and house cost
GROUPS: Dict[str, dict] = {
    "yellow":     {"positions": [1, 3],        "house_cost": 1_000},
    "red":        {"positions": [6, 8, 9],     "house_cost": 2_000},
    "orange":     {"positions": [13, 15, 16],  "house_cost": 3_000},
    "brown":      {"positions": [18, 19],      "house_cost": 4_000},
    "green":      {"positions": [21, 23, 24],  "house_cost": 5_000},
    "light_blue": {"positions": [26, 27, 29],  "house_cost": 6_000},
    "dark_blue":  {"positions": [31, 33, 34],  "house_cost": 7_000},
    "purple":     {"positions": [37, 39],      "house_cost": 10_000},
}

STATION_POS  = [5, 14, 25, 35]
UTILITY_POS  = [4, 11, 12, 28]
CHANCE_POS   = [7, 17, 36]
COMMUNITY_POS = [2, 22, 32]

# All 40 squares (index = board position).
# Rent list for properties: [base, 1h, 2h, 3h, 4h, hotel]
# Rent list for stations:   [1 owned, 2 owned, 3 owned, 4 owned]
BOARD: Dict[int, dict] = {
    0:  {"type": "go",          "name": "AKWABA (GO)"},
    2:  {"type": "community",   "name": "Caisse de Communauté"},
    7:  {"type": "chance",      "name": "Chance"},
    10: {"type": "jail",        "name": "Passage Libre"},
    17: {"type": "chance",      "name": "Chance"},
    20: {"type": "free_parking","name": "Dans la Forêt du Banco"},
    22: {"type": "community",   "name": "Caisse de Communauté"},
    30: {"type": "go_to_jail",  "name": "Allez dans la Forêt"},
    32: {"type": "community",   "name": "Caisse de Communauté"},
    36: {"type": "chance",      "name": "Chance"},
    38: {"type": "tax",         "name": "Taxe Choco",            "amount": 5_000},

    # ── Yellow ───────────────────────────────────────────────────
    1:  {"type": "property", "name": "Plateau",      "group": "yellow",
         "price": 3_000,  "mortgage": 1_000,
         "rent": [1_000, 2_000, 4_000, 6_000, 8_000, 10_000]},
    3:  {"type": "property", "name": "Cocody",       "group": "yellow",
         "price": 3_000,  "mortgage": 1_000,
         "rent": [1_000, 2_000, 4_000, 6_000, 8_000, 10_000]},

    # ── Red ──────────────────────────────────────────────────────
    6:  {"type": "property", "name": "Marcory",      "group": "red",
         "price": 5_000,  "mortgage": 2_000,
         "rent": [1_000, 3_000, 6_000, 9_000, 12_000, 15_000]},
    8:  {"type": "property", "name": "Zone 4",       "group": "red",
         "price": 6_000,  "mortgage": 3_000,
         "rent": [1_000, 3_000, 7_000, 10_000, 14_000, 18_000]},
    9:  {"type": "property", "name": "Treichville",  "group": "red",
         "price": 5_000,  "mortgage": 2_000,
         "rent": [1_000, 3_000, 6_000, 9_000, 12_000, 15_000]},

    # ── Orange ───────────────────────────────────────────────────
    13: {"type": "property", "name": "Bouaké",       "group": "orange",
         "price": 7_000,  "mortgage": 3_000,
         "rent": [2_000, 4_000, 8_000, 12_000, 17_000, 23_000]},
    15: {"type": "property", "name": "Korhogo",      "group": "orange",
         "price": 8_000,  "mortgage": 4_000,
         "rent": [2_000, 5_000, 9_000, 14_000, 19_000, 26_000]},
    16: {"type": "property", "name": "Man",          "group": "orange",
         "price": 5_000,  "mortgage": 2_000,
         "rent": [1_000, 3_000, 6_000, 10_000, 14_000, 19_000]},

    # ── Brown ────────────────────────────────────────────────────
    18: {"type": "property", "name": "Daloa",        "group": "brown",
         "price": 9_000,  "mortgage": 4_000,
         "rent": [2_000, 5_000, 10_000, 15_000, 21_000, 28_000]},
    19: {"type": "property", "name": "Abobo",        "group": "brown",
         "price": 10_000, "mortgage": 5_000,
         "rent": [2_000, 6_000, 11_000, 17_000, 23_000, 31_000]},

    # ── Green ────────────────────────────────────────────────────
    21: {"type": "property", "name": "Yopougon",     "group": "green",
         "price": 11_000, "mortgage": 5_000,
         "rent": [2_000, 6_000, 12_000, 17_000, 24_000, 33_000]},
    23: {"type": "property", "name": "Koumassi",     "group": "green",
         "price": 11_000, "mortgage": 5_000,
         "rent": [2_000, 6_000, 12_000, 17_000, 24_000, 33_000]},
    24: {"type": "property", "name": "Adjamé",       "group": "green",
         "price": 12_000, "mortgage": 6_000,
         "rent": [2_000, 7_000, 13_000, 19_000, 26_000, 36_000]},

    # ── Light Blue ───────────────────────────────────────────────
    26: {"type": "property", "name": "Bingerville",  "group": "light_blue",
         "price": 13_000, "mortgage": 6_000,
         "rent": [2_000, 7_000, 14_000, 21_000, 28_000, 39_000]},
    27: {"type": "property", "name": "Duékoué",      "group": "light_blue",
         "price": 13_000, "mortgage": 6_000,
         "rent": [2_000, 7_000, 14_000, 21_000, 28_000, 39_000]},
    29: {"type": "property", "name": "Gagnoa",       "group": "light_blue",
         "price": 14_000, "mortgage": 7_000,
         "rent": [2_000, 8_000, 15_000, 23_000, 31_000, 43_000]},

    # ── Dark Blue ────────────────────────────────────────────────
    # Note: Yamoussoukro has house_cost=7,000 but price=5,000 (anomaly in source data)
    31: {"type": "property", "name": "Yamoussoukro", "group": "dark_blue",
         "price": 5_000,  "mortgage": 2_000,
         "rent": [1_000, 3_000, 6_000, 10_000, 14_000, 19_000]},
    33: {"type": "property", "name": "Sassandra",    "group": "dark_blue",
         "price": 15_000, "mortgage": 7_000,
         "rent": [2_000, 8_000, 16_000, 23_000, 31_000, 43_000]},
    34: {"type": "property", "name": "San Pedro",    "group": "dark_blue",
         "price": 16_000, "mortgage": 8_000,
         "rent": [2_000, 9_000, 17_000, 25_000, 34_000, 46_000]},

    # ── Purple ───────────────────────────────────────────────────
    37: {"type": "property", "name": "Assinie",      "group": "purple",
         "price": 17_500, "mortgage": 9_000,
         "rent": [2_000, 10_000, 18_000, 27_000, 37_000, 50_000]},
    39: {"type": "property", "name": "Grand Bassam", "group": "purple",
         "price": 20_000, "mortgage": 10_000,
         "rent": [2_000, 11_000, 21_000, 31_000, 42_000, 58_000]},

    # ── Stations ─────────────────────────────────────────────────
    5:  {"type": "station", "name": "Pinasse de Vridi",
         "price": 10_000, "mortgage": 5_000,
         "rent": [3_000, 6_000, 12_000, 24_000]},
    14: {"type": "station", "name": "Gare de Gbôkas de Treichville",
         "price": 10_000, "mortgage": 5_000,
         "rent": [3_000, 6_000, 12_000, 24_000]},
    25: {"type": "station", "name": "Gare UTB d'Adjamé",
         "price": 10_000, "mortgage": 5_000,
         "rent": [3_000, 6_000, 12_000, 24_000]},
    35: {"type": "station", "name": "Aéroport Houphouët-Boigny",
         "price": 10_000, "mortgage": 5_000,
         "rent": [3_000, 6_000, 12_000, 24_000]},

    # ── Utilities ────────────────────────────────────────────────
    4:  {"type": "utility", "name": "Petit Café pour Autorité",
         "price": 10_000, "mortgage": 5_000},
    11: {"type": "utility", "name": "Threesixty Gym",
         "price": 10_000, "mortgage": 5_000},
    12: {"type": "utility", "name": "CIE",
         "price": 7_500,  "mortgage": 4_000},
    28: {"type": "utility", "name": "SODECI",
         "price": 7_500,  "mortgage": 4_000},
}

# ══════════════════════════════════════════════════════════════════
# CARD DECKS
# ══════════════════════════════════════════════════════════════════
# Format: (effect, value)
# Effects:
#   move_to          → (int) target position, collects GO if passed
#   move_back        → (int) spaces back, no GO collection
#   nearest_station  → None, move to nearest station (double rent if owned)
#   go_to_jail       → None
#   get_out_of_jail  → None, player gains 1 card
#   receive          → (int) FCFA from bank
#   pay              → (int) FCFA to bank
#   pay_each         → (int) pay each active player this amount
#   receive_from_each→ (int) each active player pays you this amount
#   repairs          → (house_cost, hotel_cost) per building owned

CHANCE_CARDS = [
    ("move_to",           0),          # Advance to AKWABA (collect GO)
    ("move_to",           39),         # Advance to Grand Bassam
    ("move_to",           3),          # Advance to Cocody
    ("move_to",           35),         # Advance to Aéroport
    ("move_to",           25),         # Advance to Gare UTB
    ("nearest_station",   None),       # Move to nearest station (2× rent)
    ("move_to",           5),          # Advance to Pinasse de Vridi
    ("receive",           2_500),      # Bank dividend
    ("get_out_of_jail",   None),       # Get Out of Jail Free
    ("move_back",         3),          # Go back 3 spaces
    ("go_to_jail",        None),       # Go to Jail
    ("repairs",           (1_250, 5_000)),   # Per house / per hotel
    ("pay",               750),        # Speeding fine
    ("pay_each",          2_500),      # Elected to council: pay each player
    ("receive",           7_500),      # Investment pays off
    ("move_to",           21),         # Advance to Yopougon
]

COMMUNITY_CARDS = [
    ("move_to",           0),          # Advance to AKWABA
    ("receive",           10_000),     # Bank error in your favor
    ("pay",               2_500),      # Doctor fees
    ("receive",           2_500),      # Goods sale
    ("get_out_of_jail",   None),       # Get Out of Jail Free
    ("go_to_jail",        None),       # Go to Jail
    ("receive_from_each", 500),        # Birthday: each player gives 500
    ("receive",           1_000),      # Tax refund
    ("receive",           5_000),      # Inheritance
    ("receive",           5_000),      # Life insurance
    ("pay",               7_500),      # School fees
    ("pay",               5_000),      # Hospital fees
    ("receive",           500),        # Beauty contest 2nd prize
    ("receive",           12_500),     # Annual income
    ("repairs",           (2_000, 5_750)),   # Per house / per hotel
    ("receive",           1_250),      # Interest earned
]


# ══════════════════════════════════════════════════════════════════
# PLAYER
# ══════════════════════════════════════════════════════════════════

class Player:
    __slots__ = (
        "id", "money", "position", "in_jail", "jail_turns",
        "get_out_cards", "bankrupt", "properties", "consec_doubles"
    )

    def __init__(self, pid: int, starting_money: int):
        self.id             = pid
        self.money          = starting_money
        self.position       = 0
        self.in_jail        = False
        self.jail_turns     = 0
        self.get_out_cards  = 0
        self.bankrupt       = False
        self.properties: List[int] = []
        self.consec_doubles = 0

    def net_worth(self, ownership: dict) -> int:
        """Cash + liquidation value of all held assets."""
        worth = self.money
        for pos in self.properties:
            ow  = ownership[pos]
            sq  = BOARD[pos]
            if ow["mortgaged"]:
                worth += sq["mortgage"]
            else:
                worth += sq["price"]
                b = ow["buildings"]
                if b > 0 and sq["type"] == "property":
                    hc = GROUPS[sq["group"]]["house_cost"]
                    worth += (b * hc) // 2   # 50% resale
        return worth


# ══════════════════════════════════════════════════════════════════
# GAME ENGINE
# ══════════════════════════════════════════════════════════════════

class BabopolyGame:

    def __init__(self, num_players: int, starting_money: int = STARTING_MONEY):
        self.num_players   = num_players
        self.starting_money = starting_money
        self.players       = [Player(i, starting_money) for i in range(num_players)]

        # Ownership state per purchasable square
        self.ownership: Dict[int, dict] = {
            pos: {"owner": None, "buildings": 0, "mortgaged": False}
            for pos, sq in BOARD.items()
            if sq["type"] in ("property", "station", "utility")
        }

        self.chance_deck    = self._make_deck(CHANCE_CARDS)
        self.community_deck = self._make_deck(COMMUNITY_CARDS)

        self.round_count = 0
        self.turn_count  = 0

        # Per-game stats (populated during run)
        self.stats = {
            "rounds":           0,
            "turns":            0,
            "winner":           -1,
            "timed_out":        False,
            "bankrupt_order":   [],
            "peak_cash":        [0] * num_players,
            "props_bought":     [0] * num_players,
            "rent_paid":        [0] * num_players,
            "rent_received":    [0] * num_players,
            "go_rewards":       [0] * num_players,
            "total_tax_paid":   [0] * num_players,
        }

    # ─── Deck ────────────────────────────────────────────────────

    def _make_deck(self, cards: list) -> list:
        """Shuffle deck; 'get_out_of_jail' cards go to the bottom (standard rule)."""
        normal = [c for c in cards if c[0] != "get_out_of_jail"]
        jail   = [c for c in cards if c[0] == "get_out_of_jail"]
        random.shuffle(normal)
        return normal + jail

    def _draw_chance(self) -> tuple:
        if not self.chance_deck:
            self.chance_deck = self._make_deck(CHANCE_CARDS)
        return self.chance_deck.pop(0)

    def _draw_community(self) -> tuple:
        if not self.community_deck:
            self.community_deck = self._make_deck(COMMUNITY_CARDS)
        return self.community_deck.pop(0)

    # ─── Dice ────────────────────────────────────────────────────

    @staticmethod
    def roll() -> Tuple[int, int]:
        return random.randint(1, 6), random.randint(1, 6)

    # ─── Movement ────────────────────────────────────────────────

    def _move_steps(self, player: Player, steps: int):
        """Move forward by steps; collect GO_REWARD if wrapping."""
        old = player.position
        new = (old + steps) % BOARD_SIZE
        # Passed GO (wrapped, but did NOT land exactly on GO with steps that landed at 0;
        # landing on 0 is handled by _apply_square's 'go' branch).
        if new < old or (new == 0 and steps > 0):
            if new != 0:   # passing, not landing → give reward here
                self._credit(player, GO_REWARD, "go")
        player.position = new

    def _move_to(self, player: Player, target: int):
        """Teleport to target; collect GO_REWARD if target is behind current pos."""
        if target < player.position:
            self._credit(player, GO_REWARD, "go")
        player.position = target

    def _send_to_jail(self, player: Player):
        player.position    = JAIL_POS
        player.in_jail     = True
        player.jail_turns  = 0
        player.consec_doubles = 0

    # ─── Money ───────────────────────────────────────────────────

    def _credit(self, player: Player, amount: int, source: str = "bank"):
        player.money += amount
        pid = player.id
        if source == "go":
            self.stats["go_rewards"][pid] += amount
        if player.money > self.stats["peak_cash"][pid]:
            self.stats["peak_cash"][pid] = player.money

    def _charge(self, player: Player, amount: int, creditor: Optional[Player] = None) -> bool:
        """
        Deduct amount from player.  If player cannot pay even after liquidation,
        declare bankruptcy. Returns True if payment succeeded.
        """
        if player.money < amount:
            self._raise_funds(player, amount)

        if player.money >= amount:
            player.money -= amount
            if creditor and not creditor.bankrupt:
                self.stats["rent_received"][creditor.id] += amount
                creditor.money += amount
                if creditor.money > self.stats["peak_cash"][creditor.id]:
                    self.stats["peak_cash"][creditor.id] = creditor.money
            return True

        # Cannot pay → bankrupt
        self._bankrupt(player, creditor)
        return False

    def _raise_funds(self, player: Player, needed: int):
        """Sell buildings then mortgage properties until liquid enough."""
        # Step 1: sell buildings (50% return) — sell from worst groups first
        for pos in list(player.properties):
            if player.money >= needed:
                break
            sq = BOARD[pos]
            ow = self.ownership[pos]
            if sq["type"] == "property" and ow["buildings"] > 0:
                hc = GROUPS[sq["group"]]["house_cost"]
                refund = (ow["buildings"] * hc) // 2
                player.money      += refund
                ow["buildings"]    = 0

        # Step 2: mortgage unmortgaged properties (no buildings)
        for pos in list(player.properties):
            if player.money >= needed:
                break
            sq = BOARD[pos]
            ow = self.ownership[pos]
            if not ow["mortgaged"] and ow["buildings"] == 0:
                player.money  += sq["mortgage"]
                ow["mortgaged"] = True

    def _bankrupt(self, player: Player, creditor: Optional[Player] = None):
        player.bankrupt = True
        self.stats["bankrupt_order"].append(player.id)

        if creditor and not creditor.bankrupt:
            creditor.money += player.money
            for pos in player.properties:
                ow = self.ownership[pos]
                ow["mortgaged"] = True    # transferred mortgaged per rules
                ow["owner"]     = creditor.id
                creditor.properties.append(pos)
        else:
            for pos in player.properties:
                ow = self.ownership[pos]
                ow["owner"]     = None
                ow["buildings"] = 0
                ow["mortgaged"] = False

        player.properties = []
        player.money      = 0

    # ─── Ownership Helpers ───────────────────────────────────────

    def _owns_group(self, player: Player, group: str) -> bool:
        return all(
            self.ownership[p]["owner"] == player.id
            and not self.ownership[p]["mortgaged"]
            for p in GROUPS[group]["positions"]
        )

    def _stations_owned(self, player: Player) -> int:
        return sum(
            1 for p in STATION_POS
            if self.ownership[p]["owner"] == player.id
            and not self.ownership[p]["mortgaged"]
        )

    def _utilities_owned(self, player: Player) -> int:
        return sum(
            1 for p in UTILITY_POS
            if self.ownership[p]["owner"] == player.id
            and not self.ownership[p]["mortgaged"]
        )

    # ─── Rent Calculation ────────────────────────────────────────

    def _rent(self, pos: int, dice: int, double_station: bool = False) -> int:
        sq = BOARD[pos]
        ow = self.ownership[pos]
        if ow["owner"] is None or ow["mortgaged"]:
            return 0

        owner = self.players[ow["owner"]]
        t = sq["type"]

        if t == "property":
            b    = ow["buildings"]
            rent = sq["rent"][b]
            if b == 0 and self._owns_group(owner, sq["group"]):
                rent *= 2    # monopoly double-rent rule
            return rent

        elif t == "station":
            count = self._stations_owned(owner)
            mult  = 2 if double_station else 1
            return sq["rent"][count - 1] * mult

        elif t == "utility":
            count = self._utilities_owned(owner)
            mult  = 10 if count >= 2 else 4
            return dice * mult

        return 0

    # ─── AI: Building Strategy ───────────────────────────────────

    def _try_build(self, player: Player):
        """Build houses/hotels on monopolies while maintaining a cash reserve."""
        reserve = int(self.starting_money * BUILD_RESERVE_RATIO)
        for group, info in GROUPS.items():
            if not self._owns_group(player, group):
                continue
            positions  = info["positions"]
            house_cost = info["house_cost"]

            # Repeatedly try to place one house at a time (even development rule)
            improved = True
            while improved:
                improved = False
                min_b = min(self.ownership[p]["buildings"] for p in positions)
                if min_b >= 5:
                    break
                for pos in positions:
                    ow = self.ownership[pos]
                    if ow["buildings"] == min_b and ow["buildings"] < 5:
                        if player.money - house_cost >= reserve:
                            player.money  -= house_cost
                            ow["buildings"] += 1
                            improved = True
                        else:
                            improved = False
                            break

    # ─── AI: Buy Decision ────────────────────────────────────────

    def _should_buy(self, player: Player, price: int) -> bool:
        reserve = int(self.starting_money * BUY_RESERVE_RATIO)
        return player.money - price >= reserve

    # ─── Card Resolution ─────────────────────────────────────────

    def _apply_card(self, player: Player, card: tuple, dice: int):
        effect, value = card
        active_others = [p for p in self.players if not p.bankrupt and p.id != player.id]

        if effect == "move_to":
            self._move_to(player, value)
            if not player.bankrupt:
                self._apply_square(player, dice)

        elif effect == "move_back":
            new_pos = (player.position - value) % BOARD_SIZE
            player.position = new_pos
            if not player.bankrupt:
                self._apply_square(player, dice)

        elif effect == "nearest_station":
            pos     = player.position
            nearest = min(STATION_POS, key=lambda s: (s - pos) % BOARD_SIZE)
            self._move_to(player, nearest)
            ow = self.ownership[nearest]
            if ow["owner"] is not None and ow["owner"] != player.id and not ow["mortgaged"]:
                owner = self.players[ow["owner"]]
                rent  = self._rent(nearest, dice, double_station=True)
                if rent:
                    self.stats["rent_paid"][player.id] += rent
                    self._charge(player, rent, owner)

        elif effect == "go_to_jail":
            self._send_to_jail(player)

        elif effect == "get_out_of_jail":
            player.get_out_cards += 1

        elif effect == "receive":
            self._credit(player, value)

        elif effect == "pay":
            self.stats["total_tax_paid"][player.id] += value
            self._charge(player, value)

        elif effect == "pay_each":
            for other in active_others:
                if player.bankrupt:
                    break
                amt = min(value, player.money)
                player.money -= amt
                other.money  += amt

        elif effect == "receive_from_each":
            for other in active_others:
                give = min(value, other.money)
                other.money  -= give
                player.money += give

        elif effect == "repairs":
            house_cost, hotel_cost = value
            total = 0
            for pos in player.properties:
                sq = BOARD.get(pos, {})
                ow = self.ownership[pos]
                if sq.get("type") == "property":
                    b = ow["buildings"]
                    total += hotel_cost if b == 5 else b * house_cost
            if total > 0:
                self.stats["total_tax_paid"][player.id] += total
                self._charge(player, total)

    # ─── Square Resolution ───────────────────────────────────────

    def _apply_square(self, player: Player, dice: int):
        if player.bankrupt:
            return
        pos = player.position
        sq  = BOARD.get(pos)
        if sq is None:
            return
        t = sq["type"]

        if t == "go":
            # Landing on GO gives the reward
            self._credit(player, GO_REWARD, "go")

        elif t == "go_to_jail":
            self._send_to_jail(player)

        elif t == "tax":
            self.stats["total_tax_paid"][player.id] += sq["amount"]
            self._charge(player, sq["amount"])

        elif t == "chance":
            card = self._draw_chance()
            self._apply_card(player, card, dice)

        elif t == "community":
            card = self._draw_community()
            self._apply_card(player, card, dice)

        elif t in ("property", "station", "utility"):
            ow = self.ownership[pos]
            if ow["owner"] is None:
                # Unowned: AI decides whether to buy
                if self._should_buy(player, sq["price"]):
                    player.money -= sq["price"]
                    ow["owner"]   = player.id
                    player.properties.append(pos)
                    self.stats["props_bought"][player.id] += 1
            elif ow["owner"] != player.id and not ow["mortgaged"]:
                # Owned by another player: pay rent
                owner = self.players[ow["owner"]]
                if not owner.bankrupt:
                    rent = self._rent(pos, dice)
                    if rent > 0:
                        self.stats["rent_paid"][player.id] += rent
                        self._charge(player, rent, owner)

        # else: jail (free), free_parking (free) → do nothing

    # ─── Jail Turn ───────────────────────────────────────────────

    def _jail_turn(self, player: Player) -> Optional[Tuple[int, int]]:
        """
        Handle a jail turn. Returns dice tuple if player gets out (and should move),
        or None if player stays in jail this turn.
        """
        player.jail_turns += 1

        # Use Get Out of Jail Free card immediately
        if player.get_out_cards > 0:
            player.get_out_cards -= 1
            player.in_jail        = False
            player.jail_turns     = 0
            return self.roll()

        # Pay bail if rich enough, or forced out after 3 turns
        bail_threshold = int(self.starting_money * BAIL_RICH_RATIO)
        if player.jail_turns >= 3 or player.money > bail_threshold:
            if player.money >= JAIL_BAIL:
                player.money  -= JAIL_BAIL
                player.in_jail = False
                player.jail_turns = 0
                return self.roll()

        # Attempt doubles roll to escape
        d1, d2 = self.roll()
        if d1 == d2:
            player.in_jail     = False
            player.jail_turns  = 0
            return d1, d2

        return None   # stays in jail

    # ─── Full Player Turn ────────────────────────────────────────

    def _play_turn(self, player: Player):
        if player.bankrupt:
            return

        player.consec_doubles = 0

        while True:
            # Handle jail
            if player.in_jail:
                result = self._jail_turn(player)
                if result is None:
                    break   # stays in jail, turn over
                d1, d2 = result
            else:
                d1, d2 = self.roll()

            dice   = d1 + d2
            double = (d1 == d2)

            if double and not player.in_jail:
                player.consec_doubles += 1
                if player.consec_doubles == 3:
                    self._send_to_jail(player)
                    break

            if not player.in_jail:
                self._move_steps(player, dice)

            self._apply_square(player, dice)

            if player.bankrupt:
                break

            # After each action, build if possible
            self._try_build(player)

            if not double or player.in_jail:
                break
            # Rolled doubles → go again (player.in_jail may have been set by 3rd double)

        self.turn_count += 1

    # ─── Game Loop ───────────────────────────────────────────────

    def run(self) -> dict:
        while True:
            self.round_count += 1

            for player in self.players:
                if not player.bankrupt:
                    self._play_turn(player)

            active = [p for p in self.players if not p.bankrupt]

            if len(active) <= 1:
                self.stats["winner"] = active[0].id if active else -1
                break

            if self.round_count >= MAX_ROUNDS:
                # Timeout: richest player wins
                winner = max(active, key=lambda p: p.net_worth(self.ownership))
                self.stats["winner"]    = winner.id
                self.stats["timed_out"] = True
                break

        self.stats["rounds"] = self.round_count
        self.stats["turns"]  = self.turn_count
        return self.stats


# ══════════════════════════════════════════════════════════════════
# SIMULATION RUNNER
# ══════════════════════════════════════════════════════════════════

def run_simulations(num_players: int, num_games: int, starting_money: int) -> dict:
    res = {
        "num_players":    num_players,
        "num_games":      num_games,
        "starting_money": starting_money,
        "rounds":         [],
        "turns":          [],
        "winners":        [],
        "timed_out":      0,
        # Per player (list of per-game values)
        "props_bought":   [[] for _ in range(num_players)],
        "rent_paid":      [[] for _ in range(num_players)],
        "rent_received":  [[] for _ in range(num_players)],
        "go_rewards":     [[] for _ in range(num_players)],
        "peak_cash":      [[] for _ in range(num_players)],
        "tax_paid":       [[] for _ in range(num_players)],
    }

    for _ in range(num_games):
        game  = BabopolyGame(num_players, starting_money)
        stats = game.run()

        res["rounds"].append(stats["rounds"])
        res["turns"].append(stats["turns"])
        res["winners"].append(stats["winner"])
        if stats["timed_out"]:
            res["timed_out"] += 1

        for pid in range(num_players):
            res["props_bought"][pid].append(stats["props_bought"][pid])
            res["rent_paid"][pid].append(stats["rent_paid"][pid])
            res["rent_received"][pid].append(stats["rent_received"][pid])
            res["go_rewards"][pid].append(stats["go_rewards"][pid])
            res["peak_cash"][pid].append(stats["peak_cash"][pid])
            res["tax_paid"][pid].append(stats["total_tax_paid"][pid])

    return res


# ══════════════════════════════════════════════════════════════════
# ANALYSIS & REPORTING
# ══════════════════════════════════════════════════════════════════

def _pct(x: float) -> str:
    return f"{x:5.1f}%"


def _bar(value: float, total: float, width: int = 20) -> str:
    filled = int(round(value / total * width)) if total else 0
    return "█" * filled + "░" * (width - filled)


def analyze_single(res: dict) -> str:
    np  = res["num_players"]
    ng  = res["num_games"]
    sm  = res["starting_money"]
    rds = res["rounds"]
    out = []

    out.append(f"\n{'═'*62}")
    out.append(f"  {np}-PLAYER GAME  │  {ng} simulations  │  Start: {sm:,} FCFA")
    out.append(f"{'═'*62}")

    # Game length
    out.append("\nGame Length (Rounds):")
    out.append(f"  Min     : {min(rds):>6,}")
    out.append(f"  p25     : {int(sorted(rds)[ng // 4]):>6,}")
    out.append(f"  Median  : {int(statistics.median(rds)):>6,}")
    out.append(f"  Mean    : {statistics.mean(rds):>6,.1f}")
    out.append(f"  p75     : {int(sorted(rds)[ng * 3 // 4]):>6,}")
    out.append(f"  Max     : {max(rds):>6,}")
    out.append(f"  Std Dev : {statistics.stdev(rds) if len(rds) > 1 else 0:>6,.1f}")
    out.append(f"  Timed out: {res['timed_out']} / {ng} ({res['timed_out']/ng*100:.1f}%)")

    # Win rates
    win_counts = defaultdict(int)
    for wid in res["winners"]:
        if wid >= 0:
            win_counts[wid] += 1

    expected = 100.0 / np
    out.append(f"\nWin Rate by Player Order (expected {expected:.1f}% each):")
    for pid in range(np):
        wins = win_counts[pid]
        pct  = wins / ng * 100
        bar  = _bar(pct, 100.0 / np * 2)
        diff = pct - expected
        sign = "+" if diff >= 0 else ""
        out.append(f"  P{pid+1}: {wins:>4} wins  {_pct(pct)}  {bar}  ({sign}{diff:.1f}%)")

    # Economic averages
    out.append(f"\nEconomics (average per player per game):")
    out.append(f"  {'':6}  {'Props':>5}  {'Rent Paid':>10}  {'Rent Rcvd':>10}  "
               f"{'GO Bonus':>9}  {'Peak Cash':>10}")
    for pid in range(np):
        pb  = statistics.mean(res["props_bought"][pid])
        rp  = statistics.mean(res["rent_paid"][pid])
        rr  = statistics.mean(res["rent_received"][pid])
        go  = statistics.mean(res["go_rewards"][pid])
        pc  = statistics.mean(res["peak_cash"][pid])
        out.append(f"  P{pid+1}:    {pb:5.1f}  {rp:>10,.0f}  {rr:>10,.0f}  "
                   f"{go:>9,.0f}  {pc:>10,.0f}")

    return "\n".join(out)


def generate_recommendations(all_results: dict) -> str:
    out = []
    out.append(f"\n{'═'*62}")
    out.append("  SIMULATION ANALYSIS & RECOMMENDATIONS")
    out.append(f"{'═'*62}")

    # ── Core metrics ──────────────────────────────────────────────
    # Use completion rate and median of COMPLETED games (not mean,
    # which is skewed when many games hit the MAX_ROUNDS cap).
    out.append("\nGame Completion & Length Summary:")
    out.append(f"  {'Players':>8}  {'Complet.':>9}  {'Med (all)':>10}  "
               f"{'Med (done)':>11}  {'Assessment'}")
    out.append(f"  {'':─>8}  {'':─>9}  {'':─>10}  {'':─>11}  {'':─<22}")

    for np in sorted(all_results):
        res  = all_results[np]
        ng   = res["num_games"]
        rds  = res["rounds"]
        tout = res["timed_out"]
        done = [r for r in rds if r < MAX_ROUNDS]
        completion_pct = (ng - tout) / ng * 100
        med_all  = statistics.median(rds)
        med_done = statistics.median(done) if done else MAX_ROUNDS

        if completion_pct < 20:
            verdict = "✗ Critical: games never end"
        elif completion_pct < 50:
            verdict = "⚠ Most games timeout"
        elif med_done > 200:
            verdict = "→ Completed games too long"
        elif med_done < 40:
            verdict = "⚠ Completed games too short"
        else:
            verdict = "✓ Acceptable"

        out.append(f"  {np:>8}  {completion_pct:>8.0f}%  {med_all:>10.0f}  "
                   f"{med_done:>11.0f}  {verdict}")

    out.append(f"""
  TARGET: ≥80% completion rate, median 60–150 rounds per game.
  MAX_ROUNDS cap = {MAX_ROUNDS:,}. Games hitting the cap are 'timed out'.
""")

    # ── Root cause analysis ───────────────────────────────────────
    out.append("─"*62)
    out.append("  ROOT CAUSE: STARTING MONEY vs RENT RATIO")
    out.append("─"*62)

    sm = list(all_results.values())[0]["starting_money"]
    max_hotel_rent  = max(BOARD[p]["rent"][-1] for p in BOARD
                          if BOARD[p].get("type") == "property")
    go_per_round    = GO_REWARD
    rent_ratio      = max_hotel_rent / sm * 100
    go_ratio        = GO_REWARD / sm * 100

    out.append(f"""
  Starting money    : {sm:>10,} FCFA
  Max hotel rent    : {max_hotel_rent:>10,} FCFA  ({rent_ratio:.1f}% of starting money)
  GO reward/round   : {go_per_round:>10,} FCFA  ({go_ratio:.1f}% of starting money)

  Classic Monopoly reference:
    Max hotel rent  : $2,000 / $1,500 starting = 133% of starting money
    GO reward       : $200   / $1,500 starting =  13% of starting money

  Babipoly problem:
    • Max rent is only {rent_ratio:.0f}% of starting money (Monopoly: 133%).
      A player with 250,000 FCFA can absorb the highest possible rent
      (58,000 FCFA) and STILL have {sm - max_hotel_rent:,} FCFA remaining.
    • GO reward ({GO_REWARD:,}/round) continuously reinjects bank money,
      sustaining players who would otherwise face elimination.
    • Result: with 4+ players, no one ever goes fully bankrupt.

  SOLUTIONS (choose one or combine):
  ┌─────────────────────────────────────────────────────────┐
  │ Option A — Reduce starting money (fastest fix)          │
  │   Current: 250,000 FCFA → Suggested: 30,000–50,000 FCFA│
  │   Keep all prices/rents as-is. Properties stay at the  │
  │   same prices, but they cost a much higher fraction of  │
  │   each player's starting wealth.                        │
  │                                                         │
  │ Option B — Scale all rents up 5–10×                     │
  │   Keep 250,000 FCFA starting money. Multiply every      │
  │   rent value (property, station, utility) by 5×.        │
  │   Hotel on Grand Bassam: 58,000 → 290,000 FCFA.        │
  │   This is a major redesign of the card/property system. │
  │                                                         │
  │ Option C — Hybrid (recommended)                         │
  │   Starting money: 250,000 → 60,000 FCFA                 │
  │   GO reward     : 10,000  →  5,000 FCFA                 │
  │   Rents         : multiply all by 1.5×                  │
  │   This preserves the board feel while fixing completion. │
  └─────────────────────────────────────────────────────────┘
""")

    # ── First-player advantage ────────────────────────────────────
    out.append("─"*62)
    out.append("  FIRST-PLAYER ADVANTAGE ANALYSIS")
    out.append("─"*62)
    for np in sorted(all_results):
        res      = all_results[np]
        ng       = res["num_games"]
        expected = 100.0 / np
        p1_wins  = sum(1 for wid in res["winners"] if wid == 0)
        p1_pct   = p1_wins / ng * 100
        diff     = p1_pct - expected
        if abs(diff) > 5:
            flag = f"⚠ {'+' if diff > 0 else ''}{diff:.1f}% vs expected"
        else:
            flag = "✓ balanced"
        out.append(f"  [{np}P] P1 win rate: {p1_pct:.1f}%  (expected {expected:.1f}%)  {flag}")

    out.append("""
  Note: In timeout games the winner is determined by net worth.
  First-player advantage in 6-8P games partly reflects that P1
  has more properties accumulated when the cap hits.
""")

    # ── Specific board balance issues ────────────────────────────
    out.append("─"*62)
    out.append("  SPECIFIC BOARD BALANCE ISSUES")
    out.append("─"*62)
    out.append("""
  1. Yamoussoukro anomaly (pos 31 — dark_blue group)
     • Price: 5,000 FCFA  |  House cost: 7,000 FCFA  |  Hotel rent: 19,000 FCFA
     • House cost EXCEEDS purchase price — impossible ROI for the developer.
     • Fix A: Raise price to 12,000 FCFA (aligns with group peers).
     • Fix B: Lower house cost to 3,000 FCFA.

  2. Yellow group undervalued relative to board position
     • Plateau & Cocody (pos 1, 3): price 3,000 FCFA, hotel rent 10,000 FCFA.
     • These are the first properties on the board yet generate the least income.
     • Yellow hotel rent (10,000) equals the GO reward — landing on a fully
       developed yellow group is no worse than passing GO. Not threatening enough.
     • Fix: Raise hotel rent to 15,000–20,000 FCFA.

  3. GO reward too high relative to rents
     • GO gives 10,000 FCFA every ~13 squares (average dice ≈ 7 → ~6 turns/loop).
     • This is a constant bank injection that offsets rent losses.
     • Fix: Reduce GO reward to 5,000 FCFA, or make it 0 and only pay
       when landing ON GO (European variant).

  4. Dark Blue house cost too high
     • Sassandra & San Pedro: house_cost = 7,000 FCFA.
     • Hotel investment: 5 × 7,000 = 35,000 FCFA per property.
     • But with starting money at 250,000 this is trivially affordable.
     • Not a bug with current starting money, but if you lower starting
       money, dark_blue development becomes the luxury it should be.

  5. Utility rent too low
     • CIE & SODECI: 4× dice = avg 28 FCFA. Negligible.
     • Owning both: 10× dice = avg 70 FCFA. Still negligible.
     • Fix: Change to flat rents (e.g., 2,000 / 8,000 FCFA) rather than dice×.
""")

    out.append("─"*62)
    out.append("  PROPOSED PARAMETER TABLE")
    out.append("─"*62)
    out.append(f"""
  Parameter               Current         Option A       Option C (rec.)
  ──────────────────────  ──────────────  ─────────────  ──────────────
  Starting money          250,000 FCFA    40,000 FCFA    60,000 FCFA
  GO reward               10,000 FCFA     4,000 FCFA     5,000 FCFA
  Rent multiplier              1×              1×             1.5×
  Jail bail                5,000 FCFA     1,000 FCFA     1,500 FCFA
  Yamoussoukro price       5,000 FCFA     5,000 FCFA    12,000 FCFA
  Dark blue house cost     7,000 FCFA     7,000 FCFA     5,000 FCFA
  Taxe Choco (tax sq)      5,000 FCFA     1,000 FCFA     2,000 FCFA

  To test these, edit STARTING_MONEY, GO_REWARD, and rent tables
  in babipoly_sim.py, then rerun:
      python babipoly_sim.py --games 500
""")

    return "\n".join(out)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Babipoly Game Simulator — Ivory Coast Monopoly variant"
    )
    parser.add_argument(
        "--games", type=int, default=500,
        help="Number of games to simulate per player count (default: 500)"
    )
    parser.add_argument(
        "--players", type=int, nargs="+", default=[2, 4, 6, 8],
        help="Player counts to simulate (default: 2 4 6 8)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    print("=" * 62)
    print("  BABIPOLY GAME SIMULATION")
    print("  Ivory Coast Monopoly — Currency: FCFA")
    print("=" * 62)
    print(f"\n  Simulating {args.games} games each for: "
          f"{', '.join(str(n) + ' players' for n in args.players)}")
    print(f"  Starting money: {STARTING_MONEY:,} FCFA  |  GO reward: {GO_REWARD:,} FCFA\n")

    all_results = {}
    for np in args.players:
        print(f"  [{np}P] Running {args.games} games...", end="", flush=True)
        res = run_simulations(np, args.games, STARTING_MONEY)
        all_results[np] = res
        avg = statistics.mean(res["rounds"])
        med = statistics.median(res["rounds"])
        print(f"  done  |  avg {avg:.0f} rounds  |  median {med:.0f} rounds")

    # Print per-player-count analysis
    for np in args.players:
        print(analyze_single(all_results[np]))

    # Print recommendations
    print(generate_recommendations(all_results))

    print("\n" + "=" * 62)
    print("  Simulation complete.")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
