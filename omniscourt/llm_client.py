"""
OMNIS-COURT LLM Client
จัดการการเชื่อมต่อกับ Qwen3-14B ผ่าน Cloudflare Tunnel

รองรับ 5 Rounds ของ Agentic Workflow:
- Round A: plan_searches() - วางแผนค้นหา
- Round C: analyze_and_generate() - วิเคราะห์ + Generate code
- Round E: final_verdict() - ฟันธง
"""

import json
import requests
import re
from typing import List, Dict, Optional, Tuple


class LLMClient:
    """
    Client สำหรับสื่อสารกับ Qwen3-14B LLM
    
    หน้าที่:
    - เชื่อมต่อ API ของ Qwen3-14B (ผ่าน Cloudflare Tunnel)
    - ส่ง prompts และรับ responses
    - รองรับ 5 rounds ของ Agentic Workflow
    """
    
    def __init__(self, config_path: str = "config/platforms.json"):
        """
        Initialize LLM Client
        
        Args:
            config_path: path ไปยังไฟล์ config
        """
        # โหลด config
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # ดึง LLM API URL จาก config
        self.llm_api_url = self.config['omnis_court']['llm_api_url']
        
        print(f"✅ LLMClient initialized")
        print(f"   API URL: {self.llm_api_url}")
    
    def call_qwen(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> Optional[str]:
        """
        เรียก Qwen3-14B API
        
        Args:
            prompt: ข้อความที่จะส่งให้ LLM
            max_tokens: จำนวน tokens สูงสุดที่ LLM จะ generate
            temperature: ความสร้างสรรค์ (0 = deterministic, 1 = creative)
        
        Returns:
            ข้อความตอบกลับจาก LLM (หรือ None ถ้า error)
        """
        # สร้าง API endpoint
        url = f"{self.llm_api_url}/chat/completions"
        
        # สร้าง headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # สร้าง payload
        payload = {
            "model": "qwen3-14b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            # ส่ง POST request ไปยัง Qwen3-14B API
            print(f"📤 Calling Qwen3-14B API...")
            response = requests.post(url, headers=headers, json=payload, timeout=600)
            response.raise_for_status()
            
            # แปลง response จาก JSON เป็น Python dictionary
            data = response.json()
            
            # ดึงข้อความตอบกลับ
            reply = data['choices'][0]['message']['content']
            
            print(f"✅ Received response ({len(reply)} characters)")
            return reply
            
        except requests.exceptions.Timeout:
            print(f"❌ Request timeout (>600 seconds)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"❌ Invalid response format: {e}")
            return None
    
    def plan_searches(self, prompt_v7_1: str, match_info: Dict) -> List[str]:
        """
        Round A: LLM วางแผนค้นหา
        
        Args:
            prompt_v7_1: Prompt v7.1 ตัวเต็ม
            match_info: ข้อมูลแมตช์ (player_a, player_b, tournament, etc.)
        
        Returns:
            list ของ search queries (50+ queries)
        """
        # สร้าง prompt สำหรับ Round A
        planning_prompt = f"""
{prompt_v7_1}

═══════════════════════════════════════════════════════════════
ROUND A: SEARCH PLANNING
═══════════════════════════════════════════════════════════════

Match Information:
- Player A: {match_info['player_a']}
- Player B: {match_info['player_b']}
- Tournament: {match_info.get('tournament', 'Unknown')}
- Surface: {match_info.get('surface', 'Unknown')}
- Match Type: {match_info.get('match_type', 'singles')}

Your Task:
Based on Section 2.1 (4-Layer Search Cascade) of the prompt above, generate a COMPREHENSIVE list of search queries to gather all necessary data for analysis.

Requirements:
1. Generate AT LEAST 50 distinct search queries
2. Cover ALL 6 Tiers of data excavation
3. Include searches in multiple languages (English + Native languages of players)
4. For Doubles: include partnership-specific queries

Output Format:
Return ONLY a JSON array of search queries. No explanations, no markdown.

Example:
[
  "[Player A] injury update 2026",
  "[Player A] vs [Player B] head to head",
  "[Player A] serve statistics 2026",
  ...
]
"""
        
        print(f"\n🎯 Round A: Planning searches...")
        response = self.call_qwen(planning_prompt, max_tokens=4096, temperature=0.3)
        
        if not response:
            print(f"❌ Failed to get search plan")
            return []
        
        # Parse JSON response
        try:
            # ลอง parse เป็น JSON โดยตรง
            search_queries = json.loads(response)
            if isinstance(search_queries, list):
                print(f"✅ Generated {len(search_queries)} search queries")
                return search_queries
        except json.JSONDecodeError:
            # ถ้า parse ไม่ได้ ลอง extract JSON จาก response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    search_queries = json.loads(json_match.group())
                    print(f"✅ Generated {len(search_queries)} search queries (extracted)")
                    return search_queries
                except:
                    pass
        
        # Fallback: แยกบรรทัด
        print(f"⚠️ Could not parse JSON, falling back to line-by-line")
        queries = [line.strip() for line in response.split('\n') if line.strip() and not line.strip().startswith('#')]
        print(f"✅ Generated {len(queries)} search queries (fallback)")
        return queries
    
    def analyze_and_generate(self, prompt_v7_1: str, search_report: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Round C: วิเคราะห์ข้อมูล + Generate Python code
        
        Args:
            prompt_v7_1: Prompt v7.1 ตัวเต็ม
            search_report: รายงานผลการค้นหา (รวมจาก 50+ searches)
        
        Returns:
            (parameters_dict, python_code_string) หรือ (None, None) ถ้า error
        """
        # สร้าง prompt สำหรับ Round C
        analysis_prompt = f"""
{prompt_v7_1}

═══════════════════════════════════════════════════════════════
ROUND C: ANALYSIS + CODE GENERATION
═══════════════════════════════════════════════════════════════

Search Report (Results from 50+ searches):
───────────────────────────────────────────
{search_report}
───────────────────────────────────────────

Your Task:
1. Analyze all search results thoroughly (Section 2-6)
2. Translate qualitative data into 17 numerical parameters (Section 7)
3. Generate production-grade Python code for Monte Carlo simulation (Section 8)

Requirements:
- Follow ALL directives in the prompt above
- Use the EXACT 17-parameter structure
- Generate COMPLETE Python code (no abbreviations)
- Include ALL sections in your analysis

Output Format:
Return TWO parts separated by "=====PYTHON_CODE=====":

PART 1: Your analysis (Sections 1-7) in markdown format
=====PYTHON_CODE=====
PART 2: Complete Python code block (Section 8)

The Python code must be executable and include:
- All data structures (SinglesPlayer, DoublesTeam, etc.)
- Both SinglesMatchSimulator and DoublesMatchSimulator
- match_parameters dictionary with REAL values (not 0.0)
- compress_raw_data() function
- print_json_output() function
- Main execution block
"""
        
        print(f"\n🎯 Round C: Analyzing + Generating code...")
        response = self.call_qwen(analysis_prompt, max_tokens=16384, temperature=0.5)
        
        if not response:
            print(f"❌ Failed to get analysis")
            return None, None
        
        # แยก analysis กับ code
        if "=====PYTHON_CODE=====" in response:
            parts = response.split("=====PYTHON_CODE=====")
            analysis = parts[0].strip()
            python_code = parts[1].strip()
        else:
            # ลองหา code block แบบ ```python ... ```
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                python_code = code_match.group(1)
                analysis = response[:code_match.start()].strip()
            else:
                print(f"⚠️ Could not separate analysis and code")
                analysis = response
                python_code = None
        
        # Extract parameters จาก analysis (ถ้ามี)
        parameters = None
        param_match = re.search(r'```json\s*(.*?)\s*```', analysis, re.DOTALL)
        if param_match:
            try:
                parameters = json.loads(param_match.group(1))
                print(f"✅ Extracted parameters from analysis")
            except:
                pass
        
        print(f"✅ Analysis length: {len(analysis)} characters")
        if python_code:
            print(f"✅ Python code length: {len(python_code)} characters")
        
        return parameters, python_code
    
    def final_verdict(self, prompt_v7_1: str, simulation_json: Dict) -> Optional[Dict]:
        """
        Round E: ฟันธงจาก Monte Carlo results
        
        Args:
            prompt_v7_1: Prompt v7.1 ตัวเต็ม
            simulation_json: JSON จาก Monte Carlo simulation
        
        Returns:
            verdict dictionary หรือ None ถ้า error
        """
        # สร้าง prompt สำหรับ Round E
        verdict_prompt = f"""
{prompt_v7_1}

═══════════════════════════════════════════════════════════════
ROUND E: FINAL VERDICT
═══════════════════════════════════════════════════════════════

Monte Carlo Simulation Results (10,000 iterations):
────────────────────────────────────────────────────
{json.dumps(simulation_json, indent=2, ensure_ascii=False)}
────────────────────────────────────────────────────

Your Task:
Execute Round 2 analysis (Section 9-10 of the prompt):
1. Ingest raw JSON data
2. Vacuum Analysis (Line Quarantine)
3. Option Crucible Matrix
4. Apex Selection
5. In-Play Trigger Matrix
6. Final Directive

Requirements:
- Follow ALL directives in Section 9-10
- Use the EXACT output topology
- Provide actionable betting recommendations
- Include risk warnings and confidence levels

Output Format:
Return a JSON object with this structure:
{{
  "match_type": "singles/doubles",
  "vacuum_analysis": {{
    "dominant_patterns": [...],
    "key_risks": [...]
  }},
  "option_crucible": [
    {{
      "option": "...",
      "true_hit_probability": 0.XX,
      "edge": "+X.X%",
      "status": "RESILIENT/MODERATE/FRAGILE",
      "reasoning": "..."
    }}
  ],
  "apex_pick": {{
    "option": "...",
    "probability": 0.XX,
    "bet_sizing": "X units",
    "confidence": "HIGH/MEDIUM/LOW",
    "most_likely_path": "...",
    "backup_paths": [...],
    "risk_warning": "..."
  }},
  "in_play_triggers": [
    {{
      "trigger": "...",
      "action": "BUY/SELL/ABORT",
      "reasoning": "..."
    }}
  ],
  "final_directive": {{
    "recommendation": "...",
    "summary": "..."
  }}
}}

Return ONLY the JSON object, no markdown, no explanations.
"""
        
        print(f"\n🎯 Round E: Generating final verdict...")
        response = self.call_qwen(verdict_prompt, max_tokens=8192, temperature=0.4)
        
        if not response:
            print(f"❌ Failed to get verdict")
            return None
        
        # Parse JSON response
        try:
            verdict = json.loads(response)
            print(f"✅ Final verdict generated")
            return verdict
        except json.JSONDecodeError:
            # ลอง extract JSON จาก response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    verdict = json.loads(json_match.group())
                    print(f"✅ Final verdict extracted")
                    return verdict
                except:
                    pass
        
        print(f"⚠️ Could not parse verdict as JSON")
        return None


# ========================================
# TEST FUNCTION
# ========================================

if __name__ == "__main__":
    print("="*70)
    print("🧪 OMNIS-COURT LLM Client Test Suite")
    print("="*70)
    
    # สร้าง LLMClient instance
    client = LLMClient()
    
    # Test 1: Basic API call
    print("\n" + "─"*70)
    print("Test 1: Basic API Call")
    print("─"*70)
    test_prompt = "Hello! Please respond with 'OK' if you can read this."
    response = client.call_qwen(test_prompt, max_tokens=50, temperature=0.1)
    
    if response:
        print(f"✅ Test 1 PASSED")
        print(f"   Response: {response[:100]}...")
    else:
        print(f"❌ Test 1 FAILED")
        print(f"   Check: Colab running? URL correct?")
    
    # Test 2: Plan searches (mock)
    print("\n" + "─"*70)
    print("Test 2: Plan Searches (Mock)")
    print("─"*70)
    
    mock_prompt_v7_1 = """
    [SYSTEM PROMPT v7.1 - Abbreviated for testing]
    You are OMNIS-COURT v7.1, a tennis analytics engine.
    Section 2.1: Generate 50+ search queries covering 6 tiers.
    """
    
    mock_match_info = {
        "player_a": "Alcaraz",
        "player_b": "Sinner",
        "tournament": "US Open 2026",
        "surface": "Hard",
        "match_type": "singles"
    }
    
    queries = client.plan_searches(mock_prompt_v7_1, mock_match_info)
    
    if queries and len(queries) > 0:
        print(f"✅ Test 2 PASSED")
        print(f"   Generated {len(queries)} queries")
        print(f"   Sample: {queries[0] if queries else 'N/A'}")
    else:
        print(f"❌ Test 2 FAILED")
    
    print("\n" + "="*70)
    print("✅ Test suite completed!")
    print("="*70)
