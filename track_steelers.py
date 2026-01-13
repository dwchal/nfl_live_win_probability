#!/usr/bin/env python3
"""
Steelers Game Tracker

Quick launcher to monitor Pittsburgh Steelers games with live win probabilities.
Just run this script during game day!
"""

from live_tracker import LiveGameTracker


def main():
    """Track Steelers game with live win probability updates."""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║       🏈  PITTSBURGH STEELERS LIVE WIN PROBABILITY  🏈       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    print("Starting Steelers game tracker...")
    print("This will automatically find and monitor live Steelers games.")
    print("Win probability will update every 30 seconds during the game.\n")

    tracker = LiveGameTracker(update_interval=30)
    tracker.track_team('Steelers')


if __name__ == "__main__":
    main()
