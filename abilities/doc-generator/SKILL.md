---
name: doc-generator
description: Generate comprehensive documentation with Mermaid architecture diagrams, health dashboards, and API references from codebase analysis data. Use when asked to document a project, create architecture docs, or visualize dependencies. Requires analysis JSON from the codebase-analyzer ability.
license: MIT
compatibility: Requires Python 3.10+
metadata:
  author: Elijah Umana
  version: "1.0"
  category: development
allowed-tools: Bash(python3:*) Read Write
---

<skill-directive>

# Documentation Generator

## Overview
Generates intelligent, comprehensive documentation from DevDoc analysis data. Produces Markdown with Mermaid architecture diagrams, health dashboards, scored metrics, API references, and trend visualizations. Output is optimized for WithAI's WYSIWYG editor.

## When to Use
- User asks to "document this project" or "generate docs"
- User wants architecture diagrams or dependency visualizations
- User asks for an API reference
- User wants a health dashboard view
- After running the **codebase-analyzer** ability
- User asks to "visualize the architecture"

## Prerequisites
Run the **codebase-analyzer** ability first to produce the analysis JSON files.

## Usage

```bash
python3 ~/.withai/abilities/devdoc/doc-generator/scripts/generate_docs.py \
  --analysis analysis.json \
  --security security.json \
  --governance governance.json \
  --architecture architecture.json \
  --git git.json \
  --trends trends.json \
  --output DOCUMENTATION.md
```

All flags except `--analysis` are optional. The more data provided, the richer the output.

## What It Generates

1. **Project Overview** — languages, frameworks, file counts, line counts
2. **Health Dashboard** — color-coded scores for architecture, security, AI governance, documentation coverage
3. **Architecture Section** — detected pattern, directory tree, strategic recommendations
4. **Mermaid Dependency Diagram** — auto-generated flowchart showing module relationships with fan-in highlighting
5. **Module Breakdown** — per-file metrics table
6. **API Reference** — auto-generated from extracted function signatures and class definitions
7. **Security Scan Results** — findings with severity and code snippets
8. **AI Governance Report** — code quality patterns with recommendations
9. **Trend Visualization** — Mermaid xychart showing complexity over time (if snapshots exist)
10. **Setup Guide** — extracted from README and config files
11. **Dependencies Table** — parsed from requirements.txt / package.json

## After Generation
Open the generated .md file — it will automatically open in WithAI's WYSIWYG editor for visual editing and polishing. The Mermaid diagrams render inline. You can export to PDF using WithAI's generate-pdf-from-md skill.

</skill-directive>
