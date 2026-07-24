# 📘 OMNIS-COURT Operations Manual

## 🔄 Daily Startup Routine (Every Day, ~12 min)

### Morning Check (8:00 AM)

1. **Open Dashboard**: [DASHBOARD_URL]
2. **Check Status**:
   - 🟢 SearXNG = Online → OK
   - 🔴 Colab LLM = Offline → Must open now
   - 🔴 Jina Reader = Offline → Must open now

### If Colab Needs Opening

1. Go to: [COLAB_NOTEBOOK_LINK]
2. Menu: **Runtime → Change runtime type → T4 GPU → Save**
3. Click **Run All** (or press Ctrl+F9)
4. **Wait 10 minutes** (model download + server startup)
5. When you see both URLs printed:
