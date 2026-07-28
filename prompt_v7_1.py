# ==========================================
# ROUND A: True Agentic Planning (แก้ใหม่ - ไม่มี placeholder, ไม่ต้อง escape)
# ==========================================
ROUND_A_PLANNING = """
## YOUR TASK: PLAN 50+ SEARCH QUERIES (TRUE AGENTIC)

You are the BRAIN of OMNIS-COURT. Your job is to PLAN what to search for.
DO NOT use generic/hardcoded queries. Think dynamically based on THIS specific match.

## THINK FIRST:
1. What makes THIS match unique? (surface, tournament level, player styles)
2. What information gaps do I have? (injury status, recent form, H2H)
3. What languages should I search in? (player nationality, host country)
4. What sources are most credible for THIS tournament? (official site, local news)

## PLAN 50+ QUERIES ACROSS 4 LAYERS:

### Layer 1: Mainstream English (10+ queries)
- Player stats, H2H, recent form, tournament draw
- Serve/return/break point stats
- Rally length, net play frequency

### Layer 2: Native Language (8+ queries)
- Translate keywords to player's native language
- Query local portals: Sport Klub (Serbian), Nikkan Sports (JP), L'Équipe (FR), Marca (ES), etc.
- Look for interviews, press conferences, local news

### Layer 3: Social Forensics (8+ queries)
- Twitter/X mentions, Instagram practice footage
- Reddit discussions, specialist forums
- TikTok/YouTube fan-recorded clips

### Layer 4: Tangential Pivot (6+ queries)
- Flight tracking, weather archives
- Coach interviews, hitting partner info
- Equipment changes, sponsor activity

## OUTPUT FORMAT:
Return ONLY a JSON array of strings (no markdown, no explanations):
[
  "query 1",
  "query 2",
  ...
  "query 50+"
]

## RULES:
- Minimum 50 queries total
- Must cover all 4 layers
- Must include at least 3 languages
- Queries must be SPECIFIC to this match (not generic)
- Return ONLY JSON array, no other text
"""

# ==========================================
# ROUND C: Analysis + Chain-of-Thought (ไม่มี placeholder)
# ==========================================
ROUND_C_ANALYSIS = """
## YOUR TASK: ANALYZE SEARCH REPORT + GENERATE SIMULATION CODE

You must prove you THINK deeply before generating code.

## OUTPUT FORMAT (MUST FOLLOW EXACTLY):

REASONING (200-400 words):
- Briefly explain your analysis logic
- List the KEY parameters you extracted (top 5-7)
- Justify your most critical parameter values
- Note any DATA VOIDS or CONTRADICTIONS found
- Explain how surface/tournament context affects parameters

=====PYTHON_CODE=====
[Your complete, runnable Python simulation code here]

## RULES:
1. REASONING section: 200-400 words (PROVE you thought deeply)
2. =====PYTHON_CODE===== marker: MUST be EXACT (case-sensitive)
3. Code section: Complete, runnable, uses the 17-parameter structure
4. Do NOT include ```python or ``` markers
5. Code must handle the specific match_type (singles/doubles) correctly
"""

# ==========================================
# ROUND E: Final Verdict (ESCAPED)
# ==========================================
ROUND_E_VERDICT = """
## YOUR TASK: SYNTHESIZE SIMULATION RESULTS INTO APEX VERDICT

Analyze the Monte Carlo simulation results and produce the final betting verdict.

## REQUIRED OUTPUT FORMAT (JSON):
{{
  "option_crucible": [
    {{
      "option": "option name",
      "true_hit_probability": 0.XX,
      "status": "PASS/FAIL",
      "reasoning": "detailed path analysis"
    }}
  ],
  "apex_pick": {{
    "option": "best option",
    "probability": 0.XX,
    "confidence": "HIGH/MEDIUM/LOW",
    "bet_sizing": "1-5 units",
    "most_likely_path": "description",
    "risk_warning": "key risks"
  }},
  "in_play_triggers": [],
  "final_verdict": "summary"
}}

## QUALITY GATE:
- Probability must be >= 0.60 to PASS
- Apex pick must have clear reasoning
- All options must be evaluated
"""

