#!/usr/bin/env python3
"""
DevDoc Codebase Analyzer — Core AST Analysis Engine

Deep static analysis using Python's ast module:
- Function/class extraction with full signatures
- Cyclomatic complexity calculation
- Import chain mapping + dependency graph
- Dead code detection (unused functions/imports)
- Type hint coverage analysis
- Docstring coverage analysis
- File-level and project-level metrics

Usage:
    python analyze.py <project-root> [--output analysis.json] [--config devdoc.config.json]

Part of the codebase-analyzer WithAI ability.
"""

import ast
import os
import sys
import json
import argparse
import textwrap
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Optional


# ─── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', '.next', 'coverage', '.pytest_cache', '.mypy_cache',
    '.tox', '.idea', '.vscode', '.vs', 'vendor', '.cache', '.devdoc',
    '.claude', '.withai', 'target', 'bin', 'obj',
}

LANGUAGE_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.jsx': 'React JSX', '.tsx': 'React TSX',
    '.java': 'Java', '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby',
    '.php': 'PHP', '.cs': 'C#', '.cpp': 'C++', '.c': 'C',
    '.swift': 'Swift', '.kt': 'Kotlin', '.dart': 'Dart',
}

TECH_INDICATORS = {
    'package.json': 'Node.js', 'requirements.txt': 'Python (pip)',
    'Pipfile': 'Python (Pipenv)', 'pyproject.toml': 'Python',
    'Cargo.toml': 'Rust', 'go.mod': 'Go', 'Gemfile': 'Ruby',
    'composer.json': 'PHP', 'pom.xml': 'Java (Maven)',
    'build.gradle': 'Gradle', 'Dockerfile': 'Docker',
    'docker-compose.yml': 'Docker Compose', 'tsconfig.json': 'TypeScript',
    'Makefile': 'Make', '.env': 'dotenv',
}

FRAMEWORK_PACKAGES = {
    'react': 'React', 'vue': 'Vue.js', '@angular/core': 'Angular',
    'express': 'Express.js', 'fastify': 'Fastify', 'next': 'Next.js',
    'nuxt': 'Nuxt.js', 'django': 'Django', 'flask': 'Flask',
    'fastapi': 'FastAPI', 'prisma': 'Prisma', 'tailwindcss': 'Tailwind CSS',
    'nestjs': 'NestJS', '@nestjs/core': 'NestJS',
    'svelte': 'Svelte', 'remix': 'Remix',
}

ENTRY_POINT_NAMES = {
    'main.py', 'app.py', 'server.py', 'index.py', 'manage.py', 'wsgi.py',
    'index.js', 'index.ts', 'main.js', 'main.ts', 'server.js', 'server.ts',
    'app.js', 'app.ts', 'main.go', 'main.rs', 'Main.java', 'Program.cs',
}


# ─── AST Analysis ──────────────────────────────────────────────────────────────

class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity of a function/method."""

    def __init__(self):
        self.complexity = 1  # Base complexity

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds a branch
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)


def calculate_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity for an AST node."""
    visitor = ComplexityVisitor()
    visitor.visit(node)
    return visitor.complexity


def extract_function_signature(node) -> str:
    """Extract full function signature including type hints."""
    args = node.args
    parts = []

    # Positional args
    defaults_offset = len(args.args) - len(args.defaults)
    for i, arg in enumerate(args.args):
        name = arg.arg
        annotation = ""
        if arg.annotation:
            try:
                annotation = f": {ast.unparse(arg.annotation)}"
            except:
                annotation = ": ..."

        default = ""
        default_idx = i - defaults_offset
        if default_idx >= 0 and default_idx < len(args.defaults):
            try:
                default = f" = {ast.unparse(args.defaults[default_idx])}"
            except:
                default = " = ..."

        parts.append(f"{name}{annotation}{default}")

    # *args
    if args.vararg:
        ann = ""
        if args.vararg.annotation:
            try:
                ann = f": {ast.unparse(args.vararg.annotation)}"
            except:
                ann = ""
        parts.append(f"*{args.vararg.arg}{ann}")

    # **kwargs
    if args.kwarg:
        ann = ""
        if args.kwarg.annotation:
            try:
                ann = f": {ast.unparse(args.kwarg.annotation)}"
            except:
                ann = ""
        parts.append(f"**{args.kwarg.arg}{ann}")

    sig = f"({', '.join(parts)})"

    # Return annotation
    if node.returns:
        try:
            sig += f" -> {ast.unparse(node.returns)}"
        except:
            sig += " -> ..."

    return sig


