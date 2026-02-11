# CLAUDE.md — DevDoc Intelligence Platform

This is the development workspace for the DevDoc project. DevDoc provides 3 WithAI abilities for continuous codebase governance:

1. **codebase-analyzer** — AST analysis, security scanning, AI governance detection, architecture reasoning
2. **doc-generator** — Mermaid diagrams, health dashboards, API references
3. **review-reporter** — Scored report cards, risk matrices, regression detection

## Project Structure

- `abilities/` — Source code for all 3 abilities (SKILL.md + scripts/)
- `automation/` — GitHub Action + git hook for CI/CD integration
- `demo/` — Sample project + generated outputs showing the full pipeline
- `settings/` — Recommended WithAI permission configuration
- `workspace-template/` — Template CLAUDE.md for user workspaces

## Development Commands

```bash
# Run full pipeline on the sample project
python3 abilities/codebase-analyzer/scripts/analyze.py demo/sample-project --output demo/outputs/analysis.json
python3 abilities/codebase-analyzer/scripts/security_scanner.py demo/sample-project --output demo/outputs/security.json
python3 abilities/codebase-analyzer/scripts/ai_governance.py demo/sample-project --analysis demo/outputs/analysis.json --output demo/outputs/governance.json
python3 abilities/codebase-analyzer/scripts/architecture_reasoner.py demo/sample-project --analysis demo/outputs/analysis.json --output demo/outputs/architecture.json
python3 abilities/doc-generator/scripts/generate_docs.py --analysis demo/outputs/analysis.json --security demo/outputs/security.json --governance demo/outputs/governance.json --architecture demo/outputs/architecture.json --output demo/outputs/DOCUMENTATION.md
python3 abilities/review-reporter/scripts/generate_report.py --analysis demo/outputs/analysis.json --security demo/outputs/security.json --governance demo/outputs/governance.json --architecture demo/outputs/architecture.json --output demo/outputs/REVIEW-REPORT.md
```

## Notes
- All scripts use Python 3.10+ and only stdlib (no pip installs needed)
- Abilities are installed to `~/.withai/abilities/devdoc/` and registered via `node ~/.claude/skills/ability-creator/scripts/register.js`
- Generated markdown is optimized for WithAI's WYSIWYG editor

