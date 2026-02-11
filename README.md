# DevDoc Intelligence Platform

> Continuous codebase governance through AI-powered analysis, comprehensive documentation generation, and visual health reporting — built on WithAI's abilities system.

## What This Is

**DevDoc** is a suite of 3 WithAI abilities that transform how developers understand and document their codebases. It goes beyond simple documentation — it's a continuous intelligence system that tracks code health, detects regressions, and provides actionable insights.

Built for the WithAI Software Engineering Internship application by **Elijah Umana**.

## The 3 Abilities

| Ability | Purpose | Output |
|---------|---------|--------|
| **codebase-analyzer** | Deep AST analysis, security scanning, AI governance detection, architecture reasoning | JSON metrics |
| **doc-generator** | Mermaid diagrams, health dashboards, API references, trend charts | Markdown docs |
| **review-reporter** | Scored report cards, risk matrices, regression detection, action items | Markdown reports |

## Why This Use Case

1. **Real problem**: Every developer team struggles with documentation debt and code quality visibility
2. **Full WithAI integration**: Uses abilities system, WYSIWYG editor, workspace setup, settings management
3. **Deep product understanding**: Built using WithAI's most advanced feature — custom abilities with scripts
4. **Practically useful**: Something I'd genuinely use on every project

## Project Structure

```
devdoc-withai-project/
├── abilities/
│   ├── codebase-analyzer/        # AST analysis, security, governance, architecture
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── analyze.py            # Core AST parser (888 lines)
│   │       ├── security_scanner.py   # 70+ vulnerability patterns
│   │       ├── ai_governance.py      # AI code pattern detection
│   │       ├── architecture_reasoner.py  # Strategic insights
│   │       ├── git_tracker.py        # Commit velocity, churn
│   │       └── snapshot_manager.py   # Trend tracking
│   ├── doc-generator/            # Documentation generation
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── generate_docs.py      # Mermaid diagrams, health dashboard
│   └── review-reporter/          # Governance reports
│       ├── SKILL.md
│       └── scripts/
│           └── generate_report.py    # Scored report cards
├── automation/
│   ├── devdoc-action.yml         # GitHub Action for CI/CD
│   └── devdoc-hook.sh            # Git hook for continuous tracking
├── demo/
│   ├── sample-project/           # Flask app to demonstrate analysis
│   └── outputs/                  # Generated docs and reports
├── settings/
│   └── recommended-permissions.json
├── workspace-template/
│   └── CLAUDE.md                 # Template for user workspaces
├── .claude/
│   └── CLAUDE.md                 # Project-specific Claude instructions
└── product-feedback.md           # Honest WithAI product feedback
```

## Installation

### 1. Install WithAI Extension
```
ext install withai-research.withai-extension
```

### 2. Install DevDoc Abilities
```bash
# Create the ability directories
mkdir -p ~/.withai/abilities/devdoc/codebase-analyzer/scripts
mkdir -p ~/.withai/abilities/devdoc/doc-generator/scripts
mkdir -p ~/.withai/abilities/devdoc/review-reporter/scripts

# Copy ability files
cp abilities/codebase-analyzer/SKILL.md ~/.withai/abilities/devdoc/codebase-analyzer/
cp abilities/codebase-analyzer/scripts/*.py ~/.withai/abilities/devdoc/codebase-analyzer/scripts/
cp abilities/doc-generator/SKILL.md ~/.withai/abilities/devdoc/doc-generator/
cp abilities/doc-generator/scripts/*.py ~/.withai/abilities/devdoc/doc-generator/scripts/
cp abilities/review-reporter/SKILL.md ~/.withai/abilities/devdoc/review-reporter/
cp abilities/review-reporter/scripts/*.py ~/.withai/abilities/devdoc/review-reporter/scripts/

# Register all abilities
node ~/.claude/skills/ability-creator/scripts/register.js codebase-analyzer
node ~/.claude/skills/ability-creator/scripts/register.js doc-generator
node ~/.claude/skills/ability-creator/scripts/register.js review-reporter
```

### 3. Run the Analysis Pipeline
```bash
# Analyze any project
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/analyze.py /path/to/project --output analysis.json

# Generate documentation
python3 ~/.withai/abilities/devdoc/doc-generator/scripts/generate_docs.py --analysis analysis.json --output DOCUMENTATION.md

# Generate review report
python3 ~/.withai/abilities/devdoc/review-reporter/scripts/generate_report.py --analysis analysis.json --output REVIEW-REPORT.md
```

## Demo Output

The `demo/outputs/` folder contains real generated outputs from analyzing the sample Flask project:

- `DOCUMENTATION.md` — 268 lines with Mermaid dependency graph, health dashboard, API reference
- `REVIEW-REPORT.md` — 91 lines with scorecard, risk assessment, action items
- `analysis.json` — 41KB of structured metrics (29 functions, complexity scores, dependency graph)

## WithAI Features Used

| Feature | How DevDoc Uses It |
|---------|-------------------|
| Abilities System | 3 custom abilities with SKILL.md + Python scripts |
| WYSIWYG Editor | Visual editing of generated Markdown |
| Workspace Setup | Auto-creates .claude/CLAUDE.md |
| Settings Panel | Permission configuration |
| Ability Registration | Validated and enabled via register.js |

## Technical Details

- **Language**: Python 3.10+ (stdlib only, no pip dependencies)
- **Total code**: 4,338 lines across 8 scripts
- **Analysis**: Real AST parsing, not regex hacks
- **Output**: Markdown optimized for WithAI's WYSIWYG editor

## Author

Built by **Elijah Umana** for the WithAI Software Engineering Internship application.
