#!/usr/bin/env python3
"""
Belmond Bug Tracking Dashboard

A Streamlit dashboard for tracking Belmond defects from Jira.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
from io import BytesIO

# Import Jira client
from jira_client import JiraClient, get_belmond_bugs

# Page configuration
st.set_page_config(
    page_title="Belmond Bug Tracker",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .blocker-alert {
        background-color: #ff4b4b;
        color: white;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        font-weight: bold;
    }
    .critical-alert {
        background-color: #ffa500;
        color: white;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        font-weight: bold;
    }
    .stAlert > div {
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)


# Cache data for 5 minutes
@st.cache_data(ttl=300)
def load_bug_data() -> pd.DataFrame:
    """Load bug data from Jira and convert to DataFrame."""
    try:
        bugs = get_belmond_bugs()
        if not bugs:
            return pd.DataFrame()
        df = pd.DataFrame(bugs)
        return df
    except Exception as e:
        st.error(f"Error loading bug data: {e}")
        return pd.DataFrame()


def format_dataframe_for_display(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Format DataFrame for display in Streamlit."""
    display_df = df[columns].copy()
    
    # Format dates
    for col in display_df.columns:
        if 'created' in col.lower() or 'updated' in col.lower() or 'resolved' in col.lower():
            if col in display_df.columns:
                display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%Y-%m-%d')
    
    return display_df


