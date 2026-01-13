#!/usr/bin/env python3
"""
NFL Live Win Probability Tracker

Monitors live NFL games and displays real-time win probability updates.
Includes special support for tracking specific teams like the Steelers.
"""

import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from nfl_api import NFLGameAPI
from win_probability import NFLWinProbability


class LiveGameTracker:
    """Track live NFL games and calculate win probabilities in real-time."""

    def __init__(self, update_interval: int = 30):
        """
        Initialize the live game tracker.

        Args:
            update_interval: Seconds between API updates (default: 30)
        """
        self.api = NFLGameAPI()
        self.calculator = NFLWinProbability()
        self.update_interval = update_interval
        self.last_game_state = {}

    def track_team(self, team_name: str, show_updates: bool = True):
        """
        Track a specific team's game and display live win probabilities.

        Args:
            team_name: Team name or abbreviation (e.g., 'Steelers', 'PIT')
            show_updates: Whether to show continuous updates
        """
        team_abbr = self.api._normalize_team_name(team_name)
        print(f"\n{'=' * 70}")
        print(f"NFL Live Win Probability Tracker - {team_name.upper()}")
        print(f"{'=' * 70}")
        print(f"Monitoring for live games... (Updates every {self.update_interval}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                game = self.api.get_team_game(team_abbr)

                if not game:
                    print(f"[{self._timestamp()}] No live game found for {team_name}. Checking again...")
                    time.sleep(self.update_interval)
                    continue

                if game['state'] != 'in':
                    if game['state'] == 'post':
                        print(f"[{self._timestamp()}] Game has ended. Final score:")
                        self._display_game_summary(game, team_abbr)
                        break
                    else:
                        time.sleep(self.update_interval)
                        continue

                # Display live update
                self._display_live_update(game, team_abbr, show_updates)

                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            print("\n\nTracking stopped by user.")

    def track_all_games(self):
        """Track all live NFL games and display win probabilities."""
        print(f"\n{'=' * 70}")
        print("NFL Live Win Probability Tracker - ALL GAMES")
        print(f"{'=' * 70}")
        print(f"Monitoring all live games... (Updates every {self.update_interval}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                games = self.api.get_live_games()

                if not games:
                    print(f"[{self._timestamp()}] No live games at the moment. Checking again...")
                    time.sleep(self.update_interval)
                    continue

                print(f"\n[{self._timestamp()}] Live Games Update:")
                print("=" * 70)

                for game in games:
                    if game['state'] == 'in':
                        # Show win probability for home team
                        self._display_live_update(
                            game,
                            game['home_team']['abbr'],
                            show_full=False
                        )
                        print("-" * 70)

                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            print("\n\nTracking stopped by user.")

    def _display_live_update(
        self,
        game: Dict[str, Any],
        team_abbr: str,
        show_updates: bool = True
    ):
        """Display a live game update with win probability."""
        # Get game state for probability calculation
        state = self.api.get_game_state_for_probability(game, team_abbr)

        if not state:
            return

        # Calculate win probability with enhanced factors
        win_prob = self.calculator.calculate_win_probability(
            score_diff=state['score_diff'],
            time_remaining=state['time_remaining'],
            has_possession=state['has_possession'],
            field_position=state['field_position'],
            down=state.get('down'),
            distance=state.get('distance'),
            team_timeouts=state.get('team_timeouts'),
            opponent_timeouts=state.get('opponent_timeouts'),
            team_win_pct=state.get('team_win_pct'),
            opponent_win_pct=state.get('opponent_win_pct')
        )

        # Determine if we should show this update (state changed)
        game_key = f"{game['id']}_{state['period']}_{state['clock']}"
        if game_key == self.last_game_state.get(game['id']) and show_updates:
            return  # No change, skip update

        self.last_game_state[game['id']] = game_key

        # Display update
        if show_updates:
            print(f"\n[{self._timestamp()}] Game Update:")

        self._display_game_summary(game, team_abbr, win_prob, state)

        # Show comeback probability if trailing
        if state['score_diff'] < 0:
            comeback_prob = self.calculator.calculate_comeback_probability(
                score_deficit=abs(state['score_diff']),
                time_remaining=state['time_remaining'],
                has_possession=state['has_possession'],
                field_position=state['field_position'],
                down=state.get('down'),
                distance=state.get('distance'),
                team_timeouts=state.get('team_timeouts'),
                opponent_timeouts=state.get('opponent_timeouts'),
                team_win_pct=state.get('team_win_pct'),
                opponent_win_pct=state.get('opponent_win_pct')
            )
            print(f"  Comeback Probability: {comeback_prob:>6.1%}")

    def _display_game_summary(
        self,
        game: Dict[str, Any],
        focus_team_abbr: str,
        win_prob: Optional[float] = None,
        state: Optional[Dict[str, Any]] = None
    ):
        """Display a formatted game summary."""
        is_home = game['home_team']['abbr'] == focus_team_abbr
        team = game['home_team'] if is_home else game['away_team']
        opponent = game['away_team'] if is_home else game['home_team']

        # Display team records if available
        away_record = game['away_team'].get('record', '')
        home_record = game['home_team'].get('record', '')

        print(f"\n  {game['away_team']['abbr']:>4} ({away_record}) {game['away_team']['score']:>3}  @  "
              f"{game['home_team']['abbr']:>4} ({home_record}) {game['home_team']['score']:>3}")
        print(f"  Period: {game['period']}, Clock: {game['clock']}")

        # Display timeouts if available
        away_timeouts = game['away_team'].get('timeouts')
        home_timeouts = game['home_team'].get('timeouts')
        if away_timeouts is not None and home_timeouts is not None:
            print(f"  Timeouts: {game['away_team']['abbr']} {away_timeouts}, {game['home_team']['abbr']} {home_timeouts}")

        if game.get('possession_text'):
            print(f"  Possession: {game['possession_text']}")
        if game.get('down_distance'):
            print(f"  {game['down_distance']}")

        if win_prob is not None and state:
            print(f"\n  {team['abbr']} Win Probability: {win_prob:>6.1%}")

            # Show score context
            if state['score_diff'] > 0:
                print(f"  Leading by {state['score_diff']} points")
            elif state['score_diff'] < 0:
                print(f"  Trailing by {abs(state['score_diff'])} points")
            else:
                print(f"  Game tied")

    def get_game_snapshot(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a single snapshot of a team's current game state with win probability.

        Args:
            team_name: Team name or abbreviation

        Returns:
            Dictionary with game info and win probability, or None if no game
        """
        team_abbr = self.api._normalize_team_name(team_name)
        game = self.api.get_team_game(team_abbr)

        if not game or game['state'] != 'in':
            return None

        state = self.api.get_game_state_for_probability(game, team_abbr)
        if not state:
            return None

        win_prob = self.calculator.calculate_win_probability(
            score_diff=state['score_diff'],
            time_remaining=state['time_remaining'],
            has_possession=state['has_possession'],
            field_position=state['field_position'],
            down=state.get('down'),
            distance=state.get('distance'),
            team_timeouts=state.get('team_timeouts'),
            opponent_timeouts=state.get('opponent_timeouts'),
            team_win_pct=state.get('team_win_pct'),
            opponent_win_pct=state.get('opponent_win_pct')
        )

        return {
            'game': game,
            'state': state,
            'win_probability': win_prob
        }

    def _timestamp(self) -> str:
        """Get formatted timestamp."""
        return datetime.now().strftime("%H:%M:%S")


def main():
    """Main entry point for the live tracker."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Track live NFL games with real-time win probabilities"
    )
    parser.add_argument(
        '--team',
        '-t',
        type=str,
        help='Team name or abbreviation to track (e.g., Steelers, PIT)'
    )
    parser.add_argument(
        '--interval',
        '-i',
        type=int,
        default=30,
        help='Update interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--all',
        '-a',
        action='store_true',
        help='Track all live games'
    )

    args = parser.parse_args()

    tracker = LiveGameTracker(update_interval=args.interval)

    if args.all:
        tracker.track_all_games()
    elif args.team:
        tracker.track_team(args.team)
    else:
        # Default: track Steelers
        print("No team specified, defaulting to Steelers.")
        print("Use --team <name> to track a different team, or --all for all games.\n")
        tracker.track_team('Steelers')


if __name__ == "__main__":
    main()
