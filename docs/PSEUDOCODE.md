# 📝 NBABot v10.0 — Pseudo-Code Documentation

## Overview

This document contains the pseudo-code logic for each component of NBABot v10.0.

---

## 🎯 Core Flow

```
USER COMMAND: /parlay legs:4 wager:10 ladder:5

┌─────────────────────────────────────────────────────────────┐
│ 1. PARSE COMMAND                                            │
│    - Extract legs count (4)                                 │
│    - Extract wager amount (10)                              │
│    - Extract ladder window (5, default if not provided)     │
├─────────────────────────────────────────────────────────────┤
│ 2. FETCH TODAY'S GAMES                                      │
│    - Call API-Basketball for today's schedule               │
│    - Get list of available matchups                         │
├─────────────────────────────────────────────────────────────┤
│ 3. GENERATE CANDIDATE LEGS                                  │
│    - For each game, generate possible legs                  │
│    - Player props, moneylines, spreads, totals              │
├─────────────────────────────────────────────────────────────┤
│ 4. CHECK ELIGIBILITY (per leg)                              │
│    - Calculate hit rate                                     │
│    - Apply ladder threshold                                 │
│    - REJECT if below threshold                              │
├─────────────────────────────────────────────────────────────┤
│ 5. SELECT LEGS                                              │
│    - From eligible pool, randomly select N legs             │
│    - Ensure variety (not all same type)                     │
├─────────────────────────────────────────────────────────────┤
│ 6. CALCULATE ODDS                                           │
│    - Combine individual leg odds                            │
│    - Calculate potential payout                             │
├─────────────────────────────────────────────────────────────┤
│ 7. BUILD EMBED                                              │
│    - Format parlay for Discord                              │
│    - Add interactive buttons                                │
├─────────────────────────────────────────────────────────────┤
│ 8. SEND RESPONSE                                            │
│    - Post embed to channel                                  │
│    - Store parlay data for button interactions              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Eligibility Checker

```python
FUNCTION check_eligibility(hits, games, ladder):
    """
    Determine if a leg meets the eligibility threshold.
    
    THRESHOLDS:
    - Ladder 5:  Reject if hits <= 2  (need 3+ to pass)
    - Ladder 10: Reject if hits <= 6  (need 7+ to pass)
    - Ladder 15: Reject if hits <= 9  (need 10+ to pass)
    """
    
    IF ladder == 5:
        threshold = 3
    ELSE IF ladder == 10:
        threshold = 7
    ELSE IF ladder == 15:
        threshold = 10
    
    IF hits >= threshold:
        RETURN True, None  # Eligible, no rejection reason
    ELSE:
        RETURN False, f"Hit rate {hits}/{games} below threshold {threshold}/{ladder}"
```

---

## 🧩 Leg Type: Player Prop

```python
FUNCTION generate_player_prop_leg(player, prop_type, line, ladder):
    """
    Generate a player prop leg.
    
    INPUTS:
    - player: Player object with ID, name, team
    - prop_type: 'points', 'rebounds', 'assists', etc.
    - line: The betting line (e.g., 25.5)
    - ladder: Game window (5, 10, 15)
    """
    
    # Step 1: Fetch game logs
    game_logs = API.get_player_game_logs(player.id, limit=ladder)
    
    # Step 2: Count hits
    hits = 0
    FOR game IN game_logs:
        stat_value = game.stats[prop_type]
        IF stat_value > line:
            hits += 1
    
    # Step 3: Check eligibility
    is_eligible, rejection = check_eligibility(hits, ladder, ladder)
    
    IF NOT is_eligible:
        RETURN None  # Leg rejected - NEVER SHOW
    
    # Step 4: Build leg object
    leg = {
        "type": "player_prop",
        "selection": {
            "label": f"{player.name} — Over {line} {prop_type.title()}",
            "value": line,
            "direction": "over",
            "player_name": player.name,
            "prop_type": prop_type
        },
        "hit_rate": {
            "hits": hits,
            "games": ladder,
            "percentage": (hits / ladder) * 100
        },
        "eligible": True
    }
    
    RETURN leg
