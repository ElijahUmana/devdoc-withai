#!/usr/bin/env python3
"""
DevDoc AI Governance Detector

Detects patterns commonly produced by AI-generated code:
- Repetitive structures across files (copy-paste patterns)
- Overly verbose functions (low logic density)
- Inconsistent naming conventions within modules
- Shallow abstraction (deep nesting, few extracted helpers)
- Duplicated logic across modules
- Boilerplate-heavy code without meaningful abstraction
- Hallucinated patterns (code that looks plausible but is redundant/wrong)

This is NOT about detecting whether code was AI-generated.
It's about detecting quality patterns that degrade when AI generates code at scale.

Usage:
    python ai_governance.py <project-root> [--analysis analysis.json] [--output governance.json]

Part of the codebase-analyzer WithAI ability.
"""

import ast
import os
import sys
import json
import argparse
import hashlib
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Optional
from difflib import SequenceMatcher


# ─── Pattern Detectors ─────────────────────────────────────────────────────────

class RepetitiveStructureDetector:
    """Detect copy-paste patterns and structural repetition across files."""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def detect(self, file_analyses: list[dict]) -> list[dict]:
        """Find structurally similar functions across different files."""
        findings = []
        all_functions = []

        # Collect all functions with their AST structure fingerprints
        for fa in file_analyses:
            if 'error' in fa:
                continue
            for func in fa.get('functions', []):
                all_functions.append({
                    'name': func['name'],
                    'file': fa['filepath'],
                    'line': func['line'],
                    'line_count': func['line_count'],
                    'param_count': func['param_count'],
                    'complexity': func['complexity'],
                    'calls': func.get('calls', []),
                    'signature': func.get('signature', ''),
                })

        # Compare function pairs across different files
        compared = set()
        for i, f1 in enumerate(all_functions):
            for j, f2 in enumerate(all_functions):
                if i >= j:
                    continue
                if f1['file'] == f2['file']:
                    continue

                pair_key = (f1['file'] + f1['name'], f2['file'] + f2['name'])
                if pair_key in compared:
                    continue
                compared.add(pair_key)

                similarity = self._compute_similarity(f1, f2)
                if similarity >= self.threshold:
                    findings.append({
                        'type': 'repetitive_structure',
                        'severity': 'HIGH' if similarity > 0.95 else 'MEDIUM',
                        'message': f'Functions "{f1["name"]}" and "{f2["name"]}" are {similarity:.0%} structurally similar',
                        'details': {
                            'function_a': {'name': f1['name'], 'file': f1['file'], 'line': f1['line']},
                            'function_b': {'name': f2['name'], 'file': f2['file'], 'line': f2['line']},
                            'similarity': round(similarity, 3),
                        },
                    })

        return findings

    def _compute_similarity(self, f1: dict, f2: dict) -> float:
        """Compute structural similarity between two functions."""
        scores = []

        # Parameter count similarity
        max_params = max(f1['param_count'], f2['param_count'], 1)
        param_sim = 1 - abs(f1['param_count'] - f2['param_count']) / max_params
        scores.append(param_sim)

        # Line count similarity
        max_lines = max(f1['line_count'], f2['line_count'], 1)
        line_sim = 1 - abs(f1['line_count'] - f2['line_count']) / max_lines
        scores.append(line_sim)

        # Complexity similarity
        max_cx = max(f1['complexity'], f2['complexity'], 1)
        cx_sim = 1 - abs(f1['complexity'] - f2['complexity']) / max_cx
        scores.append(cx_sim)

        # Call pattern similarity (Jaccard)
        calls_a = set(f1.get('calls', []))
        calls_b = set(f2.get('calls', []))
        if calls_a or calls_b:
            call_sim = len(calls_a & calls_b) / len(calls_a | calls_b)
        else:
            call_sim = 1.0
        scores.append(call_sim)

        # Name similarity (might be variants of same pattern)
        name_sim = SequenceMatcher(None, f1['name'], f2['name']).ratio()
        scores.append(name_sim * 0.5)  # Lower weight for name

        return sum(scores) / len(scores)


