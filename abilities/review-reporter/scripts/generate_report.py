#!/usr/bin/env python3
"""
DevDoc Review Reporter

Generates a scored governance report card combining all analysis dimensions:
- Overall health grade with breakdown
- Risk assessment matrix
- Regression detection (if snapshots available)
- Before/after comparison (if diff data available)
- Prioritized action items
- Executive summary for stakeholders

Output: Clean Markdown report optimized for WithAI's WYSIWYG editor.

Usage:
    python generate_report.py --analysis analysis.json [--security security.json]
        [--governance governance.json] [--architecture architecture.json]
        [--diff diff.json] [--output REVIEW-REPORT.md]

Part of the review-reporter WithAI ability.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional


class ReviewReporter:
    """Generates comprehensive code review report cards."""

    def __init__(self, analysis: dict, security: Optional[dict] = None,
                 governance: Optional[dict] = None, architecture: Optional[dict] = None,
                 diff: Optional[dict] = None):
        self.analysis = analysis
        self.security = security or {}
        self.governance = governance or {}
        self.architecture = architecture or {}
        self.diff = diff or {}

    def generate(self) -> str:
        """Generate the full review report."""
        sections = [
            self._header(),
            self._executive_summary(),
            self._scorecard(),
            self._risk_matrix(),
            self._regression_section(),
            self._hotspot_analysis(),
            self._action_items(),
            self._detailed_findings(),
            self._footer(),
        ]

        return '\n\n'.join(s for s in sections if s)

    # ─── Header ────────────────────────────────────────────────────────────

    def _header(self) -> str:
        name = self.analysis.get('project_name', 'Project')
        return f"""# {name} — Code Review Report

> **DevDoc Intelligence Platform** — Automated Governance Review
> Report Date: {datetime.now().strftime('%B %d, %Y at %H:%M')}
> Analysis Scope: {self.analysis.get('summary', {}).get('total_files', 0)} files, {self.analysis.get('summary', {}).get('total_code_lines', 0):,} lines of code

---"""

    # ─── Executive Summary ─────────────────────────────────────────────────

    def _executive_summary(self) -> str:
        overall = self._compute_overall_score()
        metrics = self.analysis.get('project_metrics', {})

        # Build narrative
        if overall['score'] >= 90:
            assessment = "The codebase is in **excellent health**. No critical issues detected. Maintain current engineering practices."
        elif overall['score'] >= 75:
            assessment = "The codebase is in **good health** with some areas requiring attention. Address the action items below to prevent technical debt accumulation."
        elif overall['score'] >= 60:
            assessment = "The codebase has **moderate health concerns**. Several issues need attention to ensure long-term maintainability. Prioritize the critical findings."
        elif overall['score'] >= 45:
            assessment = "The codebase has **significant quality concerns**. Structural issues are accumulating and need prompt attention."
        else:
            assessment = "The codebase is in **poor health**. Multiple critical issues detected. Recommend a dedicated engineering sprint for remediation."

        # Highlight specific concerns
        concerns = []
        if metrics.get('docstring_coverage', 0) < 0.5:
            concerns.append(f"Low documentation coverage ({metrics['docstring_coverage']:.0%})")
        if metrics.get('type_hint_coverage', 0) < 0.3:
            concerns.append(f"Limited type hint usage ({metrics['type_hint_coverage']:.0%})")
        if metrics.get('max_complexity', 0) > 15:
            concerns.append(f"Critical complexity in some functions (max: {metrics['max_complexity']})")
        if self.security.get('severity_counts', {}).get('CRITICAL', 0) > 0:
            concerns.append(f"{self.security['severity_counts']['CRITICAL']} critical security issues")
        if self.governance.get('total_findings', 0) > 5:
            concerns.append(f"{self.governance['total_findings']} AI governance issues detected")

        concern_text = ""
        if concerns:
            concern_text = "\n\n**Key Concerns:**\n" + '\n'.join(f"- ⚠️ {c}" for c in concerns)

        return f"""## Executive Summary

**Overall Health Score: {overall['score']}/100 (Grade: {overall['grade']})**

{assessment}{concern_text}"""

    # ─── Scorecard ─────────────────────────────────────────────────────────

    def _scorecard(self) -> str:
        overall = self._compute_overall_score()
        breakdown = overall['breakdown']

        def grade_bar(score):
            filled = int(score / 10)
            empty = 10 - filled
            return '█' * filled + '░' * empty

        rows = []
        for dimension, data in breakdown.items():
            name = dimension.replace('_', ' ').title()
            score = data['score']
            weight = data['weight']
            grade = data['grade']
            rows.append(
                f"| {name} | {grade_bar(score)} | {score}/100 | {grade} | {weight:.0%} |"
            )

        return f"""## Scorecard

