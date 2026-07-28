"""
OMNIS-COURT Search Client v3.0 - TRUE AGENTIC
LLM-Driven Search Pipeline: LLM (Brain) → SearXNG (Scout) → Jina (Analyst) → LLM (Decide)
"""

import json
import requests
import time
import re
from typing import List, Dict, Optional, Callable
from urllib.parse import quote
from datetime import datetime, timedelta
import trafilatura


class SearchClient:
    """True Agentic Search Client"""
    
    def __init__(self, config_path: str = "config/platforms.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.searxng_url = self.config['search_engine']['searxng_url']
        self.jina_url = self.config['omnis_court']['jina_reader_url']
    
    # ==========================================
    # CORE TOOLS: SEARCH + EXTRACT
    # ==========================================
    
    def search_searxng(self, query: str, num_results: int = 80) -> List[Dict]:
        """SearXNG over-fetch (Scout)"""
        search_url = f"{self.searxng_url}/search"
        params = {
            'q': query,
            'format': 'json',
            'categories': 'news,general',
            'language': 'en',
            'time_range': 'month'
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('results', [])[:num_results]:
                results.append({
                    'url': item.get('url'),
                    'title': item.get('title'),
                    'snippet': item.get('content', ''),
                    'engine': item.get('engine', 'unknown')
                })
            
            return results
            
        except Exception as e:
            print(f"❌ SearXNG error: {e}")
            return []
    
    def extract_with_jina(self, url: str) -> Optional[str]:
        """Jina Reader extract full content (Analyst)"""
        try:
            base_url = self.jina_url.split('?')[0].rstrip('/')
            if not base_url.endswith('/extract'):
                base_url = base_url + '/extract'
            
            jina_request_url = f"{base_url}?url={quote(url)}"
            response = requests.get(jina_request_url, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            content = data.get('content', '')
            
            if len(content) > 200:
                return content
            return None
            
        except Exception as e:
            print(f"⚠️ Jina error for {url[:50]}: {e}")
            return None
    
    def extract_with_trafilatura(self, url: str) -> Optional[str]:
        """Fallback: Trafilatura"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            content = trafilatura.extract(response.text)
            if content and len(content) > 200:
                return content
            return None
        except Exception as e:
            print(f"⚠️ Trafilatura error: {e}")
            return None
    
    def extract_content(self, url: str) -> Optional[str]:
        """Jina → Trafilatura fallback"""
        content = self.extract_with_jina(url)
        if content:
            return content
        time.sleep(0.3)
        return self.extract_with_trafilatura(url)
    
    # ==========================================
    # MAIN RESEARCH (ROUND B)
    # ==========================================
    
    def research_queries(self, queries: List[str], max_articles_per_query: int = 3,
                         progress_callback=None) -> str:
        """Search + Extract → Search Report"""
        total_queries = len(queries)
        all_articles = []
        seen_urls = set()
        
        for i, query in enumerate(queries, 1):
            if progress_callback:
                progress_callback(i, total_queries, f"🔍 Searching: {query[:50]}...")
            
            results = self.search_searxng(query, num_results=20)
            
            extracted = 0
            for result in results[:max_articles_per_query * 2]:
                url = result['url']
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                content = self.extract_content(url)
                if content:
                    all_articles.append({
                        'query': query,
                        'url': url,
                        'title': result['title'],
                        'content': content[:3000],
                        'word_count': len(content.split())
                    })
                    extracted += 1
                    if extracted >= max_articles_per_query:
                        break
                time.sleep(0.3)
            
            if progress_callback:
                progress_callback(i, total_queries, f"✅ Query {i}/{total_queries}: {extracted} articles")
        
        report = self._build_search_report(all_articles)
        
        if progress_callback:
            progress_callback(total_queries, total_queries,
                            f"📊 Total: {len(all_articles)} articles, {len(report)} chars")
        
        return report
    
    def _build_search_report(self, articles: List[Dict]) -> str:
        """Build Search Report"""
        if not articles:
            return "No articles found."
        
        report_lines = [
            "=" * 70,
            "OMNIS-COURT SEARCH REPORT",
            f"Total articles: {len(articles)}",
            "=" * 70, ""
        ]
        
        by_query = {}
        for article in articles:
            q = article['query']
            if q not in by_query:
                by_query[q] = []
            by_query[q].append(article)
        
        for query, query_articles in by_query.items():
            report_lines.append(f"\n### Query: {query}")
            report_lines.append("-" * 70)
            for i, article in enumerate(query_articles, 1):
                report_lines.append(f"\n[{i}] {article['title']}")
                report_lines.append(f"URL: {article['url']}")
                report_lines.append(f"Words: {article['word_count']}")
                report_lines.append(f"Content:\n{article['content'][:2000]}\n")
        
        return "\n".join(report_lines)
    
    # ==========================================
    # 🆕 TRUE AGENTIC SEARCH EXECUTOR (COMMON HELPER)
    # ==========================================
    
    def _execute_agentic_search(self, queries: List[str],
                                  extract_all: bool = True,
                                  progress_callback=None,
                                  progress_prefix: str = "") -> str:
        """
        Execute agentic search: SearXNG (over-fetch) → Jina (extract ALL) → Search Report
        
        Args:
            queries: List of search queries
            extract_all: If True, extract ALL URLs (not just top N)
            progress_callback: function(current, total, message)
            progress_prefix: Prefix for progress messages
        """
        all_articles = []
        seen_urls = set()
        total_queries = len(queries)
        
        for i, query in enumerate(queries, 1):
            if progress_callback:
                progress_callback(i, total_queries * 2,
                                f"{progress_prefix}🔍 [{i}/{total_queries}] {query[:50]}...")
            
            # SearXNG: over-fetch 80 URLs
            results = self.search_searxng(query, num_results=80)
            
            # Filter relevant URLs (skip if too many)
            urls_to_extract = []
            for r in results:
                url = r['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    urls_to_extract.append((url, r['title']))
                    if not extract_all and len(urls_to_extract) >= 10:
                        break
            
            # Jina: extract ALL (or top 10)
            extracted_count = 0
            for url, title in urls_to_extract:
                content = self.extract_content(url)
                if content:
                    all_articles.append({
                        'query': query,
                        'url': url,
                        'title': title,
                        'content': content[:5000],  # เก็บเยอะขึ้น
                        'word_count': len(content.split())
                    })
                    extracted_count += 1
                time.sleep(0.3)
            
            if progress_callback:
                progress_callback(total_queries + i, total_queries * 2,
                                f"{progress_prefix}✅ [{i}/{total_queries}] extracted {extracted_count} articles")
        
        # Build report
        return self._build_search_report(all_articles)
    
    # ==========================================
    # 🆕 PHASE 0: TRUE AGENTIC TOURNAMENT DETECTION
    # ==========================================
    
    def detect_tournament(self, player_a: str, player_b: str, max_retries: int = 3,
                         progress_callback=None, llm_client=None) -> Optional[Dict]:
        """
        TRUE AGENTIC Tournament Detection
        
        Flow: LLM THINK → SearXNG ACT → Jina EXTRACT ALL → LLM OBSERVE → ADAPTIVE RETRY
        
        Returns: {
            "tournament", "surface", "round", "court", "court_speed",
            "ball", "weather", "confidence", "evidence", "source_urls",
            "attempt": N, "total_searches": N, "total_articles": N
        }
        """
        from prompt_v7_1 import ROUND_0_PLAN, ROUND_0_OBSERVE, ROUND_0_RETRY
        
        if llm_client is None:
            from llm_client import LLMClient
            llm_client = LLMClient()
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        previous_feedback = "First attempt - no previous data"
        previous_strategy = ""
        total_searches = 0
        total_articles = 0
        
        for attempt in range(1, max_retries + 1):
            if progress_callback:
                progress_callback(attempt, max_retries,
                                f"🧠 Attempt {attempt}/{max_retries}: LLM planning strategy...")
            
            # ═══ STEP 1: LLM THINK (Plan Queries) ═══
            if attempt == 1:
                plan_prompt = ROUND_0_PLAN.format(
                    player_a=player_a,
                    player_b=player_b,
                    current_date=current_date,
                    previous_feedback=previous_feedback
                )
            else:
                plan_prompt = ROUND_0_RETRY.format(
                    player_a=player_a,
                    player_b=player_b,
                    attempt_number=attempt,
                    max_attempts=max_retries,
                    previous_strategy=previous_strategy,
                    previous_results="See analysis below",
                    failure_reason=previous_feedback
                )
            
            plan_response = llm_client.call_qwen(plan_prompt, max_tokens=2000, temperature=0.3)
            if not plan_response:
                continue
            
            # Parse LLM plan
            try:
                plan_json = json.loads(plan_response)
            except:
                json_match = re.search(r'\{.*\}', plan_response, re.DOTALL)
                if json_match:
                    try:
                        plan_json = json.loads(json_match.group())
                    except:
                        continue
                else:
                    continue
            
            queries = plan_json.get('queries', [])
            if not queries:
                continue
            
            previous_strategy = plan_json.get('reasoning', '') or plan_json.get('new_strategy', '')
            total_searches += len(queries)
            
            # ═══ STEP 2: SearXNG ACT + Jina EXTRACT ALL ═══
            if progress_callback:
                progress_callback(attempt, max_retries,
                                f"🔍 Attempt {attempt}/{max_retries}: Executing {len(queries)} searches + extracting ALL content...")
            
            search_report = self._execute_agentic_search(
                queries,
                extract_all=True,
                progress_callback=progress_callback if attempt == max_retries else None,
                progress_prefix=f"[A{attempt}] "
            )
            
            # นับบทความ
            article_count = search_report.count("### Query:")
            total_articles += article_count
            
            if len(search_report) < 500:
                previous_feedback = f"No results found. Queries: {queries[:3]}"
                continue
            
            # ═══ STEP 3: LLM OBSERVE (Analyze + Decide) ═══
            if progress_callback:
                progress_callback(attempt, max_retries,
                                f"🧠 Attempt {attempt}/{max_retries}: LLM analyzing results...")
            
            observe_prompt = ROUND_0_OBSERVE.format(
                player_a=player_a,
                player_b=player_b,
                current_date=current_date,
                search_report=search_report[:25000]  # truncate for context
            )
            
            observe_response = llm_client.call_qwen(observe_prompt, max_tokens=1500, temperature=0.2)
            if not observe_response:
                continue
            
            # Parse observation
            try:
                observation = json.loads(observe_response)
            except:
                json_match = re.search(r'\{.*\}', observe_response, re.DOTALL)
                if json_match:
                    try:
                        observation = json.loads(json_match.group())
                    except:
                        continue
                else:
                    continue
            
            # ═══ STEP 4: Decision ═══
            confidence = observation.get('confidence', 'LOW')
            tournament = observation.get('tournament')
            
            if confidence == 'HIGH' and tournament:
                # ✅ SUCCESS
                observation['attempt'] = attempt
                observation['total_searches'] = total_searches
                observation['total_articles'] = total_articles
                return observation
            elif confidence == 'MEDIUM' and tournament:
                # ⚠️ Partial success - use it but note low confidence
                observation['attempt'] = attempt
                observation['total_searches'] = total_searches
                observation['total_articles'] = total_articles
                if attempt == max_retries:
                    return observation
                # Otherwise try one more time for HIGH confidence
                previous_feedback = f"MEDIUM confidence. Evidence: {observation.get('evidence', '')}"
            else:
                # ❌ Failed - retry
                previous_feedback = f"LOW confidence or no tournament. Evidence: {observation.get('evidence', 'None')}"
        
        # ❌ Exhausted all retries
        return None
    
    # ==========================================
    # 🆕 FIND UPCOMING MATCH (TEST FEATURE)
    # ==========================================
    
    def find_upcoming_match(self, hours_ahead: int = 2, max_retries: int = 2,
                            progress_callback=None, llm_client=None) -> Optional[Dict]:
        """
        Find tennis matches starting in next N hours
        
        Returns: {
            "matches_found": [...],
            "total_found": N,
            "best_match": {...} or null,
            "time_window": "HH:MM - HH:MM",
            "reasoning": "..."
        }
        """
        from prompt_v7_1 import FIND_UPCOMING_PLAN, FIND_UPCOMING_OBSERVE
        
        if llm_client is None:
            from llm_client import LLMClient
            llm_client = LLMClient()
        
        now = datetime.now()
        current_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        future = now + timedelta(hours=hours_ahead)
        time_window = f"{now.strftime('%H:%M')} - {future.strftime('%H:%M')}"
        timezone = "Local"
        
        for attempt in range(1, max_retries + 1):
            if progress_callback:
                progress_callback(attempt, max_retries,
                                f"🧠 Attempt {attempt}/{max_retries}: Planning search for upcoming matches...")
            
            # STEP 1: LLM PLAN
            plan_prompt = FIND_UPCOMING_PLAN.format(
                current_datetime=current_datetime,
                timezone=timezone
            )
            
            plan_response = llm_client.call_qwen(plan_prompt, max_tokens=1500, temperature=0.3)
            if not plan_response:
                continue
            
            try:
                plan_json = json.loads(plan_response)
            except:
                json_match = re.search(r'\{.*\}', plan_response, re.DOTALL)
                if json_match:
                    try:
                        plan_json = json.loads(json_match.group())
                    except:
                        continue
                else:
                    continue
            
            queries = plan_json.get('queries', [])
            if not queries:
                continue
            
            # STEP 2: EXECUTE SEARCH
            if progress_callback:
                progress_callback(attempt, max_retries,
                                f"🔍 Attempt {attempt}/{max_retries}: Searching {len(queries)} queries...")
            
            search_report = self._execute_agentic_search(
                queries,
                extract_all=True,
                progress_callback=progress_callback if attempt == max_retries else None,
                progress_prefix=f"[Find] "
            )
            
            if len(search_report) < 500:
                continue
            
            # STEP 3: LLM OBSERVE
            if progress_callback:
                progress_callback(attempt, max_retries,
                                f"🧠 Attempt {attempt}/{max_retries}: LLM finding matches...")
            
            observe_prompt = FIND_UPCOMING_OBSERVE.format(
                current_datetime=current_datetime,
                timezone=timezone,
                search_report=search_report[:25000]
            )
            
            observe_response = llm_client.call_qwen(observe_prompt, max_tokens=2000, temperature=0.2)
            if not observe_response:
                continue
            
            try:
                observation = json.loads(observe_response)
            except:
                json_match = re.search(r'\{.*\}', observe_response, re.DOTALL)
                if json_match:
                    try:
                        observation = json.loads(json_match.group())
                    except:
                        continue
                else:
                    continue
            
            # Check if found
            if observation.get('best_match') and observation.get('total_found', 0) > 0:
                observation['attempt'] = attempt
                observation['time_window'] = time_window
                return observation
        
        # Not found
        return {
            "matches_found": [],
            "total_found": 0,
            "best_match": None,
            "time_window": time_window,
            "reasoning": "No matches found in the specified time window",
            "attempt": max_retries
        }
