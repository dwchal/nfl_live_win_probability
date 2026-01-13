# NFL Live Win Probability Calculator

A Python application to calculate live win probabilities for NFL games based on current game state.

## Features

- **Live Game Tracking**: Monitor real-time NFL games with automatic win probability updates
- **Team-Specific Monitoring**: Track your favorite team (including Steelers-specific script)
- **Enhanced Win Probability Model**: Advanced calculations with multiple factors:
  - Score differential and time remaining
  - Down and distance (e.g., 3rd & 1 vs 3rd & 15)
  - Timeout differential (more valuable late in games)
  - Team strength ratings based on season records
  - Possession and field position
- **Comeback Probability**: Calculate comeback probability for trailing teams
- **ESPN API Integration**: Fetch live game data automatically including:
  - Real-time score and game clock
  - Down, distance, and field position
  - Timeouts remaining for each team
  - Team season records
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

#### Basic Usage

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

#### Enhanced Usage (All Factors)

For the most accurate predictions, include all situational factors:

```python
calculator = NFLWinProbability()

# Steelers (10-3) up by 3, 3rd & 2 at own 40, 2 min left
prob = calculator.calculate_win_probability(
    score_diff=3,
    time_remaining=120,
    has_possession=True,
    field_position=40,
    down=3,                    # 3rd down
    distance=2,                # 2 yards to go
    team_timeouts=2,           # Steelers have 2 timeouts
    opponent_timeouts=1,       # Opponent has 1
    team_win_pct=0.769,        # 10-3 record = 76.9%
    opponent_win_pct=0.538     # 7-6 record = 53.8%
)
print(f"Win probability: {prob:.1%}")  # ~86.8%
```

**Key Factors Impact:**
- **Down & Distance**: 3rd & 1 significantly better than 3rd & 10
- **Timeouts**: More valuable in final 5 minutes; 2 vs 0 = +5-7% win prob
- **Team Strength**: Strong team (75%) vs weak team (30%) = +3-4% boost

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

When tracking a live game, you'll see updates with enhanced information:

```
[14:23:45] Game Update:

  BAL (8-5)  17  @   PIT (10-3)  20
  Period: 4, Clock: 5:23
  Timeouts: BAL 1, PIT 2
  Possession: PIT 30
  2nd & 7

  PIT Win Probability:  89.2%
  Leading by 3 points
```

The enhanced model now shows:
- **Team Records**: Season records displayed for context
- **Timeout Tracking**: Remaining timeouts for each team
- **Down & Distance**: Current down and yards to go
- **More Accurate Probabilities**: Factors in game situation, timeouts, and team strength

## Model Details

The enhanced win probability model uses a logistic regression approach with the following factors:

| Factor | Weight | Impact |
|--------|--------|--------|
| Score Differential | 0.15 per point | Each point ≈ 15% contribution |
| Time Remaining | 0.008 per second | More time = more uncertainty |
| Possession | +0.3 | Worth ~2 points |
| Field Position | 0.01 per yard from midfield | Better position = higher win prob |
| Down | 1st: +0.2, 2nd: +0.1, 3rd: -0.1, 4th: -0.5 | Situation pressure |
| Distance | -0.02 per yard (1.5x on 3rd/4th) | Long distance = worse |
| Timeouts | 0.15 per TO (1.5x in final 5 min) | Clock management value |
| Team Strength | 0.8 × win% difference | Quality matters |

## Future Features

- Historical game data integration for model training with ML
- Machine learning model improvements with actual game data
- Visualization dashboard with live probability charts
- Weather and venue factors
- Advanced EPA (Expected Points Added) integration
- Play-by-play prediction