# ==========================================
# PHASE 0: ROUND_0_PLAN (ESCAPED, เก็บ placeholders ไว้)
# ==========================================
ROUND_0_PLAN = """
## YOUR TASK: PLAN TOURNAMENT DETECTION STRATEGY

You are planning how to find the TOURNAMENT CONTEXT for a specific tennis match.

## INPUT:
- Player A: {player_a}
- Player B: {player_b}
- Current date: {current_date}
- Previous attempt feedback: {previous_feedback}

## THINK:
1. What tournament level are these players likely playing? (Grand Slam? ATP 1000? 250? Challenger?)
2. What time of year is it? Which tournaments happen NOW?
3. If previous attempt failed, what went wrong? Try different angles.

## PLAN 8-12 SMART QUERIES across these categories:

### Category A: Direct Match Search
- "[Player A] vs [Player B] [current month] [current year]"
- "[Tournament name] draw [current year]"
- "ATP/WTA schedule this week"

### Category B: Tournament Calendar
- "ATP tournaments [current month] [current year]"
- "WTA events this week"
- "tennis schedule [current date]"

### Category C: Player Current Status
- "[Player A] current tournament [current month]"
- "[Player B] playing this week"
- "[Player A] latest news"

### Category D: Multilingual (if previous failed)
- Translate key terms to player's native language
- Query local sports portals

### Category E: Social/News
- "[Player A] twitter tournament"
- "[Player A] instagram practice"
- "ATP news [current date]"

## OUTPUT FORMAT:
Return ONLY a JSON object:
{{
  "reasoning": "brief explanation of your strategy (50-100 words)",
  "queries": [
    "query 1",
    "query 2",
    "query 8-12"
  ],
  "focus_areas": ["tournament", "surface", "round", "court"],
  "expected_sources": ["ATP official", "ESPN", "local news"]
}}

## RULES:
- 8-12 queries (not too many, focused)
- Must be SPECIFIC to current date and players
- If previous attempt failed, try COMPLETELY DIFFERENT angles
- Return ONLY JSON, no markdown
"""

# ==========================================
# PHASE 0: ROUND_0_OBSERVE (ESCAPED, เก็บ placeholders ไว้)
# ==========================================
ROUND_0_OBSERVE = """
## YOUR TASK: DETECT TOURNAMENT CONTEXT FROM SEARCH RESULTS

You are a TENNIS TOURNAMENT DETECTIVE. Analyze the search results and extract tournament context.

## INPUT:
- Player A: {player_a}
- Player B: {player_b}
- Current date: {current_date}
- Search report (full articles): {search_report}

## EXTRACT THESE FIELDS:
1. **tournament**: Full tournament name with year (e.g., "Hamburg European Open 2026")
2. **surface**: Clay / Hard / Grass / Indoor Hard / Indoor Carpet
3. **round**: R128 / R64 / R32 / R16 / QF / SF / F / RR
4. **court**: Specific court name if found (e.g., "Center Court", "Court 1")
5. **court_speed**: Float 1.0-4.0 (1.8=Roland Garros slow clay, 2.5=medium hard, 3.8=Wimbledon fast grass)
6. **ball**: Ball brand (Dunlop ATP, Penn, Slazenger, Head, Wilson)
7. **weather**: temp (int), humidity (int), wind (int km/h), condition (sunny/cloudy/rainy)
8. **confidence**: HIGH / MEDIUM / LOW
9. **evidence**: 1-2 sentences explaining WHY you believe this
10. **match_time**: ISO datetime if found (e.g., "2026-07-29T15:30:00")
11. **source_urls**: List of URLs where you found this info (top 3-5)

## CONFIDENCE RULES:
- **HIGH**: Tournament name + round + surface confirmed by 2+ official sources (ATP/WTA)
- **MEDIUM**: Tournament name found but some details uncertain
- **LOW**: Only guessing, tournament name NOT confirmed → set tournament to null

## COURT SPEED REFERENCE:
- Roland Garros (Clay): 1.8
- Monte Carlo (Clay): 2.0
- Rome (Clay): 2.2
- Hamburg (Clay): 2.2
- Indian Wells (Hard): 2.7
- Australian Open (Hard): 2.7
- US Open (Hard): 2.9
- Cincinnati (Hard): 3.0
- Wimbledon (Grass): 3.8
- Halle (Grass): 3.7

## OUTPUT FORMAT:
Return ONLY JSON (no markdown):
{{
  "tournament": "...",
  "surface": "...",
  "round": "...",
  "court": "...",
  "court_speed": 0.0,
  "ball": "...",
  "weather": {{"temp": 0, "humidity": 0, "wind": 0, "condition": "..."}},
  "confidence": "HIGH/MEDIUM/LOW",
  "evidence": "...",
  "match_time": "...",
  "source_urls": ["..."]
}}

## RULES:
- If tournament NOT clearly found → confidence=LOW, tournament=null
- Use realistic court_speed values from reference
- Return ONLY JSON
"""

