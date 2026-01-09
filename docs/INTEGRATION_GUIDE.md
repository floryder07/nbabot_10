# 🔗 Integration Guide — v10.1.0 New Modules

This guide shows how to connect the new `projection_engine.py` and `explanation_engine.py` to your existing bot.

---

## 📁 File Placement

```
nbabot_v10/
├── CHANGELOG.md              ← REPLACE with new version
├── src/
│   ├── projection_engine.py  ← NEW FILE (add here)
│   ├── explanation_engine.py ← NEW FILE (add here)
│   ├── parlay_engine.py      ← UPDATE (add imports)
│   ├── embeds.py             ← UPDATE (use new explanations)
│   ├── config.py             ← UPDATE version to "10.1.0"
│   └── ...
```

---

## 1️⃣ Update config.py

```python
BOT_VERSION = "10.1.0"
```

---

## 2️⃣ Update parlay_engine.py

Add these imports at the top:

```python
# Add after existing imports
from projection_engine import projection_engine, ProjectionResult
from explanation_engine import explanation_engine
```

---

## 3️⃣ Using the Projection Engine

### Example: Player Prop with Alt Lines

```python
# In parlay_engine.py or wherever you generate player props

async def generate_smart_player_prop(player_id, stat_type, alt_lines):
    """Generate player prop using projection engine."""
    
    # Get player's last 15 games
    stats = await api_client.get_player_stats(player_id, limit=15)
    
    # Extract stat values (e.g., points)
    game_values = [s.get(stat_type, 0) for s in stats]
    
    # Use projection engine to find best line
    projection = projection_engine.analyze_player_prop(
        game_logs=game_values,
        alt_lines=alt_lines,  # e.g., [20.5, 22.5, 24.5, 26.5]
        direction="over"
    )
    
    # projection.selected_line = best line
    # projection.confidence = confidence score
    # projection.reasoning = detailed explanation
    
    return projection
```

### Example: Team Total

```python
async def generate_smart_team_total(team_id, opponent_id, line, direction):
    """Generate team total using projection engine."""
    
    # Get team's scores
    team_games = await api_client.get_team_games(team_id, limit=15)
    team_scores = [parse_team_score(g, team_id) for g in team_games]
    
    # Get opponent's allowed points
    opp_games = await api_client.get_team_games(opponent_id, limit=15)
    opp_allowed = [parse_opponent_score(g, opponent_id) for g in opp_games]
    
    # Use projection engine
    projection = projection_engine.analyze_team_total(
        team_scores=team_scores,
        opponent_allowed=opp_allowed,
        line=line,
        direction=direction
    )
    
    return projection
```

### Example: Spread with Alts

```python
async def generate_smart_spread(team_id, main_spread, alt_spreads):
    """Generate spread using projection engine."""
    
    # Get team's margins
    team_games = await api_client.get_team_games(team_id, limit=15)
    margins = [parse_margin(g, team_id) for g in team_games]
    
    # Use projection engine
    projection = projection_engine.analyze_spread(
        margins=margins,
        main_spread=main_spread,
        alt_spreads=alt_spreads  # e.g., [-4.5, -6.5, -8.5]
    )
    
    return projection
```

---

## 4️⃣ Using the Explanation Engine

### In embeds.py — Update build_explain_embed()

```python
from explanation_engine import explanation_engine

def build_explain_embed(leg) -> discord.Embed:
    """Build detailed explanation using explanation engine."""
    
    if leg.type == "player_prop":
        # Get game values from leg data or cache
        game_values = leg.game_values  # You'll need to store this
        
        explanation = explanation_engine.explain_player_prop(
            player_name=leg.selection.player_name,
            stat_type=leg.selection.prop_type,
            line=leg.selection.value,
            direction=leg.selection.direction,
            game_values=game_values
        )
    
    elif leg.type == "team_total":
        explanation = explanation_engine.explain_team_total(
            team_name=leg.selection.team_name,
            opponent_name=leg.matchup.away_team,
            line=leg.selection.value,
            direction=leg.selection.direction,
            team_scores=leg.team_scores,  # Store this
            opponent_allowed=leg.opp_allowed  # Store this
        )
    
    elif leg.type == "spread":
        explanation = explanation_engine.explain_spread(
            team_name=leg.selection.team_name,
            spread=leg.selection.value,
            margins=leg.margins,  # Store this
            main_spread=leg.main_spread  # Store this
        )
    
    elif leg.type == "moneyline":
        explanation = explanation_engine.explain_moneyline(
            team_name=leg.selection.team_name,
            opponent_name=leg.matchup.away_team,
            team_wins=leg.team_wins,  # Store this
            h2h_wins=leg.h2h.wins if leg.h2h else None,
            h2h_games=leg.h2h.games if leg.h2h else None
        )
    
    embed = discord.Embed(
        title=f"📖 DETAILED EXPLANATION",
        description=explanation,
        color=BOT_COLOR
    )
    
    return embed
```

---

## 5️⃣ Store Extra Data in Legs

To use the explanation engine fully, you need to store the raw game data in each leg. Update your `Leg` dataclass:

```python
@dataclass
class Leg:
    # ... existing fields ...
    
    # NEW: Store raw data for explanations
    game_values: List[float] = field(default_factory=list)  # For player props
    team_scores: List[float] = field(default_factory=list)  # For team totals
    opp_allowed: List[float] = field(default_factory=list)  # For team totals
    margins: List[float] = field(default_factory=list)      # For spreads
    team_wins: List[bool] = field(default_factory=list)     # For moneyline
    main_spread: float = 0.0                                 # For spread alts
```

---

## 6️⃣ Data Source Fallback

The spec mentions fallback logic. Add this helper:

```python
# In api_client.py or a new data_sources.py

async def get_player_stats_with_fallback(player_id: int, limit: int = 15):
    """
    Get player stats with fallback sources.
    
    Order: API-Sports → Derived averages
    """
    try:
        # Primary source
        stats = await api_client.get_player_stats(player_id, limit)
        if stats:
            return stats, "api_sports", 100  # data, source, confidence
    except Exception:
        pass
    
    # Fallback: Return empty with reduced confidence
    return [], "fallback", 50
```

---

## ✅ Quick Checklist

1. [ ] Add `projection_engine.py` to `src/`
2. [ ] Add `explanation_engine.py` to `src/`
3. [ ] Update `config.py` → `BOT_VERSION = "10.1.0"`
4. [ ] Replace `CHANGELOG.md` with new version
5. [ ] Add imports to `parlay_engine.py`
6. [ ] Update `Leg` dataclass to store raw data
7. [ ] Update `build_explain_embed()` to use explanation engine
8. [ ] Restart bot

---

## 🧪 Testing

Test the projection engine directly:

```python
# test_projection.py
from projection_engine import projection_engine

# Test player prop
game_logs = [26, 23, 20, 25, 30, 26, 23, 20, 25, 30]
alt_lines = [20.5, 22.5, 24.5, 26.5]

result = projection_engine.analyze_player_prop(
    game_logs=game_logs,
    alt_lines=alt_lines,
    direction="over"
)

print(f"Selected line: {result.selected_line}")
print(f"Confidence: {result.confidence}%")
print(f"Reasoning:\n{result.reasoning}")
```

---

That's everything! The new modules ADD functionality without replacing your existing code. 🏀