def export_to_excel(df: pd.DataFrame, filename: str = "belmond_bugs.xlsx") -> BytesIO:
    """Export DataFrame to Excel."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bugs')
    output.seek(0)
    return output


def show_executive_summary(df: pd.DataFrame):
    """Display executive summary page."""
    st.title("🎯 Belmond Bug Tracker - Executive Summary")
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")
    
    if df.empty:
        st.warning("No bug data available")
        return
    
    # BLOCKER ALERTS (exclude Done and Rejected)
    blockers = df[
        (df['priority'] == 'Blocker') & 
        (~df['status'].isin(['Done', 'Rejected', 'Closed', 'Resolved']))
    ]
    if not blockers.empty:
        st.markdown("### 🚨 BLOCKER ALERTS")
        for _, bug in blockers.iterrows():
            days_in_status = bug['time_in_status_days']
            status_flag = "🔴" if days_in_status > 3 else "🟡"
            st.markdown(
                f"""<div class="blocker-alert">
                {status_flag} <a href="{bug['url']}" target="_blank" style="color: white;">{bug['key']}</a> - {bug['summary']}<br/>
                Status: {bug['status']} | Assignee: {bug['assignee']} | Days in Status: {days_in_status}
                </div>""",
                unsafe_allow_html=True
            )
        st.caption("ℹ️ Showing active blockers only (Done, Rejected, Closed, and Resolved statuses are filtered out)")
        st.markdown("---")
    else:
        st.success("✅ No active blockers!")
        st.markdown("---")
    
    # KEY METRICS
    st.subheader("📊 Bug Status Overview")
    st.caption("ℹ️ Rejected bugs are excluded from all views")
    
    # Single row with all 5 KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_bugs = len(df)
        st.metric("📦 Total", total_bugs)
    
    with col2:
        done_bugs = len(df[df['status'].isin(['Done', 'Resolved', 'Closed'])])
        done_pct = (done_bugs / total_bugs * 100) if total_bugs > 0 else 0
        st.metric("✅ Done", done_bugs, delta=f"{done_pct:.1f}%")
    
    with col3:
        dev_in_progress = len(df[df['status'].isin(['In Progress', 'In Development'])])
        st.metric("👨‍💻 Dev", dev_in_progress)
    
    with col4:
        qa_in_progress = len(df[df['status'].isin(['Ready for QA', 'In QA', 'Testing', 'In Review'])])
        st.metric("🧪 QA", qa_in_progress)
    
    with col5:
        to_do = len(df[df['status'].isin(['To Do', 'Open', 'Backlog', 'Selected for Development'])])
        st.metric("📋 To Do", to_do)
    
    # HIGH PRIORITY COUNTS
    st.markdown("")
    col7, col8 = st.columns(2)
    
    with col7:
        active_blockers = df[
            (df['priority'] == 'Blocker') & 
            (~df['status'].isin(['Done', 'Rejected', 'Closed', 'Resolved', 'Won\'t Fix', 'Cancelled']))
        ]
        st.metric("🚨 Active Blockers", len(active_blockers), delta_color="inverse")
    
    with col8:
        active_criticals = df[
            (df['priority'] == 'Critical') & 
            (~df['status'].isin(['Done', 'Rejected', 'Closed', 'Resolved', 'Won\'t Fix', 'Cancelled']))
        ]
        st.metric("⚠️ Active Critical", len(active_criticals), delta_color="inverse")
    
    st.markdown("---")
    
    # PRIORITY × STATUS MATRIX (replaces pie charts - more actionable)
    st.subheader("🎯 Priority × Status Matrix")
    st.caption("Where are the problems concentrated?")
    
    # Create matrix
    matrix_data = df.groupby(['priority', 'status']).size().reset_index(name='count')
    
    # Define priority order
    priority_order = ['Blocker', 'Critical', 'Major', 'Minor', 'Trivial']
    matrix_pivot = matrix_data.pivot(index='priority', columns='status', values='count').fillna(0)
    
    # Reorder priorities
    matrix_pivot = matrix_pivot.reindex([p for p in priority_order if p in matrix_pivot.index])
    
    # Create heatmap
    fig = px.imshow(
        matrix_pivot,
        labels=dict(x="Status", y="Priority", color="Bug Count"),
        title="Priority × Status Heatmap",
        color_continuous_scale="Reds",
        aspect="auto",
        text_auto=True
    )
    fig.update_xaxes(side="bottom")
    st.plotly_chart(fig, use_container_width=True)
    
    # AGING ANALYSIS (replaces confidence indicators - more actionable)
    st.markdown("---")
    st.subheader("⏰ Aging Analysis - How Long Bugs Have Been Open")
    st.caption("Identifies stuck tickets automatically")
    
    # Calculate aging buckets for open bugs only
    open_df = df[~df['status'].isin(['Done', 'Resolved', 'Closed', 'Rejected', 'Won\'t Fix'])]
    
    def categorize_age(days):
        if days <= 7:
            return '0-7 days'
        elif days <= 14:
            return '8-14 days'
        elif days <= 30:
            return '15-30 days'
        else:
            return '30+ days (STUCK)'
    
    if not open_df.empty:
        open_df_copy = open_df.copy()
        open_df_copy['age_bucket'] = open_df_copy['age_days'].apply(categorize_age)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Aging by priority
            aging_data = open_df_copy.groupby(['age_bucket', 'priority']).size().reset_index(name='count')
            
            # Define order
            age_order = ['0-7 days', '8-14 days', '15-30 days', '30+ days (STUCK)']
            aging_data['age_bucket'] = pd.Categorical(aging_data['age_bucket'], categories=age_order, ordered=True)
            aging_data = aging_data.sort_values('age_bucket')
            
            fig = px.bar(
                aging_data,
                x='age_bucket',
                y='count',
                color='priority',
                title='Open Bugs by Age and Priority',
                labels={'age_bucket': 'Age', 'count': 'Number of Bugs'},
                color_discrete_map={
                    'Blocker': '#ff0000',
                    'Critical': '#ff6600',
                    'Major': '#ffaa00',
                    'Minor': '#ffdd00',
                    'Trivial': '#90EE90'
                },
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Aging summary
            age_summary = open_df_copy['age_bucket'].value_counts().reindex(age_order, fill_value=0)
            
            st.markdown("**Aging Summary**")
            for bucket in age_order:
                count = age_summary.get(bucket, 0)
                if '30+' in bucket:
                    st.error(f"🔴 {bucket}: **{count}** bugs")
                elif '15-30' in bucket:
                    st.warning(f"🟡 {bucket}: **{count}** bugs")
                else:
                    st.info(f"🟢 {bucket}: **{count}** bugs")
    else:
        st.success("✅ No open bugs!")
    
    # CYCLE TIME METRICS (process efficiency)
    st.markdown("---")
    st.subheader("⚡ Cycle Time by Priority")
    st.caption("Are high-priority bugs actually resolved faster?")
    
    # Calculate cycle time for resolved bugs
    resolved_df = df[df['resolved'].notna()].copy()
    
    if not resolved_df.empty:
        resolved_df['cycle_time_days'] = (resolved_df['resolved'] - resolved_df['created']).dt.days
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Average cycle time by priority
            cycle_by_priority = resolved_df.groupby('priority')['cycle_time_days'].agg(['mean', 'median', 'count']).reset_index()
            cycle_by_priority = cycle_by_priority.sort_values('mean')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Average',
                x=cycle_by_priority['priority'],
                y=cycle_by_priority['mean'],
                marker_color='lightblue',
                text=cycle_by_priority['mean'].round(1),
                textposition='outside'
            ))
            fig.add_trace(go.Bar(
                name='Median',
                x=cycle_by_priority['priority'],
                y=cycle_by_priority['median'],
                marker_color='darkblue',
                text=cycle_by_priority['median'].round(1),
                textposition='outside'
            ))
            fig.update_layout(
                title='Average & Median Resolution Time (Days)',
                xaxis_title='Priority',
                yaxis_title='Days to Resolve',
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Resolution Times**")
            for _, row in cycle_by_priority.iterrows():
                st.metric(
                    f"{row['priority']}",
                    f"{row['mean']:.1f} days avg",
                    f"{int(row['count'])} resolved"
                )
    else:
        st.info("No resolved bugs yet to calculate cycle time")
    
    # OPEN VS CLOSED TREND (velocity)
    st.markdown("---")
    st.subheader("📊 Open vs Closed Trend - Are We Gaining Ground?")
    st.caption("Monthly velocity showing if bug backlog is growing or shrinking")
    
    # Calculate monthly created and resolved
    df_with_dates = df.copy()
    df_with_dates['created_month'] = pd.to_datetime(df_with_dates['created']).dt.to_period('M')
    
    created_monthly = df_with_dates.groupby('created_month').size().reset_index(name='Created')
    
    resolved_monthly_df = df_with_dates[df_with_dates['resolved'].notna()].copy()
    if not resolved_monthly_df.empty:
        resolved_monthly_df['resolved_month'] = pd.to_datetime(resolved_monthly_df['resolved']).dt.to_period('M')
        resolved_monthly = resolved_monthly_df.groupby('resolved_month').size().reset_index(name='Resolved')
        
        # Merge and fill
        velocity_df = created_monthly.merge(
            resolved_monthly, 
            left_on='created_month', 
            right_on='resolved_month', 
            how='outer'
        ).fillna(0)
        
        velocity_df['month'] = velocity_df['created_month'].combine_first(velocity_df['resolved_month'])
        velocity_df = velocity_df.sort_values('month').tail(12)  # Last 12 months
        
        # Format month labels for display (e.g., "Jan 2025")
        velocity_df['month_label'] = velocity_df['month'].astype(str).apply(
            lambda x: pd.Period(x, freq='M').strftime('%b %Y')
        )
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Created',
            x=velocity_df['month_label'],
            y=velocity_df['Created'],
            marker_color='red'
        ))
        fig.add_trace(go.Bar(
            name='Resolved',
            x=velocity_df['month_label'],
            y=velocity_df['Resolved'],
            marker_color='green'
        ))
        fig.update_layout(
            title='Monthly Created vs Resolved (Last 12 Months)',
            xaxis_title='Month',
            yaxis_title='Number of Bugs',
            barmode='group',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Net change
        if not velocity_df.empty:
            recent_created = velocity_df['Created'].tail(3).sum()
            recent_resolved = velocity_df['Resolved'].tail(3).sum()
            net_change = recent_resolved - recent_created
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Last 3 Months Created", f"{int(recent_created)}")
            with col2:
                st.metric("Last 3 Months Resolved", f"{int(recent_resolved)}")
            with col3:
                if net_change > 0:
                    st.metric("Net Change", f"+{int(net_change)}", delta="Gaining ground ✅", delta_color="normal")
                elif net_change < 0:
                    st.metric("Net Change", f"{int(net_change)}", delta="Backlog growing ⚠️", delta_color="inverse")
                else:
                    st.metric("Net Change", "0", delta="Breaking even")
    else:
        st.info("Not enough resolved data for trend analysis")


def show_team_workload(df: pd.DataFrame):
    """Display team workload analysis."""
    st.title("👥 Team Workload Analysis")
    st.markdown("---")
    
    if df.empty:
        st.warning("No bug data available")
        return
    
    # Filter out Done and Unassigned for workload
    active_bugs = df[(df['status'] != 'Done') & (df['assignee'] != 'Unassigned')]
    
    if active_bugs.empty:
        st.info("No active assigned bugs")
        return
    
    # BUGS PER ASSIGNEE
    st.subheader("📊 Active Bugs per Assignee")
    
    assignee_priority = active_bugs.groupby(['assignee', 'priority']).size().reset_index(name='count')
    fig = px.bar(
        assignee_priority,
        x='assignee',
        y='count',
        color='priority',
        title="Active Bugs by Assignee and Priority",
        labels={'assignee': 'Assignee', 'count': 'Number of Bugs'},
        color_discrete_map={
            'Blocker': '#ff0000',
            'Critical': '#ff6600',
            'Major': '#ffaa00',
            'Minor': '#ffdd00',
            'Trivial': '#90EE90'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ENHANCED WORKLOAD TABLE WITH PERFORMANCE METRICS
    st.subheader("📋 Team Performance & Workload")
    st.caption("Who's working on what + their resolution efficiency")
    
    workload_data = []
    for assignee in active_bugs['assignee'].unique():
        assignee_bugs = active_bugs[active_bugs['assignee'] == assignee]
        
        # Calculate resolution metrics
        assignee_resolved = df[
            (df['assignee'] == assignee) & 
            (df['resolved'].notna())
        ]
        
        if not assignee_resolved.empty:
            assignee_resolved_copy = assignee_resolved.copy()
            assignee_resolved_copy['cycle_time'] = (
                assignee_resolved_copy['resolved'] - assignee_resolved_copy['created']
            ).dt.days
            avg_resolution_time = assignee_resolved_copy['cycle_time'].mean()
            resolved_count = len(assignee_resolved)
        else:
            avg_resolution_time = None
            resolved_count = 0
        
        workload_data.append({
            'Assignee': assignee,
            'Active Bugs': len(assignee_bugs),
            'Blockers': len(assignee_bugs[assignee_bugs['priority'] == 'Blocker']),
            'Critical': len(assignee_bugs[assignee_bugs['priority'] == 'Critical']),
            'In Dev': len(assignee_bugs[assignee_bugs['status'].isin(['In Progress', 'In Development'])]),
            'In QA': len(assignee_bugs[assignee_bugs['status'].isin(['Ready for QA', 'In QA', 'Testing'])]),
            'Resolved (Total)': resolved_count,
            'Avg Resolution (Days)': avg_resolution_time,
            'Avg Days in Status': assignee_bugs['time_in_status_days'].mean(),
        })
    
    workload_df = pd.DataFrame(workload_data).sort_values('Active Bugs', ascending=False)
    
    # Highlight overloaded team members
    def highlight_overload(row):
        if row['Active Bugs'] > 5:
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)
    
    # Format function for optional values
    def format_optional_float(val):
        if pd.isna(val) or val is None:
            return '-'
        return f'{val:.1f}'
    
    styled_df = workload_df.style.apply(highlight_overload, axis=1).format({
        'Avg Resolution (Days)': format_optional_float,
        'Avg Days in Status': '{:.1f}'
    })
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    st.caption("⚠️ Rows highlighted in red indicate team members with >5 active bugs | Resolution time shows historical average")
    
    # STATUS HEATMAP
    st.markdown("---")
    st.subheader("🔥 Team Member × Status Heatmap")
    
    heatmap_data = active_bugs.groupby(['assignee', 'status']).size().reset_index(name='count')
    pivot_data = heatmap_data.pivot(index='assignee', columns='status', values='count').fillna(0)
    
    fig = px.imshow(
        pivot_data,
        labels=dict(x="Status", y="Assignee", color="Bug Count"),
        title="Bug Distribution by Assignee and Status",
        color_continuous_scale="Reds",
        aspect="auto"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # UNASSIGNED HIGH PRIORITY
    st.markdown("---")
    st.subheader("⚠️ Unassigned High Priority Bugs")
    
    unassigned_high = df[
        (df['assignee'] == 'Unassigned') & 
        (df['priority'].isin(['Blocker', 'Critical'])) &
        (df['status'] != 'Done')
    ]
    
    if not unassigned_high.empty:
        st.error(f"🚨 {len(unassigned_high)} high-priority bugs are unassigned!")
        st.dataframe(
            unassigned_high[['key', 'summary', 'priority', 'status', 'fix_version', 'url']],
            use_container_width=True
        )
    else:
        st.success("✅ All high-priority bugs are assigned")


def show_blocker_dashboard(df: pd.DataFrame):
    """Display blocker and critical bugs dashboard."""
    st.title("🚨 Blocker & Critical Dashboard")
    st.markdown("---")
    
    if df.empty:
        st.warning("No bug data available")
        return
    
    # Filter for active high priority bugs (exclude Done, Rejected, etc.)
    high_priority = df[
        (df['priority'].isin(['Blocker', 'Critical'])) &
        (~df['status'].isin(['Done', 'Rejected', 'Closed', 'Resolved']))
    ]
    
    if high_priority.empty:
        st.success("✅ No active blocker or critical bugs!")
        st.caption("ℹ️ Done, Rejected, Closed, and Resolved issues are filtered out")
        return
    
    # KEY METRICS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        blockers = len(high_priority[high_priority['priority'] == 'Blocker'])
        st.metric("Blockers", blockers)
    
    with col2:
        criticals = len(high_priority[high_priority['priority'] == 'Critical'])
        st.metric("Criticals", criticals)
    
    with col3:
        stuck = len(high_priority[high_priority['time_in_status_days'] > 3])
        st.metric("Stuck >3 Days", stuck, delta_color="inverse")
    
    with col4:
        unassigned = len(high_priority[high_priority['assignee'] == 'Unassigned'])
        st.metric("Unassigned", unassigned, delta_color="inverse")
    
    # FILTERS
    st.markdown("---")
    st.subheader("🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.multiselect(
            "Priority",
            options=['Blocker', 'Critical'],
            default=['Blocker', 'Critical'],
            key="blocker_priority_filter"
        )
    
    with col2:
        status_filter = st.multiselect(
            "Status",
            options=high_priority['status'].unique().tolist(),
            default=high_priority['status'].unique().tolist(),
            key="blocker_status_filter"
        )
    
    with col3:
        assignee_filter = st.multiselect(
            "Assignee",
            options=high_priority['assignee'].unique().tolist(),
            default=high_priority['assignee'].unique().tolist(),
            key="blocker_assignee_filter"
        )
    
    # Apply filters
    filtered_df = high_priority[
        (high_priority['priority'].isin(priority_filter)) &
        (high_priority['status'].isin(status_filter)) &
        (high_priority['assignee'].isin(assignee_filter))
    ]
    
    # DETAILED TABLE
    st.markdown("---")
    st.subheader(f"📋 Active High Priority Bugs ({len(filtered_df)} bugs)")
    st.caption("ℹ️ Showing only active bugs (Done, Rejected, Closed, and Resolved are filtered out)")
    
    # Add status flag
    def get_status_flag(days):
        if days > 7:
            return "🔴"
        elif days > 3:
            return "🟡"
        else:
            return "🟢"
    
    display_df = filtered_df.copy()
    display_df['Flag'] = display_df['time_in_status_days'].apply(get_status_flag)
    
    # Reorder columns
    columns_to_show = [
        'Flag', 'key', 'priority', 'summary', 'status', 'assignee',
        'time_in_status_days', 'fix_version', 'age_days', 'url'
    ]
    
    st.dataframe(
        display_df[columns_to_show].sort_values(['priority', 'time_in_status_days'], ascending=[True, False]),
        use_container_width=True,
        height=600,
        column_config={
            "url": st.column_config.LinkColumn("Jira Link"),
            "time_in_status_days": st.column_config.NumberColumn("Days in Status", format="%d"),
            "age_days": st.column_config.NumberColumn("Age (Days)", format="%d"),
        }
    )
    
    st.caption("🔴 Red: >7 days | 🟡 Yellow: 3-7 days | 🟢 Green: <3 days")
    
    # EXPORT
    st.markdown("---")
    excel_data = export_to_excel(display_df)
    st.download_button(
        label="📥 Download as Excel",
        data=excel_data,
        file_name=f"belmond_high_priority_bugs_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def show_sprint_tracker(df: pd.DataFrame):
    """Display fix version progress - simplified and focused."""
    st.title("🎯 Fix Version Progress")
    st.markdown("---")
    
    if df.empty:
        st.warning("No bug data available")
        return
    
    # BUGS BY FIX VERSION - Simplified
    st.subheader("📊 Bugs by Fix Version Status")
    st.caption("Completion progress for each release")
    
    fix_version_data = []
    for version in df['fix_version'].unique():
        if version == 'None':
            continue
        
        version_bugs = df[df['fix_version'] == version]
        done = len(version_bugs[version_bugs['status'].isin(['Done', 'Resolved', 'Closed'])])
        in_progress = len(version_bugs[version_bugs['status'].isin(['In Progress', 'In Development', 'Ready for QA', 'In QA'])])
        to_do = len(version_bugs[version_bugs['status'].isin(['To Do', 'Open', 'Backlog'])])
        total = len(version_bugs)
        
        fix_version_data.append({
            'Fix Version': version,
            'Total': total,
            'Done': done,
            'In Progress': in_progress,
            'To Do': to_do,
            '% Complete': (done / total * 100) if total > 0 else 0,
            'Blockers': len(version_bugs[version_bugs['priority'] == 'Blocker']),
            'Critical': len(version_bugs[version_bugs['priority'] == 'Critical']),
        })
    
    if fix_version_data:
        fix_version_df = pd.DataFrame(fix_version_data).sort_values('Fix Version')
        
        # Visual progress bar
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Done',
            x=fix_version_df['Fix Version'],
            y=fix_version_df['Done'],
            marker_color='green',
            text=fix_version_df['Done'],
            textposition='inside'
        ))
        fig.add_trace(go.Bar(
            name='In Progress',
            x=fix_version_df['Fix Version'],
            y=fix_version_df['In Progress'],
            marker_color='blue',
            text=fix_version_df['In Progress'],
            textposition='inside'
        ))
        fig.add_trace(go.Bar(
            name='To Do',
            x=fix_version_df['Fix Version'],
            y=fix_version_df['To Do'],
            marker_color='gray',
            text=fix_version_df['To Do'],
            textposition='inside'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Fix Version Progress',
            xaxis_title='Fix Version',
            yaxis_title='Number of Bugs',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary table
        st.dataframe(
            fix_version_df.style.format({
                '% Complete': '{:.1f}%'
            }),
            use_container_width=True
        )
    else:
        st.info("No bugs with fix versions assigned")


def show_status_flow(df: pd.DataFrame):
    """Display status flow analysis."""
    st.title("🔄 Status Flow Analysis")
    st.markdown("---")
    
    if df.empty:
        st.warning("No bug data available")
        return
    
    # AVERAGE TIME IN STATUS
    st.subheader("⏱️ Average Time in Current Status")
    
    status_time = df.groupby('status')['time_in_status_days'].agg(['mean', 'median', 'max', 'count']).reset_index()
    status_time.columns = ['Status', 'Avg Days', 'Median Days', 'Max Days', 'Bug Count']
    status_time = status_time.sort_values('Avg Days', ascending=False)
    
    fig = px.bar(
        status_time,
        x='Status',
        y='Avg Days',
        title='Average Days in Status',
        labels={'Avg Days': 'Average Days'},
        color='Avg Days',
        color_continuous_scale='Reds',
        text='Avg Days'
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(
        status_time.style.format({
            'Avg Days': '{:.1f}',
            'Median Days': '{:.1f}',
            'Max Days': '{:.0f}'
        }),
        use_container_width=True
    )
    
    # BOTTLENECK IDENTIFICATION
    st.markdown("---")
    st.subheader("🚧 Bottleneck: Bugs Stuck >7 Days")
    
    stuck_bugs = df[df['time_in_status_days'] > 7].copy()
    stuck_bugs = stuck_bugs.sort_values('time_in_status_days', ascending=False)
    
    if not stuck_bugs.empty:
        st.error(f"⚠️ {len(stuck_bugs)} bugs stuck for more than 7 days!")
        
        # Group by status
        stuck_by_status = stuck_bugs.groupby('status').size().reset_index(name='count')
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(stuck_by_status, use_container_width=True)
        
        with col2:
            fig = px.pie(
                stuck_by_status,
                values='count',
                names='status',
                title='Stuck Bugs by Status'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed list
        st.markdown("#### Detailed List of Stuck Bugs")
        st.dataframe(
            stuck_bugs[['key', 'summary', 'status', 'assignee', 'priority', 'time_in_status_days', 'url']],
            use_container_width=True,
            height=400,
            column_config={
                "url": st.column_config.LinkColumn("Jira Link"),
                "time_in_status_days": st.column_config.NumberColumn("Days Stuck", format="%d"),
            }
        )
    else:
        st.success("✅ No bugs stuck for more than 7 days!")
    
    # STATUS DISTRIBUTION
    st.markdown("---")
    st.subheader("📊 Current Status Distribution")
    
    status_dist = df['status'].value_counts().reset_index()
    status_dist.columns = ['Status', 'Count']
    
    fig = px.treemap(
        status_dist,
        path=['Status'],
        values='Count',
        title='Bug Status Distribution (Treemap)',
        color='Count',
        color_continuous_scale='RdYlGn_r'
    )
    st.plotly_chart(fig, use_container_width=True)


def show_bug_list(df: pd.DataFrame):
    """Display detailed bug list with filters."""
    st.title("📋 Detailed Bug List")
    st.markdown("---")
    
    if df.empty:
        st.warning("No bug data available")
        return
    
    # FILTERS
    st.subheader("🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        priority_filter = st.multiselect(
            "Priority",
            options=df['priority'].unique().tolist(),
            default=df['priority'].unique().tolist(),
            key="buglist_priority_filter"
        )
    
    with col2:
        status_filter = st.multiselect(
            "Status",
            options=df['status'].unique().tolist(),
            default=df['status'].unique().tolist(),
            key="buglist_status_filter"
        )
    
    with col3:
        assignee_filter = st.multiselect(
            "Assignee",
            options=df['assignee'].unique().tolist(),
            default=df['assignee'].unique().tolist(),
            key="buglist_assignee_filter"
        )
    
    with col4:
        parent_filter = st.multiselect(
            "Epic",
            options=df['parent_key'].unique().tolist(),
            default=df['parent_key'].unique().tolist(),
            key="buglist_parent_filter"
        )
    
    # Search
    search_term = st.text_input("🔎 Search in Summary", "")
    
    # Apply filters
    filtered_df = df[
        (df['priority'].isin(priority_filter)) &
        (df['status'].isin(status_filter)) &
        (df['assignee'].isin(assignee_filter)) &
        (df['parent_key'].isin(parent_filter))
    ]
    
    if search_term:
        filtered_df = filtered_df[filtered_df['summary'].str.contains(search_term, case=False, na=False)]
    
    # RESULTS
    st.markdown("---")
    st.subheader(f"📊 Results: {len(filtered_df)} bugs")
    
    # Sort options
    col1, col2 = st.columns(2)
    
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            options=['key', 'priority', 'status', 'assignee', 'created', 'updated', 'time_in_status_days', 'age_days']
        )
    
    with col2:
        sort_order = st.radio("Order", options=['Ascending', 'Descending'], horizontal=True)
    
    # Sort DataFrame
    ascending = sort_order == 'Ascending'
    sorted_df = filtered_df.sort_values(sort_by, ascending=ascending)
    
    # Display columns
    display_columns = [
        'key', 'summary', 'priority', 'status', 'assignee',
        'fix_version', 'time_in_status_days', 'age_days', 'parent_key', 'url'
    ]
    
    st.dataframe(
        sorted_df[display_columns],
        use_container_width=True,
        height=600,
        column_config={
            "url": st.column_config.LinkColumn("Jira Link"),
            "time_in_status_days": st.column_config.NumberColumn("Days in Status", format="%d"),
            "age_days": st.column_config.NumberColumn("Age (Days)", format="%d"),
        }
    )
    
    # EXPORT OPTIONS
    st.markdown("---")
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = sorted_df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name=f"belmond_bugs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        excel_data = export_to_excel(sorted_df)
        st.download_button(
            label="Download as Excel",
            data=excel_data,
            file_name=f"belmond_bugs_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


def main():
    """Main application."""
    
    # Sidebar
    st.sidebar.title("🐛 Belmond Bug Tracker")
    st.sidebar.markdown("---")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    with st.spinner("Loading bug data from Jira..."):
        df = load_bug_data()
    
    # GLOBAL PRIORITY FILTER (before error checking)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎚️ Priority Filter")
    
    all_priorities = ['Blocker', 'Critical', 'Major', 'Minor', 'Trivial']
    available_priorities = [p for p in all_priorities if p in df['priority'].unique()] if not df.empty else all_priorities
    
    # Default to Blocker + Critical only
    default_priorities = [p for p in ['Blocker', 'Critical'] if p in available_priorities]
    
    priority_filter = st.sidebar.multiselect(
        "Show priorities:",
        options=available_priorities,
        default=default_priorities,
        help="Filter all sections by priority. Default shows Blocker + Critical only.",
        key="global_priority_filter"
    )
    
    # Filter out rejected bugs FIRST (always excluded)
    if not df.empty:
        df = df[~df['status'].isin(['Rejected', 'Won\'t Fix', 'Cancelled', 'Won\'t Do'])]
    
    # Apply global priority filter
    if not df.empty and priority_filter:
        df = df[df['priority'].isin(priority_filter)]
        st.sidebar.caption(f"✅ Filtered to {len(df)} bugs")
    elif not df.empty and not priority_filter:
        st.sidebar.warning("⚠️ No priorities selected - showing all")
    
    # Show filtered count
    if not df.empty:
        total_bugs = len(load_bug_data())
        rejected_count = len(load_bug_data()[load_bug_data()['status'].isin(['Rejected', 'Won\'t Fix', 'Cancelled', 'Won\'t Do'])])
        st.sidebar.caption(f"📊 Showing {len(df)} bugs (excluded {rejected_count} rejected)")
    
    if df.empty:
        st.error("❌ No data loaded. Please check Jira connection and credentials.")
        st.sidebar.markdown("---")
        st.sidebar.info("""
        **Troubleshooting:**
        1. Check `.env` file exists
        2. Verify credentials
        3. Check network connection
        4. Verify JQL query in Jira
        """)
        return
    
    # Show last update time
    st.sidebar.success(f"✅ Loaded {len(df)} bugs")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Navigation links in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📑 Quick Navigation")
    st.sidebar.markdown("""
    - [Executive Summary](#belmond-bug-tracker-executive-summary)
    - [Team Workload](#team-workload-analysis)
    - [Blocker & Critical](#blocker-critical-dashboard)
    - [Fix Version Progress](#fix-version-progress)
    - [Status Flow](#status-flow-analysis)
    - [Bug List](#detailed-bug-list)
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Key Insights")
    st.sidebar.info("""
    **New Visualizations:**
    - Priority × Status Matrix
    - Aging Analysis (30+ days = stuck)
    - Cycle Time by Priority
    - Open vs Closed Trends
    - Team Performance Metrics
    """)
    
    # Display all sections on one page
    show_executive_summary(df)
    st.markdown("---")
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    show_team_workload(df)
    st.markdown("---")
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    show_blocker_dashboard(df)
    st.markdown("---")
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    show_sprint_tracker(df)
    st.markdown("---")
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    show_status_flow(df)
    st.markdown("---")
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    show_bug_list(df)


if __name__ == "__main__":
    main()

