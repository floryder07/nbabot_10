# 🏀 NBABot_Version 10.0 🤖

**NBA Analytics Discord Bot — Rule-Based Parlay Generator**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ⚠️ Disclaimer

**Educational analytics only.**  
- ❌ No betting advice  
- ❌ No predictions  
- ❌ No guarantees  

This bot provides **historical data analysis** for educational purposes only.

---

## 🎯 What Does This Bot Do?

NBABot v10.0 generates **rule-based NBA parlays** using **strict historical hit-rate ladders**.

| Feature | Description |
|---------|-------------|
| **Eligibility Rules** | Only legs meeting hit-rate thresholds are included |
| **Multiple Leg Types** | Player props, moneylines, spreads, totals |
| **Transparency** | Every pick shows its data source |
| **No AI/Predictions** | Pure historical data, no speculation |

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- Discord Bot Token
- API-Basketball API Key (Pro Plan)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/nbabot-v10.git
cd nbabot-v10

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens
```

### Environment Variables

```env
DISCORD_TOKEN=your_discord_bot_token
API_BASKETBALL_KEY=your_api_basketball_key
GUILD_ID=your_discord_server_id
```

### Run the Bot

```bash
python src/bot.py
```

---

## 🧱 Commands

### Primary Command

```
/parlay legs:<number> wager:<amount> ladder:<5|10|15>
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `legs` | Integer | ✅ Yes | — | Number of legs (2-10) |
| `wager` | Number | ✅ Yes | — | Wager amount in USD |
| `ladder` | Choice | ❌ No | 5 | Historical window (5, 10, or 15 games) |

**Example:**
```
/parlay legs:4 wager:10 ladder:5
```

---

### Utility Commands

| Command | Description |
|---------|-------------|
| `/parlay-help` | Show command usage and examples |
| `/parlay-rules` | Display eligibility rules |
| `/parlay-stats` | Show bot statistics |

---

## 📊 Eligibility Rules

### The Ladder System

The bot uses a **hit-rate ladder** to determine leg eligibility.

#### ❌ EXCLUDED (Never Allowed)

| Ladder | Rejection Threshold |
|--------|---------------------|
| 5-game | 0-2 hits out of 5 |
| 10-game | 0-6 hits out of 10 |
| 15-game | 0-9 hits out of 15 |

#### ✅ ALLOWED

| Ladder | Acceptance Threshold |
|--------|----------------------|
| 5-game | 3-5 hits out of 5 |
| 10-game | 7-10 hits out of 10 |
| 15-game | 10-15 hits out of 15 |

**Rule:** If a leg fails eligibility, it is **never shown, never explained, never displayed**.

---

## 🧩 Supported Leg Types

### 1. Player Props
```
MATCHUP: Lakers vs Suns
LEG: LeBron James — Over 25.5 Points
HIT RATE: 3 / 5 games
ODDS: -110
```
- Uses last 5/10/15 games
- No H2H data for player props

### 2. Team Moneyline
```
MATCHUP: Bucks vs Heat
LEG: Bucks ML
HIT RATE: 3 / 5 games
H2H (1 Year): 3 / 5 wins
ODDS: -125
```
- H2H is supporting data only
- Max H2H window: 1 year

### 3. Spread (ATS)
```
MATCHUP: Nuggets vs Blazers
LEG: Nuggets -7.5
AVG MARGIN: +10.2 points
COVER RATE: 3 / 5 games
ODDS: -110
```
- Uses margin of victory
- Uses ATS cover history

### 4. Game Total (Over/Under)
```
MATCHUP: Mavericks vs Rockets
LEG: Game Total Over 230.5
TOTAL HIT RATE: 4 / 5 games
ODDS: -105
```

### 5. Team Total
```
MATCHUP: Celtics vs Knicks
LEG: Celtics Team Total Over 113.5
HIT RATE: 3 / 5 games
ODDS: -115
```

---

## 🖥️ Discord Output Format

### Parlay Header
```
🏀 PARLAY — 4 LEGS
━━━━━━━━━━━━━━━━━━━━━
💰 TOTAL ODDS: +1180
💵 WAGER: $10 → POTENTIAL WIN: $128
```

