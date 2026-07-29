"""
OMNIS-COURT LLM Client
จัดการการเชื่อมต่อกับ Qwen3-8B ผ่าน Cloudflare Tunnel
"""

import json
import requests
import re
from typing import List, Dict, Optional, Tuple


class LLMClient:
    """Client สำหรับสื่อสารกับ Qwen3-8B LLM"""
    
    def __init__(self, config_path: str = "config/platforms.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.llm_api_url = self.config['omnis_court']['llm_api_url']
    
    def call_qwen(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7, 
                  thinking: bool = False) -> Optional[str]:
        """
        เรียก Qwen3-8B API
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            thinking: If True, enable thinking mode (default: False for speed)
        
        Returns:
            Generated text or None if error
        """
        url = f"{self.llm_api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        # Disable thinking mode by default (faster, cleaner output)
        if not thinking:
            prompt = f"/no_think\n{prompt}"
        
        payload = {
            "model": "qwen3",  # ✅ Must match --served-model-name in Colab
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=600)
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # Strip  tags if present (Qwen3 thinking mode leak)
            if "" in content:
                # Remove everything between  and 
                content = re.sub(r'', '', content, flags=re.DOTALL)
                content = content.strip()
            
            return content
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return None
