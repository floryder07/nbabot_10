# 📋 Changelog

All notable changes to NBABot will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [10.1.0] - 2025-01-08

### ✨ New Features

#### Alt Line Selection Engine
- Bot now analyzes **all available alt lines** instead of using default market lines
- Selects the **optimal line** based on consistency across L5/L10/L15 windows
- For Overs: Chooses lowest line that clears consistently
- For Unders: Chooses highest line player stays under consistently

#### Enhanced Projection System
- New `projection_engine.py` module for smart line selection
- Analyzes hit rates across 5, 10, and 15 game windows
- Calculates consistency scores to avoid single-game spike picks
- Works for: Player Props, Team Totals, Spreads

#### Detailed Explanation Engine
- New `explanation_engine.py` module with number-based explanations
- Every explanation includes specific stats, not vague language
- Shows exactly WHY each line was chosen
- Includes: hit rates, averages, margins, alt lines considered

### 📊 New Logic

#### Player Props
```
• Evaluates all alt lines (e.g., 20.5, 22.5, 24.5)
• Calculates hit rate for each across L5/L10/L15
• Selects line with highest consistency
• Shows average margin above/below line
```

#### Team Totals
```
• Checks both conditions:
  - Team average vs line
  - Opponent allows vs line
• Both must qualify for high confidence
• Shows qualifying status for each
```

#### Spreads
```
• Compares main spread vs alt spreads
• Selects spread with highest cover rate
• Avoids thin margins
• Shows cover % for each option
```

### 🔧 Technical
- Added `projection_engine.py` — Alt line selection logic
- Added `explanation_engine.py` — Detailed explanations
- No existing code replaced — new modules only
- Reuses existing Parlay/Leg structures

---

## [10.0.1] - 2025-01-08

### 🔧 Fixed
- **Odds Display** — Per-leg odds now show proper American format (`-110`, `+120`) instead of truncated values
- **Button Interactions** — Fixed "Interaction Failed" errors on Insights, Explain, and Refresh buttons
- **Refresh Button** — Now properly edits existing message instead of failing silently

### ✨ Improved
- **Insights vs Explain Separation**
  - 📊 **Insights** = Statistical data, risk analysis, numerical breakdown
  - 📖 **Explain** = Human reasoning, why picks were selected, educational content
- **Odds Display** — Now shows implied probability alongside American odds
- **Embed Layout** — Cleaner formatting with `PICK:` label and visual separators
- **Refresh UX** — Shows timestamp (`🔄 Refreshed: 6:45 PM`) and has 5-second cooldown

### 🛠 Technical Changes
- Added proper `interaction.response.defer()` before async operations
- Added `interaction.followup.send()` pattern for button responses
- Refresh uses `deferUpdate()` + `message.edit()` instead of `reply()`
- Realistic odds generation based on bet type (spreads ~-110, props vary more)

---

## [10.0.0] - 2025-01-08

### 🎉 Initial Release
- Rule-based NBA parlay generation
- 5 leg types: Player Props, Moneyline, Spread, Game Total, Team Total
- Eligibility ladder system (5/10/15 game windows)
- Interactive Discord buttons (Insights, Explain, Refresh)
- API-Basketball integration
- Mock mode for testing without API key

### 📊 Eligibility Rules
| Ladder | Required | Rejected |
|--------|----------|----------|
| 5-game | 3+ hits | 0-2 hits |
| 10-game | 7+ hits | 0-6 hits |
| 15-game | 10+ hits | 0-9 hits |

### 🔧 Commands
- `/parlay legs:<2-10> wager:<amount> ladder:<5|10|15>`
- `/parlay-help`
- `/parlay-rules`
- `/parlay-stats`

---

## Future Plans

### [10.1.0] - Planned
- [ ] Additional prop types (rebounds, assists, 3PM)
- [ ] Injury report integration
- [ ] Better player name matching

### [11.0.0] - Planned
- [ ] AI-enhanced leg selection
- [ ] Confidence scoring
- [ ] Historical tracking

