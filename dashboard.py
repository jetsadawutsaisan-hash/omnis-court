import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from llm_client import LLMClient
from search_client import SearchClient
from monte_carlo import MonteCarloExecutor
from orchestrator import Orchestrator
from streamlit_js_eval import streamlit_js_eval

# ==========================================
# OMNIS-COURT DASHBOARD v4.10 FINAL
# LocalStorage: Auto-Load + Manual Save (Fixed)
# ==========================================

st.set_page_config(
    page_title="OMNIS-COURT Dashboard",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 OMNIS-COURT Command Center")

# ==========================================
# LOCALSTORAGE HELPER (streamlit-js-eval)
# ==========================================
def save_to_localstorage(key, value):
    """Save to browser LocalStorage"""
    try:
        json_value = json.dumps(value, default=str)
        # ใช้ fixed key (ไม่เปลี่ยนตามเวลา)
        result = streamlit_js_eval(
            js_expressions=f"localStorage.setItem('omnis_{key}', {json.dumps(json_value)}); 'ok';",
            key=f'save_{key}_fixed'
        )
        return True  # Assume success (JS async)
    except Exception as e:
        print(f"Save error: {e}")
        return False

def load_from_localstorage_once():
    """Load from LocalStorage (ครั้งเดียวตอนเริ่มต้น)
    
    IMPORTANT: streamlit_js_eval returns None on first run (async).
    On second run (rerun), it returns actual value from JS.
    We use '_load_attempted' flag to avoid retrying forever.
    """
    # Check if already attempted
    if st.session_state.get('_load_attempted', False):
        return
    
    # Mark as attempted (prevent retry)
    st.session_state._load_attempted = True
    
    try:
        # Load queue
        queue_str = streamlit_js_eval(
            js_expressions="localStorage.getItem('omnis_queue') || '[]'",
            key='load_queue_fixed'
        )
        
        # First run: queue_str is None (async)
        # Second run: queue_str is actual string
        if queue_str is not None and queue_str != 'null' and queue_str != '[]':
            try:
                queue_data = json.loads(queue_str)
                if isinstance(queue_data, list) and len(queue_data) > 0:
                    st.session_state.analysis_queue = queue_data
            except Exception as e:
                print(f"Load queue parse error: {e}")
        
        # Load results
        results_str = streamlit_js_eval(
            js_expressions="localStorage.getItem('omnis_results') || '[]'",
            key='load_results_fixed'
        )
        
        if results_str is not None and results_str != 'null' and results_str != '[]':
            try:
                results_data = json.loads(results_str)
                if isinstance(results_data, list) and len(results_data) > 0:
                    st.session_state.analysis_results = results_data
            except Exception as e:
                print(f"Load results parse error: {e}")
        
    except Exception as e:
        print(f"Load from LocalStorage error: {e}")

def clear_localstorage():
    """Clear all LocalStorage + session state"""
    try:
        streamlit_js_eval(
            js_expressions="localStorage.removeItem('omnis_queue'); localStorage.removeItem('omnis_results'); 'ok';",
            key='clear_storage_fixed'
        )
        
        st.session_state.analysis_queue = []
        st.session_state.analysis_results = []
        st.session_state.current_analysis = None
        st.session_state.phase_0_state = 'idle'
        st.session_state.phase_0_data = None
        st.session_state.find_upcoming_result = None
        st.session_state._load_attempted = False  # Allow reload
        
    except Exception as e:
        st.error(f"❌ Clear error: {e}")

# ==========================================
# INITIALIZE SESSION STATE
# ==========================================
if 'analysis_queue' not in st.session_state:
    st.session_state.analysis_queue = []

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []

if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

if 'current_progress' not in st.session_state:
    st.session_state.current_progress = {"round": "", "message": ""}

if 'phase_0_state' not in st.session_state:
    st.session_state.phase_0_state = 'idle'

if 'phase_0_data' not in st.session_state:
    st.session_state.phase_0_data = None

if 'find_upcoming_result' not in st.session_state:
    st.session_state.find_upcoming_result = None

if '_load_attempted' not in st.session_state:
    st.session_state._load_attempted = False

# ==========================================
# AUTO-LOAD FROM LOCALSTORAGE
# ==========================================
load_from_localstorage_once()

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
    check_health("Qwen3-8B", f"{llm_url}/models", "🧠")

jina_url = omnis.get('jina_reader_url', '')
if jina_url:
    health_url = jina_url.split('?')[0].replace('/extract', '/health')
    check_health("Jina Reader", health_url, "📖")

# ==========================================
# 📝 ADD NEW MATCH (Form)
# ==========================================
st.markdown("---")
st.subheader("📝 Add New Match")

with st.form("add_match_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        player_a = st.text_input("🎾 Player A", placeholder="e.g., Alcaraz")
        player_b = st.text_input("🎾 Player B", placeholder="e.g., Sinner")
        tournament = st.text_input("🏆 Tournament (optional - auto-detect)",
                                   placeholder="e.g., US Open 2026")
    
    with col2:
        hc_line_a = st.number_input("📊 HC Line A", value=-2.5, step=0.5)
        hc_line_b = st.number_input("📊 HC Line B", value=2.5, step=0.5)
        ou_line = st.number_input("📊 O/U Line", value=22.5, step=0.5)
        
        match_time = datetime.now() + timedelta(hours=2)
        st.info(f"⏰ Match Time: **{match_time.strftime('%H:%M %d/%m/%Y')}** (auto-set)")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        skip_queue = st.form_submit_button("⚡ ลัดคิว (Analyze Now)",
                                          type="primary", use_container_width=True)
    
    with col_btn2:
        add_to_queue = st.form_submit_button("➕ เพิ่มคิว", use_container_width=True)

if skip_queue or add_to_queue:
    if not player_a or not player_b:
        st.error("❌ กรุณาใส่ชื่อผู้เล่นทั้งสอง")
    else:
        match_info = {
            "player_a": player_a,
            "player_b": player_b,
            "tournament": tournament if tournament else "",
            "surface": "Unknown",
            "hc_line_a": hc_line_a,
            "hc_line_b": hc_line_b,
            "ou_line": ou_line,
            "match_time": match_time.isoformat() if isinstance(match_time, datetime) else match_time,
            "added_at": datetime.now().isoformat()
        }
        
        if skip_queue:
            st.session_state.current_analysis = match_info
            st.session_state.phase_0_state = 'detecting'
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
            if match.get('tournament'):
                st.caption(match['tournament'])
        
        with col2:
            mt = match['match_time']
            if isinstance(mt, str):
                try:
                    mt = datetime.fromisoformat(mt)
                except:
                    pass
            st.caption(f"⏰ {mt.strftime('%H:%M %d/%m') if isinstance(mt, datetime) else mt}")
        
        with col3:
            st.caption(f"HC: {match['hc_line_a']}/{match['hc_line_b']} | O/U: {match['ou_line']}")
        
        with col4:
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state.analysis_queue.pop(i)
                st.rerun()
        
        st.markdown("---")
    
    if not st.session_state.current_analysis and st.session_state.phase_0_state == 'idle':
        if st.button("▶️ Start Queue Analysis", type="primary"):
            st.session_state.current_analysis = st.session_state.analysis_queue.pop(0)
            st.session_state.phase_0_state = 'detecting'
            st.rerun()
else:
    st.info("💡 คิวว่าง - เพิ่มแมตช์ด้านบน")

# ==========================================
# 🎯 PHASE 0 + CURRENT ANALYSIS
# ==========================================
if st.session_state.current_analysis:
    st.markdown("---")
    st.subheader("🎯 Current Analysis")
    
    match = st.session_state.current_analysis
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎾 Match", f"{match['player_a']} vs {match['player_b']}")
    with col2:
        mt = match['match_time']
        if isinstance(mt, str):
            try:
                mt = datetime.fromisoformat(mt)
            except:
                pass
        st.metric("⏰ Time", mt.strftime('%H:%M') if isinstance(mt, datetime) else mt)
    with col3:
        st.metric("📊 Lines", f"HC: {match['hc_line_a']} | O/U: {match['ou_line']}")
    
    # ═══ STATE 1: DETECTING ═══
    if st.session_state.phase_0_state == 'detecting':
        st.markdown("### 🔍 Phase 0: True Agentic Tournament Detection")
        st.info("⏳ LLM วางแผน → SearXNG ค้นหา → Jina extract ALL → LLM ตัดสินใจ")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def detect_progress(current, total, message):
            progress_bar.progress(current / total)
            status_text.markdown(f"**{message}**")
        
        try:
            search_client = SearchClient()
            detected = search_client.detect_tournament(
                player_a=match['player_a'],
                player_b=match['player_b'],
                max_retries=3,
                progress_callback=detect_progress,
                llm_client=LLMClient()
            )
            
            progress_bar.progress(1.0)
            
            if detected:
                st.session_state.phase_0_data = detected
                st.session_state.phase_0_state = 'confirm'
                st.rerun()
            else:
                st.session_state.phase_0_data = None
                st.session_state.phase_0_state = 'editing'
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Detection error: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state.phase_0_state = 'editing'
            st.rerun()
    
    # ═══ STATE 2: CONFIRM ═══
    elif st.session_state.phase_0_state == 'confirm' and st.session_state.phase_0_data:
        st.markdown("### 🤖 Auto-Detected Match Context (True Agentic)")
        
        data = st.session_state.phase_0_data
        
        col_c1, col_c2 = st.columns([3, 1])
        
        with col_c1:
            st.markdown(f"""
            | Field | Value |
            |-------|-------|
            | 🏆 **Tournament** | **{data.get('tournament', 'Unknown')}** |
            | 🎨 **Surface** | **{data.get('surface', 'Unknown')}** |
            | 🎯 **Round** | {data.get('round', 'Unknown')} |
            | 🏟️ **Court** | {data.get('court', 'Unknown')} |
            | ⚡ **Court Speed** | {data.get('court_speed', 'N/A')} |
            | 🎾 **Ball** | {data.get('ball', 'Unknown')} |
            | 🌡️ **Weather** | {data.get('weather', {})} |
            | 🎲 **Confidence** | **{data.get('confidence', 'LOW')}** |
            | 🔍 **Searches** | {data.get('total_searches', 0)} queries |
            | 📄 **Articles** | {data.get('total_articles', 0)} articles |
            """)
            
            conf = data.get('confidence', 'LOW')
            if conf == 'HIGH':
                st.success(f"✅ **HIGH Confidence** (Attempt {data.get('attempt', 0)}/3)")
            elif conf == 'MEDIUM':
                st.warning(f"⚠️ **MEDIUM Confidence** (Attempt {data.get('attempt', 0)}/3)")
            else:
                st.error(f"❌ **LOW Confidence** (Attempt {data.get('attempt', 0)}/3)")
            
            if data.get('evidence'):
                st.info(f"📝 **Evidence:** {data['evidence']}")
            
            source_urls = data.get('source_urls', [])
            if source_urls:
                with st.expander(f"🔗 Source URLs ({len(source_urls)})"):
                    for url in source_urls:
                        st.caption(f"• {url}")
        
        with col_c2:
            st.markdown("### Actions:")
            
            if st.button("✅ ยืนยัน", type="primary", use_container_width=True, key="confirm_yes"):
                match['tournament'] = data.get('tournament') or 'Unknown'
                match['surface'] = data.get('surface') or 'Hard'
                match['round'] = data.get('round', 'Unknown')
                match['court'] = data.get('court', 'Unknown')
                match['court_speed'] = data.get('court_speed')
                match['ball'] = data.get('ball', 'Unknown')
                match['weather'] = data.get('weather', {})
                st.session_state.current_analysis = match
                st.session_state.phase_0_state = 'analyzing'
                st.rerun()
            
            if st.button("✏️ แก้ไข", use_container_width=True, key="confirm_edit"):
                st.session_state.phase_0_state = 'editing'
                st.rerun()
            
            if st.button("🗑️ ลบ/ใช้ Default", use_container_width=True, key="confirm_delete"):
                match['tournament'] = 'Unknown Tournament'
                match['surface'] = 'Hard'
                st.session_state.current_analysis = match
                st.session_state.phase_0_state = 'analyzing'
                st.rerun()
    
    # ═══ STATE 3: EDITING ═══
    elif st.session_state.phase_0_state == 'editing':
        st.markdown("### ✏️ Manual Tournament Input")
        
        if not st.session_state.phase_0_data:
            st.warning("⚠️ Auto-detect ไม่พบ tournament กรุณากรอกเอง")
        else:
            st.info("✏️ แก้ไขข้อมูลที่ตรวจพบ")
        
        data = st.session_state.phase_0_data or {}
        
        with st.form("manual_tournament_form"):
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                manual_tournament = st.text_input("🏆 Tournament",
                                                 value=data.get('tournament', ''),
                                                 placeholder="e.g., Roland Garros 2026")
                
                manual_surface = st.selectbox("🎨 Surface",
                                             options=["Hard", "Clay", "Grass"],
                                             index=["Hard", "Clay", "Grass"].index(data.get('surface', 'Hard')) if data.get('surface') in ["Hard", "Clay", "Grass"] else 0)
                
                manual_round = st.text_input("🎯 Round",
                                            value=data.get('round', ''),
                                            placeholder="e.g., Semi-Final, R16")
            
            with col_m2:
                manual_court = st.text_input("🏟️ Court Name",
                                            value=data.get('court', ''),
                                            placeholder="e.g., Philippe Chatrier")
                
                manual_speed = st.number_input("⚡ Court Speed (1.0-4.0)",
                                              min_value=1.0, max_value=4.0,
                                              value=float(data.get('court_speed', 2.5)) if data.get('court_speed') else 2.5,
                                              step=0.1)
                
                manual_ball = st.text_input("🎾 Ball Brand",
                                           value=data.get('ball', ''),
                                           placeholder="e.g., Dunlop ATP")
            
            col_mbtn1, col_mbtn2 = st.columns(2)
            
            with col_mbtn1:
                submit_manual = st.form_submit_button("✅ ยืนยันข้อมูล",
                                                     type="primary",
                                                     use_container_width=True)
            
            with col_mbtn2:
                retry_detect = st.form_submit_button("🔄 ลอง Auto-Detect อีกครั้ง",
                                                    use_container_width=True)
        
        if submit_manual:
            match['tournament'] = manual_tournament or 'Unknown Tournament'
            match['surface'] = manual_surface
            match['round'] = manual_round or 'Unknown'
            match['court'] = manual_court or 'Unknown'
            match['court_speed'] = manual_speed
            match['ball'] = manual_ball or 'Unknown'
            st.session_state.current_analysis = match
            st.session_state.phase_0_state = 'analyzing'
            st.rerun()
        
        if retry_detect:
            st.session_state.phase_0_state = 'detecting'
            st.rerun()
    
    # ═══ STATE 4: ANALYZING ═══
    elif st.session_state.phase_0_state == 'analyzing':
        st.markdown("### 🧠 Running Analysis Pipeline (True Agentic)")
        
        st.markdown(f"""
        **Using Context:**
        - 🏆 {match.get('tournament', 'Unknown')}
        - 🎨 {match.get('surface', 'Unknown')}
        - 🎯 {match.get('round', 'Unknown')}
        """)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(round_name, message):
            status_text.markdown(f"**{round_name}:** {message}")
            round_progress = {
                "Round 0": 0.05,
                "Round A": 0.20,
                "Round B": 0.45,
                "Round C": 0.65,
                "Round D": 0.80,
                "Round E": 0.95,
                "Done": 1.0
            }
            if round_name in round_progress:
                progress_bar.progress(round_progress[round_name])
        
        try:
            orchestrator = Orchestrator()
            with st.spinner("🧠 Running analysis pipeline..."):
                verdict = orchestrator.analyze_match(
                    match,
                    progress_callback=progress_callback,
                    skip_tournament_detection=True
                )
            
            progress_bar.progress(1.0)
            status_text.markdown("**✅ Analysis Complete!**")
            
            if verdict:
                st.session_state.analysis_results.append({
                    'match_info': match,
                    'verdict': verdict,
                    'completed_at': datetime.now().isoformat()
                })
                
                st.session_state.current_analysis = None
                st.session_state.phase_0_state = 'idle'
                st.session_state.phase_0_data = None
                
                if st.session_state.analysis_queue:
                    st.session_state.current_analysis = st.session_state.analysis_queue.pop(0)
                    st.session_state.phase_0_state = 'detecting'
                
                st.rerun()
            else:
                st.error("❌ Analysis failed")
                st.session_state.current_analysis = None
                st.session_state.phase_0_state = 'idle'
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state.current_analysis = None
            st.session_state.phase_0_state = 'idle'

# ==========================================
# 💎 RESULTS
# ==========================================
if st.session_state.analysis_results:
    st.markdown("---")
    st.subheader(f"💎 Results ({len(st.session_state.analysis_results)} completed)")
    
    for i, result in enumerate(reversed(st.session_state.analysis_results)):
        match = result['match_info']
        verdict = result['verdict']
        
        completed_at = result['completed_at']
        if isinstance(completed_at, str):
            try:
                completed_at = datetime.fromisoformat(completed_at)
            except:
                pass
        
        with st.expander(f"**{match['player_a']} vs {match['player_b']}** — {completed_at.strftime('%H:%M %d/%m') if isinstance(completed_at, datetime) else completed_at}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🎾 Match", f"{match['player_a']} vs {match['player_b']}")
            with col2:
                st.metric("🏆 Tournament", match.get('tournament', 'Unknown'))
            with col3:
                st.metric("🎨 Surface", match.get('surface', 'Unknown'))
            
            # Show reasoning (Chain-of-Thought)
            if verdict.get('_metadata', {}).get('reasoning'):
                with st.expander("🧠 LLM Reasoning (Chain-of-Thought)"):
                    st.markdown(verdict['_metadata']['reasoning'])
            
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
# 🧪 TEST: FIND UPCOMING MATCH
# ==========================================
st.markdown("---")
st.subheader("🧪 System Test: Find Upcoming Match")

st.markdown("""
ปุ่มนี้จะทดสอบว่า **LLM Team** ทำงานได้ถูกต้องหรือไม่:
- 🧠 LLM คิดว่าจะหาแมตช์ยังไง
- 🔍 SearXNG over-fetch URLs
- 📖 Jina extract **ALL** content
- 🧠 LLM วิเคราะห์หาแมตช์ที่จะแข่งใน 2 ชม. ข้างหน้า
""")

col_test1, col_test2 = st.columns([1, 3])

with col_test1:
    if st.button("🔍 Find Upcoming Match (Next 2 Hours)", type="primary"):
        with st.spinner("🧠 LLM Team กำลังทำงาน..."):
            try:
                search_client = SearchClient()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def test_progress(current, total, message):
                    progress_bar.progress(current / total)
                    status_text.markdown(f"**{message}**")
                
                result = search_client.find_upcoming_match(
                    hours_ahead=2,
                    max_retries=2,
                    progress_callback=test_progress,
                    llm_client=LLMClient()
                )
                
                progress_bar.progress(1.0)
                st.session_state.find_upcoming_result = result
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
                import traceback
                st.code(traceback.format_exc())

with col_test2:
    if st.session_state.find_upcoming_result:
        result = st.session_state.find_upcoming_result
        
        if result.get('best_match'):
            best = result['best_match']
            st.success(f"✅ **พบ {result.get('total_found', 0)} แมตช์! Best match:**")
            st.markdown(f"""
            - 🎾 **{best.get('player_a')}** vs **{best.get('player_b')}**
            - 🏆 {best.get('tournament', 'Unknown')}
            - 🎨 {best.get('surface', 'Unknown')} | 🎯 {best.get('round', 'Unknown')}
            - ⏰ {best.get('scheduled_time', 'N/A')}
            - 🏟️ {best.get('court', 'Unknown')}
            - 🔗 [Source]({best.get('source_url', '#')})
            """)
        else:
            st.warning(f"⚠️ ไม่พบแมตช์ใน window {result.get('time_window', 'N/A')}")
            if result.get('reasoning'):
                st.info(result['reasoning'])
        
        if st.button("🗑️ Clear Test Result"):
            st.session_state.find_upcoming_result = None
            st.rerun()

# ==========================================
# 🧪 DEBUG TESTS
# ==========================================
with st.expander("🧪 Debug Tests"):
    col1, col2, col3 = st.columns(3)
    
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
    
    with col3:
        if st.button("🗑️ Clear All Data", type="secondary"):
            clear_localstorage()
            st.success("✅ All data cleared!")
            st.rerun()

# ==========================================
# 💾 MANUAL SAVE TO LOCALSTORAGE
# ==========================================
st.markdown("---")
st.subheader("💾 Save Data to Browser (Manual)")

st.info("""
**LocalStorage ทำงานเมื่อกดปุ่มเท่านั้น** (ไม่ auto-save เพื่อป้องกัน hang)
- กด **Save** เพื่อบันทึกข้อมูลลง browser
- **Auto-load** เมื่อ refresh หน้าเว็บ (ข้อมูลจะไม่หาย)
- กด **Clear** เพื่อลบข้อมูลทั้งหมด
""")

col_save1, col_save2 = st.columns(2)

with col_save1:
    if st.button("💾 Save to LocalStorage", type="primary", use_container_width=True):
        save_to_localstorage('queue', st.session_state.analysis_queue)
        save_to_localstorage('results', st.session_state.analysis_results)
        st.success(f"✅ Saved! Queue: {len(st.session_state.analysis_queue)} | Results: {len(st.session_state.analysis_results)}")
        st.info("💡 Refresh หน้าเว็บเพื่อเช็คว่า load กลับมา")

with col_save2:
    if st.button("🗑️ Clear LocalStorage", use_container_width=True):
        clear_localstorage()
        st.success("✅ LocalStorage cleared!")
        st.rerun()

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("OMNIS-COURT v7.1 | True Agentic + LocalStorage (v4.10) | Fixed async loading")
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
st.caption(f"💾 Queue: {len(st.session_state.analysis_queue)} | Results: {len(st.session_state.analysis_results)}")
