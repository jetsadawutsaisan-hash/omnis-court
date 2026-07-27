"""
OMNIS-COURT Search Client v2.0
จัดการ SearXNG (ค้นหา) + Jina Reader (extract) + Auto-Detect Tournament
"""

import json
import requests
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote
import trafilatura


class SearchClient:
    """Client สำหรับค้นหาและดึงเนื้อหา"""
    
    def __init__(self, config_path: str = "config/platforms.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.searxng_url = self.config['search_engine']['searxng_url']
        self.jina_url = self.config['omnis_court']['jina_reader_url']
    
    def search_searxng(self, query: str, num_results: int = 80) -> List[Dict]:
        """ค้นหาด้วย SearXNG (over-fetch)"""
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
        """ดึงเนื้อหาด้วย Jina Reader"""
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
        """Fallback: ดึงเนื้อหาด้วย Trafilatura (local)"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            content = trafilatura.extract(response.text)
            if content and len(content) > 200:
                return content
            return None
        except Exception as e:
            print(f"⚠️ Trafilatura error for {url[:50]}: {e}")
            return None
    
    def extract_content(self, url: str) -> Optional[str]:
        """ดึงเนื้อหา (Jina → Trafilatura fallback)"""
        content = self.extract_with_jina(url)
        if content:
            return content
        
        time.sleep(0.5)
        return self.extract_with_trafilatura(url)
    
    def research_queries(self, queries: List[str], max_articles_per_query: int = 3, 
                         progress_callback=None) -> str:
        """ค้นหาและ extract หลาย queries → รวมเป็น Search Report"""
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
                            f"📊 Total: {len(all_articles)} articles, {len(report)} characters")
        
        return report
    
    def _build_search_report(self, articles: List[Dict]) -> str:
        """รวมทุกบทความเป็น Search Report"""
        if not articles:
            return "No articles found."
        
        report_lines = [
            "=" * 70,
            "OMNIS-COURT SEARCH REPORT",
            f"Total articles extracted: {len(articles)}",
            "=" * 70,
            ""
        ]
        
        by_query = {}
        for article in articles:
            query = article['query']
            if query not in by_query:
                by_query[query] = []
            by_query[query].append(article)
        
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
    # 🆕 PHASE 0: AUTO-DETECT TOURNAMENT
    # ==========================================
    
    def detect_tournament(self, player_a: str, player_b: str, max_retries: int = 5,
                         progress_callback=None, llm_client=None) -> Optional[Dict]:
        """
        Auto-detect tournament context (5 retry loops)
        
        Retry Strategy:
        1. Direct match (English)
        2. Multilingual (ES/FR/IT/DE/JP)
        3. Broader player search (current tournament)
        4. Social/news (Twitter/Instagram/news)
        5. Tournament calendar (ATP/WTA schedule)
        
        Returns: {
            "tournament": "Roland Garros 2026",
            "surface": "Clay",
            "round": "Semi-Final",
            "court": "Philippe Chatrier",
            "court_speed": 1.8,
            "ball": "Dunlop ATP",
            "weather": {"temp": 22, "humidity": 65, "wind": 5},
            "confidence": "HIGH/MEDIUM/LOW",
            "source_urls": [...],
            "attempt": 2
        }
        """
        from llm_client import LLMClient
        
        if llm_client is None:
            llm_client = LLMClient()
        
        # 5 Retry Loops with different strategies
        retry_strategies = [
            {
                "name": "Direct Match",
                "queries": [
                    f"{player_a} vs {player_b} tennis match 2026",
                    f"{player_a} {player_b} tennis schedule",
                    f"ATP WTA draw {player_a} {player_b}"
                ]
            },
            {
                "name": "Multilingual",
                "queries": [
                    f"{player_a} {player_b} partido tenis",  # Spanish
                    f"{player_a} {player_b} match tennis",   # French
                    f"{player_a} {player_b} テニス 試合"      # Japanese
                ]
            },
            {
                "name": "Broader Search",
                "queries": [
                    f"{player_a} current tournament 2026",
                    f"{player_b} ATP schedule this week",
                    f"tennis tournaments {player_a} playing"
                ]
            },
            {
                "name": "Social & News",
                "queries": [
                    f"{player_a} twitter tournament",
                    f"{player_a} instagram practice",
                    f"ATP news {player_a} {player_b}"
                ]
            },
            {
                "name": "Tournament Calendar",
                "queries": [
                    "ATP calendar this week 2026",
                    "WTA tournaments schedule 2026",
                    f"{player_a} {player_b} head to head recent"
                ]
            }
        ]
        
        for attempt in range(min(max_retries, len(retry_strategies))):
            strategy = retry_strategies[attempt]
            
            if progress_callback:
                progress_callback(attempt + 1, max_retries, 
                                f"🔄 Attempt {attempt+1}/{max_retries}: {strategy['name']}")
            
            # ค้นหาทุก queries ใน strategy
            all_snippets = []
            source_urls = []
            
            for query in strategy['queries']:
                results = self.search_searxng(query, num_results=15)
                for r in results:
                    all_snippets.append({
                        'title': r['title'],
                        'snippet': r['snippet'],
                        'url': r['url']
                    })
                    if r['url'] not in source_urls:
                        source_urls.append(r['url'])
                time.sleep(0.3)
            
            if not all_snippets:
                continue
            
            # ใช้ LLM วิเคราะห์ snippets เพื่อดึง tournament context
            analysis = self._llm_analyze_tournament(
                player_a, player_b, all_snippets, llm_client
            )
            
            if analysis and analysis.get('tournament'):
                analysis['attempt'] = attempt + 1
                analysis['source_urls'] = source_urls[:5]  # เก็บแค่ 5 URLs แรก
                return analysis
        
        # สุดทางแล้ว ไม่เจอ
        return None
    
    def _llm_analyze_tournament(self, player_a: str, player_b: str, 
                                 snippets: List[Dict], llm_client) -> Optional[Dict]:
        """ใช้ LLM วิเคราะห์ snippets เพื่อดึง tournament context"""
        
        # รวม snippets เป็น text สั้นๆ (ไม่เกิน 8000 chars)
        snippets_text = ""
        for i, s in enumerate(snippets[:20], 1):  # จำกัด 20 snippets
            snippets_text += f"\n[{i}] {s['title']}\n{s['snippet'][:300]}\n"
            if len(snippets_text) > 7000:
                break
        
        prompt = f"""You are a tennis tournament detective.

Match: {player_a} vs {player_b}

Based on the search snippets below, detect the tournament context:

SNIPPETS:
{snippets_text}

Return ONLY a JSON object with these fields:
{{
  "tournament": "name of tournament (e.g., Roland Garros 2026) or null if not found",
  "surface": "Clay" or "Hard" or "Grass" or null,
  "round": "R128/R64/R32/R16/QF/SF/F or null",
  "court": "court name if found, or null",
  "court_speed": float (1.0=slow clay, 2.5=medium hard, 3.8=fast grass) or null,
  "ball": "ball brand (Dunlop/Penn/Slazenger/Head) or null",
  "weather": {{"temp": int celsius, "humidity": int percent, "wind": int km/h}} or null,
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "evidence": "brief 1-sentence reason for your answer"
}}

Rules:
- If tournament is clearly found, set confidence to HIGH
- If partially found (e.g., tournament name but no round), set MEDIUM
- If only guessing, set LOW and set tournament to null
- Use realistic court_speed values: Roland Garros = 1.8, Wimbledon = 3.8, US Open = 2.9
- Return ONLY JSON, no markdown, no explanations
"""
        
        response = llm_client.call_qwen(prompt, max_tokens=1000, temperature=0.2)
        if not response:
            return None
        
        # Parse JSON
        try:
            result = json.loads(response)
            if isinstance(result, dict):
                # กรอง null values ออก
                return {k: v for k, v in result.items() if v is not None and v != {}}
        except:
            pass
        
        # Fallback: extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                if isinstance(result, dict):
                    return {k: v for k, v in result.items() if v is not None and v != {}}
            except:
                pass
        
        return None