class PythonFileAnalyzer(ast.NodeVisitor):
    """Deep AST analysis of a single Python file."""

    def __init__(self, filepath: str, source: str):
        self.filepath = filepath
        self.source = source
        self.lines = source.split('\n')
        self.total_lines = len(self.lines)

        # Extracted data
        self.functions: list[dict] = []
        self.classes: list[dict] = []
        self.imports: list[dict] = []
        self.global_vars: list[dict] = []
        self.decorators_used: set = set()
        self.all_names_defined: set = set()
        self.all_names_used: set = set()

        # Metrics
        self.has_module_docstring = False
        self.type_hint_count = 0
        self.type_hint_possible = 0

    def analyze(self) -> dict:
        """Run full analysis and return structured result."""
        try:
            tree = ast.parse(self.source)
        except SyntaxError as e:
            return {
                'filepath': self.filepath,
                'error': f'SyntaxError: {e.msg} (line {e.lineno})',
                'total_lines': self.total_lines,
            }

        # Check module docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)):
            self.has_module_docstring = True

        self.visit(tree)
        self._collect_name_usage(tree)

        # Compute file-level metrics
        code_lines = sum(1 for l in self.lines if l.strip() and not l.strip().startswith('#'))
        comment_lines = sum(1 for l in self.lines if l.strip().startswith('#'))
        blank_lines = self.total_lines - code_lines - comment_lines

        # Identify potentially unused imports
        imported_names = set()
        for imp in self.imports:
            for name in imp.get('names', []):
                imported_names.add(name.split('.')[-1])  # Get the short name
        unused_imports = imported_names - self.all_names_used

        # Type hint coverage
        type_hint_coverage = (
            self.type_hint_count / self.type_hint_possible
            if self.type_hint_possible > 0 else None
        )

        avg_complexity = 0
        if self.functions:
            avg_complexity = sum(f['complexity'] for f in self.functions) / len(self.functions)

        return {
            'filepath': self.filepath,
            'total_lines': self.total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
            'has_module_docstring': self.has_module_docstring,
            'functions': self.functions,
            'classes': self.classes,
            'imports': self.imports,
            'global_variables': self.global_vars,
            'decorators_used': sorted(self.decorators_used),
            'unused_imports': sorted(unused_imports),
            'type_hint_coverage': round(type_hint_coverage, 2) if type_hint_coverage is not None else None,
            'avg_complexity': round(avg_complexity, 2),
            'max_complexity': max((f['complexity'] for f in self.functions), default=0),
            'function_count': len(self.functions),
            'class_count': len(self.classes),
        }

    def visit_FunctionDef(self, node):
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def _process_function(self, node, is_async=False):
        """Extract function metadata."""
        self.all_names_defined.add(node.name)

        # Signature
        signature = extract_function_signature(node)

        # Complexity
        complexity = calculate_complexity(node)

        # Docstring
        docstring = ast.get_docstring(node)
        has_docstring = docstring is not None

        # Line count
        end_lineno = getattr(node, 'end_lineno', node.lineno)
        line_count = end_lineno - node.lineno + 1

        # Type hints
        args = node.args
        total_params = len(args.args) + (1 if args.vararg else 0) + (1 if args.kwarg else 0)
        # Exclude 'self' and 'cls'
        non_self_params = [a for a in args.args if a.arg not in ('self', 'cls')]
        typed_params = sum(1 for a in non_self_params if a.annotation is not None)
        has_return_type = node.returns is not None

        self.type_hint_possible += len(non_self_params) + 1  # +1 for return
        self.type_hint_count += typed_params + (1 if has_return_type else 0)

        # Decorators
        decorator_names = []
        for dec in node.decorator_list:
            try:
                dec_name = ast.unparse(dec)
                decorator_names.append(dec_name)
                self.decorators_used.add(dec_name.split('(')[0])
            except:
                pass

        # Determine nesting depth
        nesting = self._measure_nesting_depth(node)

        # What does this function call?
        calls = self._extract_calls(node)

        func_info = {
            'name': node.name,
            'signature': f"{node.name}{signature}",
            'line': node.lineno,
            'end_line': end_lineno,
            'line_count': line_count,
            'complexity': complexity,
            'has_docstring': has_docstring,
            'docstring_summary': (docstring.split('\n')[0][:100] if docstring else None),
            'is_async': is_async,
            'is_method': any(a.arg == 'self' for a in args.args),
            'is_classmethod': 'classmethod' in decorator_names,
            'is_staticmethod': 'staticmethod' in decorator_names,
            'is_property': any('property' in d for d in decorator_names),
            'decorators': decorator_names,
            'param_count': len(non_self_params),
            'has_return_type': has_return_type,
            'typed_param_ratio': round(typed_params / len(non_self_params), 2) if non_self_params else 1.0,
            'nesting_depth': nesting,
            'calls': calls[:20],  # Top 20 calls
        }
        self.functions.append(func_info)

    def visit_ClassDef(self, node):
        self.all_names_defined.add(node.name)

        # Base classes
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except:
                bases.append('...')

        # Docstring
        docstring = ast.get_docstring(node)

        # Methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        # Class variables
        class_vars = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                class_vars.append(item.target.id)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_vars.append(target.id)

        end_lineno = getattr(node, 'end_lineno', node.lineno)

        class_info = {
            'name': node.name,
            'line': node.lineno,
            'end_line': end_lineno,
            'line_count': end_lineno - node.lineno + 1,
            'bases': bases,
            'has_docstring': docstring is not None,
            'docstring_summary': (docstring.split('\n')[0][:100] if docstring else None),
            'method_count': len(methods),
            'methods': methods,
            'class_variables': class_vars,
            'decorators': [ast.unparse(d) for d in node.decorator_list] if node.decorator_list else [],
        }
        self.classes.append(class_info)
        self.generic_visit(node)

    def visit_Import(self, node):
        names = [alias.name for alias in node.names]
        self.imports.append({
            'type': 'import',
            'names': names,
            'line': node.lineno,
        })
        for alias in node.names:
            self.all_names_defined.add(alias.asname or alias.name.split('.')[0])

    def visit_ImportFrom(self, node):
        module = node.module or ''
        names = [alias.name for alias in node.names]
        self.imports.append({
            'type': 'from_import',
            'module': module,
            'names': names,
            'line': node.lineno,
        })
        for alias in node.names:
            self.all_names_defined.add(alias.asname or alias.name)

    def visit_Assign(self, node):
        """Track global variable assignments."""
        # Only top-level assignments
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.all_names_defined.add(target.id)
                # Only capture module-level globals (we check context in analyze())
                self.global_vars.append({
                    'name': target.id,
                    'line': node.lineno,
                })
        self.generic_visit(node)

    def _collect_name_usage(self, tree: ast.AST):
        """Collect all names used (referenced) in the module."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self.all_names_used.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Track attribute chains like 'os.path'
                try:
                    self.all_names_used.add(ast.unparse(node))
                except:
                    pass
                if isinstance(node.value, ast.Name):
                    self.all_names_used.add(node.value.id)

    def _measure_nesting_depth(self, node: ast.AST) -> int:
        """Measure maximum nesting depth within a function."""
        max_depth = 0

        def _walk(n, depth):
            nonlocal max_depth
            if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth += 1
                max_depth = max(max_depth, depth)
            for child in ast.iter_child_nodes(n):
                _walk(child, depth)

        _walk(node, 0)
        return max_depth

    def _extract_calls(self, node: ast.AST) -> list[str]:
        """Extract function/method calls within a node."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                try:
                    call_name = ast.unparse(child.func)
                    calls.append(call_name)
                except:
                    pass
        return calls


