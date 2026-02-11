#!/usr/bin/env python3
"""
DevDoc Security Scanner

Detects security-sensitive patterns in Python codebases:
- Hardcoded secrets (passwords, API keys, tokens)
- SQL injection vulnerabilities (string formatting in queries)
- Unvalidated input (request data used without sanitization)
- Unsafe deserialization (pickle, yaml.load)
- Path traversal risks (user input in file paths)
- Insecure crypto/hashing
- Debug/development leftovers in production code

Usage:
    python security_scanner.py <project-root> [--output security.json]
    
    # Or import and use programmatically:
    from security_scanner import SecurityScanner
    scanner = SecurityScanner(root_path)
    results = scanner.scan(file_analyses)

Part of the codebase-analyzer WithAI ability.
"""

import ast
import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Optional


# ─── Pattern Definitions ──────────────────────────────────────────────────────

SECRET_PATTERNS = [
    # Variable assignment patterns
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']', 'Hardcoded password'),
    (r'(?i)(api_?key|apikey)\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded API key'),
    (r'(?i)(secret|secret_?key)\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded secret'),
    (r'(?i)(token|auth_?token|access_?token)\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded token'),
    (r'(?i)(aws_secret|aws_access_key)\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded AWS credential'),
    # Inline secrets
    (r'-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----', 'Private key in source'),
    (r'(?i)bearer\s+[a-zA-Z0-9\-_.]{20,}', 'Hardcoded bearer token'),
    # Connection strings with credentials
    (r'(?i)(mysql|postgres|mongodb)://[^:]+:[^@]+@', 'Database URL with credentials'),
]

SQL_INJECTION_PATTERNS = [
    (r'\.execute\s*\(\s*f["\']', 'f-string in SQL execute()'),
    (r'\.execute\s*\(\s*["\'].*%s', 'String formatting in SQL execute()'),
    (r'\.execute\s*\(\s*.*\.format\(', '.format() in SQL execute()'),
    (r'\.execute\s*\(\s*.*\+\s*', 'String concatenation in SQL execute()'),
    (r'cursor\.execute\s*\(\s*f["\']', 'f-string in cursor.execute()'),
]

UNSAFE_DESERIALIZE_PATTERNS = [
    (r'pickle\.loads?\s*\(', 'pickle.load() — arbitrary code execution risk'),
    (r'yaml\.load\s*\([^)]*(?!Loader)', 'yaml.load() without safe Loader'),
    (r'yaml\.unsafe_load\s*\(', 'yaml.unsafe_load() — arbitrary code execution'),
    (r'marshal\.loads?\s*\(', 'marshal.load() — arbitrary code execution risk'),
    (r'shelve\.open\s*\(', 'shelve.open() — uses pickle internally'),
    (r'jsonpickle\.decode\s*\(', 'jsonpickle.decode() — arbitrary code execution'),
]

PATH_TRAVERSAL_PATTERNS = [
    (r'open\s*\(\s*.*request\.(form|args|data|json)', 'User input in file open()'),
    (r'os\.path\.join\s*\(\s*.*request\.(form|args|data|json)', 'User input in path join'),
    (r'Path\s*\(\s*.*request\.(form|args|data|json)', 'User input in Path()'),
    (r'send_file\s*\(\s*.*request\.(form|args|data|json)', 'User input in send_file()'),
]

INSECURE_CRYPTO_PATTERNS = [
    (r'hashlib\.(md5|sha1)\s*\(', 'Weak hash algorithm (MD5/SHA1)'),
    (r'from\s+Crypto\.Cipher\s+import\s+DES', 'Weak cipher (DES)'),
    (r'random\.(random|randint|choice|seed)\s*\(', 'Non-cryptographic random for potential security use'),
]

DEBUG_LEFTOVER_PATTERNS = [
    (r'(?i)# ?TODO\s*:?\s*.*secur', 'Security-related TODO'),
    (r'(?i)# ?FIXME\s*:?\s*.*secur', 'Security-related FIXME'),
    (r'(?i)# ?HACK\s*:', 'HACK comment in code'),
    (r'app\.run\s*\(.*debug\s*=\s*True', 'Debug mode enabled in production'),
    (r'FLASK_DEBUG\s*=\s*["\']?1', 'Flask debug mode enabled'),
    (r'verify\s*=\s*False', 'SSL verification disabled'),
    (r'print\s*\(.*password|print\s*\(.*secret|print\s*\(.*token', 'Sensitive data in print()'),
]

INPUT_VALIDATION_PATTERNS = [
    (r'request\.(form|args|data|json)\[', 'Direct request data access without validation'),
    (r'eval\s*\(\s*.*request', 'eval() with user input'),
    (r'exec\s*\(\s*.*request', 'exec() with user input'),
    (r'os\.system\s*\(\s*.*request', 'os.system() with user input — command injection'),
    (r'subprocess\.\w+\s*\(\s*.*request', 'subprocess with user input — command injection'),
]