```

---

## 🧩 Leg Type: Team Moneyline

```python
FUNCTION generate_moneyline_leg(team, opponent, ladder):
    """
    Generate a team moneyline leg.
    H2H is SUPPORTING DATA ONLY - does not affect eligibility.
    """
    
    # Step 1: Fetch recent games
    recent_games = API.get_team_games(team.id, limit=ladder)
    
    # Step 2: Count wins
    wins = 0
    FOR game IN recent_games:
        IF game.winner == team.id:
            wins += 1
    
    # Step 3: Fetch H2H (supporting data only)
    h2h_games = API.get_head_to_head(team.id, opponent.id, window="1_year")
    h2h_wins = COUNT(game FOR game IN h2h_games WHERE game.winner == team.id)
    
    # Step 4: Check eligibility (based on recent form, NOT H2H)
    is_eligible, rejection = check_eligibility(wins, ladder, ladder)
    
    IF NOT is_eligible:
        RETURN None  # Leg rejected - NEVER SHOW
    
    # Step 5: Build leg object
    leg = {
        "type": "moneyline",
        "selection": {"label": f"{team.name} ML"},
        "hit_rate": {"hits": wins, "games": ladder},
        "h2h": {"wins": h2h_wins, "games": LEN(h2h_games)},
        "eligible": True
    }
    
    RETURN leg
```

---

## 🧩 Leg Type: Spread (ATS)

```python
FUNCTION generate_spread_leg(team, spread_line, ladder):
    """
    Generate a spread/ATS leg.
    """
    
    recent_games = API.get_team_games(team.id, limit=ladder)
    
    covers = 0
    total_margin = 0
    
    FOR game IN recent_games:
        margin = game.team_score - game.opponent_score
        total_margin += margin
        
        # For favorite (-7.5): need to win by MORE than 7.5
        IF spread_line < 0:
            IF margin > ABS(spread_line):
                covers += 1
        # For underdog (+7.5): need to lose by LESS than 7.5 or win
        ELSE:
            IF margin > -spread_line:
                covers += 1
    
    avg_margin = total_margin / ladder
    
    is_eligible, rejection = check_eligibility(covers, ladder, ladder)
    
    IF NOT is_eligible:
        RETURN None
    
    RETURN {
        "type": "spread",
        "selection": {"label": f"{team.name} {spread_line:+}"},
        "hit_rate": {"hits": covers, "games": ladder},
        "spread_data": {"avg_margin": avg_margin, "cover_rate": covers}
    }
```

---

## 🧩 Leg Type: Game Total

```python
FUNCTION generate_game_total_leg(home_team, away_team, total_line, direction, ladder):
    """
    Generate a game total (over/under) leg.
    """
    
    home_games = API.get_team_games(home_team.id, limit=ladder)
    
    hits = 0
    FOR game IN home_games:
        game_total = game.team_score + game.opponent_score
        IF direction == "over" AND game_total > total_line:
            hits += 1
        ELIF direction == "under" AND game_total < total_line:
            hits += 1
    
    is_eligible, rejection = check_eligibility(hits, ladder, ladder)
    
    IF NOT is_eligible:
        RETURN None
    
    RETURN {
        "type": "game_total",
        "selection": {"label": f"Game Total {direction.title()} {total_line}"},
        "hit_rate": {"hits": hits, "games": ladder}
    }
```

---

## 🧩 Leg Type: Team Total

```python
FUNCTION generate_team_total_leg(team, total_line, direction, ladder):
    """
    Generate a team total leg.
    """
    
    recent_games = API.get_team_games(team.id, limit=ladder)
    
    hits = 0
    FOR game IN recent_games:
        team_score = game.team_score
        IF direction == "over" AND team_score > total_line:
            hits += 1
        ELIF direction == "under" AND team_score < total_line:
            hits += 1
    
    is_eligible, rejection = check_eligibility(hits, ladder, ladder)
    
    IF NOT is_eligible:
        RETURN None
    
    RETURN {
        "type": "team_total",
        "selection": {"label": f"{team.name} Team Total {direction.title()} {total_line}"},
        "hit_rate": {"hits": hits, "games": ladder}
    }
```

---

## 💰 Odds Calculator

```python
FUNCTION calculate_parlay_odds(legs):
    """
    Calculate combined parlay odds.
    """
    
    FUNCTION american_to_decimal(american):
        IF american > 0:
            RETURN (american / 100) + 1
        ELSE:
            RETURN (100 / ABS(american)) + 1
    
    combined_decimal = 1.0
    FOR leg IN legs:
        combined_decimal *= american_to_decimal(leg.odds.american)
    
    RETURN combined_decimal


FUNCTION calculate_potential_win(wager, decimal_odds):
    RETURN wager * decimal_odds - wager
```

---

## 🚫 Rejection Example

```python
# Kevin Durant Over 29.5 Points
# Last 5 games: [28, 31, 25, 27, 30]

hits = 2  # Only 31 and 30 exceeded 29.5
threshold = 3  # Need 3+ for ladder 5

is_eligible = check_eligibility(hits=2, games=5, ladder=5)
# Returns: False

# THIS LEG IS REJECTED
# - Never appears in parlay
# - Never shown to user
# - Silently filtered out
```

---

**End of Pseudo-Code Documentation**
