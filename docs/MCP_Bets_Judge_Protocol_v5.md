# 🏈 MCP Bets — Judge Protocol v5.0

## 📌 Part 1: Prompt Template (Ruleset)

Create a Judge Research Pack for **[GAME(S)]**.

**Rules:**
- Use **ONLY** the props and players provided (via my screenshots or JSON files). Do not add players from prior seasons or outside data.
- Include: Game Lines, Passing Props, Receiving Props, Rushing Props, Combo Props.
- Apply MCP Bets Judge framework:
  - **Ultra Locks** Criteria (95-100% Confidence)
  - **Super Locks (85%+)** → Tease-down props that can realistically hit by halftime.
  - **Standard Locks (70–84%)** → Moderate tease-downs, good probability but may require 3–4 quarters.
  - **Lotto (<70%)** → Higher-risk ladders, bigger odds, less reliable.
- Prioritize **Receptions** as the most stable category. Then safe alt receiving yards, then rushing yards, then QB passing/rushing.
- Exclude risky props for Super Locks (RB receiving yards, anytime TDs) unless they’re clear system edges.
- Always integrate:
  - Weather context
  - Game script
  - Injuries (exclude Questionable players from Super Locks).

# The Five Pillars of ULTRA LOCK Status

For a prop to qualify as an **Ultra Lock**, it must pass all five pillars:

---

## Pillar 1: Historical Dominance (95%+ Hit Rate)

The player must have demonstrated elite consistency hitting this specific prop threshold.

**Requirements (meet at least one):**
- Hit the prop 4+ consecutive games this season
- Hit the prop 80%+ of games this season (minimum 5 games played)
- Hit the prop 85%+ over last 2 seasons (minimum 10 games)

**Examples:**
- Bijan Robinson Over 100.5 Combined Rush+Rec: 4/4 games hit (100%)
- Christian McCaffrey Over 110.5 Combined (2023): 14/16 games (87.5%)
- Tyreek Hill Over 80.5 Rec Yards (Chiefs 2022): 13/15 games (86.7%)

---

## Pillar 2: Game-Script Proof

The prop must be resilient to all game flows—winning, losing, or close games.

**Characteristics:**
- Player accumulates stats regardless of score differential
- Usage remains high in all scenarios
- No single game-script dependency

**Game-Script Proof Players:**
- **Dual-threat RBs:** Get rushes when leading, receptions when trailing  
  _Examples: Bijan Robinson, Christian McCaffrey, Alvin Kamara_
- **Target-hog slot WRs:** Always get volume regardless of score  
  _Examples: Cooper Kupp, Amon-Ra St. Brown, Puka Nacua_
- **Workhorse RBs with passing game role:** Never leave the field  
  _Examples: CMC, Saquon Barkley (with Giants)_

**NOT Game-Script Proof:**
- Power backs (only viable when leading): Derrick Henry, AJ Dillon
- Deep-threat WRs (volume drops in garbage time): DK Metcalf, Brandin Cooks
- Pass-catching specialists (only viable when trailing): James White, Nyheim Hines

---

## Pillar 3: Elite Matchup

The opponent's defense must be demonstrably exploitable for this specific prop type.

**Metrics to evaluate:**
- Defensive ranking against position (bottom 25% of league)
- Historical performance allowed to similar players
- Specific weakness (e.g., slot coverage, outside runs, red zone defense)

**Examples:**
- RB facing defense ranked 28th against rush yards
- WR facing defense ranked 30th in receptions allowed to slot WRs
- TE facing defense that's allowed 80+ yards to TEs in 5 straight games

**Matchup Quality Score:**
- **Elite (90+):** Defense in bottom 3 against this stat category
- **Strong (80-89):** Defense in bottom 8
- **Good (70-79):** Defense in bottom 12

---

## Pillar 4: Volume Lock

The player must have guaranteed, elite usage that ensures opportunity.

**Usage Requirements:**
- Snap count: 80%+ of offensive snaps (or 70%+ for RBs)
- Target/Touch share: Top 3 on the team
- Red zone usage: Featured player inside the 20

**Advanced Indicators:**
- Target share: 25%+ of team targets (WR/TE)
- Rush attempt share: 60%+ of team rushes (RB)
- Route participation: 85%+ of passing plays (WR/TE)

