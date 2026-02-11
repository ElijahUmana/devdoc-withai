#!/usr/bin/env python3
"""
DevDoc Snapshot Manager

Stores, loads, and diffs historical analysis snapshots for trend tracking:
- Save analysis results with timestamps to .devdoc/snapshots/
- Load previous snapshots for comparison
- Compute diffs between any two snapshots
- Detect regressions (metric degradation beyond threshold)
- Generate trend summaries across multiple snapshots

Usage:
    python snapshot_manager.py save <analysis.json> [--project-dir .]
    python snapshot_manager.py diff [--last 2] [--project-dir .]
    python snapshot_manager.py trend [--project-dir .]
    python snapshot_manager.py list [--project-dir .]

Part of the codebase-analyzer WithAI ability.
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional


DEFAULT_SNAPSHOT_DIR = '.devdoc/snapshots'
REGRESSION_THRESHOLD = 0.10  # 10% degradation triggers alert


class SnapshotManager:
    """Manage historical analysis snapshots for continuous intelligence."""

    def __init__(self, project_dir: str, snapshot_dir: Optional[str] = None):
        self.project_dir = Path(project_dir).resolve()
        self.snapshot_dir = self.project_dir / (snapshot_dir or DEFAULT_SNAPSHOT_DIR)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def save(self, analysis: dict, label: Optional[str] = None) -> str:
        """Save an analysis snapshot. Returns the snapshot filename."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        content_hash = hashlib.md5(
            json.dumps(analysis, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]

        label_part = f"_{label}" if label else ""
        filename = f"snapshot_{timestamp}{label_part}_{content_hash}.json"
        filepath = self.snapshot_dir / filename

        snapshot = {
            'snapshot_metadata': {
                'timestamp': datetime.now().isoformat(),
                'label': label,
                'content_hash': content_hash,
                'filename': filename,
            },
            'analysis': analysis,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, default=str)

        return filename

    def list_snapshots(self) -> list[dict]:
        """List all available snapshots, sorted by timestamp (newest first)."""
        snapshots = []
        for fpath in sorted(self.snapshot_dir.glob('snapshot_*.json'), reverse=True):
            try:
                with open(fpath, 'r') as f:
                    data = json.load(f)
                meta = data.get('snapshot_metadata', {})
                meta['filepath'] = str(fpath)
                meta['size_bytes'] = fpath.stat().st_size
                snapshots.append(meta)
            except:
                pass
        return snapshots

    def load(self, index: int = 0) -> Optional[dict]:
        """Load a snapshot by index (0 = most recent)."""
        snapshots = self.list_snapshots()
        if index >= len(snapshots):
            return None
        filepath = snapshots[index]['filepath']
        with open(filepath, 'r') as f:
            return json.load(f)

    def diff(self, older_index: int = 1, newer_index: int = 0) -> Optional[dict]:
        """Compare two snapshots and return a structured diff."""
        older = self.load(older_index)
        newer = self.load(newer_index)

        if not older or not newer:
            return None

        older_analysis = older['analysis']
        newer_analysis = newer['analysis']
        older_meta = older['snapshot_metadata']
        newer_meta = newer['snapshot_metadata']

        # Compare project metrics
        old_metrics = older_analysis.get('project_metrics', {})
        new_metrics = newer_analysis.get('project_metrics', {})

        metric_changes = {}
        tracked_metrics = [
            'avg_complexity', 'max_complexity', 'median_complexity',
            'avg_function_length', 'max_function_length',
            'docstring_coverage', 'type_hint_coverage',
            'total_functions', 'total_classes',
        ]

        regressions = []

        for metric in tracked_metrics:
            old_val = old_metrics.get(metric, 0)
            new_val = new_metrics.get(metric, 0)

            if old_val == 0 and new_val == 0:
                continue

            change = new_val - old_val
            pct_change = (change / old_val * 100) if old_val != 0 else float('inf')

            direction = 'unchanged'
            if change > 0:
                direction = 'increased'
            elif change < 0:
                direction = 'decreased'

            metric_changes[metric] = {
                'old': old_val,
                'new': new_val,
                'change': round(change, 4),
                'pct_change': round(pct_change, 2),
                'direction': direction,
            }

            # Check for regressions
            # Complexity increasing is bad
            if metric in ('avg_complexity', 'max_complexity', 'median_complexity',
                         'avg_function_length', 'max_function_length'):
                if pct_change > REGRESSION_THRESHOLD * 100:
                    regressions.append({
                        'metric': metric,
                        'severity': 'HIGH' if pct_change > 25 else 'MEDIUM',
                        'message': f'{metric} increased by {pct_change:.1f}% ({old_val} → {new_val})',
                    })
            # Coverage decreasing is bad
            elif metric in ('docstring_coverage', 'type_hint_coverage'):
                if change < 0 and abs(pct_change) > REGRESSION_THRESHOLD * 100:
                    regressions.append({
                        'metric': metric,
                        'severity': 'HIGH' if abs(pct_change) > 20 else 'MEDIUM',
                        'message': f'{metric} decreased by {abs(pct_change):.1f}% ({old_val} → {new_val})',
                    })

        # Compare summary stats
        old_summary = older_analysis.get('summary', {})
        new_summary = newer_analysis.get('summary', {})

        summary_changes = {}
        for key in ['total_files', 'total_functions', 'total_classes', 'total_lines', 'total_code_lines']:
            old_v = old_summary.get(key, 0)
            new_v = new_summary.get(key, 0)
            if old_v != new_v:
                summary_changes[key] = {
                    'old': old_v,
                    'new': new_v,
                    'change': new_v - old_v,
                }

        # File-level changes
        old_files = {fa['filepath'] for fa in older_analysis.get('file_analyses', []) if 'error' not in fa}
        new_files = {fa['filepath'] for fa in newer_analysis.get('file_analyses', []) if 'error' not in fa}

        added_files = sorted(new_files - old_files)
        removed_files = sorted(old_files - new_files)

        # Per-file complexity changes
        old_file_metrics = {
            fa['filepath']: fa for fa in older_analysis.get('file_analyses', []) if 'error' not in fa
        }
        new_file_metrics = {
            fa['filepath']: fa for fa in newer_analysis.get('file_analyses', []) if 'error' not in fa
        }

        file_changes = []
        for fp in sorted(old_files & new_files):
            old_fa = old_file_metrics[fp]
            new_fa = new_file_metrics[fp]
            old_cx = old_fa.get('avg_complexity', 0)
            new_cx = new_fa.get('avg_complexity', 0)
            if old_cx != new_cx:
                file_changes.append({
                    'file': fp,
                    'old_complexity': old_cx,
                    'new_complexity': new_cx,
                    'change': round(new_cx - old_cx, 2),
                    'direction': 'worse' if new_cx > old_cx else 'better',
                })

        return {
            'comparison': {
                'older': older_meta,
                'newer': newer_meta,
            },
            'metric_changes': metric_changes,
            'summary_changes': summary_changes,
            'regressions': regressions,
            'regression_detected': len(regressions) > 0,
            'added_files': added_files,
            'removed_files': removed_files,
            'file_complexity_changes': sorted(file_changes, key=lambda x: abs(x['change']), reverse=True),
        }

    def trend(self, max_snapshots: int = 20) -> dict:
        """Generate trend data across all snapshots."""
        snapshots = self.list_snapshots()[:max_snapshots]

        if len(snapshots) < 2:
            return {
                'message': f'Need at least 2 snapshots for trends. Currently have {len(snapshots)}.',
                'data_points': [],
            }

        data_points = []
        for i, snap_meta in enumerate(reversed(snapshots)):  # Oldest first
            snap = self.load(len(snapshots) - 1 - i)
            if not snap:
                continue

            analysis = snap['analysis']
            metrics = analysis.get('project_metrics', {})
            summary = analysis.get('summary', {})

            data_points.append({
                'timestamp': snap_meta.get('timestamp', ''),
                'label': snap_meta.get('label', ''),
                'avg_complexity': metrics.get('avg_complexity', 0),
                'max_complexity': metrics.get('max_complexity', 0),
                'docstring_coverage': metrics.get('docstring_coverage', 0),
                'type_hint_coverage': metrics.get('type_hint_coverage', 0),
                'total_functions': metrics.get('total_functions', 0),
                'total_lines': summary.get('total_lines', 0),
                'total_files': summary.get('total_files', 0),
            })

        # Compute trends (direction over time)
        if len(data_points) >= 2:
            first = data_points[0]
            last = data_points[-1]
            trends = {}
            for key in ['avg_complexity', 'max_complexity', 'docstring_coverage',
                       'type_hint_coverage', 'total_functions', 'total_lines']:
                old = first.get(key, 0)
                new = last.get(key, 0)
                if old != 0:
                    pct = round((new - old) / old * 100, 1)
                else:
                    pct = 0
                trends[key] = {
                    'start': old, 'end': new,
                    'change_pct': pct,
                    'direction': 'increasing' if pct > 0 else 'decreasing' if pct < 0 else 'stable',
                }
        else:
            trends = {}

        return {
            'snapshot_count': len(data_points),
            'time_range': {
                'oldest': data_points[0]['timestamp'] if data_points else None,
                'newest': data_points[-1]['timestamp'] if data_points else None,
            },
            'trends': trends,
            'data_points': data_points,
        }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DevDoc Snapshot Manager')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # save
    save_p = subparsers.add_parser('save', help='Save an analysis snapshot')
    save_p.add_argument('analysis_file', help='Path to analysis JSON file')
    save_p.add_argument('--project-dir', default='.', help='Project root directory')
    save_p.add_argument('--label', help='Optional label for this snapshot')

    # list
    list_p = subparsers.add_parser('list', help='List all snapshots')
    list_p.add_argument('--project-dir', default='.', help='Project root directory')

    # diff
    diff_p = subparsers.add_parser('diff', help='Compare two snapshots')
    diff_p.add_argument('--older', type=int, default=1, help='Older snapshot index (default: 1)')
    diff_p.add_argument('--newer', type=int, default=0, help='Newer snapshot index (default: 0)')
    diff_p.add_argument('--project-dir', default='.', help='Project root directory')

    # trend
    trend_p = subparsers.add_parser('trend', help='Show trends across snapshots')
    trend_p.add_argument('--max', type=int, default=20, help='Max snapshots to analyze')
    trend_p.add_argument('--project-dir', default='.', help='Project root directory')

    args = parser.parse_args()
    mgr = SnapshotManager(args.project_dir)

    if args.command == 'save':
        with open(args.analysis_file, 'r') as f:
            analysis = json.load(f)
        filename = mgr.save(analysis, label=args.label)
        print(f"Snapshot saved: {filename}", file=sys.stderr)

    elif args.command == 'list':
        snapshots = mgr.list_snapshots()
        for i, snap in enumerate(snapshots):
            label = f" [{snap.get('label')}]" if snap.get('label') else ""
            print(f"  [{i}] {snap.get('timestamp', '?')}{label} — {snap.get('filename', '?')}")

    elif args.command == 'diff':
        result = mgr.diff(args.older, args.newer)
        if result:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("Not enough snapshots for comparison.", file=sys.stderr)

    elif args.command == 'trend':
        result = mgr.trend(args.max)
        print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