SEVERITY_MAP = {
    'Hardcoded password': 'HIGH',
    'Hardcoded API key': 'HIGH',
    'Hardcoded secret': 'HIGH',
    'Hardcoded token': 'HIGH',
    'Hardcoded AWS credential': 'CRITICAL',
    'Private key in source': 'CRITICAL',
    'Hardcoded bearer token': 'HIGH',
    'Database URL with credentials': 'HIGH',
    'f-string in SQL execute()': 'CRITICAL',
    'String formatting in SQL execute()': 'CRITICAL',
    '.format() in SQL execute()': 'CRITICAL',
    'String concatenation in SQL execute()': 'HIGH',
    'pickle.load() — arbitrary code execution risk': 'HIGH',
    'yaml.load() without safe Loader': 'MEDIUM',
    'yaml.unsafe_load() — arbitrary code execution': 'HIGH',
    'marshal.load() — arbitrary code execution risk': 'HIGH',
    'User input in file open()': 'HIGH',
    'User input in path join': 'MEDIUM',
    'User input in Path()': 'MEDIUM',
    'User input in send_file()': 'HIGH',
    'Weak hash algorithm (MD5/SHA1)': 'LOW',
    'Weak cipher (DES)': 'MEDIUM',
    'Non-cryptographic random for potential security use': 'LOW',
    'Debug mode enabled in production': 'MEDIUM',
    'Flask debug mode enabled': 'MEDIUM',
    'SSL verification disabled': 'HIGH',
    'Sensitive data in print()': 'MEDIUM',
    'Direct request data access without validation': 'LOW',
    'eval() with user input': 'CRITICAL',
    'exec() with user input': 'CRITICAL',
    'os.system() with user input — command injection': 'CRITICAL',
    'subprocess with user input — command injection': 'CRITICAL',
}


# ─── AST-Based Security Checks ────────────────────────────────────────────────

