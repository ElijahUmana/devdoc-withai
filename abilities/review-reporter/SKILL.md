---
name: review-reporter
description: Generate scored code review report cards with risk assessment, regression detection, and prioritized action items. Use when asked for a code review, health report, or quality assessment. Requires analysis JSON from the codebase-analyzer ability.
license: MIT
compatibility: Requires Python 3.10+
metadata:
  author: Elijah Umana
  version: "1.0"
  category: development
allowed-tools: Bash(python3:*) Read Write
---

<skill-directive>

# Review Reporter

## Overview
Generates scored governance report cards that combine all analysis dimensions into an actionable review. Includes executive summaries, risk assessment matrices, regression detection, code hotspot analysis, and prioritized action items. Output is optimized for WithAI's WYSIWYG editor.

## When to Use
- User asks for a "code review" or "review report"
- User wants a "quality assessment" or "health report"
- User asks "what should we fix first?" or "what's the risk?"
- User wants regression detection (before vs after comparison)
- After running the **codebase-analyzer** ability
- User wants to share a report with stakeholders

## Prerequisites
Run the **codebase-analyzer** ability first to produce the analysis JSON files.

## Usage

```bash
python3 ~/.withai/abilities/devdoc/review-reporter/scripts/generate_report.py \
  --analysis analysis.json \
  --security security.json \
  --governance governance.json \
  --architecture architecture.json \
  --diff diff.json \
  --output REVIEW-REPORT.md
```

All flags except `--analysis` are optional. Include `--diff` for regression detection.

## What It Generates

1. **Executive Summary** — overall health score with narrative assessment
2. **Scorecard** — visual health bars for each dimension (complexity, architecture, documentation, testing, security, AI governance) with weighted scoring
3. **Risk Assessment Matrix** — severity-ordered risk table with impact analysis
4. **Regression Check** — before/after metric comparison with regression alerts (requires diff.json from snapshot_manager)
5. **Code Hotspots** — highest complexity and longest functions
6. **Prioritized Action Items** — numbered list of improvements ordered by impact
7. **Detailed Findings** — expandable list of all issues across all dimensions

## Scoring System
- **Complexity** (20%): Based on average cyclomatic complexity
- **Architecture** (20%): Bottlenecks, coupling, circular deps, god modules
- **Documentation** (15%): Docstring coverage ratio
- **Testing** (15%): Test file presence and coverage
- **Security** (15%): Security vulnerabilities detected
- **AI Governance** (15%): Code quality pattern issues

Grade boundaries: A (90+), B (75+), C (60+), D (45+), F (<45)

## After Generation
Open the generated .md file in WithAI's WYSIWYG editor. Export to PDF for stakeholder distribution. Use regression reports in PR reviews for quality gatekeeping.

</skill-directive>
