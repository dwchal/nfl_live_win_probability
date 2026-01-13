# NFL Live Win Probability Calculator

A Python application to calculate live win probabilities for NFL games based on current game state.

## Features

- **Live Game Tracking**: Monitor real-time NFL games with automatic win probability updates
- **Team-Specific Monitoring**: Track your favorite team (including Steelers-specific script)
- **Win Probability Calculation**: Calculate win probability based on score differential and time remaining
- **Comeback Probability**: Calculate comeback probability for trailing teams
- **ESPN API Integration**: Fetch live game data automatically
- Account for possession and field position
- Support for different game situations (regulation, overtime)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Live Game Tracking

#### Track Steelers Games (Quick Start)

The easiest way to monitor Steelers games:

```bash
python track_steelers.py
```

This will automatically find live Steelers games and display win probability updates every 30 seconds.

#### Track Any Team

```bash
# Track a specific team
python live_tracker.py --team Steelers
python live_tracker.py --team "Kansas City Chiefs"
python live_tracker.py --team KC

# Track all live games
python live_tracker.py --all

# Customize update interval (in seconds)
python live_tracker.py --team Steelers --interval 15
```

#### Programmatic Usage

```python
from live_tracker import LiveGameTracker

# Create tracker
tracker = LiveGameTracker(update_interval=30)

# Track a specific team
tracker.track_team('Steelers')

# Track all games
tracker.track_all_games()

# Get a single snapshot
snapshot = tracker.get_game_snapshot('Steelers')
if snapshot:
    print(f"Win probability: {snapshot['win_probability']:.1%}")
```

### Manual Win Probability Calculation

```python
from win_probability import NFLWinProbability

calculator = NFLWinProbability()
prob = calculator.calculate_win_probability(
    score_diff=3,
    time_remaining=300,  # 5 minutes in seconds
    has_possession=True,
    field_position=50
)
print(f"Win probability: {prob:.1%}")
```

### Comeback Probability

Calculate the probability of a comeback for a trailing team:

```python
from win_probability import NFLWinProbability

calculator = NFLWinProbability()
comeback_prob = calculator.calculate_comeback_probability(
    score_deficit=7,  # Down by 7 points
    time_remaining=300,  # 5 minutes in seconds
    has_possession=True,
    field_position=30  # At own 30 yard line
)
print(f"Comeback probability: {comeback_prob:.1%}")
```

## Example Output

When tracking a live game, you'll see updates like:

```
[14:23:45] Game Update:

  BAL  17  @   PIT  20
  Period: 4, Clock: 5:23
  Possession: PIT 30
  2nd & 7

  PIT Win Probability:  87.3%
  Leading by 3 points
```

## Future Features

- Historical game data integration for model training
- Machine learning model improvements with actual game data
- Visualization dashboard with probability charts
- Enhanced down and distance consideration
- Timeout tracking
- Weather and venue factors
