"""
NFL Live Game Data API Integration

This module provides functionality to fetch live game data from ESPN's API
for real-time win probability calculations.
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime


class NFLGameAPI:
    """Fetch live NFL game data from ESPN's API."""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

    # NFL team name mappings
    TEAM_MAPPINGS = {
        'steelers': 'PIT',
        'pittsburgh': 'PIT',
        'ravens': 'BAL',
        'browns': 'CLE',
        'bengals': 'CIN',
        'chiefs': 'KC',
        'bills': 'BUF',
        'cowboys': 'DAL',
        'eagles': 'PHI',
        'packers': 'GB',
        '49ers': 'SF',
        'rams': 'LAR',
        'patriots': 'NE',
        # Add more as needed
    }

    def __init__(self):
        """Initialize the NFL Game API client."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_live_games(self) -> List[Dict[str, Any]]:
        """
        Fetch all live NFL games.

        Returns:
            List of game dictionaries with current game state
        """
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            games = []
            for event in data.get('events', []):
                game_info = self._parse_game(event)
                if game_info:
                    games.append(game_info)

            return games
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []

    def get_team_game(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a live game for a specific team.

        Args:
            team_name: Team name or abbreviation (e.g., 'Steelers', 'PIT')

        Returns:
            Game dictionary if found, None otherwise
        """
        team_abbr = self._normalize_team_name(team_name)
        games = self.get_live_games()

        for game in games:
            if game['home_team']['abbr'] == team_abbr or game['away_team']['abbr'] == team_abbr:
                return game

        return None

    def _normalize_team_name(self, team_name: str) -> str:
        """Convert team name to standard abbreviation."""
        team_lower = team_name.lower().strip()

        # Check if it's already an abbreviation
        if len(team_name) <= 3:
            return team_name.upper()

        # Look up in mappings
        return self.TEAM_MAPPINGS.get(team_lower, team_name.upper())

    def _parse_win_percentage(self, record: str) -> float:
        """
        Parse win percentage from record string.

        Args:
            record: Record string like "10-3" or "5-8-1"

        Returns:
            Win percentage as float (0.0-1.0)
        """
        try:
            parts = record.split('-')
            wins = int(parts[0])
            losses = int(parts[1])
            ties = int(parts[2]) if len(parts) > 2 else 0

            total_games = wins + losses + ties
            if total_games == 0:
                return 0.5  # Default to 50% if no games played

            # Ties count as 0.5 wins
            win_pct = (wins + 0.5 * ties) / total_games
            return win_pct

        except (ValueError, IndexError):
            return 0.5  # Default to 50% if parsing fails

    def _parse_game(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse game data from ESPN API response.

        Args:
            event: Raw event data from ESPN API

        Returns:
            Parsed game information dictionary
        """
        try:
            competition = event['competitions'][0]
            status = competition['status']

            # Only include live or recently completed games
            state = status['type']['state']
            if state not in ['in', 'post']:
                return None

            competitors = competition['competitors']
            home_team = next(c for c in competitors if c['homeAway'] == 'home')
            away_team = next(c for c in competitors if c['homeAway'] == 'away')

            # Parse game clock
            clock = status.get('displayClock', '0:00')
            period = status.get('period', 1)

            # Parse possession
            possession_id = competition.get('situation', {}).get('possession')
            home_has_possession = possession_id == home_team['id'] if possession_id else None
            away_has_possession = possession_id == away_team['id'] if possession_id else None

            # Parse field position
            situation = competition.get('situation', {})
            possession_text = situation.get('possessionText', '')
            down_distance = situation.get('shortDownDistanceText', '')

            # Extract team records (wins-losses)
            home_record = home_team.get('records', [{}])[0].get('summary', '0-0')
            away_record = away_team.get('records', [{}])[0].get('summary', '0-0')

            # Parse timeouts remaining
            home_timeouts = situation.get('homeTimeouts', 3)
            away_timeouts = situation.get('awayTimeouts', 3)

            # Parse down and distance from situation
            down = situation.get('down')
            distance = situation.get('distance')

            game_info = {
                'id': event['id'],
                'state': state,
                'status_text': status['type']['description'],
                'home_team': {
                    'name': home_team['team']['displayName'],
                    'abbr': home_team['team']['abbreviation'],
                    'score': int(home_team['score']),
                    'has_possession': home_has_possession,
                    'record': home_record,
                    'timeouts': home_timeouts
                },
                'away_team': {
                    'name': away_team['team']['displayName'],
                    'abbr': away_team['team']['abbreviation'],
                    'score': int(away_team['score']),
                    'has_possession': away_has_possession,
                    'record': away_record,
                    'timeouts': away_timeouts
                },
                'period': period,
                'clock': clock,
                'possession_text': possession_text,
                'down_distance': down_distance,
                'down': down,
                'distance': distance,
                'situation': situation
            }

            return game_info

        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing game: {e}")
            return None

    def get_game_state_for_probability(
        self,
        game: Dict[str, Any],
        team_abbr: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract game state parameters for win probability calculation.

        Args:
            game: Game dictionary from get_live_games()
            team_abbr: Team abbreviation to calculate probability for

        Returns:
            Dictionary with parameters for calculate_win_probability()
        """
        if not game or game['state'] != 'in':
            return None

        is_home = game['home_team']['abbr'] == team_abbr
        team = game['home_team'] if is_home else game['away_team']
        opponent = game['away_team'] if is_home else game['home_team']

        # Calculate score differential
        score_diff = team['score'] - opponent['score']

        # Parse time remaining
        time_remaining = self._parse_time_remaining(game['clock'], game['period'])

        # Determine possession
        has_possession = team.get('has_possession', False)

        # Try to parse field position from situation
        field_position = self._parse_field_position(game['situation'], team_abbr)

        # Get down and distance (only meaningful if team has possession)
        down = game.get('down') if has_possession else None
        distance = game.get('distance') if has_possession else None

        # Get timeouts
        team_timeouts = team.get('timeouts', 3)
        opponent_timeouts = opponent.get('timeouts', 3)

        # Parse team records to win percentages
        team_win_pct = self._parse_win_percentage(team.get('record', '0-0'))
        opponent_win_pct = self._parse_win_percentage(opponent.get('record', '0-0'))

        return {
            'score_diff': score_diff,
            'time_remaining': time_remaining,
            'has_possession': has_possession,
            'field_position': field_position,
            'down': down,
            'distance': distance,
            'team_timeouts': team_timeouts,
            'opponent_timeouts': opponent_timeouts,
            'team_win_pct': team_win_pct,
            'opponent_win_pct': opponent_win_pct,
            'team_name': team['name'],
            'team_record': team.get('record', '0-0'),
            'opponent_name': opponent['name'],
            'opponent_record': opponent.get('record', '0-0'),
            'period': game['period'],
            'clock': game['clock']
        }

    def _parse_time_remaining(self, clock: str, period: int) -> int:
        """
        Calculate total time remaining in the game.

        Args:
            clock: Time string (e.g., "5:23")
            period: Current period (1-4 for regulation, 5+ for OT)

        Returns:
            Seconds remaining in the game
        """
        try:
            # Parse minutes and seconds from clock
            parts = clock.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                time_in_period = minutes * 60 + seconds
            else:
                time_in_period = 0

            # Calculate total time remaining
            if period < 4:
                # Time in current period + all remaining periods
                remaining_periods = 4 - period
                total_remaining = time_in_period + (remaining_periods * 15 * 60)
            elif period == 4:
                # Just time in 4th quarter
                total_remaining = time_in_period
            else:
                # Overtime - treat as final 5 minutes
                total_remaining = min(time_in_period, 300)

            return total_remaining

        except (ValueError, IndexError):
            return 0

    def _parse_field_position(
        self,
        situation: Dict[str, Any],
        team_abbr: str
    ) -> Optional[int]:
        """
        Parse field position from situation data.

        Args:
            situation: Situation dictionary from game data
            team_abbr: Team abbreviation

        Returns:
            Field position (0-100) or None if not available
        """
        try:
            # ESPN provides yard line in situation
            possession_abbr = situation.get('possession')
            yard_line = situation.get('yardLine')

            if not yard_line:
                return None

            # Parse yard line (e.g., 75 means team's own 25)
            # ESPN uses 0-100 where 0 is team's own goal line
            return yard_line

        except (KeyError, ValueError):
            return None


def main():
    """Example usage of the NFL Game API."""
    api = NFLGameAPI()

    print("Fetching live NFL games...")
    print("=" * 70)

    games = api.get_live_games()

    if not games:
        print("No live games found at the moment.")
        return

    for game in games:
        print(f"\n{game['away_team']['name']} @ {game['home_team']['name']}")
        print(f"Score: {game['away_team']['score']} - {game['home_team']['score']}")
        print(f"Status: {game['status_text']}")
        print(f"Period: {game['period']}, Clock: {game['clock']}")

        if game['possession_text']:
            print(f"Possession: {game['possession_text']}")
        if game['down_distance']:
            print(f"Down & Distance: {game['down_distance']}")

    # Check for Steelers game specifically
    print("\n" + "=" * 70)
    print("Checking for Steelers game...")
    steelers_game = api.get_team_game('Steelers')

    if steelers_game:
        print(f"\nSteelers game found!")
        print(f"{steelers_game['away_team']['name']} @ {steelers_game['home_team']['name']}")
        print(f"Score: {steelers_game['away_team']['score']} - {steelers_game['home_team']['score']}")
    else:
        print("\nNo live Steelers game at the moment.")


if __name__ == "__main__":
    main()