| Dimension | Health Bar | Score | Grade | Weight |
|-----------|-----------|-------|-------|--------|
{''.join(chr(10) + r for r in rows)}

**Weighted Total: {overall['score']}/100 ({overall['grade']})**"""

    # ─── Risk Matrix ───────────────────────────────────────────────────────

    def _risk_matrix(self) -> str:
        risks = []

        # Architecture risks
        bottlenecks = self.architecture.get('bottlenecks', [])
        for b in bottlenecks:
            risks.append({
                'area': 'Architecture',
                'risk': f"Bottleneck: {b['file']}",
                'severity': b['severity'],
                'impact': f"{b['fan_in']} dependent modules affected",
                'likelihood': 'HIGH' if b['fan_in'] >= 5 else 'MEDIUM',
            })

        # Security risks
        for f in self.security.get('findings', []):
            if f.get('severity') in ('CRITICAL', 'HIGH'):
                risks.append({
                    'area': 'Security',
                    'risk': f['description'],
                    'severity': f['severity'],
                    'impact': f"Potential vulnerability in {f['file']}",
                    'likelihood': 'HIGH' if f['severity'] == 'CRITICAL' else 'MEDIUM',
                })

        # AI governance risks
        for f in self.governance.get('findings', []):
            if f.get('severity') == 'HIGH':
                risks.append({
                    'area': 'AI Governance',
                    'risk': f['type'].replace('_', ' ').title(),
                    'severity': f['severity'],
                    'impact': f['message'][:80],
                    'likelihood': 'MEDIUM',
                })

        if not risks:
            return """## Risk Assessment

🟢 **No significant risks identified.** The codebase maintains acceptable risk levels across all dimensions."""

        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        risks.sort(key=lambda r: severity_order.get(r['severity'], 4))

        rows = []
        for r in risks[:15]:
            severity_icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(r['severity'], '⬜')
            rows.append(
                f"| {severity_icon} {r['severity']} | {r['area']} | {r['risk'][:50]} | {r['impact'][:50]} |"
            )

        return f"""## Risk Assessment

| Severity | Area | Risk | Impact |
|----------|------|------|--------|
{''.join(chr(10) + r for r in rows)}"""

    # ─── Regression Section ────────────────────────────────────────────────

    def _regression_section(self) -> str:
        if not self.diff:
            return """## Regression Check

> No previous snapshot available for comparison. Run DevDoc at least twice to enable regression detection."""

        regressions = self.diff.get('regressions', [])
        metric_changes = self.diff.get('metric_changes', {})
        regression_detected = self.diff.get('regression_detected', False)

        if not regression_detected:
            status = "🟢 **No regressions detected.** All metrics are stable or improving."
        else:
            status = f"🔴 **{len(regressions)} regression(s) detected.** Review the changes below."

        sections = [f"""## Regression Check

{status}

### Metric Changes