class SecurityASTVisitor(ast.NodeVisitor):
    """AST-level security analysis for deeper pattern detection."""

    def __init__(self, filepath: str, source_lines: list[str]):
        self.filepath = filepath
        self.source_lines = source_lines
        self.findings: list[dict] = []

    def visit_Call(self, node):
        """Check function calls for security issues."""
        try:
            func_name = ast.unparse(node.func)
        except:
            self.generic_visit(node)
            return

        # eval/exec with non-literal args
        if func_name in ('eval', 'exec', '__import__'):
            if node.args and not isinstance(node.args[0], ast.Constant):
                self.findings.append({
                    'type': 'dangerous_function',
                    'description': f'{func_name}() called with dynamic argument',
                    'severity': 'CRITICAL',
                    'line': node.lineno,
                    'code': self._get_line(node.lineno),
                })

        # subprocess.call/run with shell=True
        if 'subprocess' in func_name:
            for kw in node.keywords:
                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append({
                        'type': 'shell_injection',
                        'description': f'{func_name}() with shell=True',
                        'severity': 'HIGH',
                        'line': node.lineno,
                        'code': self._get_line(node.lineno),
                    })

        # os.system
        if func_name == 'os.system':
            self.findings.append({
                'type': 'command_injection',
                'description': 'os.system() — prefer subprocess with shell=False',
                'severity': 'MEDIUM',
                'line': node.lineno,
                'code': self._get_line(node.lineno),
            })

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Check for hardcoded sensitive values in assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                name_lower = target.id.lower()
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    val = node.value.value
                    # Skip empty, placeholder, and env-fetched values
                    if len(val) > 3 and val not in ('', 'None', 'null', 'dev-secret-key'):
                        sensitive_names = ('password', 'secret', 'api_key', 'apikey',
                                          'token', 'private_key', 'auth')
                        if any(s in name_lower for s in sensitive_names):
                            self.findings.append({
                                'type': 'hardcoded_secret',
                                'description': f'Potential hardcoded secret in variable "{target.id}"',
                                'severity': 'HIGH',
                                'line': node.lineno,
                                'code': self._get_line(node.lineno),
                            })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Check function-level security patterns."""
        # Functions with 'password', 'auth', 'secret' in name but no validation
        name_lower = node.name.lower()
        if any(s in name_lower for s in ('password', 'auth', 'login', 'token')):
            # Check if function validates input length/format
            has_validation = False
            for child in ast.walk(node):
                if isinstance(child, ast.Compare):
                    has_validation = True
                    break
                if isinstance(child, ast.Call):
                    try:
                        if 'validate' in ast.unparse(child.func).lower():
                            has_validation = True
                            break
                    except:
                        pass
            if not has_validation:
                self.findings.append({
                    'type': 'missing_validation',
                    'description': f'Security-sensitive function "{node.name}" may lack input validation',
                    'severity': 'LOW',
                    'line': node.lineno,
                    'code': self._get_line(node.lineno),
                })
        self.generic_visit(node)

    def _get_line(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()[:120]
        return ""


# ─── Scanner ───────────────────────────────────────────────────────────────────

class SecurityScanner:
    """Full security scan combining regex patterns + AST analysis."""

    def __init__(self, root_path: str, config: Optional[dict] = None):
        self.root = Path(root_path).resolve()
        self.config = config or {}
        self.skip_dirs = {
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', 'coverage', '.devdoc',
        }

    def scan(self, file_analyses: Optional[list] = None) -> dict:
        """Run security scan across the project."""
        findings = []
        files_scanned = 0

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in self.skip_dirs]

            for fname in filenames:
                if not fname.endswith('.py'):
                    continue

                fpath = Path(dirpath) / fname
                rel_path = str(fpath.relative_to(self.root))
                files_scanned += 1

                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        source = f.read()
                    lines = source.split('\n')
                except:
                    continue

                # Regex-based scanning
                for pattern_group, patterns in [
                    ('secrets', SECRET_PATTERNS),
                    ('sql_injection', SQL_INJECTION_PATTERNS),
                    ('unsafe_deserialization', UNSAFE_DESERIALIZE_PATTERNS),
                    ('path_traversal', PATH_TRAVERSAL_PATTERNS),
                    ('insecure_crypto', INSECURE_CRYPTO_PATTERNS),
                    ('debug_leftovers', DEBUG_LEFTOVER_PATTERNS),
                    ('input_validation', INPUT_VALIDATION_PATTERNS),
                ]:
                    for regex, description in patterns:
                        for i, line in enumerate(lines, 1):
                            if re.search(regex, line):
                                # Skip comments and docstrings (basic filter)
                                stripped = line.strip()
                                if stripped.startswith('#'):
                                    continue
                                findings.append({
                                    'file': rel_path,
                                    'line': i,
                                    'category': pattern_group,
                                    'description': description,
                                    'severity': SEVERITY_MAP.get(description, 'MEDIUM'),
                                    'code': stripped[:120],
                                })

                # AST-based scanning
                try:
                    visitor = SecurityASTVisitor(rel_path, lines)
                    tree = ast.parse(source)
                    visitor.visit(tree)
                    for finding in visitor.findings:
                        finding['file'] = rel_path
                        finding['category'] = finding.get('type', 'ast_check')
                        findings.append(finding)
                except SyntaxError:
                    pass

        # Deduplicate findings (same file + line + description)
        seen = set()
        unique_findings = []
        for f in findings:
            key = (f['file'], f['line'], f['description'])
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        # Score
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for f in unique_findings:
            severity_counts[f.get('severity', 'MEDIUM')] += 1

        # Security score: start at 100, deduct per finding
        score = 100
        score -= severity_counts['CRITICAL'] * 20
        score -= severity_counts['HIGH'] * 10
        score -= severity_counts['MEDIUM'] * 5
        score -= severity_counts['LOW'] * 2
        score = max(0, score)

        return {
            'files_scanned': files_scanned,
            'total_findings': len(unique_findings),
            'severity_counts': severity_counts,
            'security_score': score,
            'security_grade': self._score_to_grade(score),
            'findings': sorted(unique_findings, key=lambda f:
                {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}.get(f.get('severity', 'MEDIUM'), 4)
            ),
            'summary': self._build_summary(unique_findings, severity_counts),
        }

    def _score_to_grade(self, score: int) -> str:
        if score >= 90: return 'A'
        if score >= 75: return 'B'
        if score >= 60: return 'C'
        if score >= 45: return 'D'
        return 'F'

    def _build_summary(self, findings, severity_counts) -> str:
        if not findings:
            return "No security issues detected. Clean scan."

        parts = []
        if severity_counts['CRITICAL']:
            parts.append(f"{severity_counts['CRITICAL']} CRITICAL")
        if severity_counts['HIGH']:
            parts.append(f"{severity_counts['HIGH']} HIGH")
        if severity_counts['MEDIUM']:
            parts.append(f"{severity_counts['MEDIUM']} MEDIUM")
        if severity_counts['LOW']:
            parts.append(f"{severity_counts['LOW']} LOW")

        categories = set(f['category'] for f in findings)
        return f"Found {len(findings)} issues ({', '.join(parts)}) across categories: {', '.join(sorted(categories))}"


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DevDoc Security Scanner')
    parser.add_argument('project_path', help='Path to project root')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    args = parser.parse_args()

    scanner = SecurityScanner(args.project_path)
    results = scanner.scan()

    output = json.dumps(results, indent=2, default=str)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Security scan saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
