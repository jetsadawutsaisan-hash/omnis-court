import streamlit as st
import requests
import json
import time
from llm_client import LLMClient

# ==========================================
# OMNIS-COURT STATUS DASHBOARD v2.0
# Deployed on Render - Free Tier
# ==========================================

st.set_page_config(
    page_title="OMNIS-COURT Dashboard",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 OMNIS-COURT Command Center")
st.markdown("ระบบตรวจสอบสุขภาพ Infrastructure แบบ Real-time")

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

# SearXNG
searxng_url = search_cfg.get('searxng_url', 'http://localhost:8080')
check_health("SearXNG", searxng_url, "🔍")
st.markdown("")

# Qwen3 LLM
llm_url = omnis.get('llm_api_url', '')
if llm_url:
    check_health("Qwen3-14B LLM", f"{llm_url}/models", "🧠")
else:
    st.warning("⚠️ ไม่พบ LLM URL ใน config")
st.markdown("")

# Jina Reader
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
# 🧠 TEST LLM (NEW!)
# ==========================================
st.markdown("---")
st.subheader("🧠 Test LLM (Qwen3-14B)")
st.markdown("ทดสอบการส่ง prompt ไปยัง Qwen3-14B โดยตรง")

# Prompt templates
prompt_templates = {
    "🔹 ทดสอบพื้นฐาน": "Hello! Please respond with 'OK' if you can read this.",
    "🔹 ทดสอบภาษาไทย": "สวัสดีครับ ช่วยตอบกลับเป็นภาษาไทยว่า 'ระบบทำงานปกติ'",
    "🔹 ทดสอบ JSON": "Return a JSON object: {\"status\": \"ok\", \"model\": \"qwen3-14b\"}. Return ONLY JSON, no markdown.",
    "🔹 ทดสอบเทนนิส": "Who won Wimbledon 2024 men's singles? Answer in one sentence.",
    "🔹 ทดสอบยาว": "Explain the rules of tennis scoring in 3 paragraphs."
}

col_template, col_params = st.columns([2, 1])

with col_template:
    selected_template = st.selectbox(
        "📝 เลือก Prompt Template (หรือพิมพ์เองด้านล่าง):",
        options=list(prompt_templates.keys())
    )

with col_params:
    temperature = st.slider("🌡️ Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("📏 Max Tokens", 100, 8192, 1024, 100)

# Text area for prompt
user_prompt = st.text_area(
    "✍️ Prompt (แก้ไขได้):",
    value=prompt_templates[selected_template],
    height=150
)

# Send button
col_send, col_clear = st.columns([1, 4])

with col_send:
    send_button = st.button("🚀 Send to Qwen", type="primary", use_container_width=True)

with col_clear:
    if st.button("🗑️ Clear Output"):
        st.session_state['llm_response'] = None
        st.rerun()

# Process send button
if send_button:
    if not user_prompt.strip():
        st.warning("⚠️ กรุณาใส่ prompt")
    else:
        with st.spinner("🧠 กำลังส่งไปยัง Qwen3-14B... (อาจใช้เวลา 10-60 วินาที)"):
            try:
                # Initialize LLM Client
                client = LLMClient()
                
                # Call LLM
                start_time = time.time()
                response = client.call_qwen(
                    prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                elapsed = time.time() - start_time
                
                if response:
                    st.session_state['llm_response'] = response
                    st.session_state['llm_elapsed'] = elapsed
                    st.session_state['llm_chars'] = len(response)
                    st.rerun()
                else:
                    st.error("❌ ไม่ได้รับการตอบกลับจาก LLM")
                    st.info("💡 ตรวจสอบว่า Colab ยังรันอยู่ และ URL ใน config ถูกต้อง")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

# Display response
if 'llm_response' in st.session_state and st.session_state['llm_response']:
    st.markdown("### 📨 Response")
    
    # Metadata
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("⏱️ เวลา", f"{st.session_state['llm_elapsed']:.1f} วินาที")
    with col_m2:
        st.metric("📏 ตัวอักษร", f"{st.session_state['llm_chars']:,}")
    with col_m3:
        st.metric("🔤 คำ (ประมาณ)", f"{st.session_state['llm_chars'] // 5:,}")
    
    # Response content
    with st.expander("📄 ดูคำตอบเต็ม", expanded=True):
        # ลอง render เป็น markdown ถ้าได้
        try:
            st.markdown(st.session_state['llm_response'])
        except:
            st.text(st.session_state['llm_response'])
    
    # Raw response
    with st.expander("🔍 ดู Raw Text (สำหรับ debug)"):
        st.code(st.session_state['llm_response'], language="text")

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("OMNIS-COURT v7.1 | $0 System Architecture | Config-Driven | Deployed on Render")
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
