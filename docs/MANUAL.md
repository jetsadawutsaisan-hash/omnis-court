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
LLM URL: https://xxx.trycloudflare.com 7

JINA URL: https://yyy.trycloudflare.com
6. **Copy both URLs**
7. Open `config/platforms.json` on GitHub
8. Replace:
- `llm.primary.tunnel_url` → paste LLM URL
- `search.jina_primary_url` → paste Jina URL
9. Commit changes
10. Refresh Dashboard → should show 🟢

### After Setup

- **Close the Colab tab** (anti-idle keeps it running)
- Servers will run for up to 12 hours
- No need to keep browser open

---

## 🔀 Platform Swap Guide

### When to Swap

- Dashboard shows Colab quota < 5 hours remaining
- Colab disconnects permanently
- LINE alert notifies you

### How to Swap (Colab → Kaggle)

1. Go to: [KAGGLE_NOTEBOOK_LINK]
2. Ensure GPU is enabled (Settings → Accelerator → GPU)
3. Click **Run All**
4. Wait 10 minutes for URLs
5. Copy both URLs
6. Edit `config/platforms.json`:
- Set `llm.primary.tunnel_url` → Kaggle LLM URL
- Set `search.jina_primary_url` → Kaggle Jina URL
- Optionally update `llm.primary.name` to "kaggle_backup"
7. Commit changes
8. Refresh Dashboard
9. Close Kaggle tab when done

### Swap Back (Kaggle → Colab)

Same steps but with Colab notebook. Usually done after weekly quota reset (Monday).

---

## ⚠️ Troubleshooting

### Dashboard Shows 🔴 But Just Ran Notebook

**Cause**: Wrong runtime type  
**Fix**: Runtime → Change runtime type → Select **T4 GPU** → Re-run

### No Tunnel URL Appears

**Cause**: Cloudflare temporary issue  
**Fix**: 
1. Wait 2 minutes
2. Re-run Cell 5 only
3. If still fails → Runtime → Restart runtime → Run All

### SearXNG Not Responding

**Cause**: Render free tier sleep or crash  
**Fix**:
1. Go to [RENDER_DASHBOARD](https://render.com)
2. Check logs for errors
3. If crashed → click "Manual Deploy → Deploy latest commit"
4. UptimeRobot will auto-wake within 10 minutes

### Content Valid < 20 URLs

**Cause**: Small tournament / obscure players  
**Action**: System auto-SKIPS this match. No manual action needed.

### Both Colab + Kaggle Quota Exhausted

**Cause**: Heavy usage week  
**Options**:
1. Wait for Monday reset
2. Open backup Gmail account (if prepared)
3. Skip analysis for remaining days

---

## 🔗 Quick Reference Links

| Resource | Link |
|----------|------|
| Dashboard | [TO_BE_FILLED] |
| Colab Notebook | [TO_BE_FILLED] |
| Kaggle Notebook | [TO_BE_FILLED] |
| GitHub Repo | https://github.com/YOUR_USERNAME/omnis-court |
| SearXNG API | https://omnis-search.onrender.com |
| Config File | https://github.com/YOUR_USERNAME/omnis-court/blob/main/config/platforms.json |
| Render Dashboard | https://render.com |
| UptimeRobot | https://uptimerobot.com |

---

## 📊 Understanding Dashboard Status

| Icon | Meaning | Action Required |
|------|---------|----------------|
| 🟢 ONLINE | Service running normally | None |
| 🟡 WARNING | Quota low (<5 hrs) or degraded | Prepare to swap |
| 🔴 OFFLINE | Service not running | Open notebook immediately |
| ⚪ UNKNOWN | Cannot reach service | Check internet / retry |

---

## 🆘 Emergency Contacts

If everything fails and you cannot restore:
1. Check GitHub Issues for known problems
2. Review Render/Colab logs
3. Wait for quota reset
4. System is designed to gracefully SKIP matches when unavailable
