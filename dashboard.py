import streamlit as st
import requests
import json
import time

# ==========================================
# OMNIS-COURT STATUS DASHBOARD
# Deployed on Render - Free Tier
# ==========================================

st.set_page_config(
    page_title="OMNIS-COURT Dashboard",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 OMNIS-COURT Command Center")
st.markdown("ระบบตรวจสอบสุขภาพ Infrastructure แบบ Real-time")

# Auto-refresh every 60 seconds
if st.button("🔄 Refresh Now"):
    st.rerun()

# Load Config
st.markdown("---")
st.subheader("📁 Configuration")

try:
    with open('config/platforms.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    st.success("✅ โหลด config/platforms.json สำเร็จ")
except FileNotFoundError:
    st.error("❌ ไม่พบไฟล์ config/platforms.json")
    st.info("💡 สร้างไฟล์ config/platforms.json ในโฟลเดอร์ config/")
    st.stop()
except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
    st.stop()

omnis = config.get('omnis_court', {})
search_cfg = config.get('search_engine', {})

# Health check function
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
# DASHBOARD GRID
# ==========================================

st.markdown("---")
st.subheader("🔍 Service Status")

# Service 1: SearXNG
searxng_url = search_cfg.get('searxng_url', 'http://localhost:8080')
check_health("SearXNG", searxng_url, "🔍")

st.markdown("")

# Service 2: LLM (Qwen3)
llm_url = omnis.get('llm_api_url', '')
if llm_url:
    check_health("Qwen3-14B LLM", f"{llm_url}/models", "🧠")
else:
    st.warning("⚠️ ไม่พบ LLM URL ใน config")

st.markdown("")

# Service 3: Jina Reader
jina_url = omnis.get('jina_reader_url', '')
if jina_url:
    jina_health_url = jina_url.split('?')[0].replace('/extract', '/health')
    check_health("Jina Reader", jina_health_url, "📖")
else:
    st.warning("⚠️ ไม่พบ Jina URL ใน config")

# ==========================================
# QUICK TESTS
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
                        st.json(data['results'][0])
                else:
                    st.error(f"❌ HTTP {r.status_code}")
            except Exception as e:
                st.error(f"❌ {str(e)[:50]}")

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
                    st.text_area("เนื้อหา (500 คำแรก)", 
                               data.get('content', '')[:500], 
                               height=150)
                else:
                    st.error(f"❌ HTTP {r.status_code}")
            except Exception as e:
                st.error(f"❌ {str(e)[:50]}")

# ==========================================
# FOOTER
# ==========================================

st.markdown("---")
st.caption("OMNIS-COURT v7.1 | $0 System Architecture | Config-Driven | Deployed on Render")
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