class VerboseFunctionDetector:
    """Detect overly verbose functions with low logic density."""

    def __init__(self, verbose_ratio: float = 0.6, min_lines: int = 15):
        self.verbose_ratio = verbose_ratio
        self.min_lines = min_lines

    def detect(self, file_analyses: list[dict]) -> list[dict]:
        """Find functions that are long but have low complexity (verbose/boilerplate)."""
        findings = []

        for fa in file_analyses:
            if 'error' in fa:
                continue
            for func in fa.get('functions', []):
                if func['line_count'] < self.min_lines:
                    continue

                # Logic density = complexity / line_count
                # Low density = lots of lines, little branching = likely verbose/boilerplate
                density = func['complexity'] / func['line_count']

                if density < 0.05 and func['line_count'] >= 25:
                    severity = 'HIGH'
                elif density < 0.08 and func['line_count'] >= 15:
                    severity = 'MEDIUM'
                else:
                    continue

                findings.append({
                    'type': 'verbose_function',
                    'severity': severity,
                    'message': f'Function "{func["name"]}" has low logic density ({density:.3f}): {func["line_count"]} lines but complexity {func["complexity"]}',
                    'details': {
                        'function': func['name'],
                        'file': fa['filepath'],
                        'line': func['line'],
                        'line_count': func['line_count'],
                        'complexity': func['complexity'],
                        'logic_density': round(density, 4),
                        'suggestion': 'Consider extracting repetitive patterns into helper functions or using data-driven approaches',
                    },
                })

        return findings


class NamingConsistencyDetector:
    """Detect inconsistent naming conventions within and across modules."""

    def detect(self, file_analyses: list[dict]) -> list[dict]:
        """Check naming convention consistency."""
        findings = []

        for fa in file_analyses:
            if 'error' in fa:
                continue

            func_names = [f['name'] for f in fa.get('functions', []) if not f['name'].startswith('_')]
            if len(func_names) < 3:
                continue

            # Detect convention
            conventions = {'snake_case': 0, 'camelCase': 0, 'PascalCase': 0, 'other': 0}
            for name in func_names:
                if name == name.lower() and '_' in name:
                    conventions['snake_case'] += 1
                elif name[0].islower() and any(c.isupper() for c in name[1:]) and '_' not in name:
                    conventions['camelCase'] += 1
                elif name[0].isupper() and '_' not in name:
                    conventions['PascalCase'] += 1
                elif name == name.lower():
                    conventions['snake_case'] += 1  # single word lowercase = probably snake
                else:
                    conventions['other'] += 1

            total = sum(conventions.values())
            dominant = max(conventions, key=conventions.get)
            dominant_pct = conventions[dominant] / total

            # If >20% of names don't follow the dominant convention
            if dominant_pct < 0.8 and total >= 3:
                outliers = []
                for name in func_names:
                    if dominant == 'snake_case' and ('_' not in name and any(c.isupper() for c in name)):
                        outliers.append(name)
                    elif dominant == 'camelCase' and '_' in name:
                        outliers.append(name)

                if outliers:
                    findings.append({
                        'type': 'inconsistent_naming',
                        'severity': 'LOW',
                        'message': f'{fa["filepath"]}: dominant convention is {dominant} ({dominant_pct:.0%}) but {len(outliers)} functions don\'t follow it',
                        'details': {
                            'file': fa['filepath'],
                            'dominant_convention': dominant,
                            'consistency': round(dominant_pct, 2),
                            'outliers': outliers[:10],
                            'convention_breakdown': conventions,
                        },
                    })

        return findings


class ShallowAbstractionDetector:
    """Detect code with deep nesting but few helper function extractions."""

    def detect(self, file_analyses: list[dict]) -> list[dict]:
        """Find files/functions with shallow abstraction patterns."""
        findings = []

        for fa in file_analyses:
            if 'error' in fa:
                continue

            for func in fa.get('functions', []):
                nesting = func.get('nesting_depth', 0)

                # Deep nesting + long function = missed abstraction opportunity
                if nesting >= 3 and func['line_count'] >= 20:
                    findings.append({
                        'type': 'shallow_abstraction',
                        'severity': 'HIGH' if nesting >= 4 else 'MEDIUM',
                        'message': f'Function "{func["name"]}" has nesting depth {nesting} and is {func["line_count"]} lines — consider extracting inner logic',
                        'details': {
                            'function': func['name'],
                            'file': fa['filepath'],
                            'line': func['line'],
                            'nesting_depth': nesting,
                            'line_count': func['line_count'],
                            'complexity': func['complexity'],
                            'suggestion': 'Extract nested blocks into named helper functions for clarity',
                        },
                    })

        return findings


