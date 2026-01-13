"""
NFL Live Win Probability Calculator

This module provides functionality to calculate win probabilities for NFL games
based on current game state including score, time, possession, and field position.
"""

import numpy as np
from typing import Optional


class NFLWinProbability:
    """Calculate win probability for NFL games based on current game state."""

    def __init__(self):
        """Initialize the win probability calculator."""
        # Base coefficients for logistic regression model
        # Score weight is scaled by time - this is the base weight at end of game
        self.score_weight = 0.4
        self.possession_bonus = 0.3
        self.field_position_weight = 0.02

        # Enhanced factors
        self.timeout_weight = 0.15  # Value of each timeout
        self.team_strength_weight = 0.5  # Impact of team quality difference

        # Down and distance weights
        self.down_distance_weights = {
            1: 0.2,   # 1st down - good situation
            2: 0.1,   # 2nd down - neutral
            3: -0.1,  # 3rd down - pressure situation
            4: -0.5,  # 4th down - critical situation
        }
        self.distance_weight = -0.02  # Penalty per yard to go

        # Full game duration in seconds (4 quarters * 15 minutes)
        self.full_game_seconds = 3600

    def calculate_win_probability(
        self,
        score_diff: int,
        time_remaining: int,
        has_possession: bool = False,
        field_position: Optional[int] = None,
        down: Optional[int] = None,
        distance: Optional[int] = None,
        team_timeouts: Optional[int] = None,
        opponent_timeouts: Optional[int] = None,
        team_win_pct: Optional[float] = None,
        opponent_win_pct: Optional[float] = None
    ) -> float:
        """
        Calculate win probability for the team with enhanced situational factors.

        Args:
            score_diff: Point differential (positive if team is leading)
            time_remaining: Seconds remaining in the game
            has_possession: Whether the team has possession
            field_position: Yard line (0-100, own 0 to opponent 0)
            down: Current down (1-4), only relevant if has_possession=True
            distance: Yards to go for first down, only relevant if has_possession=True
            team_timeouts: Number of timeouts remaining for team (0-3)
            opponent_timeouts: Number of timeouts remaining for opponent (0-3)
            team_win_pct: Team's win percentage (0.0-1.0)
            opponent_win_pct: Opponent's win percentage (0.0-1.0)

        Returns:
            Win probability as a float between 0 and 1

        Examples:
            >>> calculator = NFLWinProbability()
            >>> # Up by 3, 2 min left, 3rd & 7, 2 timeouts vs 0
            >>> prob = calculator.calculate_win_probability(
            ...     score_diff=3,
            ...     time_remaining=120,
            ...     has_possession=True,
            ...     field_position=65,
            ...     down=3,
            ...     distance=7,
            ...     team_timeouts=2,
            ...     opponent_timeouts=0
            ... )
        """
        # Calculate time scaling factor
        # As time decreases, score differential becomes MORE important
        # At start of game (3600s), time_scale ~ 0.33 (score matters less)
        # At end of game (0s), time_scale ~ 1.0 (score matters most)
        time_scale = self._calculate_time_scale(time_remaining)

        # Start with z = 0 (50% baseline for tied game)
        z = 0.0

        # Score differential scaled by time
        # A 7-point lead with 1 minute left is worth more than with 30 minutes left
        z += score_diff * self.score_weight * time_scale

        # Add possession bonus (also scaled by time - possession matters more late)
        if has_possession:
            z += self.possession_bonus * time_scale

        # Add field position factor (scaled by time)
        if field_position is not None:
            # Field position bonus (closer to opponent endzone = better)
            z += (field_position - 50) * self.field_position_weight * time_scale

        # Add down and distance factors
        if has_possession and down is not None:
            # Down situation impact
            z += self.down_distance_weights.get(down, 0) * time_scale

            # Distance to go impact (longer distance = worse)
            if distance is not None:
                # Scale distance penalty: 3rd & 1 is much better than 3rd & 10
                distance_penalty = distance * self.distance_weight
                # Extra penalty for 3rd/4th down with long distance
                if down >= 3 and distance >= 7:
                    distance_penalty *= 1.5
                z += distance_penalty * time_scale

        # Add timeout differential factor
        if team_timeouts is not None and opponent_timeouts is not None:
            timeout_diff = team_timeouts - opponent_timeouts
            # Timeouts are more valuable late in the game
            if time_remaining < 300:  # Last 5 minutes
                timeout_value = self.timeout_weight * 2.0
            else:
                timeout_value = self.timeout_weight
            z += timeout_diff * timeout_value * time_scale

        # Add team strength rating factor (not scaled by time - represents base ability)
        if team_win_pct is not None and opponent_win_pct is not None:
            strength_diff = team_win_pct - opponent_win_pct
            z += strength_diff * self.team_strength_weight

        # Convert to probability using logistic function
        probability = self._logistic(z)

        return max(0.0, min(1.0, probability))

    def _calculate_time_scale(self, time_remaining: int) -> float:
        """
        Calculate time scaling factor for win probability.

        As time decreases, the current game state becomes more predictive.
        Returns a value between ~0.33 (start of game) and 1.0 (end of game).
        """
        # Fraction of game remaining (0.0 = game over, 1.0 = just started)
        fraction_remaining = min(time_remaining / self.full_game_seconds, 1.0)

        # Use square root to make the scaling non-linear
        # Early game: small changes in time don't affect certainty much
        # Late game: small changes in time matter a lot
        # Scale ranges from 0.33 (full game left) to 1.0 (no time left)
        time_scale = 1.0 / (1.0 + 2.0 * np.sqrt(fraction_remaining))

        return time_scale

    def calculate_win_probability_explained(
        self,
        score_diff: int,
        time_remaining: int,
        has_possession: bool = False,
        field_position: Optional[int] = None,
        down: Optional[int] = None,
        distance: Optional[int] = None,
        team_timeouts: Optional[int] = None,
        opponent_timeouts: Optional[int] = None,
        team_win_pct: Optional[float] = None,
        opponent_win_pct: Optional[float] = None
    ) -> dict:
        """
        Calculate win probability with detailed explanation of all factors.

        Returns a dictionary containing:
        - probability: The final win probability (0.0-1.0)
        - factors: Dictionary of each factor's contribution to the z-score
        - z_total: The total z-score before logistic transformation
        - explanation: Human-readable explanation of the prediction

        Args:
            (same as calculate_win_probability)

        Returns:
            Dictionary with probability and detailed breakdown
        """
        factors = {}
        z = 0.0

        # Calculate time scaling factor
        time_scale = self._calculate_time_scale(time_remaining)

        # Time scale factor (shown for transparency)
        factors['time_scale'] = {
            'value': time_remaining,
            'weight': time_scale,
            'contribution': 0.0,  # Not a direct contributor, but a multiplier
            'description': f"{self._format_time(time_remaining)} (certainty: {time_scale:.0%})"
        }

        # Score differential scaled by time
        score_contribution = score_diff * self.score_weight * time_scale
        factors['score_diff'] = {
            'value': score_diff,
            'weight': self.score_weight * time_scale,
            'contribution': score_contribution,
            'description': f"{'+' if score_diff >= 0 else ''}{score_diff} points"
        }
        z += score_contribution

        # Add possession bonus (scaled by time)
        possession_contribution = (self.possession_bonus * time_scale) if has_possession else 0.0
        factors['possession'] = {
            'value': has_possession,
            'weight': self.possession_bonus * time_scale,
            'contribution': possession_contribution,
            'description': 'Has ball' if has_possession else 'Opponent has ball'
        }
        z += possession_contribution

        # Add field position factor (scaled by time)
        if field_position is not None:
            fp_contribution = (field_position - 50) * self.field_position_weight * time_scale
            factors['field_position'] = {
                'value': field_position,
                'weight': self.field_position_weight * time_scale,
                'contribution': fp_contribution,
                'description': self._describe_field_position(field_position)
            }
            z += fp_contribution
        else:
            factors['field_position'] = {
                'value': None,
                'weight': self.field_position_weight * time_scale,
                'contribution': 0.0,
                'description': 'Unknown'
            }

        # Add down and distance factors (scaled by time)
        if has_possession and down is not None:
            down_contribution = self.down_distance_weights.get(down, 0) * time_scale
            distance_penalty = 0.0

            if distance is not None:
                distance_penalty = distance * self.distance_weight
                if down >= 3 and distance >= 7:
                    distance_penalty *= 1.5
                distance_penalty *= time_scale

            factors['down_distance'] = {
                'value': (down, distance),
                'down_weight': self.down_distance_weights.get(down, 0) * time_scale,
                'distance_weight': self.distance_weight * time_scale,
                'contribution': down_contribution + distance_penalty,
                'description': f"{self._ordinal(down)} & {distance if distance else '?'}"
            }
            z += down_contribution + distance_penalty
        else:
            factors['down_distance'] = {
                'value': None,
                'contribution': 0.0,
                'description': 'N/A (no possession)'
            }

        # Add timeout differential factor (scaled by time)
        if team_timeouts is not None and opponent_timeouts is not None:
            timeout_diff = team_timeouts - opponent_timeouts
            if time_remaining < 300:  # Last 5 minutes
                timeout_value = self.timeout_weight * 2.0
                timeout_desc = f"{team_timeouts} vs {opponent_timeouts} (late game bonus)"
            else:
                timeout_value = self.timeout_weight
                timeout_desc = f"{team_timeouts} vs {opponent_timeouts}"

            timeout_contribution = timeout_diff * timeout_value * time_scale
            factors['timeouts'] = {
                'value': (team_timeouts, opponent_timeouts),
                'weight': timeout_value * time_scale,
                'contribution': timeout_contribution,
                'description': timeout_desc
            }
            z += timeout_contribution
        else:
            factors['timeouts'] = {
                'value': None,
                'contribution': 0.0,
                'description': 'Unknown'
            }

        # Add team strength rating factor (NOT scaled by time - represents base ability)
        if team_win_pct is not None and opponent_win_pct is not None:
            strength_diff = team_win_pct - opponent_win_pct
            strength_contribution = strength_diff * self.team_strength_weight
            factors['team_strength'] = {
                'value': (team_win_pct, opponent_win_pct),
                'weight': self.team_strength_weight,
                'contribution': strength_contribution,
                'description': f"{team_win_pct:.1%} vs {opponent_win_pct:.1%}"
            }
            z += strength_contribution
        else:
            factors['team_strength'] = {
                'value': None,
                'contribution': 0.0,
                'description': 'Unknown'
            }

        # Convert to probability using logistic function
        probability = self._logistic(z)
        probability = max(0.0, min(1.0, probability))

        # Generate human-readable explanation
        explanation = self._generate_explanation(factors, z, probability)

        return {
            'probability': probability,
            'z_total': z,
            'factors': factors,
            'explanation': explanation
        }

    def _format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS remaining."""
        if seconds >= 3600:
            mins = seconds // 60
            return f"{mins}:{seconds % 60:02d} remaining"
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d} remaining"

    def _describe_field_position(self, field_pos: int) -> str:
        """Describe field position in human terms."""
        if field_pos >= 80:
            return f"Red zone (opp {100 - field_pos})"
        elif field_pos >= 50:
            return f"Opponent territory ({100 - field_pos} yard line)"
        elif field_pos <= 20:
            return f"Own territory (own {field_pos})"
        else:
            return f"Own territory ({field_pos} yard line)"

    def _ordinal(self, n: int) -> str:
        """Convert number to ordinal (1st, 2nd, etc.)."""
        if n == 1:
            return "1st"
        elif n == 2:
            return "2nd"
        elif n == 3:
            return "3rd"
        elif n == 4:
            return "4th"
        return f"{n}th"

    def _generate_explanation(self, factors: dict, z: float, probability: float) -> str:
        """Generate a human-readable explanation of the prediction."""
        lines = []

        # Sort factors by absolute contribution
        sorted_factors = sorted(
            [(k, v) for k, v in factors.items() if v.get('contribution', 0) != 0],
            key=lambda x: abs(x[1]['contribution']),
            reverse=True
        )

        if not sorted_factors:
            return "Insufficient data for detailed breakdown."

        # Identify the most influential factors
        top_factors = sorted_factors[:3]

        for name, factor in top_factors:
            contrib = factor['contribution']
            desc = factor['description']
            direction = "+" if contrib > 0 else ""
            lines.append(f"  {name}: {desc} ({direction}{contrib:.2f})")

        return "\n".join(lines)

    def _logistic(self, z: float) -> float:
        """Apply logistic function to convert value to probability.

        Uses a numerically stable implementation that prevents exact 0 or 1 values.
        """
        # Clip z to prevent numerical overflow/underflow
        z = np.clip(z, -20, 20)
        return 1 / (1 + np.exp(-z))

    def calculate_comeback_probability(
        self,
        score_deficit: int,
        time_remaining: int,
        has_possession: bool = False,
        field_position: Optional[int] = None,
        down: Optional[int] = None,
        distance: Optional[int] = None,
        team_timeouts: Optional[int] = None,
        opponent_timeouts: Optional[int] = None,
        team_win_pct: Optional[float] = None,
        opponent_win_pct: Optional[float] = None
    ) -> float:
        """
        Calculate comeback probability for a team that is currently losing.

        This method calculates the probability that a trailing team will
        come back to win the game given the current game state.

        Args:
            score_deficit: Points behind (positive number, e.g., 7 means down by 7)
            time_remaining: Seconds remaining in the game
            has_possession: Whether the trailing team has possession
            field_position: Yard line from trailing team's perspective (0-100)
            down: Current down (1-4), only relevant if has_possession=True
            distance: Yards to go for first down
            team_timeouts: Number of timeouts remaining for trailing team (0-3)
            opponent_timeouts: Number of timeouts remaining for leading team (0-3)
            team_win_pct: Trailing team's win percentage (0.0-1.0)
            opponent_win_pct: Leading team's win percentage (0.0-1.0)

        Returns:
            Comeback probability as a float between 0 and 1

        Examples:
            >>> calculator = NFLWinProbability()
            >>> # Down by 7 with 5 minutes left and the ball
            >>> prob = calculator.calculate_comeback_probability(
            ...     score_deficit=7,
            ...     time_remaining=300,
            ...     has_possession=True,
            ...     field_position=25,
            ...     down=1,
            ...     distance=10,
            ...     team_timeouts=3,
            ...     opponent_timeouts=2
            ... )
        """
        if score_deficit < 0:
            raise ValueError("score_deficit must be non-negative (use positive value for points behind)")

        # For the trailing team, we flip the score differential
        # A deficit of 7 means score_diff = -7 from their perspective
        trailing_score_diff = -score_deficit

        # Calculate win probability from trailing team's perspective
        comeback_prob = self.calculate_win_probability(
            score_diff=trailing_score_diff,
            time_remaining=time_remaining,
            has_possession=has_possession,
            field_position=field_position,
            down=down,
            distance=distance,
            team_timeouts=team_timeouts,
            opponent_timeouts=opponent_timeouts,
            team_win_pct=team_win_pct,
            opponent_win_pct=opponent_win_pct
        )

        return comeback_prob

    # TODO: Add method to calculate probability of overtime
    # TODO: Add method to get win probability chart over time


def main():
    """Example usage of the win probability calculator."""
    calculator = NFLWinProbability()

    # Example scenarios
    scenarios = [
        {"desc": "Tie game, start of 4th quarter", "score_diff": 0, "time_remaining": 900, "has_possession": True, "field_position": 50},
        {"desc": "Up by 7, 5 minutes left, has ball", "score_diff": 7, "time_remaining": 300, "has_possession": True, "field_position": 45},
        {"desc": "Down by 3, 2 minutes left, no ball", "score_diff": -3, "time_remaining": 120, "has_possession": False, "field_position": None},
        {"desc": "Up by 10, 1 minute left", "score_diff": 10, "time_remaining": 60, "has_possession": False, "field_position": None},
    ]

    print("NFL Win Probability Examples")
    print("=" * 60)

    for scenario in scenarios:
        prob = calculator.calculate_win_probability(
            score_diff=scenario["score_diff"],
            time_remaining=scenario["time_remaining"],
            has_possession=scenario["has_possession"],
            field_position=scenario["field_position"]
        )
        print(f"\n{scenario['desc']}")
        print(f"Win Probability: {prob:.1%}")

    # Demonstrate comeback probability feature
    print("\n\n" + "=" * 60)
    print("Comeback Probability Examples")
    print("=" * 60)

    comeback_scenarios = [
        {"desc": "Down by 3, 5 minutes left, has ball at own 25", "deficit": 3, "time": 300, "possession": True, "field_pos": 25},
        {"desc": "Down by 7, 2 minutes left, has ball at midfield", "deficit": 7, "time": 120, "possession": True, "field_pos": 50},
        {"desc": "Down by 10, 5 minutes left, opponent has ball", "deficit": 10, "time": 300, "possession": False, "field_pos": None},
        {"desc": "Down by 14, 8 minutes left in 4th, has ball at own 30", "deficit": 14, "time": 480, "possession": True, "field_pos": 30},
    ]

    for scenario in comeback_scenarios:
        comeback_prob = calculator.calculate_comeback_probability(
            score_deficit=scenario["deficit"],
            time_remaining=scenario["time"],
            has_possession=scenario["possession"],
            field_position=scenario["field_pos"]
        )
        print(f"\n{scenario['desc']}")
        print(f"Comeback Probability: {comeback_prob:.1%}")

    # Demonstrate enhanced features: down & distance, timeouts, team strength
    print("\n\n" + "=" * 60)
    print("Enhanced Features Examples")
    print("=" * 60)

    print("\n1. DOWN & DISTANCE IMPACT")
    print("-" * 60)
    # Same situation but different downs
    base_scenario = {
        "score_diff": 3,
        "time_remaining": 120,
        "has_possession": True,
        "field_position": 65
    }

    for down, distance, desc in [(1, 10, "1st & 10"), (2, 7, "2nd & 7"), (3, 3, "3rd & 3"), (3, 12, "3rd & 12"), (4, 1, "4th & 1")]:
        prob = calculator.calculate_win_probability(
            **base_scenario,
            down=down,
            distance=distance
        )
        print(f"{desc}: {prob:.1%}")

    print("\n2. TIMEOUT ADVANTAGE")
    print("-" * 60)
    # Show impact of timeout differential
    timeout_scenario = {
        "score_diff": 3,
        "time_remaining": 180,
        "has_possession": False,
        "field_position": None
    }

    for team_to, opp_to in [(3, 3), (3, 1), (3, 0), (0, 3)]:
        prob = calculator.calculate_win_probability(
            **timeout_scenario,
            team_timeouts=team_to,
            opponent_timeouts=opp_to
        )
        print(f"Timeouts {team_to} vs {opp_to}: {prob:.1%}")

    print("\n3. TEAM STRENGTH RATINGS")
    print("-" * 60)
    # Show impact of team quality
    strength_scenario = {
        "score_diff": 0,
        "time_remaining": 300,
        "has_possession": True,
        "field_position": 50
    }

    for team_pct, opp_pct, desc in [(0.750, 0.500, "Strong vs Average"), (0.500, 0.500, "Equal Teams"), (0.300, 0.700, "Weak vs Strong")]:
        prob = calculator.calculate_win_probability(
            **strength_scenario,
            team_win_pct=team_pct,
            opponent_win_pct=opp_pct
        )
        print(f"{desc} ({team_pct:.1%} vs {opp_pct:.1%}): {prob:.1%}")

    print("\n4. COMBINED FACTORS")
    print("-" * 60)
    # Realistic late-game scenarios with all factors
    combined_scenarios = [
        {
            "desc": "Steelers (10-3) up 3, 3rd & 2, own 40, 2 min, 2 TOs vs 1",
            "params": {
                "score_diff": 3,
                "time_remaining": 120,
                "has_possession": True,
                "field_position": 40,
                "down": 3,
                "distance": 2,
                "team_timeouts": 2,
                "opponent_timeouts": 1,
                "team_win_pct": 0.769,  # 10-3
                "opponent_win_pct": 0.538   # 7-6
            }
        },
        {
            "desc": "Browns (5-8) down 7, 1st & 10, opp 35, 5 min, 3 TOs vs 2",
            "params": {
                "score_diff": -7,
                "time_remaining": 300,
                "has_possession": True,
                "field_position": 65,
                "down": 1,
                "distance": 10,
                "team_timeouts": 3,
                "opponent_timeouts": 2,
                "team_win_pct": 0.385,  # 5-8
                "opponent_win_pct": 0.615   # 8-5
            }
        }
    ]

    for scenario in combined_scenarios:
        prob = calculator.calculate_win_probability(**scenario["params"])
        print(f"\n{scenario['desc']}")
        print(f"Win Probability: {prob:.1%}")


if __name__ == "__main__":
    main()
