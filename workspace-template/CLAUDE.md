# DevDoc Intelligence Platform — Workspace Configuration

> This workspace is configured for continuous codebase governance using DevDoc and WithAI.
> Template by DevDoc Intelligence Platform v1.0

## Installed Abilities

This workspace has 3 DevDoc abilities available:

1. **codebase-analyzer** — Deep AST analysis, security scanning, AI governance, architecture reasoning
2. **doc-generator** — Mermaid diagrams, health dashboards, API references
3. **review-reporter** — Scored report cards, risk assessment, regression detection

## Quick Commands

### Full Analysis Pipeline
```bash
# Step 1: Core analysis
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/analyze.py . --output .devdoc/latest/analysis.json

# Step 2: Security scan
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/security_scanner.py . --output .devdoc/latest/security.json

# Step 3: AI governance
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/ai_governance.py . --analysis .devdoc/latest/analysis.json --output .devdoc/latest/governance.json

# Step 4: Architecture reasoning
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/architecture_reasoner.py . --analysis .devdoc/latest/analysis.json --output .devdoc/latest/architecture.json

# Step 5: Generate docs
python3 ~/.withai/abilities/devdoc/doc-generator/scripts/generate_docs.py --analysis .devdoc/latest/analysis.json --security .devdoc/latest/security.json --governance .devdoc/latest/governance.json --architecture .devdoc/latest/architecture.json --output DOCUMENTATION.md

# Step 6: Generate review report
python3 ~/.withai/abilities/devdoc/review-reporter/scripts/generate_report.py --analysis .devdoc/latest/analysis.json --security .devdoc/latest/security.json --governance .devdoc/latest/governance.json --architecture .devdoc/latest/architecture.json --output REVIEW-REPORT.md
```

## Continuous Tracking

Save snapshots after each analysis for trend detection:
```bash
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/snapshot_manager.py save .devdoc/latest/analysis.json --project-dir . --label "v1.0"
python3 ~/.withai/abilities/devdoc/codebase-analyzer/scripts/snapshot_manager.py trend --project-dir .
```

## Documentation Standards

1. **Accuracy First**: Only document what exists in the code. Never fabricate features.
2. **Actionable Setup**: Installation steps must be copy-paste ready.
3. **Architecture Clarity**: Include directory tree and explain each major module.
4. **Code Examples**: Use real snippets from the actual codebase.
5. **Consistent Formatting**: GitHub-flavored markdown. Tables for structured data.

## Tone & Style

- Write for developers who are new to the project but experienced in the stack
- Be concise but thorough — no filler paragraphs
- Include "why" alongside "what" for architecture decisions

## WithAI Integration

- Use the WYSIWYG markdown editor for visual editing of generated docs
- Export final versions to PDF using the generate-pdf-from-md skill
- Mermaid diagrams render inline in the WYSIWYG editor
- This CLAUDE.md template optimizes Claude for DevDoc workflows

## Permissions

- File read access: enabled (needed to analyze code)
- File write access: enabled (needed to create docs and snapshots)
- Code execution: enabled (needed to run analysis scripts)
- Web access: disabled (analysis should be from code, not web)