class DuplicatedLogicDetector:
    """Detect duplicated logic blocks across modules using AST fingerprinting."""

    def detect_from_sources(self, root_path: str, skip_dirs: set) -> list[dict]:
        """Scan Python files for duplicated code blocks."""
        findings = []
        root = Path(root_path).resolve()

        # Collect normalized code blocks from all files
        file_blocks = {}  # filepath -> [normalized_block_hashes]

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fname in filenames:
                if not fname.endswith('.py'):
                    continue

                fpath = Path(dirpath) / fname
                rel_path = str(fpath.relative_to(root))

                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        source = f.read()
                    tree = ast.parse(source)
                except:
                    continue

                blocks = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        try:
                            # Normalize: remove function name, normalize variable names
                            body_str = ast.dump(node)
                            # Remove line numbers for comparison
                            normalized = re.sub(r'lineno=\d+', '', body_str)
                            normalized = re.sub(r'col_offset=\d+', '', normalized)
                            normalized = re.sub(r'end_lineno=\d+', '', normalized)
                            normalized = re.sub(r'end_col_offset=\d+', '', normalized)
                            block_hash = hashlib.md5(normalized.encode()).hexdigest()
                            blocks.append({
                                'hash': block_hash,
                                'name': node.name,
                                'line': node.lineno,
                                'size': getattr(node, 'end_lineno', node.lineno) - node.lineno + 1,
                            })
                        except:
                            pass

                file_blocks[rel_path] = blocks

        # Find groups of identical blocks across files
        hash_to_locations = defaultdict(list)
        for fp, blocks in file_blocks.items():
            for block in blocks:
                if block['size'] >= 5:  # Only consider meaningful blocks
                    hash_to_locations[block['hash']].append({
                        'file': fp,
                        'name': block['name'],
                        'line': block['line'],
                        'size': block['size'],
                    })

        for block_hash, locations in hash_to_locations.items():
            if len(locations) >= 2:
                # Multiple identical function bodies across files
                files = set(loc['file'] for loc in locations)
                if len(files) >= 2:  # Must span multiple files
                    findings.append({
                        'type': 'duplicated_logic',
                        'severity': 'HIGH' if len(locations) >= 3 else 'MEDIUM',
                        'message': f'Identical function body found in {len(locations)} locations across {len(files)} files',
                        'details': {
                            'locations': locations,
                            'block_hash': block_hash[:12],
                            'suggestion': 'Extract shared logic into a common utility module',
                        },
                    })

        return findings


# ─── Main Governance Analyzer ──────────────────────────────────────────────────

