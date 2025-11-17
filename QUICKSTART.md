# Belmond Bug Tracker - Quick Start Guide

## 🎯 What This Dashboard Does

This dashboard addresses the Belmond program's confidence crisis by providing real-time visibility into:
- **Blocker & Critical Bugs**: Immediate alerts for high-priority issues
- **Team Capacity**: Who's working on what and who's overloaded
- **Sprint Progress**: Actual velocity vs. commitments
- **Bottlenecks**: Where bugs get stuck in the workflow
- **Actionable Insights**: Clear indicators of what needs attention NOW

## 📊 Key Features

### 1. Executive Summary
- 🚨 Blocker alerts (impossible to miss)
- Key metrics dashboard
- Confidence indicators (% stuck bugs, unassigned, completion rate)
- Fix version tracking

### 2. Team Workload
- Bug distribution per assignee
- Capacity analysis with overload warnings
- Status heatmap
- Unassigned high-priority bug alerts

### 3. Blocker & Critical Dashboard
- Laser focus on P0/P1 bugs
- Time-in-status tracking with color flags:
  - 🔴 Red: >7 days (critical)
  - 🟡 Yellow: 3-7 days (warning)
  - 🟢 Green: <3 days (healthy)

### 4. Sprint Progress Tracker
- Bugs by fix version (To Do → In Progress → Done)
- Velocity trends (bugs resolved per week)
- Reopened bug rate (quality indicator)
- Completion percentages

### 5. Status Flow Analysis
- Average time in each status
- Bottleneck identification
- Bugs stuck >7 days
- Status distribution visualization

### 6. Detailed Bug List
- Full searchable/sortable table
- Multi-filter capability (priority, status, assignee, epic)
- CSV/Excel export
- Direct Jira links

## 🚀 Getting Started

### One-Command Setup & Run

```bash
cd "/Users/ragnarfjolnisson/Documents/2025 Coding/belmond-defect-insights"
./setup.sh
./run.sh
```

### Manual Setup

1. **Setup virtual environment and install dependencies:**
```bash
cd "/Users/ragnarfjolnisson/Documents/2025 Coding/belmond-defect-insights"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Run the dashboard:**
```bash
streamlit run app.py
```

3. **Open in browser:**
The dashboard will automatically open at `http://localhost:8502`

## 🔑 JQL Query

The dashboard tracks all bugs from these epics:
```
parent IN (ST-1746, ST-2049) order BY fixVersion ASC, rank
```

## 📥 Data Refresh

- Data is cached for 5 minutes (prevents excessive API calls)
- Click "🔄 Refresh Data" in the sidebar to force refresh
- Last update timestamp shown in sidebar

## 💡 Usage Tips for Leadership

### During Daily Stand-ups
1. Start with **Executive Summary** - see blocker alerts immediately
2. Check **Team Workload** - identify who needs help
3. Review **Blocker & Critical** - triage stuck bugs

### For Sprint Planning
1. Use **Sprint Progress Tracker** - see current velocity
2. Check **Bug List** with filters - plan next sprint
3. Export data for offline analysis

### For Retrospectives
1. Review **Status Flow** - identify systemic bottlenecks
2. Check reopened bug rate - quality discussions
3. Analyze time-in-status patterns - process improvements

## 🎨 Visual Indicators

### Priority Colors
- 🔴 **Blocker**: Red (stop everything)
- 🟠 **Critical**: Orange (high urgency)
- 🟡 **Major**: Yellow (important)
- 🟢 **Minor/Trivial**: Green (lower priority)

### Status Flags
- 🟢 **Green**: Bug moving quickly (<3 days)
- 🟡 **Yellow**: Bug slowing down (3-7 days)
- 🔴 **Red**: Bug stuck (>7 days) - needs intervention

### Alerts
- **Red boxes**: Blockers requiring immediate attention
- **Orange boxes**: Critical issues
- **Highlighted rows**: Team members with >5 active bugs

## 📁 Files Overview

```
belmond-defect-insights/
├── app.py              # Main Streamlit dashboard
├── jira_client.py      # Jira API integration
├── requirements.txt    # Python dependencies
├── .env               # Jira credentials (copied from jira-mcp)
├── .gitignore         # Protect sensitive files
├── README.md          # Full documentation
├── QUICKSTART.md      # This file
├── setup.sh           # Automated setup script
└── run.sh             # Run script
```

## 🔧 Troubleshooting

### "No data loaded" Error
- ✓ Check `.env` file exists and has valid credentials
- ✓ Test credentials: `python3 jira_client.py`
- ✓ Verify network connection
- ✓ Try the JQL query directly in Jira web UI

### Authentication Failed
- Regenerate API token at: https://id.atlassian.com/manage-profile/security/api-tokens
- Update `JIRA_API_TOKEN` in `.env` file

### Slow Performance
- Use filters to reduce dataset size
- Close unused browser tabs
- Clear Streamlit cache (use Refresh button)

### Module Not Found
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## 📊 Export Capabilities

All pages support data export:
- **CSV**: For quick analysis in Excel/Google Sheets
- **Excel**: Formatted workbooks with proper columns

Export buttons available on:
- Blocker & Critical Dashboard
- Bug List (with applied filters)

## 🔄 Keeping Data Fresh

The dashboard automatically refreshes from Jira, but for real-time monitoring:
1. Keep the browser tab open
2. Use the Refresh button every 5 minutes
3. Monitor the "Last updated" timestamp in sidebar

## 🎯 Addressing the Confidence Crisis

This dashboard directly addresses the issues raised in the leadership meeting:

### Problem: "Lack of progress visibility"
**Solution**: Sprint Progress Tracker shows actual completion rates and velocity

### Problem: "Team capacity unknown"
**Solution**: Team Workload page shows who's overloaded (>5 bugs flagged)

### Problem: "Blockers not getting attention"
**Solution**: Blocker alerts on every page, impossible to miss

### Problem: "No governance on sprint commitments"
**Solution**: Fix version tracking shows planned vs. actual progress

### Problem: "Bugs getting stuck"
**Solution**: Time-in-status tracking with automatic red flags >7 days

### Problem: "Unclear priorities"
**Solution**: Color-coded priority system throughout dashboard

## 📞 Support

For issues, questions, or feature requests:
- Check Jira client directly: `python3 jira_client.py`
- Review error logs in terminal
- Contact Kaptio engineering team

---

**Built for the Belmond program to restore confidence and improve velocity** 🚀