# ─── Project-Level Analysis ────────────────────────────────────────────────────

class ProjectAnalyzer:
    """Analyzes an entire project directory."""

    def __init__(self, root_path: str, config: Optional[dict] = None):
        self.root = Path(root_path).resolve()
        if not self.root.is_dir():
            raise ValueError(f"Not a valid directory: {self.root}")
        self.config = config or {}
        self.skip_dirs = DEFAULT_SKIP_DIRS

    def analyze(self) -> dict:
        """Run full project analysis."""
        file_analyses = []
        all_imports = defaultdict(set)  # module -> set of files importing it
        all_files = []
        language_stats = defaultdict(lambda: {'files': 0, 'lines': 0})
        tech_stack = {'languages': set(), 'frameworks': set(), 'tools': set()}
        entry_points = []

        # Walk the project
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in self.skip_dirs and not d.startswith('.')]

            for fname in filenames:
                fpath = Path(dirpath) / fname
                rel_path = str(fpath.relative_to(self.root))
                ext = fpath.suffix.lower()

                # Track all files
                if ext in LANGUAGE_MAP:
                    language_stats[LANGUAGE_MAP[ext]]['files'] += 1
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = sum(1 for _ in f)
                        language_stats[LANGUAGE_MAP[ext]]['lines'] += line_count
                    except:
                        line_count = 0
                    all_files.append({
                        'path': rel_path,
                        'language': LANGUAGE_MAP.get(ext, 'Unknown'),
                        'lines': line_count,
                    })

                # Detect tech stack
                if fname in TECH_INDICATORS:
                    tech_stack['tools'].add(TECH_INDICATORS[fname])

                # Entry points
                if fname in ENTRY_POINT_NAMES:
                    entry_points.append(rel_path)

                # Deep AST analysis for Python files
                if ext == '.py':
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                            source = f.read()
                        analyzer = PythonFileAnalyzer(rel_path, source)
                        result = analyzer.analyze()
                        file_analyses.append(result)

                        # Track cross-file imports
                        for imp in result.get('imports', []):
                            module = imp.get('module', '') or ', '.join(imp.get('names', []))
                            all_imports[module].add(rel_path)
                    except Exception as e:
                        file_analyses.append({
                            'filepath': rel_path,
                            'error': str(e),
                        })

        # Detect frameworks from package.json
        pkg_path = self.root / 'package.json'
        if pkg_path.exists():
            try:
                with open(pkg_path, 'r') as f:
                    pkg = json.load(f)
                all_deps = {}
                all_deps.update(pkg.get('dependencies', {}))
                all_deps.update(pkg.get('devDependencies', {}))
                for dep, fw in FRAMEWORK_PACKAGES.items():
                    if dep in all_deps:
                        tech_stack['frameworks'].add(fw)
            except:
                pass

        # Languages from stats
        for lang in language_stats:
            if language_stats[lang]['files'] >= 1:
                tech_stack['languages'].add(lang)

        # Read key config files
        config_contents = self._read_key_configs()

        # Extract dependencies
        dependencies = self._extract_dependencies()

        # Build dependency graph (which files import which modules)
        dep_graph = self._build_dependency_graph(file_analyses)

        # Build directory tree
        tree = self._build_tree()

        # Aggregate metrics
        all_functions = []
        all_classes = []
        total_code_lines = 0
        for fa in file_analyses:
            if 'error' not in fa:
                all_functions.extend(
                    [{**f, '_file': fa['filepath']} for f in fa.get('functions', [])]
                )
                all_classes.extend(
                    [{**c, '_file': fa['filepath']} for c in fa.get('classes', [])]
                )
                total_code_lines += fa.get('code_lines', 0)

        # Project-wide metrics
        project_metrics = self._compute_project_metrics(file_analyses, all_functions, all_classes)

        return {
            'project_name': self.root.name,
            'analyzed_at': datetime.now().isoformat(),
            'root_path': str(self.root),
            'directory_tree': tree,
            'tech_stack': {k: sorted(v) for k, v in tech_stack.items()},
            'language_stats': {k: dict(v) for k, v in language_stats.items()},
            'entry_points': entry_points,
            'config_contents': config_contents,
            'dependencies': dependencies,
            'file_analyses': file_analyses,
            'dependency_graph': dep_graph,
            'project_metrics': project_metrics,
            'all_files': all_files,
            'summary': {
                'total_files': len(all_files),
                'total_python_files': len(file_analyses),
                'total_lines': sum(f['lines'] for f in all_files),
                'total_code_lines': total_code_lines,
                'total_functions': len(all_functions),
                'total_classes': len(all_classes),
                'has_tests': any('test' in f['path'].lower() for f in all_files),
                'has_ci': any(
                    f['path'].startswith('.github/workflows') for f in all_files
                ),
            },
        }

    def _build_dependency_graph(self, file_analyses: list) -> dict:
        """Build a file-to-file dependency graph from imports."""
        # Map module names to file paths
        module_to_file = {}
        for fa in file_analyses:
            if 'error' in fa:
                continue
            fp = fa['filepath']
            # Convert file path to module name
            mod_name = fp.replace('/', '.').replace('\\', '.').replace('.py', '')
            module_to_file[mod_name] = fp
            # Also map the short name (last part)
            short_name = mod_name.split('.')[-1]
            module_to_file[short_name] = fp

        graph = defaultdict(list)  # file -> [files it depends on]
        reverse_graph = defaultdict(list)  # file -> [files that depend on it]

        for fa in file_analyses:
            if 'error' in fa:
                continue
            fp = fa['filepath']
            for imp in fa.get('imports', []):
                module = imp.get('module', '')
                names = imp.get('names', [])

                # Try to resolve import to a local file
                candidates = [module] + [module.split('.')[-1] if module else ''] + names
                for candidate in candidates:
                    if candidate in module_to_file:
                        target = module_to_file[candidate]
                        if target != fp:
                            graph[fp].append(target)
                            reverse_graph[target].append(fp)

        # Calculate fan-in / fan-out
        fan_metrics = {}
        all_fps = {fa['filepath'] for fa in file_analyses if 'error' not in fa}
        for fp in all_fps:
            fan_metrics[fp] = {
                'fan_out': len(set(graph.get(fp, []))),  # files this depends on
                'fan_in': len(set(reverse_graph.get(fp, []))),  # files depending on this
                'depends_on': sorted(set(graph.get(fp, []))),
                'depended_by': sorted(set(reverse_graph.get(fp, []))),
            }

        return {
            'edges': {k: sorted(set(v)) for k, v in graph.items()},
            'reverse_edges': {k: sorted(set(v)) for k, v in reverse_graph.items()},
            'fan_metrics': fan_metrics,
        }

    def _compute_project_metrics(self, file_analyses, all_functions, all_classes) -> dict:
        """Compute project-wide aggregate metrics."""
        if not all_functions:
            return {
                'avg_complexity': 0,
                'max_complexity': 0,
                'avg_function_length': 0,
                'max_function_length': 0,
                'docstring_coverage': 0,
                'type_hint_coverage': 0,
                'complexity_distribution': {},
                'hotspot_functions': [],
                'longest_functions': [],
            }

        complexities = [f['complexity'] for f in all_functions]
        lengths = [f['line_count'] for f in all_functions]

        # Complexity distribution
        complexity_dist = {'low (1-5)': 0, 'medium (6-10)': 0, 'high (11-15)': 0, 'critical (>15)': 0}
        for c in complexities:
            if c <= 5: complexity_dist['low (1-5)'] += 1
            elif c <= 10: complexity_dist['medium (6-10)'] += 1
            elif c <= 15: complexity_dist['high (11-15)'] += 1
            else: complexity_dist['critical (>15)'] += 1

        # Docstring coverage
        with_docstrings = sum(1 for f in all_functions if f['has_docstring'])
        docstring_coverage = with_docstrings / len(all_functions) if all_functions else 0

        # Type hint coverage across files
        type_coverages = [
            fa.get('type_hint_coverage')
            for fa in file_analyses
            if fa.get('type_hint_coverage') is not None
        ]
        avg_type_coverage = (
            sum(type_coverages) / len(type_coverages)
            if type_coverages else 0
        )

        # Top complexity hotspots
        hotspots = sorted(all_functions, key=lambda f: f['complexity'], reverse=True)[:10]
        hotspot_functions = [
            {
                'name': f['name'],
                'file': f['_file'],
                'complexity': f['complexity'],
                'line': f['line'],
                'line_count': f['line_count'],
            }
            for f in hotspots
        ]

        # Longest functions
        longest = sorted(all_functions, key=lambda f: f['line_count'], reverse=True)[:10]
        longest_functions = [
            {
                'name': f['name'],
                'file': f['_file'],
                'line_count': f['line_count'],
                'complexity': f['complexity'],
                'line': f['line'],
            }
            for f in longest
        ]

        return {
            'avg_complexity': round(sum(complexities) / len(complexities), 2),
            'max_complexity': max(complexities),
            'median_complexity': sorted(complexities)[len(complexities) // 2],
            'avg_function_length': round(sum(lengths) / len(lengths), 2),
            'max_function_length': max(lengths),
            'docstring_coverage': round(docstring_coverage, 2),
            'type_hint_coverage': round(avg_type_coverage, 2),
            'complexity_distribution': complexity_dist,
            'hotspot_functions': hotspot_functions,
            'longest_functions': longest_functions,
            'total_functions': len(all_functions),
            'total_classes': len(all_classes),
        }

    def _read_key_configs(self) -> dict:
        """Read contents of important config files."""
        key_files = [
            'README.md', 'package.json', 'requirements.txt', 'pyproject.toml',
            'Cargo.toml', 'go.mod', 'Gemfile', 'docker-compose.yml',
            'Dockerfile', 'Makefile', '.env.example', 'tsconfig.json',
        ]
        contents = {}
        for fname in key_files:
            fpath = self.root / fname
            if fpath.exists():
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read(5000)
                    if len(text) == 5000:
                        text += '\n... [truncated]'
                    contents[fname] = text
                except:
                    pass
        return contents

    def _extract_dependencies(self) -> dict:
        """Extract dependency lists from config files."""
        deps = {}
        # Python
        req = self.root / 'requirements.txt'
        if req.exists():
            try:
                with open(req) as f:
                    deps['python'] = [
                        l.strip() for l in f if l.strip() and not l.startswith('#')
                    ]
            except:
                pass

        # Node
        pkg = self.root / 'package.json'
        if pkg.exists():
            try:
                with open(pkg) as f:
                    data = json.load(f)
                if 'dependencies' in data:
                    deps['production'] = [f"{k}@{v}" for k, v in data['dependencies'].items()]
                if 'devDependencies' in data:
                    deps['development'] = [f"{k}@{v}" for k, v in data['devDependencies'].items()]
            except:
                pass
        return deps

    def _build_tree(self, max_depth: int = 5) -> str:
        """Build ASCII directory tree."""
        lines = [f"{self.root.name}/"]
        entries = []

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = sorted(d for d in dirnames if d not in self.skip_dirs and not d.startswith('.'))
            rel = os.path.relpath(dirpath, self.root)
            depth = 0 if rel == '.' else rel.count(os.sep) + 1
            if depth >= max_depth:
                dirnames.clear()
                continue

            indent = "│   " * depth
            dir_name = os.path.basename(dirpath)
            if rel != '.':
                entries.append((depth, dir_name + '/', True))

            for fname in sorted(filenames):
                if not fname.startswith('.'):
                    entries.append((depth + (0 if rel == '.' else 1), fname, False))

        # Simple tree rendering
        for i, (depth, name, is_dir) in enumerate(entries):
            prefix = "│   " * (depth - 1) if depth > 0 else ""
            connector = "├── " if i < len(entries) - 1 else "└── "
            lines.append(f"{prefix}{connector}{name}")

        return '\n'.join(lines[:100])  # Cap at 100 lines


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DevDoc: Deep codebase analysis with AST parsing, complexity metrics, and dependency graphs.',
    )
    parser.add_argument('project_path', help='Path to project root directory')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--config', '-c', help='Path to devdoc.config.json')

    args = parser.parse_args()

    # Load config if provided
    config = {}
    if args.config:
        try:
            with open(args.config) as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}", file=sys.stderr)

    try:
        analyzer = ProjectAnalyzer(args.project_path, config)
        result = analyzer.analyze()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(result, indent=2, default=str)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w') as f:
            f.write(output)
        print(f"Analysis saved to: {out_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