**Injury-Driven Volume Locks:**
- WR1 out → WR2 becomes volume lock (e.g., Wan'Dale Robinson when Malik Nabers out)
- RB1 out → RB2 becomes workhorse (e.g., Justice Hill when Derrick Henry out)
- TE1 out → TE2 gets all targets (e.g., Luke Musgrave when Tucker Kraft out)

---

## Pillar 5: No Red Flags

The prop must be free of all significant risk factors.

**Disqualifying Red Flags:**
- ❌ Player injury concern (Questionable/Doubtful, limited practice)
- ❌ Severe weather (20+ mph wind, heavy rain, snow)
- ❌ Negative line movement (sharp money betting against your side)
- ❌ Scheme change (new offensive coordinator, play-caller)
- ❌ Coaching uncertainty (interim coach, recent firing)
- ❌ Backup QB starting (massive game-script risk)
- ❌ Away game in hostile environment (for props sensitive to noise/crowd)

**Green Flags (Ultra Lock boosters):**
- ✅ Coming off BYE week (extra rest, preparation)
- ✅ Home game (comfort, routine)
- ✅ Revenge game (motivated performance)
- ✅ Contract year (statistically performs 8% better)
- ✅ Prime time game (stars perform better under lights)

---

# Judge LLM Workflow

Each LLM Judge receives:

**Input Package:**
- All MCP Agent outputs (weather, injuries, profiles, insider notes, etc.)
- User-submitted props (from screenshots or JSON)
- Game context (teams, spread, total, kickoff time)
- Historical prop hit rate data (e.g., "This player has hit Over 100.5 combined in 4/4 games")

**Processing:**
Each Judge independently analyzes the data and categorizes props into tiers:

| Tier         | Confidence (%) | Description                                      |
|--------------|---------------|--------------------------------------------------|
| 🔥 Ultra Lock | 95-100        | Must pass Five Pillars test                      |
| 🔒 Super Lock | 85-94         | High probability, halftime-viable                |
| ✅ Standard Lock | 70-84      | Solid probability with some variance             |
| 🎲 Lotto Pick | 40-69         | High upside but significant risk                 |
| 🎰 Mega Lotto | <40           | Long shots, lottery tickets                      |
| ❌ Avoid/Skip | low           | Low confidence or unfavorable                    |

**Provide parlay slip suggestions:**
- **Slip 1 (Ultra Lock Foundation):** 3 teased props, halftime-viable.
- **Slip 1 (Super Lock Foundation):** 3 teased props, halftime-viable.
- **Slip 2 (Standard Lock Correlation):** 3–4 moderate props.
- **Slip 3 (Lotto):** 5–7 legs, ladders, or higher-risk combos.

**Add Halftime Adjustment Notes** for live-bet potential.

**Output Format:**
- Game Lines
- Passing Props
- Receiving Props
- Rushing Props
- Combo Props
- 📊 Judge Angles (Super Lock / Standard / Lotto)
- 🎯 Suggested Slips
- ⚠️ Framework Flags

---

## 📌 Part 2: Single-Shot Example (Jets @ Dolphins, Week 4)

# 🏈 MCP Bets — Judge Research Pack

**Game:** Jets @ Dolphins (Week 4, 1 PM)  
**Weather:** Light rain possible, winds 10–15 mph  
**Game Line:** MIA -2.5 | Total 44.5

---

### 📊 Passing Props
- Tua Tagovailoa — 234.5 yds (O/U -112)
- Justin Fields — 181.5 yds (O/U -112)

### 📊 Receiving Props
- Tyreek Hill — 64.5 yds | 5.5 recs
- Garrett Wilson — 63.5 yds | 5.5 recs
- Jaylen Waddle — 48.5 yds | 4.5 recs
- De’Von Achane — 40.5 yds | 5.5 recs
- Breece Hall — 21.5 yds | 2.5 recs

### 📊 Rushing Props
- Achane — 55.5 yds
- Hall — 56.5 yds
- Fields — 47.5 yds

### 📊 Combo Props
- Achane — 90.5 rush+rec
- Hall — 78.5 rush+rec

---

### 📊 Judge Angles

#### 💎 Super Locks (85%+, halftime-viable)
- Garrett Wilson 4+ receptions (teased from 5.5) — high floor, Jets chase script.
- Jaylen Waddle 3+ receptions (teased from 4.5) — short-area target, weather hedge.
- Achane 30+ rushing yards (teased from 55.5) — usage + efficiency.

#### 🔥 Standard Locks (70–84%)
- Tyreek Hill 50+ yards — can hit in one play, but weather risk.
- Fields 35+ rush yards — designed runs + scrambles.

#### 🎲 Lotto (<70%)
- Achane 5+ receptions — boom/bust usage.
- Wilson 80+ yards — dependent on game staying competitive.

---

### 🎯 Suggested Slips

**Slip 1 — Super Lock Foundation**
- Garrett Wilson 4+ recs
- Waddle 3+ recs
- Achane 30+ rush yds

**Slip 2 — Standard Lock Correlation**
- Tyreek Hill 50+ yds
- Fields 35+ rush yds
- Garrett Wilson 60+ yds

**Slip 3 — Lotto**
- Achane 5+ recs
- Tyreek Hill 80+ yds
- Garrett Wilson 80+ yds
- Fields 50+ rush yds

---

### ⚠️ Framework Flags
- Tyreek Hill → Weather + potential shadow coverage = not safe for Super Locks.
- Questionables excluded from all Super Lock slips.
- Avoid RB receiving yards as standalone (too much variance).

---

✅ With this Judge Protocol v5.0, you now have:
- A template prompt (ruleset).
- A single-shot example (correct output format).

Any AI can follow this consistently if you paste both at the start of a session.