| Metric | Previous | Current | Change | Trend |
|--------|----------|---------|--------|-------|"""]

        for metric, data in metric_changes.items():
            pct = data.get('pct_change', 0)
            trend_icon = '📈' if pct > 0 else '📉' if pct < 0 else '➡️'

            # Mark regressions
            is_regression = any(r['metric'] == metric for r in regressions)
            if is_regression:
                trend_icon = '🔴 ' + trend_icon

            sections.append(
                f"| {metric.replace('_', ' ').title()} | {data.get('old', '-')} | "
                f"{data.get('new', '-')} | {pct:+.1f}% | {trend_icon} |"
            )

        # Specific regression details
        if regressions:
            sections.append("\n### Regression Details\n")
            for r in regressions:
                sections.append(f"- **[{r['severity']}]** {r['message']}")

        # File-level changes
        file_changes = self.diff.get('file_complexity_changes', [])
        if file_changes:
            sections.append("\n### File-Level Changes\n")
            sections.append("| File | Previous Complexity | Current | Direction |")
            sections.append("|------|--------------------|---------|-----------| ")
            for fc in file_changes[:10]:
                icon = '🔴 Worse' if fc['direction'] == 'worse' else '🟢 Better'
                sections.append(
                    f"| `{fc['file']}` | {fc['old_complexity']} | {fc['new_complexity']} | {icon} |"
                )

        return '\n'.join(sections)

    # ─── Hotspot Analysis ──────────────────────────────────────────────────

    def _hotspot_analysis(self) -> str:
        metrics = self.analysis.get('project_metrics', {})
        hotspots = metrics.get('hotspot_functions', [])
        longest = metrics.get('longest_functions', [])

        if not hotspots and not longest:
            return ''

        sections = ["## Code Hotspots\n"]

        if hotspots:
            sections.append("### Highest Complexity Functions\n")
            sections.append("| Function | File | Complexity | Lines | Risk |")
            sections.append("|----------|------|-----------|-------|------|")
            for h in hotspots[:8]:
                risk = '🔴 Critical' if h['complexity'] > 15 else '🟠 High' if h['complexity'] > 10 else '🟡 Medium'
                sections.append(
                    f"| `{h['name']}` | `{h['file']}` | {h['complexity']} | {h['line_count']} | {risk} |"
                )

        if longest:
            sections.append("\n### Longest Functions\n")
            sections.append("| Function | File | Lines | Complexity |")
            sections.append("|----------|------|-------|-----------|")
            for l in longest[:8]:
                sections.append(
                    f"| `{l['name']}` | `{l['file']}` | {l['line_count']} | {l['complexity']} |"
                )

        return '\n'.join(sections)

    # ─── Action Items ──────────────────────────────────────────────────────

    def _action_items(self) -> str:
        actions = []
        priority = 1

        # Architecture actions
        for r in self.architecture.get('strategic_recommendations', []):
            actions.append({
                'priority': priority,
                'category': r.get('category', 'Architecture'),
                'action': r.get('action', ''),
                'target': r.get('target', ''),
                'effort': r.get('effort', 'MEDIUM'),
                'impact': r.get('impact', ''),
            })
            priority += 1

        # Security actions
        for f in self.security.get('findings', []):
            if f.get('severity') in ('CRITICAL', 'HIGH'):
                actions.append({
                    'priority': priority,
                    'category': 'Security',
                    'action': f"Fix: {f['description']}",
                    'target': f"{f['file']}:{f['line']}",
                    'effort': 'LOW',
                    'impact': f"Removes {f['severity']} vulnerability",
                })
                priority += 1

        # AI governance actions
        for r in self.governance.get('recommendations', []):
            actions.append({
                'priority': priority,
                'category': 'AI Governance',
                'action': r[:120],
                'target': '',
                'effort': 'MEDIUM',
                'impact': 'Improves code quality',
            })
            priority += 1

        # Documentation actions
        metrics = self.analysis.get('project_metrics', {})
        if metrics.get('docstring_coverage', 0) < 0.5:
            actions.append({
                'priority': priority,
                'category': 'Documentation',
                'action': f"Increase docstring coverage from {metrics['docstring_coverage']:.0%} to at least 50%",
                'target': 'All modules',
                'effort': 'LOW',
                'impact': 'Improves maintainability',
            })
            priority += 1

        if not actions:
            return """## Action Items

✅ **No critical actions required.** The codebase meets quality standards across all dimensions."""

        sections = ["""## Action Items

Prioritized list of improvements, ordered by impact.\n"""]

        sections.append("| # | Category | Action | Target | Effort |")
        sections.append("|---|----------|--------|--------|--------|")
        for a in actions[:15]:
            sections.append(
                f"| {a['priority']} | {a['category']} | {a['action'][:70]} | "
                f"`{a['target'][:30]}` | {a['effort']} |"
            )

        return '\n'.join(sections)

    # ─── Detailed Findings ─────────────────────────────────────────────────

    def _detailed_findings(self) -> str:
        all_findings = []

        # Collect from all sources
        for f in self.security.get('findings', []):
            all_findings.append({
                'source': 'Security',
                'severity': f.get('severity', 'MEDIUM'),
                'message': f.get('description', ''),
                'file': f.get('file', ''),
                'line': f.get('line', 0),
            })

        for f in self.governance.get('findings', []):
            all_findings.append({
                'source': 'AI Governance',
                'severity': f.get('severity', 'MEDIUM'),
                'message': f.get('message', ''),
                'file': f.get('details', {}).get('file', ''),
                'line': f.get('details', {}).get('line', 0),
            })

        for b in self.architecture.get('bottlenecks', []):
            all_findings.append({
                'source': 'Architecture',
                'severity': b.get('severity', 'MEDIUM'),
                'message': ', '.join(b.get('reasons', [])),
                'file': b.get('file', ''),
                'line': 0,
            })

        if not all_findings:
            return ''

        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_findings.sort(key=lambda f: severity_order.get(f['severity'], 4))

        sections = ["""## All Findings