# ==========================================
# PHASE 0: ROUND_0_RETRY (ESCAPED, เก็บ placeholders ไว้)
# ==========================================
ROUND_0_RETRY = """
## YOUR TASK: LEARN FROM FAILURE AND PLAN NEW STRATEGY

Previous attempt to find tournament context FAILED. You must adapt.

## INPUT:
- Player A: {player_a}
- Player B: {player_b}
- Attempt number: {attempt_number} / {max_attempts}
- Previous strategy: {previous_strategy}
- Previous results summary: {previous_results}
- Why it failed: {failure_reason}

## THINK CRITICALLY:
1. Why did previous attempt fail?
   - Wrong tournament level?
   - Wrong language?
   - Players not actually playing this week?
   - Match is in future/past?
2. What COMPLETELY DIFFERENT angles should I try?
3. Should I check if players are INJURED or NOT PLAYING this week?

## NEW STRATEGY CATEGORIES (pick 2-3 that are DIFFERENT from before):

### A. Negative Search (Check if NOT playing)
- "[Player A] withdraw [current month]"
- "[Player A] injury update"
- "[Player B] schedule break"

### B. Tournament Level Pivot
- If searched ATP 1000, try ATP 250/Challenger
- If searched Singles, try Doubles
- Check if players are in different tournaments

### C. Language Pivot
- Use completely different language
- Query local portals of host country

### D. Social Intelligence
- Instagram/Twitter latest posts
- Coach interviews
- Fan sightings

### E. Future/Past Check
- "[Player A] next tournament after [recent tournament]"
- "tennis calendar [next month]"

## OUTPUT FORMAT:
Return ONLY JSON:
{{
  "failure_analysis": "why previous attempt failed (50-100 words)",
  "new_strategy": "description of new approach",
  "queries": ["8-12 NEW queries"],
  "focus_shift": "what to focus on differently"
}}

## RULES:
- Queries MUST be COMPLETELY DIFFERENT from previous attempt
- Consider that players might NOT be playing this week
- Return ONLY JSON
"""

# ==========================================
# FIND UPCOMING: PLAN (ESCAPED, เก็บ placeholders ไว้)
# ==========================================
FIND_UPCOMING_PLAN = """
## YOUR TASK: PLAN SEARCH FOR UPCOMING TENNIS MATCHES

Find tennis matches scheduled in the NEXT 2 HOURS from now.

## INPUT:
- Current datetime: {current_datetime}
- Timezone: {timezone}

## THINK:
1. What time is it now? What 2-hour window am I looking at?
2. Which tournaments are currently running? (ATP, WTA, Challenger, ITF)
3. What sources have live schedules? (ATP official, Tennis Abstract, FlashScore, Sofascore)

## PLAN 10-15 QUERIES:

### Category A: Live Schedule Sources
- "ATP matches today [current date]"
- "WTA schedule today"
- "tennis order of play [current date]"
- "live tennis matches now"

### Category B: Tournament-Specific
- "[current tournament name] schedule today"
- "[current tournament name] order of play"
- "tennis draw today [current date]"

### Category C: Score Sites
- "FlashScore tennis today"
- "Sofascore tennis upcoming"
- "Tennis Abstract matches today"
- "ESPN tennis schedule"

### Category D: News/Social
- "tennis matches starting soon"
- "live tennis twitter"
- "tennis starting next hour"

## OUTPUT FORMAT:
Return ONLY JSON:
{{
  "time_window": "HH:MM - HH:MM [timezone]",
  "active_tournaments": ["tournament 1", "tournament 2"],
  "queries": [
    "query 1",
    "query 2"
  ],
  "priority_sources": ["ATP official", "FlashScore"]
}}

## RULES:
- 10-15 focused queries
- Must include live schedule sources
- Return ONLY JSON
"""

# ==========================================
# FIND UPCOMING: OBSERVE (ESCAPED, เก็บ placeholders ไว้)
# ==========================================
FIND_UPCOMING_OBSERVE = """
## YOUR TASK: FIND MATCHES STARTING IN NEXT 2 HOURS

Analyze the search results and find tennis matches starting within 2 hours.

## INPUT:
- Current datetime: {current_datetime}
- Timezone: {timezone}
- Search report: {search_report}

## FOR EACH MATCH FOUND, EXTRACT:
1. player_a: Player 1 name
2. player_b: Player 2 name (or team for doubles)
3. tournament: Tournament name
4. surface: Clay/Hard/Grass
5. round: R128/R64/.../SF/F
6. scheduled_time: ISO datetime (YYYY-MM-DDTHH:MM:SS)
7. court: Court name if available
8. match_type: "singles" or "doubles"
9. source_url: Where you found this info
10. confidence: HIGH/MEDIUM/LOW

## TIME WINDOW CHECK:
- Current time: {current_datetime}
- Target window: next 2 hours
- ONLY include matches STARTING in this window

## OUTPUT FORMAT:
Return ONLY JSON:
{{
  "matches_found": [
    {{
      "player_a": "...",
      "player_b": "...",
      "tournament": "...",
      "surface": "...",
      "round": "...",
      "scheduled_time": "YYYY-MM-DDTHH:MM:SS",
      "court": "...",
      "match_type": "singles/doubles",
      "source_url": "...",
      "confidence": "HIGH/MEDIUM/LOW"
    }}
  ],
  "total_found": 0,
  "time_window_checked": "HH:MM - HH:MM",
  "best_match": null,
  "reasoning": "brief explanation of selection"
}}

## RULES:
- ONLY matches STARTING in next 2 hours
- If no matches found, best_match=null, total_found=0
- Pick best_match based on: tournament level > confidence > data completeness
- Return ONLY JSON
"""
