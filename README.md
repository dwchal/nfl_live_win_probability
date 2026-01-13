# NFL Live Win Probability Calculator

A Python application to calculate live win probabilities for NFL games based on current game state.

## Features

- Calculate win probability based on score differential and time remaining
- Calculate comeback probability for trailing teams
- Account for possession and field position
- Support for different game situations (regulation, overtime)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Win Probability

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

## TODO Features

- Historical game data integration
- Machine learning model improvements
- Real-time game tracking via API
- Visualization dashboard
- Down and distance consideration
