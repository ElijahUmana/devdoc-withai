#!/usr/bin/env python3
"""
DevDoc Architecture Reasoner

Goes beyond metrics to provide strategic architectural insights:
- Bottleneck detection (high fan-in + high complexity = structural risk)
- Concern separation analysis (mixed responsibilities in single modules)
- Circular dependency detection
- God module identification (modules that do too much)
- Coupling/cohesion scoring
- Architectural drift detection (comparing against baseline patterns)
- Natural language recommendations with reasoning chains

Instead of: "Function X has complexity 14."
It says: "This module is becoming a bottleneck because 7 files depend on it,
  it contains high-complexity logic, and it mixes business logic and IO.
  Recommendation: split into service + adapter layer."

Usage:
    python architecture_reasoner.py <project-root> --analysis analysis.json [--output architecture.json]

Part of the codebase-analyzer WithAI ability.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Optional


# ─── Architectural Patterns ────────────────────────────────────────────────────

# Import categories that indicate concern mixing
CONCERN_CATEGORIES = {
    'io': {
        'keywords': ['open', 'read', 'write', 'file', 'path', 'os.path', 'pathlib', 'shutil'],
        'imports': ['os', 'io', 'pathlib', 'shutil', 'tempfile', 'glob'],
        'label': 'File I/O',
    },
    'network': {
        'keywords': ['request', 'response', 'http', 'url', 'socket', 'api'],
        'imports': ['requests', 'urllib', 'http', 'aiohttp', 'httpx', 'socket', 'flask', 'fastapi', 'django'],
        'label': 'Network/HTTP',
    },
    'database': {
        'keywords': ['query', 'cursor', 'execute', 'commit', 'session', 'model'],
        'imports': ['sqlalchemy', 'sqlite3', 'psycopg2', 'pymongo', 'redis', 'mysql', 'peewee'],
        'label': 'Database',
    },
    'business_logic': {
        'keywords': ['calculate', 'compute', 'process', 'validate', 'transform', 'parse', 'convert'],
        'imports': [],
        'label': 'Business Logic',
    },
    'presentation': {
        'keywords': ['render', 'template', 'view', 'display', 'format', 'serialize', 'jsonify'],
        'imports': ['jinja2', 'mako', 'django.template'],
        'label': 'Presentation',
    },
    'logging': {
        'keywords': ['log', 'logger', 'logging', 'debug', 'warning', 'error'],
        'imports': ['logging', 'loguru', 'structlog'],
        'label': 'Logging/Monitoring',
    },
    'testing': {
        'keywords': ['test', 'assert', 'mock', 'fixture', 'setUp', 'tearDown'],
        'imports': ['pytest', 'unittest', 'mock', 'hypothesis'],
        'label': 'Testing',
    },
}

# Known architectural patterns
ARCHITECTURE_PATTERNS = {
    'mvc': {
        'indicators': ['models', 'views', 'controllers', 'templates'],
        'label': 'MVC (Model-View-Controller)',
    },
    'layered': {
        'indicators': ['models', 'services', 'routes', 'controllers', 'utils', 'helpers'],
        'label': 'Layered Architecture',
    },
    'microservice': {
        'indicators': ['Dockerfile', 'docker-compose', 'gateway', 'service'],
        'label': 'Microservices',
    },
    'monolith': {
        'indicators': ['app', 'main', 'server'],
        'label': 'Monolithic',
    },
}


class ArchitectureReasoner:
    """Performs architectural reasoning and generates strategic insights."""

    def __init__(self, root_path: str, config: Optional[dict] = None):
        self.root = Path(root_path).resolve()
        self.config = config or {}
        threshold_config = self.config.get('thresholds', {})
        self.fan_in_warning = threshold_config.get('dependency_fan_in', {}).get('warning', 5)
        self.fan_in_critical = threshold_config.get('dependency_fan_in', {}).get('critical', 8)

    def analyze(self, analysis: dict) -> dict:
        """Run full architectural reasoning on analysis data."""
        file_analyses = analysis.get('file_analyses', [])
        dep_graph = analysis.get('dependency_graph', {})
        project_metrics = analysis.get('project_metrics', {})

        # Run all reasoning engines
        bottlenecks = self._detect_bottlenecks(file_analyses, dep_graph)
        concern_mixing = self._analyze_concern_separation(file_analyses)
        circular_deps = self._detect_circular_dependencies(dep_graph)
        god_modules = self._detect_god_modules(file_analyses, dep_graph)
        coupling_score = self._compute_coupling_score(dep_graph, file_analyses)
        arch_pattern = self._detect_architecture_pattern(analysis)
        recommendations = self._generate_strategic_recommendations(
            bottlenecks, concern_mixing, circular_deps, god_modules, coupling_score
        )

        # Architecture health score
        score = self._compute_architecture_score(
            bottlenecks, concern_mixing, circular_deps, god_modules, coupling_score
        )

        return {
            'architecture_pattern': arch_pattern,
            'architecture_score': score['score'],
            'architecture_grade': score['grade'],
            'score_breakdown': score['breakdown'],
            'bottlenecks': bottlenecks,
            'concern_separation': concern_mixing,
            'circular_dependencies': circular_deps,
            'god_modules': god_modules,
            'coupling_analysis': coupling_score,
            'strategic_recommendations': recommendations,
            'summary': self._build_narrative_summary(
                arch_pattern, score, bottlenecks, concern_mixing, god_modules, recommendations
            ),
        }

    def _detect_bottlenecks(self, file_analyses: list, dep_graph: dict) -> list[dict]:
        """Identify modules that are structural bottlenecks with reasoning."""
        bottlenecks = []
        fan_metrics = dep_graph.get('fan_metrics', {})

        for fa in file_analyses:
            if 'error' in fa:
                continue

            fp = fa['filepath']
            metrics = fan_metrics.get(fp, {})
            fan_in = metrics.get('fan_in', 0)
            depended_by = metrics.get('depended_by', [])
            avg_cx = fa.get('avg_complexity', 0)
            max_cx = fa.get('max_complexity', 0)
            func_count = fa.get('function_count', 0)

            # Bottleneck = high fan-in + non-trivial complexity
            is_bottleneck = False
            severity = 'LOW'
            reasons = []

            if fan_in >= self.fan_in_critical:
                is_bottleneck = True
                severity = 'CRITICAL'
                reasons.append(f'{fan_in} files depend on this module')
            elif fan_in >= self.fan_in_warning:
                is_bottleneck = True
                severity = 'HIGH'
                reasons.append(f'{fan_in} files depend on this module')

            if avg_cx >= 8:
                if is_bottleneck:
                    severity = 'CRITICAL'
                else:
                    is_bottleneck = True
                    severity = 'HIGH'
                reasons.append(f'Contains high-complexity logic (avg: {avg_cx})')

            if func_count >= 10:
                reasons.append(f'Has {func_count} functions (large surface area)')
                if not is_bottleneck and fan_in >= 3:
                    is_bottleneck = True

            if max_cx >= 15:
                reasons.append(f'Contains a function with complexity {max_cx}')
                is_bottleneck = True

            if is_bottleneck:
                # Build reasoning chain
                reasoning = self._build_bottleneck_reasoning(fp, fan_in, depended_by, avg_cx, func_count, reasons)

                bottlenecks.append({
                    'file': fp,
                    'severity': severity,
                    'fan_in': fan_in,
                    'avg_complexity': avg_cx,
                    'max_complexity': max_cx,
                    'function_count': func_count,
                    'depended_by': depended_by,
                    'reasons': reasons,
                    'reasoning': reasoning,
                    'recommendation': self._bottleneck_recommendation(fp, fan_in, avg_cx, func_count),
                })

        return sorted(bottlenecks, key=lambda b: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(b['severity'], 4))

    def _build_bottleneck_reasoning(self, fp, fan_in, depended_by, avg_cx, func_count, reasons) -> str:
        """Build a natural language reasoning chain for a bottleneck."""
        parts = [f"**{fp}** is becoming a structural bottleneck because:"]
        for i, reason in enumerate(reasons, 1):
            parts.append(f"  {i}. {reason}")

        if fan_in >= 3 and avg_cx >= 5:
            parts.append("")
            parts.append(
                f"This creates compounding risk: any change to {fp} affects "
                f"{fan_in} dependent files, and the internal complexity (avg {avg_cx}) "
                f"makes safe modification harder."
            )

        return '\n'.join(parts)

    def _bottleneck_recommendation(self, fp, fan_in, avg_cx, func_count) -> str:
        """Generate specific refactoring recommendation for a bottleneck."""
        name = Path(fp).stem

        if fan_in >= 5 and avg_cx >= 5:
            return (
                f"Split {name} into a thin interface module (types/contracts) depended on by others, "
                f"and an implementation module with the complex logic. This reduces coupling "
                f"while preserving the current API surface."
            )
        elif fan_in >= 5:
            return (
                f"Consider extracting a stable interface/protocol layer from {name}. "
                f"Other modules should depend on the interface, not the implementation."
            )
        elif avg_cx >= 8:
            return (
                f"Reduce complexity in {name} by extracting pure functions for complex logic "
                f"into helper modules. Keep {name} as an orchestration layer."
            )
        elif func_count >= 10:
            return (
                f"Group the {func_count} functions in {name} into cohesive sub-modules. "
                f"Each sub-module should handle a single responsibility."
            )
        return f"Monitor {name} for growing complexity. Consider refactoring if it grows further."

    def _analyze_concern_separation(self, file_analyses: list) -> list[dict]:
        """Detect modules that mix multiple responsibilities."""
        findings = []

        for fa in file_analyses:
            if 'error' in fa:
                continue

            fp = fa['filepath']
            # Skip test files
            if 'test' in fp.lower():
                continue

            # Categorize imports and function names by concern
            concerns_found = set()
            concern_evidence = defaultdict(list)

            # Check imports
            for imp in fa.get('imports', []):
                module = imp.get('module', '')
                names = imp.get('names', [])
                for category, info in CONCERN_CATEGORIES.items():
                    for pkg in info['imports']:
                        if pkg in module or pkg in ' '.join(names):
                            concerns_found.add(category)
                            concern_evidence[category].append(f"imports {module or ', '.join(names)}")

            # Check function names for concern keywords
            for func in fa.get('functions', []):
                name_lower = func['name'].lower()
                for category, info in CONCERN_CATEGORIES.items():
                    for kw in info['keywords']:
                        if kw in name_lower:
                            concerns_found.add(category)
                            concern_evidence[category].append(f"function {func['name']}")
                            break

            # A module mixing 3+ concerns is a problem
            if len(concerns_found) >= 3:
                concern_labels = [CONCERN_CATEGORIES[c]['label'] for c in concerns_found]
                findings.append({
                    'file': fp,
                    'severity': 'HIGH' if len(concerns_found) >= 4 else 'MEDIUM',
                    'concerns': sorted(concern_labels),
                    'concern_count': len(concerns_found),
                    'evidence': {
                        CONCERN_CATEGORIES[c]['label']: concern_evidence[c][:3]
                        for c in concerns_found
                    },
                    'reasoning': (
                        f"**{fp}** mixes {len(concerns_found)} distinct concerns: "
                        f"{', '.join(sorted(concern_labels))}. "
                        f"This violates the Single Responsibility Principle and makes the module "
                        f"harder to test, maintain, and reason about independently."
                    ),
                    'recommendation': (
                        f"Separate {Path(fp).stem} into concern-specific modules: "
                        + ', '.join(f"{l.lower()}.py" for l in sorted(concern_labels)[:3])
                        + '.'
                    ),
                })

        return findings

    def _detect_circular_dependencies(self, dep_graph: dict) -> list[dict]:
        """Detect circular import chains."""
        edges = dep_graph.get('edges', {})
        cycles = []
        visited = set()

        def dfs(node, path, path_set):
            if node in path_set:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycle_key = tuple(sorted(cycle))
                if cycle_key not in visited:
                    visited.add(cycle_key)
                    cycles.append(cycle)
                return

            path.append(node)
            path_set.add(node)

            for neighbor in edges.get(node, []):
                dfs(neighbor, path, path_set)

            path.pop()
            path_set.discard(node)

        for node in edges:
            dfs(node, [], set())

        findings = []
        for cycle in cycles:
            findings.append({
                'files': cycle,
                'length': len(cycle) - 1,
                'severity': 'HIGH' if len(cycle) > 3 else 'MEDIUM',
                'reasoning': (
                    f"Circular dependency chain: {' → '.join(cycle)}. "
                    f"Circular imports make modules tightly coupled and complicate "
                    f"testing, refactoring, and understanding the dependency flow."
                ),
                'recommendation': (
                    "Break the cycle by extracting shared types/interfaces into a common module, "
                    "or use dependency injection to reverse one of the dependency arrows."
                ),
            })

        return findings

    def _detect_god_modules(self, file_analyses: list, dep_graph: dict) -> list[dict]:
        """Identify modules that do too much."""
        god_modules = []
        fan_metrics = dep_graph.get('fan_metrics', {})

        for fa in file_analyses:
            if 'error' in fa:
                continue

            fp = fa['filepath']
            func_count = fa.get('function_count', 0)
            class_count = fa.get('class_count', 0)
            total_lines = fa.get('total_lines', 0)
            avg_cx = fa.get('avg_complexity', 0)
            fan_in = fan_metrics.get(fp, {}).get('fan_in', 0)

            # God module heuristics
            reasons = []
            risk_score = 0

            if func_count >= 10:
                reasons.append(f'{func_count} functions')
                risk_score += func_count - 9

            if class_count >= 3:
                reasons.append(f'{class_count} classes')
                risk_score += (class_count - 2) * 3

            if total_lines >= 300:
                reasons.append(f'{total_lines} lines')
                risk_score += (total_lines - 299) // 50

            if fan_in >= 5:
                reasons.append(f'{fan_in} dependents')
                risk_score += fan_in - 4

            if risk_score >= 5:
                god_modules.append({
                    'file': fp,
                    'severity': 'CRITICAL' if risk_score >= 15 else 'HIGH' if risk_score >= 10 else 'MEDIUM',
                    'risk_score': risk_score,
                    'function_count': func_count,
                    'class_count': class_count,
                    'total_lines': total_lines,
                    'reasons': reasons,
                    'reasoning': (
                        f"**{fp}** shows god module characteristics: {', '.join(reasons)}. "
                        f"Large modules with many responsibilities become maintenance bottlenecks "
                        f"and resist safe modification."
                    ),
                    'recommendation': (
                        f"Decompose {Path(fp).stem} by identifying 2-3 cohesive groups of functions/classes "
                        f"and extracting each into its own module. Prioritize the highest-complexity "
                        f"functions for extraction first."
                    ),
                })

        return sorted(god_modules, key=lambda g: g['risk_score'], reverse=True)

    def _compute_coupling_score(self, dep_graph: dict, file_analyses: list) -> dict:
        """Compute overall coupling and cohesion metrics."""
        fan_metrics = dep_graph.get('fan_metrics', {})
        edges = dep_graph.get('edges', {})

        total_files = len(file_analyses)
        if total_files == 0:
            return {'coupling_score': 0, 'assessment': 'No files to analyze'}

        total_edges = sum(len(v) for v in edges.values())
        max_possible_edges = total_files * (total_files - 1)

        # Coupling density: actual edges / possible edges
        density = total_edges / max_possible_edges if max_possible_edges > 0 else 0

        # Average fan-in and fan-out
        fan_ins = [m.get('fan_in', 0) for m in fan_metrics.values()]
        fan_outs = [m.get('fan_out', 0) for m in fan_metrics.values()]

        avg_fan_in = sum(fan_ins) / len(fan_ins) if fan_ins else 0
        avg_fan_out = sum(fan_outs) / len(fan_outs) if fan_outs else 0
        max_fan_in = max(fan_ins) if fan_ins else 0

        # Instability: fan_out / (fan_in + fan_out) per module
        instability_scores = {}
        for fp, m in fan_metrics.items():
            fi = m.get('fan_in', 0)
            fo = m.get('fan_out', 0)
            total = fi + fo
            instability_scores[fp] = round(fo / total, 2) if total > 0 else 0.5

        # Overall coupling assessment
        if density > 0.5:
            assessment = 'Highly coupled — modules are tightly interconnected'
        elif density > 0.3:
            assessment = 'Moderately coupled — consider reducing dependencies'
        elif density > 0.1:
            assessment = 'Loosely coupled — good separation'
        else:
            assessment = 'Very loosely coupled — modules are independent'

        return {
            'coupling_density': round(density, 3),
            'avg_fan_in': round(avg_fan_in, 2),
            'avg_fan_out': round(avg_fan_out, 2),
            'max_fan_in': max_fan_in,
            'total_dependencies': total_edges,
            'assessment': assessment,
            'instability_by_file': instability_scores,
        }

    def _detect_architecture_pattern(self, analysis: dict) -> dict:
        """Detect the likely architectural pattern."""
        all_files = analysis.get('all_files', [])
        file_names = [Path(f['path']).stem.lower() for f in all_files]
        dir_names = set()
        for f in all_files:
            parts = Path(f['path']).parts
            for part in parts[:-1]:
                dir_names.add(part.lower())

        all_names = set(file_names) | dir_names

        best_match = None
        best_score = 0

        for pattern_name, pattern in ARCHITECTURE_PATTERNS.items():
            matches = sum(1 for ind in pattern['indicators'] if ind in all_names)
            score = matches / len(pattern['indicators'])
            if score > best_score:
                best_score = score
                best_match = pattern_name

        if best_match and best_score >= 0.3:
            return {
                'detected_pattern': ARCHITECTURE_PATTERNS[best_match]['label'],
                'confidence': round(best_score, 2),
                'matched_indicators': [
                    ind for ind in ARCHITECTURE_PATTERNS[best_match]['indicators']
                    if ind in all_names
                ],
            }

        return {
            'detected_pattern': 'Custom/Unrecognized',
            'confidence': 0,
            'matched_indicators': [],
        }

    def _compute_architecture_score(self, bottlenecks, concern_mixing, circular_deps,
                                     god_modules, coupling_score) -> dict:
        """Compute an overall architecture health score."""
        score = 100
        breakdown = {}

        # Bottleneck penalty
        bottleneck_penalty = sum(
            {'CRITICAL': 15, 'HIGH': 10, 'MEDIUM': 5, 'LOW': 2}.get(b['severity'], 0)
            for b in bottlenecks
        )
        bottleneck_penalty = min(bottleneck_penalty, 30)
        score -= bottleneck_penalty
        breakdown['bottlenecks'] = {'penalty': bottleneck_penalty, 'count': len(bottlenecks)}

        # Concern mixing penalty
        concern_penalty = len(concern_mixing) * 8
        concern_penalty = min(concern_penalty, 25)
        score -= concern_penalty
        breakdown['concern_separation'] = {'penalty': concern_penalty, 'count': len(concern_mixing)}

        # Circular dependency penalty
        circular_penalty = len(circular_deps) * 12
        circular_penalty = min(circular_penalty, 25)
        score -= circular_penalty
        breakdown['circular_dependencies'] = {'penalty': circular_penalty, 'count': len(circular_deps)}

        # God module penalty
        god_penalty = sum(min(g['risk_score'], 15) for g in god_modules)
        god_penalty = min(god_penalty, 20)
        score -= god_penalty
        breakdown['god_modules'] = {'penalty': god_penalty, 'count': len(god_modules)}

        # Coupling penalty
        density = coupling_score.get('coupling_density', 0)
        if density > 0.5:
            coupling_penalty = 15
        elif density > 0.3:
            coupling_penalty = 8
        elif density > 0.2:
            coupling_penalty = 3
        else:
            coupling_penalty = 0
        score -= coupling_penalty
        breakdown['coupling'] = {'penalty': coupling_penalty, 'density': density}

        score = max(0, score)
        grade = 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 45 else 'F'

        return {'score': score, 'grade': grade, 'breakdown': breakdown}

    def _generate_strategic_recommendations(self, bottlenecks, concern_mixing,
                                            circular_deps, god_modules, coupling_score) -> list[dict]:
        """Generate prioritized strategic recommendations."""
        recs = []
        priority = 1

        # Critical bottlenecks first
        critical_bottlenecks = [b for b in bottlenecks if b['severity'] in ('CRITICAL', 'HIGH')]
        if critical_bottlenecks:
            for b in critical_bottlenecks[:3]:
                recs.append({
                    'priority': priority,
                    'category': 'Bottleneck Resolution',
                    'target': b['file'],
                    'action': b['recommendation'],
                    'impact': f"Reduces risk for {b['fan_in']} dependent modules",
                    'effort': 'MEDIUM' if b['function_count'] < 10 else 'HIGH',
                })
                priority += 1

        # Circular dependencies
        for cd in circular_deps:
            recs.append({
                'priority': priority,
                'category': 'Circular Dependency',
                'target': ' → '.join(cd['files']),
                'action': cd['recommendation'],
                'impact': 'Removes tight coupling between modules',
                'effort': 'MEDIUM',
            })
            priority += 1

        # God modules
        for gm in god_modules[:2]:
            recs.append({
                'priority': priority,
                'category': 'Module Decomposition',
                'target': gm['file'],
                'action': gm['recommendation'],
                'impact': f"Reduces module from {gm['total_lines']} lines to manageable units",
                'effort': 'HIGH',
            })
            priority += 1

        # Concern mixing
        for cm in concern_mixing[:2]:
            recs.append({
                'priority': priority,
                'category': 'Concern Separation',
                'target': cm['file'],
                'action': cm['recommendation'],
                'impact': f"Separates {cm['concern_count']} mixed concerns for better testability",
                'effort': 'MEDIUM',
            })
            priority += 1

        return recs

    def _build_narrative_summary(self, arch_pattern, score, bottlenecks,
                                  concern_mixing, god_modules, recommendations) -> str:
        """Build a narrative summary of architectural health."""
        parts = []

        pattern = arch_pattern.get('detected_pattern', 'Unknown')
        parts.append(f"## Architecture Assessment\n")
        parts.append(f"**Detected Pattern:** {pattern} (confidence: {arch_pattern.get('confidence', 0):.0%})")
        parts.append(f"**Architecture Score:** {score['score']}/100 (Grade: {score['grade']})\n")

        if score['score'] >= 90:
            parts.append("The codebase has strong architectural health. Maintain current patterns.")
        elif score['score'] >= 75:
            parts.append("Architecture is generally sound with room for targeted improvements.")
        elif score['score'] >= 60:
            parts.append("Several architectural concerns need attention to prevent technical debt accumulation.")
        else:
            parts.append("**Warning:** Significant architectural issues detected. Prioritize refactoring.")

        if bottlenecks:
            parts.append(f"\n**Bottlenecks:** {len(bottlenecks)} module(s) identified as structural bottlenecks.")
            for b in bottlenecks[:2]:
                parts.append(f"  - {b['file']}: {', '.join(b['reasons'])}")

        if god_modules:
            parts.append(f"\n**God Modules:** {len(god_modules)} module(s) have too many responsibilities.")

        if concern_mixing:
            parts.append(f"\n**Mixed Concerns:** {len(concern_mixing)} module(s) mix multiple responsibility areas.")

        if recommendations:
            parts.append(f"\n**Top Priority:** {recommendations[0]['category']} — {recommendations[0]['action']}")

        return '\n'.join(parts)


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DevDoc Architecture Reasoner')
    parser.add_argument('project_path', help='Path to project root')
    parser.add_argument('--analysis', '-a', required=True, help='Path to analysis.json')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--config', '-c', help='Path to devdoc.config.json')
    args = parser.parse_args()

    config = {}
    if args.config:
        try:
            with open(args.config) as f:
                config = json.load(f)
        except:
            pass

    with open(args.analysis, 'r') as f:
        analysis = json.load(f)

    reasoner = ArchitectureReasoner(args.project_path, config)
    results = reasoner.analyze(analysis)

    output = json.dumps(results, indent=2, default=str)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Architecture analysis saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
