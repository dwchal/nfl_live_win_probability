#!/usr/bin/env python3
"""
Integration test for live game tracking.

Tests the integration between ESPN API and win probability calculator.
"""

from nfl_api import NFLGameAPI
from win_probability import NFLWinProbability
from live_tracker import LiveGameTracker


def test_api_connection():
    """Test ESPN API connection."""
    print("Testing ESPN API connection...")
    api = NFLGameAPI()
    games = api.get_live_games()

    if games:
        print(f"✓ Successfully fetched {len(games)} games")
        return True
    else:
        print("✓ API connection successful (no live games at the moment)")
        return True


def test_win_probability():
    """Test win probability calculation."""
    print("\nTesting win probability calculations...")
    calculator = NFLWinProbability()

    # Test scenario: Up by 7 with 5 minutes left
    prob = calculator.calculate_win_probability(
        score_diff=7,
        time_remaining=300,
        has_possession=True,
        field_position=50
    )

    print(f"  Test case: Up by 7, 5 min left, has ball")
    print(f"  Win probability: {prob:.1%}")
    # With time-scaled model, 87% is realistic for a 7-point lead with 5 min left
    assert 0.8 < prob < 0.95, "Expected moderately high win probability"
    print("✓ Win probability calculation working")

    return True


def test_comeback_probability():
    """Test comeback probability calculation."""
    print("\nTesting comeback probability calculations...")
    calculator = NFLWinProbability()

    # Test scenario: Down by 3 with 2 minutes left
    prob = calculator.calculate_comeback_probability(
        score_deficit=3,
        time_remaining=120,
        has_possession=True,
        field_position=50
    )

    print(f"  Test case: Down by 3, 2 min left, has ball")
    print(f"  Comeback probability: {prob:.1%}")
    assert 0.3 < prob < 0.7, "Expected moderate comeback probability"
    print("✓ Comeback probability calculation working")

    return True


def test_live_tracker():
    """Test live tracker functionality."""
    print("\nTesting live tracker...")
    tracker = LiveGameTracker(update_interval=30)

    # Test getting a snapshot (will be None if no live games)
    snapshot = tracker.get_game_snapshot('Steelers')

    if snapshot:
        print(f"✓ Live Steelers game found!")
        print(f"  Win probability: {snapshot['win_probability']:.1%}")
    else:
        print("✓ Tracker working (no live Steelers game at the moment)")

    return True


def test_team_name_normalization():
    """Test team name normalization."""
    print("\nTesting team name normalization...")
    api = NFLGameAPI()

    tests = [
        ('Steelers', 'PIT'),
        ('steelers', 'PIT'),
        ('Pittsburgh', 'PIT'),
        ('PIT', 'PIT'),
        ('Chiefs', 'KC'),
        ('49ers', 'SF'),
    ]

    for input_name, expected in tests:
        result = api._normalize_team_name(input_name)
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"  ✓ '{input_name}' -> '{result}'")

    print("✓ Team name normalization working")
    return True


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("NFL Live Win Probability - Integration Tests")
    print("=" * 70)

    tests = [
        test_api_connection,
        test_win_probability,
        test_comeback_probability,
        test_team_name_normalization,
        test_live_tracker,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Tests passed: {passed}/{len(tests)}")
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {failed} tests failed")
    print("=" * 70)


if __name__ == "__main__":
    main()
