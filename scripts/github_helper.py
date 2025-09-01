#!/usr/bin/env python3
"""GitHub API Helper - Automatyzacja zadań GitHub"""

import os
import json
import requests
from typing import Dict, List, Optional

class GitHubHelper:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.repo = 'Piotrek40/droga-szamana-rpg'
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Dict:
        """Tworzy nowe issue w repozytorium"""
        url = f'{self.base_url}/repos/{self.repo}/issues'
        data = {
            'title': title,
            'body': body,
            'labels': labels or []
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def list_issues(self, state: str = 'open') -> List[Dict]:
        """Listuje issues w repozytorium"""
        url = f'{self.base_url}/repos/{self.repo}/issues'
        params = {'state': state}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def create_pull_request(self, title: str, body: str, head: str, base: str = 'main') -> Dict:
        """Tworzy pull request"""
        url = f'{self.base_url}/repos/{self.repo}/pulls'
        data = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def add_labels_to_repo(self, labels: Dict[str, str]) -> None:
        """Dodaje etykiety do repozytorium"""
        url = f'{self.base_url}/repos/{self.repo}/labels'
        for name, color in labels.items():
            data = {'name': name, 'color': color}
            requests.post(url, headers=self.headers, json=data)
            print(f"✓ Added label: {name}")
    
    def create_milestone(self, title: str, description: str, due_date: str = None) -> Dict:
        """Tworzy milestone w projekcie"""
        url = f'{self.base_url}/repos/{self.repo}/milestones'
        data = {
            'title': title,
            'description': description,
            'due_on': due_date
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_repo_stats(self) -> Dict:
        """Pobiera statystyki repozytorium"""
        url = f'{self.base_url}/repos/{self.repo}'
        response = requests.get(url, headers=self.headers)
        data = response.json()
        
        return {
            'stars': data.get('stargazers_count', 0),
            'forks': data.get('forks_count', 0),
            'watchers': data.get('watchers_count', 0),
            'open_issues': data.get('open_issues_count', 0),
            'size': data.get('size', 0),
            'language': data.get('language', 'Unknown'),
            'created': data.get('created_at', ''),
            'updated': data.get('updated_at', '')
        }
    
    def analyze_code_quality(self) -> Dict:
        """Analizuje jakość kodu w repozytorium"""
        # Pobierz listę plików Python
        url = f'{self.base_url}/repos/{self.repo}/contents'
        response = requests.get(url, headers=self.headers)
        
        stats = {
            'total_files': 0,
            'python_files': 0,
            'json_files': 0,
            'documentation_files': 0,
            'test_files': 0
        }
        
        def count_files(path=''):
            url = f'{self.base_url}/repos/{self.repo}/contents/{path}'
            response = requests.get(url, headers=self.headers)
            items = response.json()
            
            for item in items:
                if item['type'] == 'file':
                    stats['total_files'] += 1
                    if item['name'].endswith('.py'):
                        stats['python_files'] += 1
                        if 'test' in item['name'].lower():
                            stats['test_files'] += 1
                    elif item['name'].endswith('.json'):
                        stats['json_files'] += 1
                    elif item['name'].endswith(('.md', '.txt', '.rst')):
                        stats['documentation_files'] += 1
                elif item['type'] == 'dir' and not item['name'].startswith('.'):
                    count_files(item['path'])
        
        count_files()
        return stats

# Przykład użycia
if __name__ == '__main__':
    # Token jest już w środowisku
    helper = GitHubHelper()
    
    # Dodaj przydatne etykiety
    labels = {
        'bug': 'd73a4a',
        'enhancement': 'a2eeef',
        'documentation': '0075ca',
        'good first issue': '7057ff',
        'help wanted': '008672',
        'question': 'd876e3',
        'wontfix': 'ffffff',
        'duplicate': 'cfd3d7',
        'invalid': 'e4e669',
        'combat': 'ff0000',
        'npc-ai': '00ff00',
        'economy': 'ffff00',
        'quest': 'ff00ff',
        'ui-ux': '00ffff'
    }
    
    print("GitHub Helper ready!")
    print(f"Repository: {helper.repo}")
    print("\nAvailable functions:")
    print("- create_issue(title, body, labels)")
    print("- list_issues(state)")
    print("- create_pull_request(title, body, head, base)")
    print("- add_labels_to_repo(labels)")
    print("- create_milestone(title, description, due_date)")
    print("- get_repo_stats()")
    print("- analyze_code_quality()")