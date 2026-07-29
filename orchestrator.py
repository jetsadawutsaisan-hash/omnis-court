"""
OMNIS-COURT Orchestrator v3.0 - TRUE AGENTIC
Think-Act-Observe pattern for all rounds
"""

import json
import re
from typing import Dict, List, Optional, Callable
from llm_client import LLMClient
from search_client import SearchClient
from monte_carlo import MonteCarloExecutor
from prompt_v7_1 import PROMPT_V7_1, ROUND_A_PLANNING, ROUND_C_ANALYSIS, ROUND_E_VERDICT


class Orchestrator:
    """ควบคุม workflow ทั้งหมด (6 Rounds)"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.search = SearchClient()
        self.executor = MonteCarloExecutor(num_iterations=10000)
    
    def analyze_match(self, match_info: Dict, progress_callback: Callable = None,
                     skip_tournament_detection: bool = False) -> Optional[Dict]:
        """วิเคราะห์แมตช์ (Round 0 + Round A-E)"""
        
        def notify(round_name, message):
            if progress_callback:
                progress_callback(round_name, message)
            print(f"[{round_name}] {message}")
        
        try:
            # ═══ ROUND 0: Auto-Detect Tournament (True Agentic) ═══
            if not skip_tournament_detection:
                has_tournament = match_info.get('tournament') and match_info['tournament'].strip()
                has_surface = match_info.get('surface') and match_info['surface'] not in ['Unknown', '', None]
                
                if has_tournament and has_surface:
                    notify("Round 0", "⏭️ Tournament context already provided, skipping")
                else:
                    notify("Round 0", "🔍 True Agentic tournament detection...")
                    match_info = self._round_0_detect_tournament(match_info, progress_callback)
                    
                    if match_info.get('_tournament_detected'):
                        notify("Round 0", f"✅ Detected: {match_info.get('tournament')} "
                                         f"(confidence: {match_info.get('tournament_confidence', 'LOW')})")
                    else:
                        notify("Round 0", "⚠️ Tournament detection failed, using defaults")
            else:
                notify("Round 0", "⏭️ Skipped by user")
            
            # ═══ ROUND A: Planning (True Agentic) ═══
            notify("Round A", "🎯 LLM planning 50+ search queries...")
            queries = self._round_a_plan(match_info)
            
            if not queries:
                notify("Round A", "❌ Failed to generate queries")
                return None
            
            notify("Round A", f"✅ Generated {len(queries)} queries")
            
            # ═══ ROUND B: Search & Extract ═══
            notify("Round B", "🔍 Searching + Extracting ALL content...")
            search_report = self._round_b_search(queries, progress_callback)
            
            if not search_report or len(search_report) < 500:
                notify("Round B", "⚠️ Search report too short")
                return None
            
            notify("Round B", f"✅ Search report: {len(search_report)} chars")
            
            # ═══ ROUND C: Analysis + Code Gen (with Chain-of-Thought) ═══
            notify("Round C", "🧠 Analyzing + Generating code (with reasoning)...")
            reasoning, python_code = self._round_c_analyze(search_report, match_info)
            
            if not python_code:
                notify("Round C", "❌ Failed to generate code")
                return None
            
            notify("Round C", f"✅ Code: {len(python_code)} chars, Reasoning: {len(reasoning or '')} chars")
            
            # ═══ ROUND D: Monte Carlo Execution ═══
            notify("Round D", "🎲 Running 10,000 simulations...")
            simulation_json = self._round_d_simulate(python_code)
            
            if not simulation_json:
                notify("Round D", "❌ Simulation failed")
                return None
            
            notify("Round D", f"✅ Simulations: {simulation_json.get('N', 0)}")
            
            # ═══ ROUND E: Final Verdict ═══
            notify("Round E", "⚖️ Generating final verdict...")
            verdict = self._round_e_verdict(simulation_json, match_info)
            
            if not verdict:
                notify("Round E", "❌ Failed to generate verdict")
                return None
            
            notify("Round E", "✅ Verdict generated!")
            
            # Metadata
            verdict['_metadata'] = {
                'queries_count': len(queries),
                'search_report_length': len(search_report),
                'python_code_length': len(python_code),
                'reasoning_length': len(reasoning or ''),
                'reasoning': reasoning,
                'simulations': simulation_json.get('N', 0),
                'match_info': match_info
            }
            
            return verdict
            
        except Exception as e:
            notify("Error", f"❌ Orchestrator failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _round_0_detect_tournament(self, match_info: Dict, progress_callback=None) -> Dict:
        """Round 0: True Agentic Tournament Detection"""
        
        def detect_progress(current, total, message):
            if progress_callback:
                progress_callback("Round 0", message)
        
        detected = self.search.detect_tournament(
            player_a=match_info.get('player_a', ''),
            player_b=match_info.get('player_b', ''),
            max_retries=3,
            progress_callback=detect_progress,
            llm_client=self.llm
        )
        
        if detected:
            enriched = match_info.copy()
            enriched['tournament'] = detected.get('tournament') or match_info.get('tournament') or 'Unknown'
            enriched['surface'] = detected.get('surface') or match_info.get('surface') or 'Hard'
            enriched['round'] = detected.get('round', 'Unknown')
            enriched['court'] = detected.get('court', 'Unknown')
            enriched['court_speed'] = detected.get('court_speed')
            enriched['ball'] = detected.get('ball', 'Unknown')
            enriched['weather'] = detected.get('weather', {})
            enriched['tournament_confidence'] = detected.get('confidence', 'LOW')
            enriched['_tournament_detected'] = True
            enriched['_source_urls'] = detected.get('source_urls', [])
            enriched['_detect_attempt'] = detected.get('attempt', 0)
            enriched['_total_searches'] = detected.get('total_searches', 0)
            enriched['_total_articles'] = detected.get('total_articles', 0)
            return enriched
        
        match_info['_tournament_detected'] = False
        return match_info
    
    def _round_a_plan(self, match_info: Dict) -> List[str]:
        """Round A: True Agentic Planning (50+ queries)"""
        prompt = f"""
{PROMPT_V7_1}

