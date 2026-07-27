"""
OMNIS-COURT LLM Client
จัดการการเชื่อมต่อกับ Qwen3-14B ผ่าน Cloudflare Tunnel
"""

import json
import requests
import re
from typing import List, Dict, Optional, Tuple


class LLMClient:
    """Client สำหรับสื่อสารกับ Qwen3-14B LLM"""
    
    def __init__(self, config_path: str = "config/platforms.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.llm_api_url = self.config['omnis_court']['llm_api_url']
    
    def call_qwen(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> Optional[str]:
        """เรียก Qwen3-14B API"""
        url = f"{self.llm_api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "qwen3-14b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=600)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return None
