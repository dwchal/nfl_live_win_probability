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
        self.score_weight = 0.15
        self.time_weight = 0.008
        self.possession_bonus = 0.3
        self.field_position_weight = 0.01

        # Enhanced factors
        self.timeout_weight = 0.15  # Value of each timeout
        self.team_strength_weight = 0.8  # Impact of team quality difference

        # Down and distance weights
        self.down_distance_weights = {
            1: 0.2,   # 1st down - good situation
            2: 0.1,   # 2nd down - neutral
            3: -0.1,  # 3rd down - pressure situation
            4: -0.5,  # 4th down - critical situation
        }
        self.distance_weight = -0.02  # Penalty per yard to go

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
        # Calculate base probability from score and time
        z = (score_diff * self.score_weight) + (time_remaining * self.time_weight)

        # Add possession bonus
        if has_possession:
            z += self.possession_bonus

        # Add field position factor
        if field_position is not None:
            # Field position bonus (closer to opponent endzone = better)
            z += (field_position - 50) * self.field_position_weight

        # Add down and distance factors
        if has_possession and down is not None:
            # Down situation impact
            z += self.down_distance_weights.get(down, 0)

            # Distance to go impact (longer distance = worse)
            if distance is not None:
                # Scale distance penalty: 3rd & 1 is much better than 3rd & 10
                distance_penalty = distance * self.distance_weight
                # Extra penalty for 3rd/4th down with long distance
                if down >= 3 and distance >= 7:
                    distance_penalty *= 1.5
                z += distance_penalty

        # Add timeout differential factor
        if team_timeouts is not None and opponent_timeouts is not None:
            timeout_diff = team_timeouts - opponent_timeouts
            # Timeouts are more valuable late in the game
            if time_remaining < 300:  # Last 5 minutes
                timeout_value = self.timeout_weight * 1.5
            else:
                timeout_value = self.timeout_weight
            z += timeout_diff * timeout_value

        # Add team strength rating factor
        if team_win_pct is not None and opponent_win_pct is not None:
            strength_diff = team_win_pct - opponent_win_pct
            z += strength_diff * self.team_strength_weight

        # Convert to probability using logistic function
        probability = self._logistic(z)

        return max(0.0, min(1.0, probability))

    def _logistic(self, z: float) -> float:
        """Apply logistic function to convert value to probability."""
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
