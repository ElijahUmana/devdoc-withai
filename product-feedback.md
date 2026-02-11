# WithAI Product Feedback

> Extension v0.1.9 | macOS | February 2026

---

## What Works Well

**The abilities system is the standout feature.** The SKILL.md + scripts architecture, the agentskills.io spec, and the create → register → publish flow are well-designed. Registration automatically injects ability descriptions into `~/.claude/CLAUDE.md` so Claude knows when to invoke them — that's elegant. I built 3 abilities with Python scripts and the whole process felt intentional and well-structured.

**WYSIWYG editor is immediately useful.** Setting `*.md` to default to `withai.markdownEditor` eliminated the constant switching between raw Markdown and preview. Tables, headings, and code blocks render cleanly. This is the feature that makes WithAI feel like a real workspace upgrade rather than just another extension.

**Workspace setup is frictionless.** One command to bootstrap `.claude/CLAUDE.md` with sensible defaults. Smart default behavior.

---

## What I'd Change Immediately

### 1. Surface abilities in the UI
The abilities system is the most powerful feature but has zero UI presence. It lives entirely in the command palette and CLI. Add an "Abilities" section to the Settings panel — show installed abilities, their registration status, and a "Create New" button. Right now, a user has to stumble onto it or read extension source code to discover it exists.

### 2. Pre-check dependencies for bundled skills
The `generate-pdf-from-md` skill crashes with `ModuleNotFoundError: No module named 'reportlab'` on first run. Before executing, check if the dependency is available and prompt: "This skill requires reportlab. Install it?" One line of pre-validation would save every new user from debugging an import error.

### 3. Show what permissions are actually active
The Settings panel shows permission toggles with risk levels, but after toggling, there's no confirmation of current state. When I reopen the panel, I can't tell what's enabled. Show a clear on/off indicator per permission group.

### 4. WYSIWYG table creation
The editor renders tables well, but there's no way to *insert* a new table from the toolbar. Users have to drop into raw Markdown syntax. A simple "Insert Table" grid picker (like Google Docs) would complete the WYSIWYG experience.

---

## Features I'd Add

1. **Ability chaining** — Let abilities declare dependencies on other abilities. My doc-generator's output is Markdown that should flow into `generate-pdf-from-md` automatically instead of requiring a separate manual step.

2. **Ability marketplace** — A curated gallery of community abilities installable with one click. This would bootstrap new users with useful abilities on day one and create an ecosystem.

3. **Status bar presence** — A small indicator showing `WithAI: 3 abilities synced` would make the extension feel alive. Currently after setup it's invisible unless you open the command palette.

4. **Live editing indicator** — When Claude Code writes to a `.md` file while it's open in the WYSIWYG editor, show a cursor with a "Claude" label so the user can watch the AI write in real-time.

---

## What Slowed Me Down

- **Abilities documentation lives only in bundled SKILL.md files.** I had to find them inside `~/.vscode/extensions/`. A docs page or even a README section in the marketplace listing would help.
- **No end-to-end ability tutorial.** The spec is documented, but a complete walkthrough — "empty directory to registered and working in 5 minutes" — would cut onboarding time significantly.

---

## Summary

WithAI's core bet — that AI workspaces need structure beyond a chat panel — is right. The abilities system is genuinely differentiated from anything else in the AI coding tool market. The main gap is discoverability: the most powerful feature is the hardest to find. Closing that gap through UI surfacing and onboarding would change how people perceive and use the product.
