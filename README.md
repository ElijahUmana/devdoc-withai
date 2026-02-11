# DevDoc — Codebase Intelligence Platform Built on WithAI

**A developer workflow improvement that turns any codebase into comprehensive, living documentation — using WithAI's abilities system, WYSIWYG markdown editor, workspace configuration, and PDF export.**

Built by **Elijah Umana** for the WithAI Software Engineering Internship.

---

## The Problem

Documentation is the most neglected part of software development. Developers don't write it because: it's tedious, it goes stale immediately, and existing tools generate superficial output (file lists and line counts). Meanwhile, new team members suffer during onboarding, code reviews miss architectural context, and technical debt accumulates invisibly.

## The Solution

**DevDoc** is a continuous codebase intelligence system implemented as **3 custom WithAI abilities**. It performs real AST-level analysis (not regex matching), generates rich documentation with Mermaid architecture diagrams, and produces scored governance report cards — all within the WithAI ecosystem.

The entire workflow runs inside VS Code through WithAI:

1. **Analyze** — Custom abilities parse Python codebases using AST, detect security vulnerabilities, identify AI-generated code patterns, and reason about architecture
2. **Document** — Generates comprehensive Markdown with dependency graphs, health dashboards, and API references
3. **Review** — Produces scored report cards with risk assessment and prioritized action items
4. **View** — Open generated `.md` files directly in WithAI's WYSIWYG editor for visual review and editing
5. **Export** — Convert to professional PDFs using WithAI's bundled `generate-pdf-from-md` skill

## Why This Use Case

- **It's a real workflow I'd actually use.** Every project I work on needs documentation. This makes it automatic.
- **It exercises every WithAI feature.** Not just the WYSIWYG editor — the abilities system, workspace setup, settings management, PDF export, and agent configuration.
- **It pushes beyond surface-level usage.** Building custom abilities with Python scripts and the agentskills.io specification goes deeper than most users would explore.
- **It creates a reusable tool.** Any developer can install these abilities and immediately use them on their own projects.

---

## How I Used WithAI

### 1. Workspace Setup

Ran `WithAI: Setup Workspace` from the command palette. This auto-created `.claude/CLAUDE.md` in the project root — the file that tells Claude Code how to behave in this workspace. I customized it with project-specific instructions for running the analysis pipeline.

### 2. Settings Configuration

Opened the WithAI Settings panel (gear icon) to configure Claude Code permissions:
- **Code Execution**: Enabled (high risk) — required to run the Python analysis scripts
- **File Operations**: Enabled (medium risk) — needed to read source files and write outputs
- **Web Access**: Disabled — all analysis is local, no external calls needed

Applied the recommended permission preset and fine-tuned for the DevDoc use case. The risk-level indicators helped me understand what each permission enables.

### 3. Agent Skills & System Prompts

Used the "AI Agent Configuration" feature to:
- Download the bundled `ability-creator` skill — this taught Claude Code how to create and register custom abilities
- Download the `generate-pdf-from-md` skill — for converting generated Markdown to professional PDFs
- Applied the "concise responses" system prompt preset for tighter output during development

### 4. Custom Ability Development

