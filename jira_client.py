#!/usr/bin/env python3
"""
Jira Client for Belmond Bug Tracking Dashboard

Fetches bug data from Kaptio Jira for epics ST-1746 and ST-2049.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JIRA_BASE_URL = os.getenv('JIRA_BASE_URL', 'https://kaptio.atlassian.net')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# JQL query for Belmond bugs
BELMOND_JQL = 'parent IN (ST-1746, ST-2049) order BY fixVersion ASC, rank'


class JiraClient:
    """Client for interacting with Jira API."""
    
    def __init__(self, base_url: str = None, username: str = None, api_token: str = None):
        """
        Initialize Jira client.
        
        Args:
            base_url: Jira instance URL (defaults to env var)
            username: Jira username (defaults to env var)
            api_token: Jira API token (defaults to env var)
        """
        self.base_url = base_url or JIRA_BASE_URL
        self.username = username or JIRA_USERNAME
        self.api_token = api_token or JIRA_API_TOKEN
        
        if not self.username or not self.api_token:
            raise ValueError("JIRA_USERNAME and JIRA_API_TOKEN must be set")
        
        self.auth = HTTPBasicAuth(self.username, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def fetch_bugs(self, jql: str = None, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch bugs from Jira using JQL query.
        
        Args:
            jql: JQL query string (defaults to BELMOND_JQL)
            max_results: Maximum number of results per page
            
        Returns:
            List of bug dictionaries with processed fields
        """
        jql = jql or BELMOND_JQL
        url = f"{self.base_url}/rest/api/3/search/jql"
        
        all_issues = []
        start_at = 0
        page_size = min(max_results, 100)  # Jira API limit per request
        
        while True:
            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': page_size,
                'fields': ','.join([
                    'summary',
                    'status',
                    'priority',
                    'assignee',
                    'reporter',
                    'created',
                    'updated',
                    'resolutiondate',
                    'fixVersions',
                    'parent',
                    'issuetype',
                    'labels',
                    'components',
                    'timeoriginalestimate',
                    'timeestimate',
                    'timespent',
                    'aggregatetimeoriginalestimate',
                    'aggregatetimeestimate',
                    'aggregatetimespent',
                    'description',
                    'resolution',
                ])
            }
            
            try:
                response = requests.get(
                    url, 
                    auth=self.auth, 
                    headers=self.headers, 
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                issues = data.get('issues', [])
                if not issues:
                    break
                
                all_issues.extend(issues)
                
                total = data.get('total', 0)
                if len(all_issues) >= total:
                    break
                
                start_at += page_size
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching bugs from Jira: {e}", file=sys.stderr)
                raise
        
        # Process and enrich the bug data
        return [self._process_bug(bug) for bug in all_issues]
    
    def _process_bug(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw Jira issue into structured bug dictionary.
        
        Args:
            issue: Raw Jira issue dict
            
        Returns:
            Processed bug dictionary
        """
        fields = issue.get('fields', {})
        key = issue.get('key', 'N/A')
        
        # Extract basic fields
        summary = fields.get('summary', 'N/A')
        status = fields.get('status', {}).get('name', 'Unknown')
        priority = fields.get('priority', {}).get('name', 'None')
        
        # Assignee
        assignee_data = fields.get('assignee')
        assignee = assignee_data.get('displayName') if assignee_data else 'Unassigned'
        assignee_email = assignee_data.get('emailAddress') if assignee_data else None
        
        # Reporter
        reporter_data = fields.get('reporter')
        reporter = reporter_data.get('displayName') if reporter_data else 'Unknown'
        
        # Dates
        created = self._parse_date(fields.get('created'))
        updated = self._parse_date(fields.get('updated'))
        resolved = self._parse_date(fields.get('resolutiondate'))
        
        # Calculate time in current status
        time_in_status = (datetime.now() - updated).days if updated else None
        
        # Fix versions
        fix_versions = [v.get('name') for v in fields.get('fixVersions', [])]
        fix_version = fix_versions[0] if fix_versions else 'None'
        
        # Parent epic
        parent = fields.get('parent', {})
        parent_key = parent.get('key', 'N/A')
        parent_summary = parent.get('fields', {}).get('summary', 'N/A')
        
        # Issue type
        issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
        
        # Labels
        labels = fields.get('labels', [])
        
        # Components
        components = [c.get('name') for c in fields.get('components', [])]
        
        # Time tracking (in seconds, convert to hours)
        time_original_estimate = self._seconds_to_hours(fields.get('timeoriginalestimate'))
        time_estimate = self._seconds_to_hours(fields.get('timeestimate'))
        time_spent = self._seconds_to_hours(fields.get('timespent'))
        
        # Age in days
        age_days = (datetime.now() - created).days if created else None
        
        # Resolution
        resolution = fields.get('resolution')
        resolution_name = resolution.get('name') if resolution else None
        
        # Description (extract text from ADF format)
        description = fields.get('description', '')
        if isinstance(description, dict):
            description = self._extract_text_from_adf(description)
        
        # Build URL
        url = f"{self.base_url}/browse/{key}"
        
        return {
            'key': key,
            'summary': summary,
            'status': status,
            'priority': priority,
            'assignee': assignee,
            'assignee_email': assignee_email,
            'reporter': reporter,
            'created': created,
            'updated': updated,
            'resolved': resolved,
            'time_in_status_days': time_in_status,
            'fix_version': fix_version,
            'fix_versions': fix_versions,
            'parent_key': parent_key,
            'parent_summary': parent_summary,
            'issue_type': issue_type,
            'labels': labels,
            'components': components,
            'time_original_estimate_hours': time_original_estimate,
            'time_estimate_hours': time_estimate,
            'time_spent_hours': time_spent,
            'age_days': age_days,
            'resolution': resolution_name,
            'description': description,
            'url': url,
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira date string to datetime object."""
        if not date_str:
            return None
        try:
            # Remove timezone info for simplicity
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except (ValueError, AttributeError):
            return None
    
    def _seconds_to_hours(self, seconds: Optional[int]) -> Optional[float]:
        """Convert seconds to hours, rounded to 1 decimal."""
        if seconds is None:
            return None
        return round(seconds / 3600, 1)
    
    def _extract_text_from_adf(self, adf_content: Dict) -> str:
        """Extract plain text from Atlassian Document Format (ADF)."""
        if not isinstance(adf_content, dict):
            return str(adf_content)
        
        text_parts = []
        
        def traverse(node):
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    text_parts.append(node.get('text', ''))
                if 'content' in node:
                    for child in node['content']:
                        traverse(child)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
        
        traverse(adf_content)
        return ' '.join(text_parts)
    
    def get_issue_history(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Fetch change history for a specific issue.
        
        Args:
            issue_key: Jira issue key (e.g., 'ST-1234')
            
        Returns:
            List of history items
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}?expand=changelog"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            changelog = data.get('changelog', {}).get('histories', [])
            return changelog
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching history for {issue_key}: {e}", file=sys.stderr)
            return []
    
    def test_connection(self) -> bool:
        """
        Test Jira API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        url = f"{self.base_url}/rest/api/3/myself"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Connection test failed: {e}", file=sys.stderr)
            return False


def get_belmond_bugs() -> List[Dict[str, Any]]:
    """
    Convenience function to fetch Belmond bugs.
    
    Returns:
        List of bug dictionaries
    """
    client = JiraClient()
    return client.fetch_bugs()


if __name__ == '__main__':
    # Test the client
    print("Testing Jira connection...")
    client = JiraClient()
    
    if client.test_connection():
        print("✅ Connection successful")
        print("\nFetching Belmond bugs...")
        bugs = client.fetch_bugs()
        print(f"✅ Found {len(bugs)} bugs")
        
        if bugs:
            print("\nFirst bug:")
            bug = bugs[0]
            print(f"  Key: {bug['key']}")
            print(f"  Summary: {bug['summary']}")
            print(f"  Status: {bug['status']}")
            print(f"  Priority: {bug['priority']}")
            print(f"  Assignee: {bug['assignee']}")
            print(f"  Fix Version: {bug['fix_version']}")
    else:
        print("❌ Connection failed")
        sys.exit(1)

