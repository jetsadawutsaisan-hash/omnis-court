import streamlit as st
import requests
import json
import time
from llm_client import LLMClient
from search_client import SearchClient
from monte_carlo import MonteCarloExecutor
from orchestrator import Orchestrator

# ==========================================
# OMNIS-COURT STATUS DASHBOARD v3.0
# Deployed on Render - Free Tier
# ==========================================

st.set_page_config(
    page_title="OMNIS-COURT Dashboard",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 OMNIS-COURT Command Center")
st.markdown("ระบบตรวจสอบสุขภาพ Infrastructure + Match Analysis")

# Auto-refresh button
if st.button("🔄 Refresh Now"):
    st.rerun()

# ==========================================
# LOAD CONFIG
# ==========================================
st.markdown("---")
st.subheader("📁 Configuration")

try:
    with open('config/platforms.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    st.success("✅ โหลด config/platforms.json สำเร็จ")
except FileNotFoundError:
    st.error("❌ ไม่พบไฟล์ config/platforms.json")
    st.stop()
except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
    st.stop()

omnis = config.get('omnis_court', {})
search_cfg = config.get('search_engine', {})

# ==========================================
# HEALTH CHECK FUNCTION
# ==========================================
def check_health(name, url, icon, timeout=10):
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        st.markdown(f"### {icon} {name}")
    
    with col2:
        st.code(url, language="text")
    
    with col3:
        start_time = time.time()
        try:
            response = requests.get(url, timeout=timeout)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                st.success(f"✅ ONLINE")
                st.caption(f"{latency:.0f} ms")
                return True
            else:
                st.error(f"❌ HTTP {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            st.error("⏱️ TIMEOUT")
            return False
        except requests.exceptions.ConnectionError:
            st.error("🔌 OFFLINE")
            return False
        except Exception as e:
            st.error(f"⚠️ {str(e)[:30]}")
            return False

# ==========================================
# SERVICE STATUS
# ==========================================
st.markdown("---")
st.subheader("🔍 Service Status")

searxng_url = search_cfg.get('searxng_url', 'http://localhost:8080')
check_health("SearXNG", searxng_url, "🔍")
st.markdown("")

llm_url = omnis.get('llm_api_url', '')
if llm_url:
    check_health("Qwen3-14B LLM", f"{llm_url}/models", "🧠")
else:
    st.warning("⚠️ ไม่พบ LLM URL ใน config")
st.markdown("")

jina_url = omnis.get('jina_reader_url', '')
if jina_url:
    jina_health_url = jina_url.split('?')[0].replace('/extract', '/health')
    check_health("Jina Reader", jina_health_url, "📖")
else:
    st.warning("⚠️ ไม่พบ Jina URL ใน config")

# ==========================================
# QUICK TESTS (SearXNG + Jina)
# ==========================================
st.markdown("---")
st.subheader("🧪 Quick Tests")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Test SearXNG Search"):
        with st.spinner("กำลังค้นหา..."):
            try:
                test_url = f"{searxng_url}/search?q=alcaraz+tennis&format=json"
                r = requests.get(test_url, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    num_results = len(data.get('results', []))
                    st.success(f"✅ พบ {num_results} ผลลัพธ์")
                    if num_results > 0:
                        with st.expander("📄 ดูผลลัพธ์แรก"):
                            st.json(data['results'][0])
                else:
                    st.error(f"❌ HTTP {r.status_code}")
            except Exception as e:
                st.error(f"❌ {str(e)[:100]}")

with col2:
    if st.button("📖 Test Jina Extract"):
        with st.spinner("กำลังดึงเนื้อหา..."):
            try:
                test_url = jina_url.split('?')[0] + "?url=https://en.wikipedia.org/wiki/Tennis"
                r = requests.get(test_url, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    word_count = data.get('word_count', 0)
                    st.success(f"✅ ดึงได้ {word_count} คำ")
                    with st.expander("📄 ดูเนื้อหา (500 คำแรก)"):
                        st.text_area("", data.get('content', '')[:500], height=150)
                else:
                    st.error(f"❌ HTTP {r.status_code}")
            except Exception as e:
                st.error(f"❌ {str(e)[:100]}")

# ==========================================
# 🧠 TEST LLM
# ==========================================
st.markdown("---")
st.subheader("🧠 Test LLM (Qwen3-14B)")

prompt_templates = {
    "🔹 ทดสอบพื้นฐาน": "Hello! Please respond with 'OK' if you can read this.",
    "🔹 ทดสอบภาษาไทย": "สวัสดีครับ ช่วยตอบกลับเป็นภาษาไทยว่า 'ระบบทำงานปกติ'",
    "🔹 ทดสอบ JSON": 'Return a JSON object: {"status": "ok", "model": "qwen3-14b"}. Return ONLY JSON.',
    "🔹 ทดสอบเทนนิส": "Who won Wimbledon 2024 men's singles? Answer in one sentence.",
}

col_template, col_params = st.columns([2, 1])

with col_template:
    selected_template = st.selectbox(
        "📝 เลือก Prompt Template:",
        options=list(prompt_templates.keys())
    )

with col_params:
    temperature = st.slider("🌡️ Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("📏 Max Tokens", 100, 8192, 1024, 100)

user_prompt = st.text_area(
    "✍️ Prompt:",
    value=prompt_templates[selected_template],
    height=100
)

if st.button("🚀 Send to Qwen", type="primary"):
    if not user_prompt.strip():
        st.warning("⚠️ กรุณาใส่ prompt")
    else:
        with st.spinner("🧠 กำลังส่งไปยัง Qwen3-14B..."):
            try:
                client = LLMClient()
                start_time = time.time()
                response = client.call_qwen(user_prompt, max_tokens=max_tokens, temperature=temperature)
                elapsed = time.time() - start_time
                
                if response:
                    st.success(f"✅ Response received in {elapsed:.1f}s")
                    with st.expander("📄 ดูคำตอบ", expanded=True):
                        st.markdown(response)
                else:
                    st.error("❌ ไม่ได้รับการตอบกลับ")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ==========================================
# 🎯 MATCH ANALYSIS (PART 4)
# ==========================================
st.markdown("---")
st.subheader("🎯 Match Analysis (Core Engine)")
st.markdown("ระบบวิเคราะห์แมตช์แบบอัตโนมัติ (5 Rounds Agentic Workflow)")

# Input 4 ฟิลด์
with st.form("match_analysis_form"):
    st.markdown("### 📥 Input")
    
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        player_a = st.text_input("🎾 Player A", value="Alcaraz", placeholder="e.g., Alcaraz")
        player_b = st.text_input("🎾 Player B", value="Sinner", placeholder="e.g., Sinner")
        tournament = st.text_input("🏆 Tournament", value="US Open 2026", placeholder="e.g., US Open 2026")
        surface = st.selectbox("🎨 Surface", ["Hard", "Clay", "Grass"], index=0)
    
    with col_input2:
        hc_line_a = st.number_input("📊 HC Line A (e.g., -2.5)", value=-2.5, step=0.5)
        hc_line_b = st.number_input("📊 HC Line B (e.g., +2.5)", value=2.5, step=0.5)
        ou_line = st.number_input("📊 O/U Line (total games)", value=22.5, step=0.5)
    
    submitted = st.form_submit_button("🎯 Analyze Match", type="primary", use_container_width=True)

# Process analysis
if submitted:
    if not player_a or not player_b:
        st.error("❌ กรุณาใส่ชื่อผู้เล่นทั้งสอง")
    else:
        match_info = {
            "player_a": player_a,
            "player_b": player_b,
            "tournament": tournament,
            "surface": surface,
            "hc_line_a": hc_line_a,
            "hc_line_b": hc_line_b,
            "ou_line": ou_line
        }
        
        st.markdown("### 🔄 Analysis Progress (5 Rounds)")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        round_progress = {
            "Round A": 0.1,
            "Round B": 0.3,
            "Round C": 0.5,
            "Round D": 0.7,
            "Round E": 0.9,
            "Done": 1.0
        }
        
        def progress_callback(round_name, message):
            status_text.markdown(f"**{round_name}:** {message}")
            if round_name in round_progress:
                progress_bar.progress(round_progress[round_name])
        
        # รัน Orchestrator
        try:
            orchestrator = Orchestrator()
            with st.spinner("🧠 Running full analysis pipeline..."):
                verdict = orchestrator.analyze_match(match_info, progress_callback=progress_callback)
            
            progress_bar.progress(1.0)
            status_text.markdown("**✅ Analysis Complete!**")
            
            if verdict:
                # เก็บผลลัพธ์ใน session_state
                st.session_state['last_verdict'] = verdict
                st.session_state['last_match_info'] = match_info
                st.rerun()
            else:
                st.error("❌ Analysis failed. ตรวจสอบ log ด้านบน")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# แสดง verdict (ถ้ามี)
if 'last_verdict' in st.session_state and st.session_state['last_verdict']:
    verdict = st.session_state['last_verdict']
    match_info = st.session_state.get('last_match_info', {})
    
    st.markdown("---")
    st.subheader("💎 Final Verdict")
    
    # Match Info
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("🎾 Match", f"{match_info.get('player_a')} vs {match_info.get('player_b')}")
    with col_info2:
        st.metric("🏆 Tournament", match_info.get('tournament', 'N/A'))
    with col_info3:
        st.metric("🎨 Surface", match_info.get('surface', 'N/A'))
    
    # Apex Pick (Best Pick)
    apex = verdict.get('apex_pick', {})
    if apex:
        st.markdown("### 🏆 APEX PICK (ฟันธง)")
        
        col_apex1, col_apex2, col_apex3 = st.columns(3)
        with col_apex1:
            st.metric("🎯 Option", apex.get('option', 'N/A'))
        with col_apex2:
            prob = apex.get('probability', 0)
            st.metric("📊 Probability", f"{prob*100:.1f}%")
        with col_apex3:
            st.metric("🎲 Confidence", apex.get('confidence', 'N/A'))
        
        with st.expander("📖 ดูรายละเอียด Apex Pick"):
            st.markdown(f"**Bet Sizing:** {apex.get('bet_sizing', 'N/A')}")
            st.markdown(f"**Most Likely Path:** {apex.get('most_likely_path', 'N/A')}")
            
            backup = apex.get('backup_paths', [])
            if backup:
                st.markdown("**Backup Paths:**")
                for path in backup:
                    st.markdown(f"- {path}")
            
            st.warning(f"**⚠️ Risk Warning:** {apex.get('risk_warning', 'N/A')}")
    
    # Option Crucible (3-Part Picks)
    crucible = verdict.get('option_crucible', [])
    if crucible:
        st.markdown("### ⚖️ Option Crucible Matrix (3-Part Picks)")
        
        for opt in crucible:
            with st.expander(f"**{opt.get('option', 'Unknown')}** — {opt.get('status', 'N/A')}"):
                col_o1, col_o2 = st.columns(2)
                with col_o1:
                    prob = opt.get('true_hit_probability', 0)
                    st.metric("📊 True Hit Probability", f"{prob*100:.1f}%")
                with col_o2:
                    st.metric("📈 Edge", opt.get('edge', 'N/A'))
                
                st.markdown(f"**Reasoning:** {opt.get('reasoning', 'N/A')}")
                
                # Quality Gate
                prob = opt.get('true_hit_probability', 0)
                if prob >= 0.60:
                    st.success(f"✅ **QUALITY GATE PASSED** ({prob*100:.1f}% ≥ 60%)")
                else:
                    st.warning(f"⚠️ **Quality Gate Not Met** ({prob*100:.1f}% < 60%)")
    
    # Vacuum Analysis
    vacuum = verdict.get('vacuum_analysis', {})
    if vacuum:
        with st.expander("🌌 Vacuum Analysis"):
            patterns = vacuum.get('dominant_patterns', [])
            if patterns:
                st.markdown("**Dominant Patterns:**")
                for p in patterns:
                    st.markdown(f"- {p}")
            
            risks = vacuum.get('key_risks', [])
            if risks:
                st.markdown("**Key Risks:**")
                for r in risks:
                    st.markdown(f"- {r}")
    
    # In-Play Triggers
    triggers = verdict.get('in_play_triggers', [])
    if triggers:
        with st.expander(f"🎯 In-Play Trigger Matrix ({len(triggers)} scenarios)"):
            for i, trigger in enumerate(triggers, 1):
                st.markdown(f"**Trigger {i}:** {trigger.get('trigger', 'N/A')}")
                st.markdown(f"- Action: **{trigger.get('action', 'N/A')}**")
                st.markdown(f"- Reasoning: {trigger.get('reasoning', 'N/A')}")
                st.markdown("---")
    
    # Final Directive
    final = verdict.get('final_directive', {})
    if final:
        with st.expander("💡 Final Directive"):
            st.markdown(f"**Recommendation:** {final.get('recommendation', 'N/A')}")
            st.markdown(f"**Summary:** {final.get('summary', 'N/A')}")
    
    # Raw Verdict
    with st.expander("🔍 Raw Verdict JSON (debug)"):
        st.json(verdict)

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("OMNIS-COURT v7.1 | $0 System | Part 4: Core Engine Active")
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
