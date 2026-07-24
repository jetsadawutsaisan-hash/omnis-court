# 🎾 OMNIS-COURT v7.2 "ADAPTIVE PREDATOR"

Neuro-Symbolic Tennis Analytics System

## 🏗️ Architecture
Search Layer: SearXNG (Render) + Jina/Trafilatura (Colab/Kaggle)

LLM Layer: Qwen3-30B-A3B (Colab primary /

Kaggle standby)

Analysis Engine: Monte Carlo Simulation

(embedded in app.py)

Tracking: 3-Part Picks + Quality Gate 60% Notification: LINE Notify

## 📁 Repository Structure
omnis-court/

notebooks/

| colab_IIm_jina.ipynb - Primary LLM + Jina

server

kaggle_lIm_jina.ipynb - Standby LLM +

Jina server

config/

platforms.json - URLs, quotas, settings - docs/

MANUAL.md- Operations manual

omniscourt/- Python package (Part 4)

app.py - Dashboard + API (Part 4)

README.md This file

## 🚀 Quick Start

1. Read [Operations Manual](docs/MANUAL.md)
2. Open Colab notebook daily
3. Copy URLs to config/platforms.json
4. Dashboard shows system status

## 📊 System Status

Check live dashboard: [DASHBOARD_URL]

## 🔧 Tech Stack

- **Search**: SearXNG (self-hosted on Render)
- **Content Extraction**: Jina Reader + Trafilatura fallback
- **LLM**: Qwen3-30B-A3B via vLLM
- **Simulation**: Custom Monte Carlo Engine
- **Infrastructure**: GitHub + Render + Colab + Kaggle
- **Cost**: $0/month
