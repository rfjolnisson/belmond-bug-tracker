# Belmond Bug Tracking Dashboard

A Streamlit dashboard for tracking Belmond defects from Jira epics ST-1746 and ST-2049, providing real-time insights into bug status, team workload, and sprint progress.

## Purpose

This dashboard addresses the Belmond program's confidence crisis by providing:
- **Blocker Visibility**: Immediate visibility into blockers and critical bugs
- **Team Accountability**: Clear view of who's working on what
- **Progress Tracking**: Sprint velocity and completion rates
- **Bottleneck Identification**: Where bugs get stuck in the workflow

## Setup

### Prerequisites
- Python 3.8 or higher
- Access to Kaptio Jira (credentials required)

### Installation

1. Clone or navigate to this directory:
```bash
cd "/Users/ragnarfjolnisson/Documents/2025 Coding/belmond-defect-insights"
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up credentials:
   - Copy `.env` file from `../jira-mcp/.env` or create a new one:
```bash
cp ../jira-mcp/.env .env
```

   - Or create `.env` manually with:
```
JIRA_BASE_URL=https://kaptio.atlassian.net
JIRA_USERNAME=your-email@kaptio.com
JIRA_API_TOKEN=your-api-token
```

### Running the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8502`

## Features

### 📊 Executive Summary
- Blocker alerts with assignee and status
- Key metrics: bugs by priority and status
- Confidence indicators and trends

### 👥 Team Workload
- Bug distribution per assignee
- Capacity analysis
- Overload alerts

### 🚨 Blocker & Critical Dashboard
- Focused view of P0/P1 bugs
- Time-in-status tracking
- Fix version assignments

### 📈 Sprint Progress
- Velocity trends
- Burn-down charts
- Reopened bug tracking

### 🔄 Status Flow Analysis
- Bottleneck identification
- Average time per status
- Workflow visualization

### 📋 Detailed Bug List
- Searchable and sortable
- Multi-filter capability
- CSV/Excel export

## Usage Tips

- **Refresh Data**: Click the "Refresh Data" button in the sidebar to get latest from Jira
- **Export Reports**: Use export buttons on each page to save data
- **Filter**: Use sidebar filters to focus on specific priorities, statuses, or assignees

## JQL Query

The dashboard tracks bugs using:
```
parent IN (ST-1746, ST-2049) order BY fixVersion ASC, rank
```

## Troubleshooting

### Authentication Errors
- Verify your `.env` file has correct credentials
- Ensure your Jira API token is valid (regenerate at https://id.atlassian.com/manage-profile/security/api-tokens)

### No Data Showing
- Check your network connection
- Verify the JQL query returns results in Jira directly
- Check console for error messages

### Performance Issues
- Data is cached for 5 minutes by default
- Use filters to reduce dataset size
- Close unused browser tabs

## Support

For issues or questions, contact the Kaptio engineering team.

