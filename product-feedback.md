# WithAI Extension — Product Feedback

> Real feedback from building 3 custom abilities and exploring the extension.
> Extension version: 0.1.9 | macOS | Date: February 11, 2026

---

## What I Actually Built

I created **DevDoc**, a suite of 3 WithAI abilities for codebase governance:
- **codebase-analyzer**: AST analysis, security scanning, AI pattern detection
- **doc-generator**: Mermaid diagrams, health dashboards
- **review-reporter**: Scored report cards, risk assessment

Total: 4,338 lines of Python across 8 scripts. All registered and working.

---

## What Works Well

### 1. Abilities System Architecture
The separation of `SKILL.md` (instructions) + `scripts/` (execution) is clean. The registration flow via `node ~/.claude/skills/ability-creator/scripts/register.js` works smoothly — validation is instant, and updating `~/.claude/CLAUDE.md` automatically is the right design.

### 2. Organization-Based Namespacing  
Having abilities in `~/.withai/abilities/{org-name}/{ability-name}/` makes sense for team collaboration. My abilities went into `devdoc/` cleanly.

### 3. Settings File Association
Setting `*.md` to open with `withai.markdownEditor` in VS Code settings worked automatically — didn't have to configure anything manually.

### 4. Workspace Setup Automation
`withai.setupWorkspace` correctly created `.claude/CLAUDE.md` in my project. One command to bootstrap a project.

---

## What Felt Confusing or Broken

### 1. Abilities Discovery is Hidden
The abilities system is powerful but completely undiscoverable from the UI. I had to:
- Read the bundled ability-creator SKILL.md to understand how abilities work
- Manually find `~/.withai/abilities/` path structure
- Figure out the org-name/ability-name hierarchy by trial and error

**Fix**: Add an "Abilities" section to the Settings panel showing installed abilities and a "Create New" button.

### 2. Settings Panel Doesn't Show Much
I opened the Settings panel via the gear icon multiple times. It shows permission toggles, but:
- No indication of what's currently enabled
- No connection to my registered abilities
- No visibility into sync status or organization

**Fix**: Show ability count, last sync time, and current permission states.

### 3. `withai.abilities.setup` Is Unclear
I ran this command but nothing visibly happened. No prompt, no dialog, no notification. Looking at `~/.withai/config.json`, I see `"organization": null` and `"enabled": false`. 

**Fix**: This should open a dialog explaining what organization setup means and prompting for an org name.

### 4. No Way to Test Abilities from UI
I registered 3 abilities but there's no "Run ability" or "Test ability" button. The only way to verify they work is to ask Claude Code directly or run the scripts manually.

**Fix**: Add a "Test" action next to each registered ability in the UI.

---

## What I Would Change Immediately

### 1. Show Registered Abilities in Settings Panel
When I open Settings, I want to see:
```
Abilities (3 registered)
├── codebase-analyzer ✓
├── doc-generator ✓  
└── review-reporter ✓
```

### 2. First-Run Tutorial
After installation, walk new users through:
1. Here's the WYSIWYG editor (open a sample .md)
2. Here's the Settings panel (show permissions)
3. Here's abilities (create your first one)

### 3. Error Messages Should Be Actionable
When something fails (like an ability not registering), show the specific line in SKILL.md that's wrong with a "Go to line" link.

---

## Features I Would Add

### 1. Ability Marketplace
A gallery of community abilities users can install with one click. Would bootstrap new users and create ecosystem.

### 2. Ability Chaining
Let abilities call other abilities. My `doc-generator` should be able to automatically invoke `generate-pdf-from-md` as a final step.

### 3. Ability Usage Analytics
Show how often each ability is triggered, so creators can understand adoption.

---

## What Slowed Me Down

1. **Finding abilities documentation**: The only docs are in the bundled SKILL.md files. Had to dig into `~/.vscode/extensions/withai-research.withai-extension-0.1.9/out/bundled-skills/`.

2. **Understanding the path structure**: `~/.withai/abilities/{org}/{ability}/` wasn't obvious. First tried creating abilities in the project directory.

3. **No end-to-end example**: Would've helped to see "here's a complete ability from empty directory to registered and working" with screenshots.

4. **WYSIWYG editor limitations**: Couldn't find a way to insert tables visually. Had to write markdown syntax manually.

---

## Summary

WithAI's core idea is right: AI workspaces need more than just a chat panel. The abilities system is the differentiator — it's genuinely powerful once you understand it. The gap is discoverability. I spent significant time figuring out how abilities work, where files go, and how to verify registration. Making that journey smoother would dramatically improve the product.

The WYSIWYG editor and Settings panel are solid table-stakes features. The abilities system is the moat — invest in making it visible and accessible.