### Interactive Buttons

Every parlay includes three buttons:

| Button | Function |
|--------|----------|
| 🧠 **Insights** | Shows detailed stats for selected leg |
| 🔍 **Explain** | Shows why the pick was included |
| 🔄 **Refresh** | Generates new parlay with same settings |

---

## 📁 Project Structure

```
nbabot-v10/
├── src/
│   ├── bot.py              # Main Discord bot
│   ├── parlay_engine.py    # Parlay generation logic
│   ├── eligibility.py      # Eligibility rule checking
│   ├── embeds.py           # Discord embed builders
│   ├── api_client.py       # API-Basketball client
│   ├── buttons.py          # Interactive button handlers
│   └── config.py           # Configuration settings
├── schemas/
│   ├── parlay.json         # Parlay data schema
│   └── leg.json            # Leg data schema
├── docs/
│   └── PSEUDOCODE.md       # Pseudo-code documentation
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 📡 Data Source

| Provider | Plan | Documentation |
|----------|------|---------------|
| API-Basketball | Pro | [api-basketball.com](https://api-basketball.com) |

**Future:** API-Sports integration planned

---

## 🧭 Design Philosophy

| Principle | Meaning |
|-----------|---------|
| **Data > Hype** | Only show what the numbers say |
| **Structure > Opinion** | Rules-based, not guesswork |
| **Transparency > Confidence** | Show the why, not just the what |
| **Education > Prediction** | Learn from data, don't gamble on it |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🔮 Roadmap

- [x] v10.0 — Rule-based parlay generation
- [ ] v10.1 — Additional prop types (rebounds, assists, 3PM)
- [ ] v10.2 — Injury report integration
- [ ] v11.0 — AI-enhanced leg selection (future)

---

**Built with 🏀 for NBA analytics enthusiasts**
---

## 1️⃣ UPDATE THE VERSION BADGE (at the top)

Change:
```
# 🏀 NBABot_Version 10.0 🤖
```

To:
```
# 🏀 NBABot v10.0.1 🤖

[![Version](https://img.shields.io/badge/version-10.0.1-blue.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()
```

---

## 2️⃣ ADD VERSION HISTORY SECTION (before Contributing section)

```markdown
---

## 📋 Version History

See [CHANGELOG.md](CHANGELOG.md) for full version history.

### Latest: v10.0.1 (Jan 8, 2025)
**Fixes:**
- ✅ Odds now display correctly (American format with implied probability)
- ✅ Button interactions fixed (no more "Interaction Failed")
- ✅ Refresh button edits message properly
- ✅ Insights vs Explain now have distinct purposes

### Previous: v10.0.0 (Jan 8, 2025)
- 🎉 Initial release with rule-based parlay generation

---
```

---

## 3️⃣ UPDATE THE CONFIG SECTION

Add version info to your config.py:

```python
# Bot Settings
BOT_NAME = "NBABot"
BOT_VERSION = "10.0.1"  # ← Update this with each patch
```

---

## 📁 WHERE TO PUT FILES

```
nbabot_v10/
├── CHANGELOG.md        ← NEW FILE (put in root)
├── README.md           ← UPDATE existing
├── docs/
│   └── PSEUDOCODE.md
├── schemas/
│   ├── parlay.json
│   └── leg.json
├── src/
│   ├── bot.py
│   ├── buttons.py      ← REPLACED
│   ├── embeds.py       ← REPLACED
│   ├── parlay_engine.py ← REPLACED
│   ├── config.py       ← UPDATE version
│   └── ...
└── ...
```

---

## 🏷️ VERSION NUMBERING

Use Semantic Versioning (SemVer):

```
MAJOR.MINOR.PATCH

10.0.0 → Initial release
10.0.1 → Bug fixes (current)
10.1.0 → New features (future)
11.0.0 → Major changes / AI mode (future)
```

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Bug fix | PATCH | 10.0.0 → 10.0.1 |
| New feature | MINOR | 10.0.1 → 10.1.0 |
| Breaking change | MAJOR | 10.1.0 → 11.0.0 |