<details>
<summary>Click to expand full findings list ({count} total)</summary>

| # | Severity | Source | File | Finding |
|---|----------|--------|------|---------|""".format(count=len(all_findings))]

        for i, f in enumerate(all_findings[:30], 1):
            icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(f['severity'], '⬜')
            file_ref = f"`{f['file']}:{f['line']}`" if f['line'] else f"`{f['file']}`" if f['file'] else '—'
            sections.append(
                f"| {i} | {icon} {f['severity']} | {f['source']} | {file_ref} | {f['message'][:60]} |"
            )

        sections.append("\n</details>")
        return '\n'.join(sections)

    # ─── Scoring ───────────────────────────────────────────────────────────

    def _compute_overall_score(self) -> dict:
        """Compute weighted overall health score."""
        metrics = self.analysis.get('project_metrics', {})

        # Individual dimension scores
        dimensions = {}

        # Complexity score
        avg_cx = metrics.get('avg_complexity', 0)
        cx_score = max(0, min(100, 100 - (avg_cx - 3) * 15))
        dimensions['complexity'] = {'score': round(cx_score), 'weight': 0.20, 'grade': self._grade(cx_score)}

        # Architecture score
        arch_score = self.architecture.get('architecture_score', 80)
        dimensions['architecture'] = {'score': arch_score, 'weight': 0.20, 'grade': self._grade(arch_score)}

        # Documentation score
        doc_cov = metrics.get('docstring_coverage', 0)
        doc_score = round(doc_cov * 100)
        dimensions['documentation'] = {'score': doc_score, 'weight': 0.15, 'grade': self._grade(doc_score)}

        # Testing (binary check since we can't deep-analyze test quality here)
        has_tests = self.analysis.get('summary', {}).get('has_tests', False)
        test_score = 70 if has_tests else 20
        dimensions['testing'] = {'score': test_score, 'weight': 0.15, 'grade': self._grade(test_score)}

        # Security score
        sec_score = self.security.get('security_score', 85)
        dimensions['security'] = {'score': sec_score, 'weight': 0.15, 'grade': self._grade(sec_score)}

        # AI Governance score
        gov_score = self.governance.get('governance_score', 85)
        dimensions['ai_governance'] = {'score': gov_score, 'weight': 0.15, 'grade': self._grade(gov_score)}

        # Weighted total
        total = sum(d['score'] * d['weight'] for d in dimensions.values())
        total = round(total)

        return {
            'score': total,
            'grade': self._grade(total),
            'breakdown': dimensions,
        }

    def _grade(self, score) -> str:
        if score >= 90: return 'A'
        if score >= 75: return 'B'
        if score >= 60: return 'C'
        if score >= 45: return 'D'
        return 'F'

    # ─── Footer ────────────────────────────────────────────────────────────

    def _footer(self) -> str:
        return """---

*This report was generated by **DevDoc Intelligence Platform**.*
*For continuous monitoring, integrate DevDoc into your CI/CD pipeline using the included GitHub Action.*
*Open this file in WithAI's WYSIWYG editor for visual editing, or export to PDF.*"""


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DevDoc Review Reporter')
    parser.add_argument('--analysis', '-a', required=True, help='Path to analysis.json')
    parser.add_argument('--security', '-s', help='Path to security.json')
    parser.add_argument('--governance', '-g', help='Path to governance.json')
    parser.add_argument('--architecture', '-r', help='Path to architecture.json')
    parser.add_argument('--diff', '-d', help='Path to diff.json (for regression check)')
    parser.add_argument('--output', '-o', help='Output markdown file path')
    args = parser.parse_args()

    def load_json(path):
        if path and Path(path).exists():
            with open(path) as f:
                return json.load(f)
        return None

    analysis = load_json(args.analysis) or {}
    security = load_json(args.security)
    governance = load_json(args.governance)
    architecture = load_json(args.architecture)
    diff = load_json(args.diff)

    reporter = ReviewReporter(analysis, security, governance, architecture, diff)
    markdown = reporter.generate()

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(markdown)
        print(f"Review report saved to: {args.output}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == '__main__':
    main()
