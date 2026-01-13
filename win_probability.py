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

    def calculate_win_probability(
        self,
        score_diff: int,
        time_remaining: int,
        has_possession: bool = False,
        field_position: Optional[int] = None
    ) -> float:
        """
        Calculate win probability for the team with the lead.

        Args:
            score_diff: Point differential (positive if team is leading)
            time_remaining: Seconds remaining in the game
            has_possession: Whether the team has possession
            field_position: Yard line (0-100, own 0 to opponent 0)

        Returns:
            Win probability as a float between 0 and 1

        # TODO: Add support for down and distance
        # TODO: Account for timeouts remaining
        # TODO: Add overtime probability calculation
        # TODO: Incorporate team strength ratings
        """
        # Calculate base probability from score and time
        z = (score_diff * self.score_weight) + (time_remaining * self.time_weight)

        # Add possession bonus
        if has_possession:
            z += self.possession_bonus

        # Add field position factor
        # TODO: Field position should have different weights in different game situations
        if field_position is not None:
            # Field position bonus (closer to opponent endzone = better)
            z += (field_position - 50) * self.field_position_weight

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
        field_position: Optional[int] = None
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

        Returns:
            Comeback probability as a float between 0 and 1

        Examples:
            >>> calculator = NFLWinProbability()
            >>> # Down by 7 with 5 minutes left and the ball
            >>> prob = calculator.calculate_comeback_probability(
            ...     score_deficit=7,
            ...     time_remaining=300,
            ...     has_possession=True,
            ...     field_position=25
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
            field_position=field_position
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


if __name__ == "__main__":
    main()
