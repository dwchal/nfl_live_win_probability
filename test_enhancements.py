#!/usr/bin/env python3
"""
Test script for enhanced win probability features.
"""

from nfl_api import NFLGameAPI
from win_probability import NFLWinProbability
from live_tracker import LiveGameTracker


def test_enhanced_features():
    """Test all enhanced features with live game data."""
    print("=" * 70)
    print("Testing Enhanced Win Probability Features")
    print("=" * 70)

    # Initialize API
    api = NFLGameAPI()
    calculator = NFLWinProbability()

    # Get a live game
    print("\n1. Fetching live games...")
    games = api.get_live_games()

    if not games:
        print("No live games available for testing.")
        print("Testing with synthetic data instead...\n")
        test_synthetic_data()
        return

    # Find first live game
    live_game = None
    for game in games:
        if game['state'] == 'in':
            live_game = game
            break

    if not live_game:
        print("No in-progress games, testing with completed game data...\n")
        test_synthetic_data()
        return

    print(f"Found live game: {live_game['away_team']['name']} @ {live_game['home_team']['name']}")

    # Test home team state
    home_abbr = live_game['home_team']['abbr']
    print(f"\n2. Testing enhanced game state extraction for {home_abbr}...")

    state = api.get_game_state_for_probability(live_game, home_abbr)

    if state:
        print(f"\n   ✓ Score differential: {state['score_diff']}")
        print(f"   ✓ Time remaining: {state['time_remaining']} seconds")
        print(f"   ✓ Has possession: {state['has_possession']}")
        print(f"   ✓ Field position: {state.get('field_position', 'N/A')}")
        print(f"   ✓ Down: {state.get('down', 'N/A')}")
        print(f"   ✓ Distance: {state.get('distance', 'N/A')}")
        print(f"   ✓ Team timeouts: {state.get('team_timeouts', 'N/A')}")
        print(f"   ✓ Opponent timeouts: {state.get('opponent_timeouts', 'N/A')}")
        print(f"   ✓ Team record: {state.get('team_record', 'N/A')} ({state.get('team_win_pct', 0):.1%})")
        print(f"   ✓ Opponent record: {state.get('opponent_record', 'N/A')} ({state.get('opponent_win_pct', 0):.1%})")

        print(f"\n3. Calculating win probability with ALL enhanced factors...")

        # Calculate with basic factors only
        basic_prob = calculator.calculate_win_probability(
            score_diff=state['score_diff'],
            time_remaining=state['time_remaining'],
            has_possession=state['has_possession'],
            field_position=state.get('field_position')
        )
        print(f"   Basic model (no enhancements): {basic_prob:.1%}")

        # Calculate with all enhanced factors
        enhanced_prob = calculator.calculate_win_probability(
            score_diff=state['score_diff'],
            time_remaining=state['time_remaining'],
            has_possession=state['has_possession'],
            field_position=state.get('field_position'),
            down=state.get('down'),
            distance=state.get('distance'),
            team_timeouts=state.get('team_timeouts'),
            opponent_timeouts=state.get('opponent_timeouts'),
            team_win_pct=state.get('team_win_pct'),
            opponent_win_pct=state.get('opponent_win_pct')
        )
        print(f"   Enhanced model (all factors): {enhanced_prob:.1%}")
        print(f"   Difference: {abs(enhanced_prob - basic_prob):.1%}")

        print(f"\n✓ All enhanced features working correctly!")
    else:
        print("   ✗ Could not extract game state")

    print("\n" + "=" * 70)


def test_synthetic_data():
    """Test with synthetic game scenarios."""
    calculator = NFLWinProbability()

    print("Testing Down & Distance Impact:")
    print("-" * 70)

    scenarios = [
        {"desc": "3rd & 1 (easy)", "down": 3, "distance": 1},
        {"desc": "3rd & 10 (medium)", "down": 3, "distance": 10},
        {"desc": "3rd & 18 (difficult)", "down": 3, "distance": 18},
        {"desc": "4th & 2 (critical)", "down": 4, "distance": 2},
    ]

    base_params = {
        "score_diff": 3,
        "time_remaining": 180,
        "has_possession": True,
        "field_position": 60
    }

    for scenario in scenarios:
        prob = calculator.calculate_win_probability(
            **base_params,
            down=scenario["down"],
            distance=scenario["distance"]
        )
        print(f"  {scenario['desc']}: {prob:.1%}")

    print("\n✓ Synthetic testing complete!")


if __name__ == "__main__":
    test_enhanced_features()