{ROUND_A_PLANNING}

Match Information:
- Player A: {match_info.get('player_a', 'Unknown')}
- Player B: {match_info.get('player_b', 'Unknown')}
- Tournament: {match_info.get('tournament', 'Unknown')}
- Surface: {match_info.get('surface', 'Unknown')}
- Round: {match_info.get('round', 'Unknown')}
- Court: {match_info.get('court', 'Unknown')}
- HC Line A: {match_info.get('hc_line_a', 'N/A')}
- HC Line B: {match_info.get('hc_line_b', 'N/A')}
- O/U Line: {match_info.get('ou_line', 'N/A')}
"""
        
        response = self.llm.call_qwen(prompt, max_tokens=4096, temperature=0.3)
        if not response:
            return []
        
        # Parse JSON array
        try:
            queries = json.loads(response)
            if isinstance(queries, list):
                return [q for q in queries if isinstance(q, str)]
        except:
            pass
        
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                queries = json.loads(json_match.group())
                return [q for q in queries if isinstance(q, str)]
            except:
                pass
        
        # Fallback
        return [line.strip().strip('"').strip("'") for line in response.split('\n')
                if line.strip() and not line.strip().startswith('#')][:50]
    
    def _round_b_search(self, queries: List[str], progress_callback=None) -> str:
        """Round B: Search + Extract"""
        max_queries = min(len(queries), 50)
        selected_queries = queries[:max_queries]
        
        def search_progress(current, total, message):
            if progress_callback:
                progress_callback("Round B", f"[{current}/{total}] {message}")
        
        return self.search.research_queries(
            selected_queries,
            max_articles_per_query=2,
            progress_callback=search_progress
        )
    
    def _round_c_analyze(self, search_report: str, match_info: Dict):
        """Round C: Analysis + Code Gen (with Chain-of-Thought)"""
        prompt = f"""
{PROMPT_V7_1}

{ROUND_C_ANALYSIS}

Match Information:
- Player A: {match_info.get('player_a')}
- Player B: {match_info.get('player_b')}
- Tournament: {match_info.get('tournament')}
- Surface: {match_info.get('surface')}
- Round: {match_info.get('round', 'Unknown')}
- Court: {match_info.get('court', 'Unknown')}
- Court Speed: {match_info.get('court_speed', 'Unknown')}
- Ball: {match_info.get('ball', 'Unknown')}
- Weather: {match_info.get('weather', {})}

User's Betting Lines:
- HC Line A: {match_info.get('hc_line_a')}
- HC Line B: {match_info.get('hc_line_b')}
- O/U Line: {match_info.get('ou_line')}

Options to Evaluate:
1. Player A - HC Line A ({match_info.get('hc_line_a')})
2. Player B - HC Line B ({match_info.get('hc_line_b')})
3. Over {match_info.get('ou_line')}
4. Under {match_info.get('ou_line')}

SEARCH REPORT:
───────────────────────────────────────────
{search_report[:30000]}
───────────────────────────────────────────
"""
        
        response = self.llm.call_qwen(prompt, max_tokens=16384, temperature=0.5)
        if not response:
            return "", None
        
        # Parse Chain-of-Thought + Code
        reasoning = ""
        python_code = None
        
        if "=====PYTHON_CODE=====" in response:
            parts = response.split("=====PYTHON_CODE=====")
            reasoning = parts[0].strip()
            python_code = parts[1].strip()
        else:
            # Fallback: code block
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                python_code = code_match.group(1)
                reasoning = response[:code_match.start()].strip()
            else:
                reasoning = response
                python_code = None
        
        # Clean reasoning (remove "REASONING:" prefix if present)
        if reasoning:
            if reasoning.startswith("REASONING"):
                reasoning = reasoning[9:].strip()
                if reasoning.startswith(":"):
                    reasoning = reasoning[1:].strip()
        
        # Clean code
        if python_code:
            python_code = python_code.replace('```python', '').replace('```', '').strip()
        
        return reasoning, python_code
    
    def _round_d_simulate(self, python_code: str) -> Optional[Dict]:
        """Round D: Execute simulation"""
        return self.executor.execute(python_code)
    
    def _round_e_verdict(self, simulation_json: Dict, match_info: Dict) -> Optional[Dict]:
        """Round E: Final verdict"""
        prompt = f"""
{PROMPT_V7_1}

{ROUND_E_VERDICT}

Match Information:
- Player A: {match_info.get('player_a')}
- Player B: {match_info.get('player_b')}
- Tournament: {match_info.get('tournament')}
- Surface: {match_info.get('surface')}
- Round: {match_info.get('round', 'Unknown')}

User's Betting Lines (MUST evaluate ALL):
- Option 1: Player A HC {match_info.get('hc_line_a')}
- Option 2: Player B HC {match_info.get('hc_line_b')}
- Option 3: Over {match_info.get('ou_line')} total games
- Option 4: Under {match_info.get('ou_line')} total games

MONTE CARLO SIMULATION RESULTS:
───────────────────────────────────────────
{json.dumps(simulation_json, indent=2, ensure_ascii=False)}
───────────────────────────────────────────
"""
        
        response = self.llm.call_qwen(prompt, max_tokens=8192, temperature=0.4)
        if not response:
            return None
        
        try:
            verdict = json.loads(response)
            return verdict
        except:
            pass
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return {"raw_response": response}
