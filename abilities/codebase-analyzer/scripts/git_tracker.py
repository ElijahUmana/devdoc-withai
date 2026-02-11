#!/usr/bin/env python3
"""
DevDoc Git Tracker

Analyzes git history for continuous intelligence:
- Commit frequency and velocity
- File churn (most frequently changed files)
- Complexity changes per commit
- Author contribution patterns
- Hotspot detection (high churn + high complexity = risk)
- Change size trends
- Recent activity summary

Requires: git CLI available in PATH

Usage:
    python git_tracker.py <project-root> [--output git_history.json] [--commits 50]

Part of the codebase-analyzer WithAI ability.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional


class GitTracker:
    """Analyze git history for trend detection and hotspot identification."""

    def __init__(self, root_path: str, max_commits: int = 50):
        self.root = Path(root_path).resolve()
        self.max_commits = max_commits

        # Verify git repo
        if not (self.root / '.git').exists():
            raise ValueError(f"Not a git repository: {self.root}")

    def analyze(self) -> dict:
        """Run full git history analysis."""
        commits = self._get_commit_log()
        file_changes = self._get_file_change_history()
        file_churn = self._compute_file_churn(file_changes)
        recent_activity = self._get_recent_activity(commits)
        author_stats = self._compute_author_stats(commits)
        velocity = self._compute_velocity(commits)
        change_sizes = self._get_change_sizes()

        return {
            'is_git_repo': True,
            'total_commits': len(commits),
            'analyzed_commits': min(len(commits), self.max_commits),
            'commits': commits[:self.max_commits],
            'file_churn': file_churn,
            'recent_activity': recent_activity,
            'author_stats': author_stats,
            'velocity': velocity,
            'change_sizes': change_sizes,
            'hotspots': self._identify_hotspots(file_churn),
            'summary': self._build_summary(commits, file_churn, velocity),
        }

    def _run_git(self, args: list[str], cwd: Optional[str] = None) -> str:
        """Execute a git command and return stdout."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=cwd or str(self.root),
                capture_output=True, text=True, timeout=30,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ''

    def _get_commit_log(self) -> list[dict]:
        """Get structured commit log."""
        # Format: hash|author|date|subject
        log = self._run_git([
            'log', f'-{self.max_commits}',
            '--pretty=format:%H|%an|%aI|%s',
            '--no-merges',
        ])

        if not log:
            return []

        commits = []
        for line in log.split('\n'):
            parts = line.split('|', 3)
            if len(parts) >= 4:
                commits.append({
                    'hash': parts[0][:8],
                    'full_hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3],
                })
        return commits

    def _get_file_change_history(self) -> list[dict]:
        """Get file-level change details for each commit."""
        log = self._run_git([
            'log', f'-{self.max_commits}',
            '--pretty=format:COMMIT:%H|%aI',
            '--numstat', '--no-merges',
        ])

        if not log:
            return []

        changes = []
        current_commit = None
        current_date = None

        for line in log.split('\n'):
            if line.startswith('COMMIT:'):
                parts = line[7:].split('|')
                current_commit = parts[0][:8]
                current_date = parts[1] if len(parts) > 1 else ''
            elif line.strip() and current_commit:
                parts = line.split('\t')
                if len(parts) == 3:
                    added = int(parts[0]) if parts[0] != '-' else 0
                    deleted = int(parts[1]) if parts[1] != '-' else 0
                    filepath = parts[2]
                    changes.append({
                        'commit': current_commit,
                        'date': current_date,
                        'file': filepath,
                        'added': added,
                        'deleted': deleted,
                        'total_change': added + deleted,
                    })

        return changes

    def _compute_file_churn(self, file_changes: list) -> list[dict]:
        """Compute change frequency and volume per file."""
        churn = defaultdict(lambda: {
            'change_count': 0, 'total_added': 0, 'total_deleted': 0,
            'total_churn': 0, 'commits': set(), 'last_changed': '',
        })

        for change in file_changes:
            fp = change['file']
            churn[fp]['change_count'] += 1
            churn[fp]['total_added'] += change['added']
            churn[fp]['total_deleted'] += change['deleted']
            churn[fp]['total_churn'] += change['total_change']
            churn[fp]['commits'].add(change['commit'])
            if not churn[fp]['last_changed'] or change['date'] > churn[fp]['last_changed']:
                churn[fp]['last_changed'] = change['date']

        result = []
        for fp, stats in churn.items():
            result.append({
                'file': fp,
                'change_count': stats['change_count'],
                'unique_commits': len(stats['commits']),
                'total_added': stats['total_added'],
                'total_deleted': stats['total_deleted'],
                'total_churn': stats['total_churn'],
                'last_changed': stats['last_changed'],
                'churn_ratio': round(stats['total_deleted'] / max(stats['total_added'], 1), 2),
            })

        return sorted(result, key=lambda x: x['total_churn'], reverse=True)

    def _get_recent_activity(self, commits: list, days: int = 30) -> dict:
        """Analyze activity in the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []

        for c in commits:
            try:
                commit_date = datetime.fromisoformat(c['date'].replace('Z', '+00:00')).replace(tzinfo=None)
                if commit_date >= cutoff:
                    recent.append(c)
            except:
                pass

        daily_counts = defaultdict(int)
        for c in recent:
            try:
                day = c['date'][:10]
                daily_counts[day] += 1
            except:
                pass

        return {
            'period_days': days,
            'total_commits': len(recent),
            'avg_commits_per_day': round(len(recent) / days, 2) if days > 0 else 0,
            'active_days': len(daily_counts),
            'most_active_day': max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else None,
            'daily_breakdown': dict(sorted(daily_counts.items())),
        }

    def _compute_author_stats(self, commits: list) -> list[dict]:
        """Compute per-author contribution statistics."""
        authors = defaultdict(lambda: {'commits': 0, 'first_commit': '', 'last_commit': ''})

        for c in commits:
            author = c['author']
            authors[author]['commits'] += 1
            if not authors[author]['first_commit'] or c['date'] < authors[author]['first_commit']:
                authors[author]['first_commit'] = c['date']
            if not authors[author]['last_commit'] or c['date'] > authors[author]['last_commit']:
                authors[author]['last_commit'] = c['date']

        total = sum(a['commits'] for a in authors.values())
        result = []
        for name, stats in authors.items():
            result.append({
                'author': name,
                'commits': stats['commits'],
                'percentage': round(stats['commits'] / total * 100, 1) if total > 0 else 0,
                'first_commit': stats['first_commit'],
                'last_commit': stats['last_commit'],
            })

        return sorted(result, key=lambda x: x['commits'], reverse=True)

    def _compute_velocity(self, commits: list) -> dict:
        """Compute development velocity metrics."""
        if len(commits) < 2:
            return {'commits_per_week': 0, 'trend': 'insufficient_data'}

        dates = []
        for c in commits:
            try:
                dates.append(datetime.fromisoformat(c['date'].replace('Z', '+00:00')).replace(tzinfo=None))
            except:
                pass

        if len(dates) < 2:
            return {'commits_per_week': 0, 'trend': 'insufficient_data'}

        dates.sort()
        total_days = (dates[-1] - dates[0]).days or 1
        total_weeks = total_days / 7

        # Split into halves for trend detection
        mid = len(dates) // 2
        first_half = dates[:mid]
        second_half = dates[mid:]

        first_span = (first_half[-1] - first_half[0]).days or 1
        second_span = (second_half[-1] - second_half[0]).days or 1

        first_rate = len(first_half) / first_span
        second_rate = len(second_half) / second_span

        if second_rate > first_rate * 1.2:
            trend = 'accelerating'
        elif second_rate < first_rate * 0.8:
            trend = 'decelerating'
        else:
            trend = 'steady'

        return {
            'total_span_days': total_days,
            'commits_per_week': round(len(commits) / max(total_weeks, 0.1), 2),
            'commits_per_day': round(len(commits) / total_days, 2),
            'trend': trend,
            'first_half_rate': round(first_rate * 7, 2),  # per week
            'second_half_rate': round(second_rate * 7, 2),
        }

    def _get_change_sizes(self) -> list[dict]:
        """Categorize commits by change size."""
        log = self._run_git([
            'log', f'-{self.max_commits}',
            '--pretty=format:%H|%s',
            '--shortstat', '--no-merges',
        ])

        if not log:
            return []

        sizes = []
        current_hash = None
        current_msg = None

        for line in log.split('\n'):
            if '|' in line and len(line.split('|')[0]) == 40:
                parts = line.split('|', 1)
                current_hash = parts[0][:8]
                current_msg = parts[1] if len(parts) > 1 else ''
            elif 'file' in line and 'changed' in line:
                # Parse: "3 files changed, 45 insertions(+), 12 deletions(-)"
                import re
                files_match = re.search(r'(\d+) files? changed', line)
                ins_match = re.search(r'(\d+) insertions?', line)
                del_match = re.search(r'(\d+) deletions?', line)

                files_changed = int(files_match.group(1)) if files_match else 0
                insertions = int(ins_match.group(1)) if ins_match else 0
                deletions = int(del_match.group(1)) if del_match else 0
                total = insertions + deletions

                # Categorize
                if total <= 10:
                    category = 'tiny'
                elif total <= 50:
                    category = 'small'
                elif total <= 200:
                    category = 'medium'
                elif total <= 500:
                    category = 'large'
                else:
                    category = 'massive'

                sizes.append({
                    'commit': current_hash,
                    'message': current_msg,
                    'files_changed': files_changed,
                    'insertions': insertions,
                    'deletions': deletions,
                    'total_changes': total,
                    'category': category,
                })

        return sizes

    def _identify_hotspots(self, file_churn: list) -> list[dict]:
        """Identify risk hotspots: files with high churn."""
        hotspots = []
        for fc in file_churn[:20]:
            if fc['change_count'] >= 3 or fc['total_churn'] >= 50:
                risk = 'low'
                if fc['change_count'] >= 5 and fc['total_churn'] >= 100:
                    risk = 'high'
                elif fc['change_count'] >= 3 and fc['total_churn'] >= 50:
                    risk = 'medium'

                hotspots.append({
                    'file': fc['file'],
                    'risk': risk,
                    'reason': f"Changed {fc['change_count']} times with {fc['total_churn']} lines churned",
                    'change_count': fc['change_count'],
                    'total_churn': fc['total_churn'],
                })

        return hotspots

    def _build_summary(self, commits, file_churn, velocity) -> str:
        """Build human-readable git history summary."""
        if not commits:
            return "No git history available."

        parts = [
            f"{len(commits)} commits analyzed.",
            f"Development velocity: {velocity.get('commits_per_week', 0)} commits/week ({velocity.get('trend', 'unknown')}).",
        ]

        if file_churn:
            top_file = file_churn[0]
            parts.append(f"Most churned file: {top_file['file']} ({top_file['total_churn']} lines changed across {top_file['change_count']} commits).")

        return ' '.join(parts)


def analyze_no_git(root_path: str) -> dict:
    """Return a stub result for projects without git."""
    return {
        'is_git_repo': False,
        'message': 'Not a git repository. Initialize with `git init` to enable trend tracking.',
        'total_commits': 0,
        'commits': [],
        'file_churn': [],
        'recent_activity': {},
        'author_stats': [],
        'velocity': {},
        'change_sizes': [],
        'hotspots': [],
        'summary': 'No git history. Continuous tracking requires git.',
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DevDoc Git Tracker')
    parser.add_argument('project_path', help='Path to project root')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--commits', type=int, default=50, help='Max commits to analyze')
    args = parser.parse_args()

    try:
        tracker = GitTracker(args.project_path, max_commits=args.commits)
        result = tracker.analyze()
    except ValueError:
        result = analyze_no_git(args.project_path)

    output = json.dumps(result, indent=2, default=str)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Git analysis saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