This is the core of the project. I created 3 custom abilities following the [agentskills.io](https://agentskills.io/specification) open specification:

**Creating ability drafts:**
```
WithAI: Create Ability Draft  →  codebase-analyzer
WithAI: Create Ability Draft  →  doc-generator
WithAI: Create Ability Draft  →  review-reporter
```

Each ability has a `SKILL.md` (instructions for Claude) and a `scripts/` directory (Python execution logic). The SKILL.md files use `<skill-directive>` tags and proper frontmatter as required by the spec.

**Registering abilities:**
```bash
node ~/.claude/skills/ability-creator/scripts/register.js codebase-analyzer
# → Validating codebase-analyzer... Validation passed.
# → Registered: codebase-analyzer. Claude can now use this ability.

node ~/.claude/skills/ability-creator/scripts/register.js doc-generator
node ~/.claude/skills/ability-creator/scripts/register.js review-reporter
```

After registration, all 3 abilities appear in `~/.claude/CLAUDE.md` under the WithAI Abilities section, so Claude Code knows when to invoke them.

**Syncing abilities:**
```
WithAI: Sync Abilities  →  Syncs ability state across the workspace
```

### 5. WYSIWYG Markdown Editor

Set `*.md` files to open with `withai.markdownEditor` as default. All generated documentation opens directly in the rich visual editor — headings, tables, code blocks, and formatted text render in real-time. This makes reviewing generated docs much faster than reading raw Markdown.

### 6. PDF Export

Used the bundled `generate-pdf-from-md` skill to convert generated reports:
```bash
python3 ~/.vscode/extensions/.../bundled-skills/generate-pdf-from-md/scripts/md_to_pdf.py \
  demo/outputs/DOCUMENTATION.md demo/outputs/DOCUMENTATION.pdf \
  --title "DevDoc Documentation"
```
Produces professionally formatted PDFs with cover pages, clean typography, and proper page breaks.

### 7. Webview Layout

Configured WithAI's webview placement settings:
- `withai.webviewPlacement.claudeCodePosition`: "right" — Claude Code panel on the right
- `withai.webviewPlacement.fileWebviewPosition`: "left" — file editors on the left
- `withai.webviewPlacement.autoCloseEnabled`: true — auto-close inactive file views

This gives a clean two-column layout: code/docs on the left, AI assistant on the right.

---

## Project Structure

```
devdoc-withai-project/
├── .claude/
│   └── CLAUDE.md                     # WithAI-generated workspace config (customized)
├── abilities/
│   ├── codebase-analyzer/            # Ability 1: Deep static analysis
│   │   ├── SKILL.md                  # agentskills.io ability definition
│   │   └── scripts/
│   │       ├── analyze.py            # Core AST parser (888 lines)
│   │       ├── security_scanner.py   # 70+ vulnerability patterns (398 lines)
│   │       ├── ai_governance.py      # AI code pattern detection (524 lines)
│   │       ├── architecture_reasoner.py  # Strategic insights (694 lines)
│   │       ├── git_tracker.py        # Commit velocity, churn (412 lines)
│   │       └── snapshot_manager.py   # Historical trend tracking (341 lines)
│   ├── doc-generator/                # Ability 2: Documentation generation
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── generate_docs.py      # Mermaid diagrams, dashboards (554 lines)
│   └── review-reporter/             # Ability 3: Governance reports
│       ├── SKILL.md
│       └── scripts/
│           └── generate_report.py    # Scored report cards (527 lines)
├── automation/
│   ├── devdoc-action.yml             # GitHub Action for CI/CD integration
│   └── devdoc-hook.sh                # Git pre-commit hook
├── demo/
│   ├── sample-project/               # Flask app used for demo analysis
│   │   ├── src/ (app.py, models.py, routes.py, utils.py)
│   │   └── tests/test_app.py
│   └── outputs/                      # Real generated outputs
│       ├── analysis.json             # 41KB structured analysis
│       ├── security.json             # Security findings
│       ├── governance.json           # AI governance assessment
│       ├── architecture.json         # Architectural insights
│       ├── DOCUMENTATION.md          # Generated docs (view in WYSIWYG!)
│       ├── DOCUMENTATION.pdf         # PDF via WithAI's bundled skill
│       ├── REVIEW-REPORT.md          # Scored report card
│       └── REVIEW-REPORT.pdf         # PDF via WithAI's bundled skill
├── settings/
│   └── recommended-permissions.json  # Claude Code permission config
├── workspace-template/
│   └── CLAUDE.md                     # Reusable CLAUDE.md template
├── devdoc.config.json                # Pipeline configuration
├── product-feedback.md               # Honest WithAI product feedback
└── README.md                         # This file
```

## What the Analysis Engine Does

This is **not** a line counter. It performs real compiler-level analysis:

| Module | What It Does | How |
|--------|-------------|-----|
| `analyze.py` | Function/class extraction, complexity scoring, dependency graphs, type hint coverage | Python `ast` module — walks the AST, computes cyclomatic complexity, resolves imports |
| `security_scanner.py` | Detects 70+ vulnerability patterns | Regex patterns + AST visitor for SQL injection, hardcoded secrets, eval(), subprocess, etc. |
| `ai_governance.py` | Identifies AI-generated code patterns | Detects excessive comments, generic naming, shallow abstractions, code duplication |
| `architecture_reasoner.py` | Architectural bottlenecks, god modules, circular deps | Graph analysis on import/dependency data, coupling scores |
| `git_tracker.py` | Commit velocity, file churn, hotspots | Parses `git log` output, computes change frequency and author distribution |
| `snapshot_manager.py` | Historical trends, regression detection | Saves/loads/diffs analysis snapshots over time |

Total: **4,338 lines of Python** using only the standard library (no pip dependencies).

## Installation (For Your Own Projects)

```bash
# 1. Install WithAI extension
# Search "WithAI" in VS Code Extensions, or:
# ext install withai-research.withai-extension

# 2. Clone this repo
git clone https://github.com/ElijahUmana/devdoc-withai.git

# 3. Install abilities
mkdir -p ~/.withai/abilities/devdoc/{codebase-analyzer,doc-generator,review-reporter}/scripts
cp abilities/codebase-analyzer/SKILL.md ~/.withai/abilities/devdoc/codebase-analyzer/
cp abilities/codebase-analyzer/scripts/*.py ~/.withai/abilities/devdoc/codebase-analyzer/scripts/
cp abilities/doc-generator/SKILL.md ~/.withai/abilities/devdoc/doc-generator/
cp abilities/doc-generator/scripts/*.py ~/.withai/abilities/devdoc/doc-generator/scripts/
cp abilities/review-reporter/SKILL.md ~/.withai/abilities/devdoc/review-reporter/
cp abilities/review-reporter/scripts/*.py ~/.withai/abilities/devdoc/review-reporter/scripts/

# 4. Register with Claude Code
node ~/.claude/skills/ability-creator/scripts/register.js codebase-analyzer
node ~/.claude/skills/ability-creator/scripts/register.js doc-generator
node ~/.claude/skills/ability-creator/scripts/register.js review-reporter

# 5. Setup workspace
# Run "WithAI: Setup Workspace" from command palette

# 6. Point at any Python project
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/analyze.py /your/project --output analysis.json
python3 ~/.withai/abilities/devdoc/doc-generator/scripts/generate_docs.py --analysis analysis.json --output DOCS.md
# Open DOCS.md → WithAI WYSIWYG editor renders it visually
```

## Author

**Elijah Umana** — WithAI Software Engineering Internship Application

GitHub: [ElijahUmana/devdoc-withai](https://github.com/ElijahUmana/devdoc-withai)
