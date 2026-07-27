"""
OMNIS-COURT Search Client
จัดการ SearXNG (ค้นหา) + Jina Reader (extract)
"""

import json
import requests
import time
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
            # Jina URL format: https://xxx.trycloudflare.com/extract?url=...
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
        """
        ค้นหาและ extract หลาย queries → รวมเป็น Search Report
        
        Args:
            queries: list ของ search queries
            max_articles_per_query: จำนวนบทความสูงสุดต่อ query
            progress_callback: function(current, total, message) สำหรับ update UI
        
        Returns:
            Search Report (text) ที่รวมทุกผลลัพธ์
        """
        total_queries = len(queries)
        all_articles = []
        seen_urls = set()
        
        for i, query in enumerate(queries, 1):
            if progress_callback:
                progress_callback(i, total_queries, f"🔍 Searching: {query[:50]}...")
            
            # ค้นหา
            results = self.search_searxng(query, num_results=20)
            
            # Extract เนื้อหา
            extracted = 0
            for result in results[:max_articles_per_query * 2]:  # ลองมากกว่าที่ต้องการ
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
                        'content': content[:3000],  # ตัดให้สั้นลง
                        'word_count': len(content.split())
                    })
                    extracted += 1
                    
                    if extracted >= max_articles_per_query:
                        break
                
                time.sleep(0.3)  # Rate limit
            
            if progress_callback:
                progress_callback(i, total_queries, f"✅ Query {i}/{total_queries}: {extracted} articles")
        
        # รวมเป็น Search Report
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
        
        # Group by query
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
