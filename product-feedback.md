# WithAI Extension — Product Feedback

> From building 3 custom abilities and using every feature over several hours.
> Extension v0.1.9 | VS Code on macOS | February 2026

---

## What Felt Confusing or Broken

### 1. The abilities system is the best feature but nearly invisible

The abilities architecture — SKILL.md + scripts + register/publish — is genuinely powerful and differentiating. But I found it almost by accident. The extension marketplace listing barely mentions it. The Settings panel doesn't reference it. The welcome flow doesn't introduce it.

I had to:
- Dig into `~/.vscode/extensions/withai-research.withai-extension-0.1.9/out/bundled-skills/` to find the `ability-creator` SKILL.md
- Read that file end-to-end to understand the `~/.withai/abilities/{org}/{ability}/` path structure
- Figure out by trial and error that you need an org-level directory before the ability directory

A new user would likely use the WYSIWYG editor, think "nice markdown editor," and never discover that abilities exist. That's a huge missed opportunity.

### 2. `withai.abilities.setup` does nothing visible

I ran "WithAI: Setup Abilities (Join Organization)" from the command palette. Nothing happened. No dialog, no notification, no error. Looking at `~/.withai/config.json` afterward, `organization` is `null` and `enabled` is `false`. I still don't know what this command is supposed to do versus what it actually did.

### 3. Settings panel shows toggles but not their current state

When I open the Settings panel via the gear icon, I see permission groups with risk levels (Code Execution: high, Web Access: low, etc.). But there's no clear indication of what's currently enabled vs disabled for my workspace. I toggled things on and off but wasn't confident the changes stuck.

### 4. `generate-pdf-from-md` requires `reportlab` but doesn't say so upfront

The bundled PDF skill fails with `ModuleNotFoundError: No module named 'reportlab'` on first run. There's no pre-check, no helpful error message suggesting `pip install reportlab`, and no auto-install. I had to read the traceback, install the package manually, and also figure out which Python interpreter it needed (`/usr/local/bin/python3` vs conda's python).

### 5. No WYSIWYG table insertion

The editor renders existing Markdown tables beautifully. But there's no toolbar button to *create* a new table. I had to switch to raw Markdown, type the pipe syntax manually, then switch back. Defeats the WYSIWYG purpose for tables.

---

## What I Would Change Immediately

### 1. Add an "Abilities" tab to the Settings panel
Show:
- List of installed abilities with status (registered / unregistered)
- "Create New Ability" button that runs `withai.abilities.create`
- Link to the agentskills.io docs
- Sync status and last sync time

This single change would make abilities discoverable.

### 2. First-run onboarding walkthrough
After install, show a 3-step guided tour:
1. "Open any `.md` file → you're using the WYSIWYG editor"
2. "Click the gear icon → configure Claude Code permissions"
3. "Create your first ability → here's how"

### 3. Show ability descriptions inline
When registered abilities appear in `~/.claude/CLAUDE.md`, the descriptions are shown in a table. But this file is hidden from most users. Surface the same descriptions in the Settings panel or a sidebar view.

### 4. Dependency pre-check for bundled skills
Before running `md_to_pdf.py`, check if `reportlab` is importable. If not, show a notification: "The PDF skill requires reportlab. Install it? [Yes] [No]"

---

## Features I Would Add

### 1. Ability chaining
Let abilities declare dependencies on other abilities. My `doc-generator` produces Markdown → it should be able to automatically invoke `generate-pdf-from-md` as its final step without the user knowing about both separately.

### 2. Ability marketplace / gallery
A curated gallery of community abilities installable with one click. Like npm for Claude Code skills. This would:
- Give new users something useful on day one
- Create ecosystem and community
- Provide templates for ability creators

### 3. Live collaborative editing indicators
When Claude Code is writing to a `.md` file while it's open in the WYSIWYG editor, show a visible cursor with a "Claude" label. Users would be able to watch the AI write in real-time. This would be a genuinely magical UX moment.

### 4. Ability usage analytics
Track how often each ability is triggered, average execution time, and success/failure rate. Surface this in the Settings panel so creators can iterate.

---

## UX / Workflow Improvements

1. **Keyboard shortcut for Settings panel** — No keybinding exists. Add `Cmd+Shift+W` or similar.

2. **Notification after workspace setup** — When `withai.setupWorkspace` creates `.claude/CLAUDE.md`, show a notification: "WithAI set up your workspace. [View CLAUDE.md] [Configure Settings]". Currently it happens silently.

3. **"Open in WYSIWYG" CodeLens** — Add a clickable CodeLens at the top of `.md` files: "Open in WithAI Editor" — helps users who haven't set it as default discover the feature.

4. **Status bar indicator** — Show a small status bar item: `WithAI: 3 abilities | Synced`. Makes the extension feel alive and present.

5. **Dark mode contrast** — Check the Settings panel webview against popular dark themes (One Dark Pro, GitHub Dark Dimmed). Some text was hard to read.

---

## What Slowed Me Down

1. **Finding abilities documentation** — No dedicated docs page. Everything lives in the bundled SKILL.md files inside the extension directory. Had to `find ~/.vscode/extensions -path '*withai*' -name 'SKILL.md'` to find them.

2. **Path structure confusion** — `~/.withai/abilities/{org}/{ability}/` requires the org-name level directory. I initially tried `~/.withai/abilities/my-ability/` and registration couldn't find it.

3. **Two Python interpreters** — My system has conda Python and `/usr/local/bin/python3`. The PDF skill needed reportlab installed on the right one. No guidance from the extension about which Python is being used.

4. **No end-to-end tutorial** — The ability-creator SKILL.md documents the spec well but doesn't walk through "here's a complete ability from empty directory to registered and working." A 2-minute screencast or step-by-step guide would save hours.

---

## Summary

**The core insight is right**: an AI workspace needs more than a chat panel. WithAI's abilities system is genuinely novel — I haven't seen anything like it in other AI coding tools. The agentskills.io spec, the create → register → publish flow, and the auto-injection into `~/.claude/CLAUDE.md` are well-designed.

**The gap is discoverability.** The most powerful feature is the hardest to find. A new user sees "nice markdown editor" and misses the entire platform. Closing that gap — through UI surfacing, onboarding, and documentation — would dramatically change how people perceive and use the product.

The WYSIWYG editor and Settings panel are solid table-stakes features. The abilities system is the moat. Invest there.
