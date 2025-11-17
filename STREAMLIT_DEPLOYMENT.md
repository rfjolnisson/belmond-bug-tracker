# Streamlit Cloud Deployment Guide

## 📦 Repository
✅ **Pushed to:** https://github.com/rfjolnisson/belmond-bug-tracker

## 🚀 Deploy to Streamlit Cloud

### 1. Go to Streamlit Cloud
Visit: https://share.streamlit.io/

### 2. Deploy New App
- Click "New app"
- Repository: `rfjolnisson/belmond-bug-tracker`
- Branch: `main`
- Main file path: `app.py`
- App URL: Choose your preferred URL

### 3. Configure Secrets (IMPORTANT!)

In the Streamlit Cloud app settings, add these secrets:

```toml
# .streamlit/secrets.toml format

JIRA_BASE_URL = "https://kaptio.atlassian.net"
JIRA_USERNAME = "your-email@kaptio.com"
JIRA_API_TOKEN = "your-api-token-here"
```

**Get your Jira API token:**
https://id.atlassian.com/manage-profile/security/api-tokens

### 4. Deploy!
Click "Deploy" and wait for the app to build (~2-3 minutes)

## 📋 Files Committed

✅ **Application Files:**
- `app.py` - Main Streamlit dashboard (1000+ lines)
- `jira_client.py` - Jira API integration
- `requirements.txt` - Python dependencies
- `.streamlit/config.toml` - Port 8502 configuration

✅ **Documentation:**
- `README.md` - Project overview
- `QUICKSTART.md` - Usage guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details

✅ **Setup Scripts:**
- `setup.sh` - Local environment setup
- `run.sh` - Local run script

✅ **Security:**
- `.gitignore` - Excludes .env and sensitive files
- ❌ `.env` - **NOT committed** (credentials protected)

## 🎯 Default Configuration

The app is configured to:
- Filter to **Blocker + Critical only** by default
- Exclude **rejected bugs** automatically
- Show bugs from epics: **ST-1746, ST-2049**
- Cache data for **5 minutes**
- Run on port **8502** (local) or auto-assigned (cloud)

## 🔧 Post-Deployment

After deployment:
1. Test the priority filter in sidebar
2. Verify blocker alerts appear
3. Check all 6 sections load correctly
4. Test data refresh button
5. Verify export buttons work

## 📊 What's Included

**6 Main Sections:**
1. Executive Summary (KPIs, Matrix, Aging, Cycle Time, Trends)
2. Team Workload (Performance + Capacity)
3. Blocker & Critical Dashboard (Filtered view)
4. Fix Version Progress (Release tracking)
5. Status Flow Analysis (Bottlenecks)
6. Detailed Bug List (Filterable + Export)

**Key Features:**
- Global priority filter (sidebar)
- Rejected bugs auto-excluded
- Monthly velocity trends
- Cycle time by priority
- Priority × Status matrix
- Aging analysis (30+ days = stuck)
- Team performance metrics
- CSV/Excel export

## ⚠️ Important Notes

1. **Credentials are NOT in the repo** - You must add them as Streamlit secrets
2. The app will error without proper Jira credentials
3. Data refreshes every 5 minutes automatically
4. Default filter shows only Blocker + Critical bugs
5. All rejected bugs are filtered out globally

## 🆘 Troubleshooting

**If app doesn't load:**
- Check secrets are properly set in Streamlit Cloud
- Verify Jira API token is valid
- Check JQL query works in Jira web UI

**If no data shows:**
- Verify JQL: `parent IN (ST-1746, ST-2049)`
- Check Jira credentials have read access
- Try refreshing the app

## 🎉 You're Done!

Once deployed, share the Streamlit Cloud URL with your team to provide instant visibility into Belmond bug status and help restore confidence! 🚀

