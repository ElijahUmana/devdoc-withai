---
name: codebase-analyzer
description: Deep static analysis of codebases using AST parsing. Run when asked to analyze a project, check code health, scan for security issues, detect AI-generated code patterns, or track codebase trends over time. Produces structured JSON with complexity metrics, dependency graphs, security findings, and architectural insights.
license: MIT
compatibility: Requires Python 3.10+
metadata:
  author: Elijah Umana
  version: "1.0"
  category: development
allowed-tools: Bash(python3:*) Read Write
---

<skill-directive>

# Codebase Analyzer

## Overview
Deep static analysis engine that provides continuous intelligence about codebase health. Uses Python AST parsing for function/class extraction, cyclomatic complexity calculation, dependency graph construction, security scanning, AI code governance, and architectural reasoning.

This is NOT a simple line counter. It performs real compiler-level analysis.

## When to Use
- User asks to "analyze this project" or "check code health"
- User wants to understand a codebase structure
- User asks about code complexity, dependencies, or architecture
- User wants security scanning or vulnerability detection
- User asks about AI-generated code quality patterns
- User wants trend tracking or regression detection
- User asks "what's the health of this codebase?"

## Analysis Pipeline

Run these scripts IN ORDER from `~/.withai/abilities/devdoc/codebase-analyzer/scripts/`:

### Step 1: Core Analysis (always run)
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/analyze.py <project-root> --output analysis.json
```
Produces: Functions, classes, complexity, imports, dependency graph, type hint coverage, docstring coverage.

### Step 2: Security Scan
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/security_scanner.py <project-root> --output security.json
```
Detects: Hardcoded secrets, SQL injection, unsafe deserialization, path traversal, debug leftovers.

### Step 3: AI Governance Check
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/ai_governance.py <project-root> --analysis analysis.json --output governance.json
```
Detects: Repetitive structures, verbose functions, inconsistent naming, shallow abstraction, duplicated logic.

### Step 4: Architecture Reasoning
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/architecture_reasoner.py <project-root> --analysis analysis.json --output architecture.json
```
Produces: Bottleneck detection, concern separation analysis, circular dependencies, god modules, coupling scores, strategic recommendations.

### Step 5 (Optional): Git Trend Tracking
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/git_tracker.py <project-root> --output git.json
```
Requires git repository. Produces: Commit velocity, file churn, hotspots, author stats.

### Step 6 (Optional): Save Snapshot for Trends
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/snapshot_manager.py save analysis.json --project-dir <project-root> --label "initial"
```

### Step 7 (Optional): Compare with Previous
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/snapshot_manager.py diff --project-dir <project-root>
```

## Output Format
All scripts produce JSON. Key fields from analysis.json:
- `project_metrics.avg_complexity` — average cyclomatic complexity
- `project_metrics.docstring_coverage` — ratio of documented functions
- `project_metrics.hotspot_functions` — highest complexity functions
- `dependency_graph.fan_metrics` — fan-in/fan-out per file
- `file_analyses[].functions[]` — full function signatures, complexity, type hints

## After Analysis
Tell the user the key findings conversationally. If they want a full report, suggest using the **doc-generator** or **review-reporter** abilities.

</skill-directive>