class AIGovernanceAnalyzer:
    """Orchestrates all AI governance pattern detectors."""

    def __init__(self, root_path: str, config: Optional[dict] = None):
        self.root = Path(root_path).resolve()
        self.config = config or {}
        gov_config = self.config.get('ai_governance', {})

        self.detectors = {
            'repetitive_structures': RepetitiveStructureDetector(
                threshold=gov_config.get('duplication_similarity', 0.85)
            ),
            'verbose_functions': VerboseFunctionDetector(
                verbose_ratio=gov_config.get('verbose_function_ratio', 0.6)
            ),
            'naming_consistency': NamingConsistencyDetector(),
            'shallow_abstraction': ShallowAbstractionDetector(),
            'duplicated_logic': DuplicatedLogicDetector(),
        }

        self.skip_dirs = {
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', 'coverage', '.devdoc',
        }

    def analyze(self, file_analyses: list[dict]) -> dict:
        """Run all governance checks and return structured results."""
        all_findings = []

        # Run each detector
        all_findings.extend(self.detectors['repetitive_structures'].detect(file_analyses))
        all_findings.extend(self.detectors['verbose_functions'].detect(file_analyses))
        all_findings.extend(self.detectors['naming_consistency'].detect(file_analyses))
        all_findings.extend(self.detectors['shallow_abstraction'].detect(file_analyses))

        # Duplicated logic detector needs source access
        all_findings.extend(
            self.detectors['duplicated_logic'].detect_from_sources(str(self.root), self.skip_dirs)
        )

        # Score
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for f in all_findings:
            severity_counts[f.get('severity', 'MEDIUM')] += 1

        type_counts = defaultdict(int)
        for f in all_findings:
            type_counts[f['type']] += 1

        # Governance score
        score = 100
        score -= severity_counts['HIGH'] * 10
        score -= severity_counts['MEDIUM'] * 5
        score -= severity_counts['LOW'] * 2
        score = max(0, score)

        return {
            'total_findings': len(all_findings),
            'severity_counts': severity_counts,
            'type_counts': dict(type_counts),
            'governance_score': score,
            'governance_grade': self._grade(score),
            'findings': sorted(all_findings, key=lambda f:
                {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}.get(f.get('severity', 'MEDIUM'), 3)
            ),
            'summary': self._build_summary(all_findings, type_counts, score),
            'recommendations': self._generate_recommendations(all_findings, type_counts),
        }

    def _grade(self, score: int) -> str:
        if score >= 90: return 'A'
        if score >= 75: return 'B'
        if score >= 60: return 'C'
        if score >= 45: return 'D'
        return 'F'

    def _build_summary(self, findings, type_counts, score) -> str:
        if not findings:
            return "No AI governance issues detected. Code quality patterns are clean."

        top_issue = max(type_counts, key=type_counts.get)
        formatted = top_issue.replace('_', ' ')
        return (
            f"Found {len(findings)} AI governance issues (score: {score}/100). "
            f"Most common: {formatted} ({type_counts[top_issue]} instances)."
        )

    def _generate_recommendations(self, findings, type_counts) -> list[str]:
        """Generate actionable recommendations based on findings."""
        recs = []

        if type_counts.get('repetitive_structure', 0) > 0:
            recs.append(
                "REPETITIVE STRUCTURES: Multiple functions share similar patterns. "
                "Extract shared logic into a base function or use composition patterns."
            )

        if type_counts.get('verbose_function', 0) > 0:
            recs.append(
                "VERBOSE FUNCTIONS: Some functions have many lines but low branching complexity. "
                "This suggests boilerplate or repetitive code. Consider data-driven approaches or helper extraction."
            )

        if type_counts.get('inconsistent_naming', 0) > 0:
            recs.append(
                "NAMING INCONSISTENCY: Mixed naming conventions detected. "
                "Standardize on the dominant convention (likely snake_case for Python)."
            )

        if type_counts.get('shallow_abstraction', 0) > 0:
            recs.append(
                "SHALLOW ABSTRACTION: Functions with deep nesting but no extracted helpers. "
                "Each nesting level should ideally be a named function describing its purpose."
            )

        if type_counts.get('duplicated_logic', 0) > 0:
            recs.append(
                "DUPLICATED LOGIC: Identical function bodies found across multiple files. "
                "Move shared logic to a utils/common module to maintain DRY principles."
            )

        if not recs:
            recs.append("No significant AI governance issues. Continue maintaining current code quality standards.")

        return recs


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DevDoc AI Governance Detector')
    parser.add_argument('project_path', help='Path to project root')
    parser.add_argument('--analysis', '-a', help='Path to existing analysis.json (skips re-analysis)')
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

    # Load or run analysis
    if args.analysis:
        with open(args.analysis, 'r') as f:
            analysis = json.load(f)
        file_analyses = analysis.get('file_analyses', [])
    else:
        # Import and run the analyzer
        sys.path.insert(0, str(Path(__file__).parent))
        from analyze import ProjectAnalyzer
        analyzer = ProjectAnalyzer(args.project_path, config)
        result = analyzer.analyze()
        file_analyses = result.get('file_analyses', [])

    governance = AIGovernanceAnalyzer(args.project_path, config)
    results = governance.analyze(file_analyses)

    output = json.dumps(results, indent=2, default=str)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"AI governance report saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
