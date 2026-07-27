import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from llm_client import LLMClient
from search_client import SearchClient
from monte_carlo import MonteCarloExecutor
from orchestrator import Orchestrator

# ==========================================
# OMNIS-COURT DASHBOARD v4.2 (Auto Match Time)
# ==========================================

st.set_page_config(
    page_title="OMNIS-COURT Dashboard",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 OMNIS-COURT Command Center")

# Initialize session_state
if 'analysis_queue' not in st.session_state:
    st.session_state.analysis_queue = []

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []

if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

if 'current_progress' not in st.session_state:
    st.session_state.current_progress = {"round": "", "message": ""}

# ==========================================
# LOAD CONFIG
# ==========================================
st.markdown("---")
st.subheader("📁 Configuration")

try:
    with open('config/platforms.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    st.success("✅ โหลด config สำเร็จ")
except Exception as e:
    st.error(f"❌ Config error: {e}")
    st.stop()

omnis = config.get('omnis_court', {})
search_cfg = config.get('search_engine', {})

# ==========================================
# HEALTH CHECK
# ==========================================
st.markdown("---")
st.subheader("🔍 Service Status")

def check_health(name, url, icon, timeout=10):
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        st.markdown(f"### {icon} {name}")
    with col2:
        display_url = url[:50] + "..." if len(url) > 50 else url
        st.code(display_url, language="text")
    with col3:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                st.success("✅ ONLINE")
                return True
            else:
                st.error(f"❌ HTTP {response.status_code}")
                return False
        except:
            st.error("🔌 OFFLINE")
            return False

searxng_url = search_cfg.get('searxng_url', '')
check_health("SearXNG", searxng_url, "🔍")

llm_url = omnis.get('llm_api_url', '')
if llm_url:
    check_health("Qwen3-14B", f"{llm_url}/models", "🧠")

jina_url = omnis.get('jina_reader_url', '')
if jina_url:
    health_url = jina_url.split('?')[0].replace('/extract', '/health')
    check_health("Jina Reader", health_url, "📖")

# ==========================================
# 📝 ADD NEW MATCH (Form) - AUTO MATCH TIME
# ==========================================
st.markdown("---")
st.subheader("📝 Add New Match")

with st.form("add_match_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        player_a = st.text_input("🎾 Player A", placeholder="e.g., Alcaraz")
        player_b = st.text_input("🎾 Player B", placeholder="e.g., Sinner")
        tournament = st.text_input("🏆 Tournament (optional)", placeholder="e.g., US Open 2026")
    
    with col2:
        hc_line_a = st.number_input("📊 HC Line A", value=-2.5, step=0.5)
        hc_line_b = st.number_input("📊 HC Line B", value=2.5, step=0.5)
        ou_line = st.number_input("📊 O/U Line", value=22.5, step=0.5)
        
        # ✅ Auto-set match time (+2 hours from now) - ไม่ต้องกรอกเอง!
        match_time = datetime.now() + timedelta(hours=2)
        st.info(f"⏰ Match Time: **{match_time.strftime('%H:%M %d/%m/%Y')}** (auto-set: +2 ชม. จากตอนนี้)")
    
    # ✅ Submit buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        skip_queue = st.form_submit_button(
            "⚡ ลัดคิว (Analyze Now)", 
            type="primary", 
            use_container_width=True
        )
    
    with col_btn2:
        add_to_queue = st.form_submit_button(
            "➕ เพิ่มคิว", 
            use_container_width=True
        )

# Process form submission
if skip_queue or add_to_queue:
    if not player_a or not player_b:
        st.error("❌ กรุณาใส่ชื่อผู้เล่นทั้งสอง")
    else:
        match_info = {
            "player_a": player_a,
            "player_b": player_b,
            "tournament": tournament,
            "surface": "Unknown",
            "hc_line_a": hc_line_a,
            "hc_line_b": hc_line_b,
            "ou_line": ou_line,
            "match_time": match_time,
            "added_at": datetime.now()
        }
        
        if skip_queue:
            st.session_state.current_analysis = match_info
            st.rerun()
        
        elif add_to_queue:
            st.session_state.analysis_queue.append(match_info)
            st.session_state.analysis_queue.sort(key=lambda x: x['match_time'])
            st.success(f"✅ เพิ่ม {player_a} vs {player_b} เข้าคิวแล้ว")
            st.rerun()

# ==========================================
# 📋 ANALYSIS QUEUE
# ==========================================
st.markdown("---")
st.subheader(f"📋 Analysis Queue ({len(st.session_state.analysis_queue)} matches)")

if st.session_state.analysis_queue:
    for i, match in enumerate(st.session_state.analysis_queue):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{match['player_a']} vs {match['player_b']}**")
            if match['tournament']:
                st.caption(match['tournament'])
        
        with col2:
            st.caption(f"⏰ {match['match_time'].strftime('%H:%M %d/%m')}")
        
        with col3:
            st.caption(f"HC: {match['hc_line_a']}/{match['hc_line_b']} | O/U: {match['ou_line']}")
        
        with col4:
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state.analysis_queue.pop(i)
                st.rerun()
        
        st.markdown("---")
    
    if not st.session_state.current_analysis:
        if st.button("▶️ Start Queue Analysis", type="primary"):
            st.session_state.current_analysis = st.session_state.analysis_queue.pop(0)
            st.rerun()
else:
    st.info("💡 คิวว่าง - เพิ่มแมตช์ด้านบน")

# ==========================================
# 🎯 CURRENT ANALYSIS
# ==========================================
if st.session_state.current_analysis:
    st.markdown("---")
    st.subheader("🎯 Current Analysis")
    
    match = st.session_state.current_analysis
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎾 Match", f"{match['player_a']} vs {match['player_b']}")
    with col2:
        st.metric("⏰ Time", match['match_time'].strftime('%H:%M'))
    with col3:
        st.metric("📊 Lines", f"HC: {match['hc_line_a']} | O/U: {match['ou_line']}")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def progress_callback(round_name, message):
        status_text.markdown(f"**{round_name}:** {message}")
        round_progress = {
            "Round A": 0.2,
            "Round B": 0.4,
            "Round C": 0.6,
            "Round D": 0.8,
            "Round E": 0.95,
            "Done": 1.0
        }
        if round_name in round_progress:
            progress_bar.progress(round_progress[round_name])
    
    try:
        orchestrator = Orchestrator()
        with st.spinner("🧠 Running analysis pipeline..."):
            verdict = orchestrator.analyze_match(match, progress_callback=progress_callback)
        
        progress_bar.progress(1.0)
        status_text.markdown("**✅ Analysis Complete!**")
        
        if verdict:
            st.session_state.analysis_results.append({
                'match_info': match,
                'verdict': verdict,
                'completed_at': datetime.now()
            })
            
            st.session_state.current_analysis = None
            
            if st.session_state.analysis_queue:
                st.session_state.current_analysis = st.session_state.analysis_queue.pop(0)
            
            st.rerun()
        else:
            st.error("❌ Analysis failed")
            st.session_state.current_analysis = None
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        st.session_state.current_analysis = None

# ==========================================
# 💎 RESULTS
# ==========================================
if st.session_state.analysis_results:
    st.markdown("---")
    st.subheader(f"💎 Results ({len(st.session_state.analysis_results)} completed)")
    
    for i, result in enumerate(reversed(st.session_state.analysis_results)):
        match = result['match_info']
        verdict = result['verdict']
        
        with st.expander(f"**{match['player_a']} vs {match['player_b']}** — {result['completed_at'].strftime('%H:%M %d/%m')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🎾 Match", f"{match['player_a']} vs {match['player_b']}")
            with col2:
                st.metric("⏰ Time", match['match_time'].strftime('%H:%M'))
            with col3:
                st.metric("📊 Lines", f"HC: {match['hc_line_a']} | O/U: {match['ou_line']}")
            
            apex = verdict.get('apex_pick', {})
            if apex:
                st.markdown("### 🏆 APEX PICK")
                
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    st.metric("🎯 Option", apex.get('option', 'N/A'))
                with col_a2:
                    prob = apex.get('probability', 0)
                    st.metric("📊 Probability", f"{prob*100:.1f}%")
                with col_a3:
                    st.metric("🎲 Confidence", apex.get('confidence', 'N/A'))
                
                if prob >= 0.60:
                    st.success(f"✅ **QUALITY GATE PASSED** ({prob*100:.1f}% ≥ 60%)")
                else:
                    st.warning(f"⚠️ **Quality Gate Not Met** ({prob*100:.1f}% < 60%)")
                
                with st.expander("📖 ดูรายละเอียด"):
                    st.markdown(f"**Bet Sizing:** {apex.get('bet_sizing', 'N/A')}")
                    st.markdown(f"**Most Likely Path:** {apex.get('most_likely_path', 'N/A')}")
                    st.warning(f"**⚠️ Risk:** {apex.get('risk_warning', 'N/A')}")
            
            crucible = verdict.get('option_crucible', [])
            if crucible:
                with st.expander(f"⚖️ Option Crucible ({len(crucible)} options)"):
                    for opt in crucible:
                        st.markdown(f"**{opt.get('option', 'Unknown')}** — {opt.get('status', 'N/A')}")
                        prob = opt.get('true_hit_probability', 0)
                        st.metric("Probability", f"{prob*100:.1f}%")
                        st.markdown(f"Reasoning: {opt.get('reasoning', 'N/A')}")
                        st.markdown("---")
            
            with st.expander("🔍 Raw Verdict JSON"):
                st.json(verdict)

# ==========================================
# 🧪 QUICK TESTS
# ==========================================
with st.expander("🧪 Quick Tests (Debug)"):
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Test SearXNG"):
            try:
                test_url = f"{searxng_url}/search?q=alcaraz+tennis&format=json"
                r = requests.get(test_url, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ Found {len(data.get('results', []))} results")
            except Exception as e:
                st.error(f"❌ {str(e)[:50]}")
    
    with col2:
        if st.button("📖 Test Jina"):
            try:
                test_url = jina_url.split('?')[0] + "?url=https://en.wikipedia.org/wiki/Tennis"
                r = requests.get(test_url, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"✅ Extracted {data.get('word_count', 0)} words")
            except Exception as e:
                st.error(f"❌ {str(e)[:50]}")

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("OMNIS-COURT v7.1 | Queue System Active | v4.2 Auto Match Time")
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
