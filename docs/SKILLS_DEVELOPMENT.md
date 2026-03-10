# IECC Skills Development Plan

> **Owner:** Alex Smith, Director of Energy Programs, ICC
> **Created:** 2026-03-05 (Session 27)
> **Last Updated:** 2026-03-05 (Session 27, second research pass)
> **Purpose:** Master reference for building, installing, and maintaining custom Claude Cowork skills for the IECC project.

---

## How Cowork Skills Work

Skills are folders of instructions, scripts, and resources that Claude loads dynamically when relevant to a task. They teach Claude *how* to do specialized work — unlike Projects (background knowledge always in context) or MCP connectors (data access). Skills follow the open Agent Skills standard (agentskills.io), meaning they work across Claude Code, Cowork, Claude.ai, and the Claude API.

### The Three-Layer Loading System

Skills use progressive disclosure to stay efficient with Claude's context window:

1. **Metadata** (~100 tokens) — The `name` and `description` from YAML frontmatter. Always loaded at session start. Claude uses this to decide whether to invoke the skill. No context penalty for having many skills installed.
2. **SKILL.md body** (<500 lines ideal, under 5k tokens) — Detailed instructions. Loaded only when the skill triggers. Once loaded, every token competes with conversation history.
3. **Bundled resources** (effectively unlimited) — Scripts, references, assets. Loaded or executed only as needed. Scripts run via bash and only their *output* enters context — the script code itself is never loaded.

This means you can bundle large reference files, database schemas, or utility scripts without wasting context on every conversation.

### Skill Directory Structure

```
my-skill/
├── SKILL.md              # Required — instructions + YAML frontmatter
├── scripts/              # Executable code (Python, Bash, Node.js)
├── references/           # Docs loaded into context as needed
└── assets/               # Templates, icons, fonts, binary files
```

### Two Types of Skill Content

Skills generally serve one of two purposes:

**Reference content** — Background knowledge Claude applies to current work. Conventions, patterns, style guides, domain rules. Runs inline alongside conversation context.

**Task content** — Step-by-step instructions for specific actions like deployments, exports, or data processing. Often invoked manually with `/skill-name`. Add `disable-model-invocation: true` to prevent Claude from auto-triggering.

### SKILL.md Anatomy

Every skill needs a SKILL.md with two parts:

```yaml
---
name: my-skill-name          # Required. Lowercase, hyphens, max 64 chars
description: >-               # Required. Max 1024 chars. Third person.
  What this skill does and when to use it. Include trigger words.
  Be specific — Claude uses this to choose from 100+ skills.
---

# Skill Title

Instructions Claude follows when this skill triggers.
Reference files, scripts, examples, workflows.
```

### Frontmatter Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Identifier. Lowercase letters, numbers, hyphens only. Max 64 chars. No "anthropic" or "claude" reserved words. |
| `description` | Yes | What it does + when to trigger. Max 1024 chars. Always in third person. No XML tags. |
| `context` | No | Set to `fork` to run in isolated subagent context. |
| `agent` | No | Which subagent type when `context: fork` is set (Explore, Plan, general-purpose, or custom from `.claude/agents/`). |
| `allowed-tools` | No | Tools Claude can use without asking permission. Space-separated. Supports patterns: `Bash(git *)`, `Bash(python *)`. |
| `disable-model-invocation` | No | `true` = only user can invoke via /command. Claude can't auto-trigger. Description removed from context entirely. |
| `user-invocable` | No | `false` = hidden from / menu. Only Claude can invoke. Good for background knowledge skills. |
| `argument-hint` | No | Hint for autocomplete, e.g., `[issue-number]` or `[filename] [format]`. |
| `model` | No | Override which model runs this skill (haiku, sonnet, opus). |
| `hooks` | No | Hooks scoped to skill lifecycle (PreToolUse, PostToolUse, Stop). |

### Invocation Control Matrix

| Frontmatter | User can invoke | Claude can invoke | Description in context? |
|-------------|----------------|-------------------|------------------------|
| (default) | Yes | Yes | Yes — always loaded |
| `disable-model-invocation: true` | Yes | No | No — removed entirely |
| `user-invocable: false` | No | Yes | Yes — always loaded |

### Description Writing Rules

The description is the single most important field — it determines whether Claude invokes your skill. Claude uses it to choose from potentially 100+ available skills.

- **Always write in third person.** "Processes PDF files" not "I can help you process PDFs." The description is injected into the system prompt — inconsistent POV causes discovery problems.
- **Include trigger words.** Think about what the user would actually say. Include both the action AND the context.
- **Be pushy.** Claude tends to under-trigger. Make descriptions slightly aggressive about when to activate.
- **Be specific.** "Helps with documents" is useless. "Generates Word documents for ICC circ forms, modifications, and agendas" is useful.
- **Include both WHAT and WHEN.** "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

---

## How to Create, Package, and Install Skills

### Step 1: Create the Skill

Write the SKILL.md and any supporting files in a temporary directory:

```bash
mkdir -p /tmp/my-skill/scripts
# Write SKILL.md, scripts, references, etc.
```

### Step 2: Package

Use the skill-creator's packaging script:

```bash
python -m scripts.package_skill /tmp/my-skill /path/to/output/
```

This creates a `my-skill.skill` file (a validated zip).

### Step 3: Install in Cowork

1. Go to **Customize > Skills** in the Cowork UI
2. Click the **"+"** button
3. Select **"Upload a skill"**
4. Upload the `.skill` file

The skill appears in the Skills list and can be toggled on/off.

### Step 4: Test and Iterate

- Test with varied prompts to verify triggering
- Use the skill-creator's eval system for rigorous testing
- Iterate on the description if Claude doesn't trigger when expected

---

## Key Authoring Principles

### Conciseness — The Context Window Is a Public Good

Claude is smart. Only add context it doesn't already have. Every token in SKILL.md competes with conversation history once loaded. Challenge every sentence: "Does Claude really need this?" and "Can I assume Claude already knows this?"

Bad (~150 tokens): "PDF (Portable Document Format) files are a common file format that contains text, images, and other content. To extract text from a PDF, you'll need to use a library..."
Good (~50 tokens): "Use pdfplumber for text extraction: `pdfplumber.open('file.pdf').pages[0].extract_text()`"

### Degrees of Freedom — Match Specificity to Fragility

Think of Claude as navigating a path. Narrow bridge with cliffs? Provide exact instructions (low freedom). Open field? Give general direction (high freedom).

- **High freedom** (guidelines, heuristics): "Analyze the code structure and check for edge cases." Use when multiple approaches are valid and decisions depend on context.
- **Medium freedom** (templates with parameters): "Use this function signature, customize as needed." Use when a preferred pattern exists but some variation is acceptable.
- **Low freedom** (exact scripts): "Run exactly this command. Do not modify." Use when operations are fragile, consistency is critical, or a specific sequence must be followed.

For the IECC project: document generation = LOW freedom (fragile, must be exact). Query skills = MEDIUM. Session management = HIGH.

### Progressive Disclosure — Keep References One Level Deep

Keep SKILL.md under 500 lines. Move detailed content to separate files. **Critical: keep all references one level deep from SKILL.md.** Claude may only partially read files that are referenced from other referenced files (nested references). If file A references file B which references file C, Claude might use `head -100` on file C instead of reading it fully.

```markdown
## Database Schema
See [references/schema.md](references/schema.md) for full table definitions.

## Common Queries
See [references/queries.md](references/queries.md) for ready-to-use SQL.
```

For reference files over 100 lines, include a table of contents at the top so Claude can see the full scope even when previewing.

### Feedback Loops — Validate-Fix-Repeat

For quality-critical tasks, build validation cycles. This pattern greatly improves output quality:

```markdown
Task Progress:
- [ ] Step 1: Generate the document
- [ ] Step 2: Run: python scripts/validate.py output.docx
- [ ] Step 3: If validation fails, fix issues and re-run
- [ ] Step 4: Only deliver when validation passes
```

The checklist format helps Claude track progress through multi-step workflows. For particularly complex workflows, provide the checklist explicitly so Claude can copy it and check items off.

### Bundled Scripts — Pre-Made Beats Generated

Pre-made scripts beat generated code: more reliable, save tokens, ensure consistency. Key benefits:
- Scripts execute via bash without loading code into context (only output consumes tokens)
- Consistent results across sessions
- No wasted time regenerating the same helper code

**Critical distinction in your SKILL.md:** Make clear whether Claude should:
- **Execute the script** (most common): "Run `analyze_form.py` to extract fields"
- **Read it as reference** (for understanding logic): "See `analyze_form.py` for the extraction algorithm"

Scripts should handle errors explicitly rather than punting to Claude. Document all magic numbers — if you don't know why a value is 47, Claude won't either.

### Naming Conventions

Use consistent, descriptive names. Consider gerund form (verb + -ing) for activity-based skills:
- Good: `processing-pdfs`, `querying-iecc-data`, `generating-circ-forms`
- Acceptable: `pdf-processing`, `iecc-query`, `circ-form-gen`
- Bad: `helper`, `utils`, `tools`, `stuff`

### Anti-Patterns to Avoid

- **Don't offer too many options.** Provide a default with an escape hatch, not 5 competing libraries.
- **Don't use Windows-style paths.** Always forward slashes: `scripts/helper.py` not `scripts\helper.py`.
- **Don't include time-sensitive info.** Use "old patterns" collapsible sections for deprecated approaches.
- **Don't deeply nest references.** Everything should be one click from SKILL.md.
- **Don't assume packages are installed.** Always include install commands.
- **Use consistent terminology.** Pick one term ("field" not "box/element/control") and stick to it.

---

## Advanced Features

### Subagent Execution (`context: fork`)

Run a skill in an isolated subagent — it gets its own context window and won't see conversation history. The skill content becomes the prompt that drives the subagent. Useful for heavy research, parallel tasks, or isolating side effects:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**Important:** `context: fork` only makes sense for skills with explicit task instructions. If your skill is just guidelines ("use these API conventions"), the subagent receives guidelines but no actionable prompt and returns nothing useful. Also, forked skills cannot spawn their own subagents — if you need hierarchical delegation, the parent must run in the main context.

### Dynamic Context Injection (`!`command``)

Run shell commands *before* the skill content reaches Claude. The command output replaces the placeholder — Claude only sees the result, not the command. This is preprocessing, not something Claude executes.

```markdown
## Current state
Database stats: !`python3 iecc_preflight.py`
PR diff: !`gh pr diff`
Changed files: !`gh pr diff --name-only`
```

This is powerful for IECC — the startup skill could inject live DB counts, pending proposal lists, or meeting status directly into the skill context.

### Extended Thinking

To enable extended thinking (deeper reasoning) in a skill, include the word "ultrathink" anywhere in your skill content. Useful for complex analysis tasks.

### String Substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking. If not present in content, appended as `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]` or `$N` | Specific argument by index (0-based). `$0` = first arg, `$1` = second. |
| `${CLAUDE_SKILL_DIR}` | Directory containing the skill's SKILL.md. Use in bash injection to reference bundled scripts regardless of working directory. |
| `${CLAUDE_SESSION_ID}` | Current session ID. Useful for logging or session-specific files. |

### Allowed Tools

Restrict what Claude can do when a skill is active. Supports patterns for bash commands:

```yaml
allowed-tools: Read, Grep, Glob, Bash(python *), Bash(git *)
```

### Visual Output Pattern

Skills can generate interactive HTML files that open in the browser — useful for dashboards, data exploration, or reports. Bundle a script that generates self-contained HTML, and tell Claude to execute it:

```markdown
Run the visualization: `python ${CLAUDE_SKILL_DIR}/scripts/visualize.py .`
This creates an interactive HTML file and opens it in your browser.
```

### Verifiable Intermediate Outputs

For complex or destructive operations, use the plan-validate-execute pattern: have Claude create an intermediate file (like `changes.json`), validate it with a script, then execute only after validation passes. Catches errors before they cause damage.

```markdown
1. Analyze the data → create changes.json
2. Run: python scripts/validate_changes.py changes.json
3. If validation fails, fix and re-validate
4. Only execute changes after validation passes
```

---

## Testing and Iteration

### Evaluation-Driven Development

Build evaluations BEFORE writing extensive docs. This ensures your skill solves real problems:

1. **Identify gaps:** Run Claude on representative tasks without the skill. Document specific failures.
2. **Create evaluations:** Build 3 scenarios that test these gaps.
3. **Establish baseline:** Measure Claude's performance without the skill.
4. **Write minimal instructions:** Just enough to address the gaps.
5. **Iterate:** Run evals, compare, refine.

### The Claude A / Claude B Pattern

The most effective development process uses two Claude instances:
- **Claude A** (the author) — helps design and refine the skill
- **Claude B** (the tester) — uses the skill on real tasks, unaware of its internals

Work through a task with Claude A. Notice what context you repeatedly provide. Ask Claude A to capture that into a skill. Then test with Claude B and observe where it struggles. Bring findings back to Claude A and iterate.

### What to Watch For During Testing

- **Unexpected exploration paths:** Claude reads files in a different order than expected? Your structure isn't intuitive.
- **Missed connections:** Claude doesn't follow references? Links need to be more explicit.
- **Overreliance on one section:** Claude keeps re-reading the same file? Move that content to SKILL.md.
- **Ignored files:** Claude never accesses a bundled file? It's either unnecessary or poorly signaled.

### Using the Skill-Creator

The `skill-creator` skill (already installed) has a full eval framework:
1. Write the skill, create test prompts
2. Run test cases in parallel (with-skill and baseline)
3. Grade assertions, aggregate benchmarks
4. Generate a review viewer for human feedback
5. Iterate based on feedback
6. Optimize the description for triggering accuracy

### Checklist Before Shipping a Skill

**Core quality:**
- [ ] Description is specific, third-person, includes trigger words
- [ ] SKILL.md body is under 500 lines
- [ ] Additional details in separate files (one level deep)
- [ ] No time-sensitive information
- [ ] Consistent terminology throughout
- [ ] Concrete examples, not abstract descriptions
- [ ] Workflows have clear steps with checklists

**Scripts and code:**
- [ ] Scripts handle errors explicitly (don't punt to Claude)
- [ ] No magic numbers (all values justified)
- [ ] Required packages listed with install commands
- [ ] No Windows-style paths
- [ ] Validation/verification steps for critical operations

**Testing:**
- [ ] At least 3 evaluation scenarios created
- [ ] Tested with varied prompts (not just exact trigger words)
- [ ] Tested on real tasks, not just synthetic ones

---

## IECC Skills Roadmap

### Installed

#### 1. iecc-startup (v2)
**Status:** Packaged, ready to install (replaces v1)
**Triggers:** "run startup", "startup", "onboard", "get up to speed", "read the docs", "check the database"
**What it does:** Uses dynamic context injection (`!`command``) to embed live DB health stats directly into the skill before the agent even sees it. Then instructs the agent to read all 6 project docs in order, verify understanding by querying a known proposal, and confirm readiness.
**Improvements over v1:** Dynamic injection eliminates a tool call, removed duplicate rules (CLAUDE.md handles that), added knowledge verification step, trimmed low-value "What You'll Learn" section.
**File:** `iecc-startup.skill`

#### 2. iecc-session-close (NEW)
**Status:** Packaged, ready to install
**Triggers:** "wrap up", "end of session", "close out", "save progress", "update the docs", "we're done"
**What it does:** Runs `session_diff.py` to detect all files modified during the session and compare DB state against the last snapshot. Then walks the agent through writing a PROJECT_MEMORY.md entry, updating relevant docs (DEVELOPMENT.md, AGENT_GUIDE.md, etc.), running a health check, and confirming to Alex.
**Bundled files:** `scripts/session_diff.py` (file change detection + snapshot comparison), `references/session-template.md` (copy-paste template for PROJECT_MEMORY entries).
**File:** `iecc-session-close.skill`

#### 3. iecc-query
**Status:** Packaged, ready to install
**Triggers:** Any data question about proposals, subgroups, meetings, votes, status lookups, "what's the status of", "how many pending", schema questions.
**What it does:** Database query assistant that knows the full schema, views, naming conventions, and common traps. Bundles CLI-first approach (iecc_query.py + direct SQL), naming traps (CEPC≠CECP, REC→RECP, status not computed_status), and pre-built queries for every common task. Serves as the shared data layer referenced by all other skills.

**Structure:**
```
iecc-query/
├── SKILL.md              # Query patterns, naming traps, CLI approach, verification protocol
└── references/
    ├── schema.md         # Full 12-table + 5-view definitions with every column
    └── queries.md        # Battle-tested SQL organized by category
```
**File:** `iecc-query.skill`

---

#### 4. iecc-web-dev
**Status:** Packaged, ready to install
**Triggers:** Working on routes, templates, HTMX partials, portal features, secretariat dashboard, chair portal, CSS, web bugs.
**What it does:** Web development patterns skill covering the two-portal rule, route registration, template inheritance, HTMX OOB swap patterns, body-to-subgroup mapping trap, auth middleware, and CSS theming. Cross-references iecc-query for data layer.

**Structure:**
```
iecc-web-dev/
├── SKILL.md              # Core patterns, hard rules, portal separation, how-to checklists
└── references/
    ├── routes.md         # Full route map + 15-point testing checklist
    └── htmx-patterns.md  # Proposal filtering, action staging OOB, circ form approve/reject
```
**File:** `iecc-web-dev.skill`

---

#### 5. iecc-doc-gen
**Status:** Packaged, ready to install
**Triggers:** Working on doc_generator.py, pdf_generator.py, Word document exports, circ form generation, modification formatting, PARSE_MOD_HTML_JS.
**What it does:** Document generation pipeline skill covering the Python→Node.js→DOCX core pattern, three document types (agenda, circ form, modification), the PARSE_MOD_HTML_JS rich text pipeline, PDF conversion via LibreOffice, and SharePoint upload service. Cross-references iecc-query and iecc-web-dev.

**Structure:**
```
iecc-doc-gen/
├── SKILL.md              # Architecture, JS-in-Python pattern, PDF pipeline, common mistakes
└── references/
    └── docx-js-patterns.md  # docx npm patterns, TextRun formatting, ICC color scheme
```
**File:** `iecc-doc-gen.skill`

---

#### 6. iecc-meeting-workflow
**Status:** Packaged, ready to install
**Triggers:** Meeting portal, chair actions, agenda management, staging flow, finalization, "Send to Secretariat", Go Live mode.
**What it does:** Full meeting workflow skill covering the end-to-end pipeline (login → agenda → stage → review → send → circ form), meeting states, agenda auto-populate with body-to-subgroup trap, action staging with Quill.js, review & finalize, and the Go Live mode specification (not yet built). Cross-references all three other skills.

**Structure:**
```
iecc-meeting-workflow/
├── SKILL.md              # End-to-end flow, state transitions, integration points
└── references/
    ├── staging-flow.md   # Table schemas, endpoint logic, auto-populate, body mapping
    └── go-live-spec.md   # Priority 2 feature spec for Teams screen-sharing mode
```
**File:** `iecc-meeting-workflow.skill`

---

## Build Priority

| Priority | Skill | Effort | Impact | Notes |
|----------|-------|--------|--------|-------|
| ✅ Done | iecc-startup (v2) | Complete | High | Packaged with dynamic injection. Ready to install. |
| ✅ Done | iecc-session-close | Complete | High | Packaged with diff script + template. Ready to install. |
| ✅ Done | iecc-query | Complete | High | Shared data layer. Schema + queries + naming traps. 96% eval pass rate. |
| ✅ Done | iecc-web-dev | Complete | High | Two-portal rule, HTMX patterns, route map. 80% eval pass rate (template pattern minor). |
| ✅ Done | iecc-doc-gen | Complete | Medium | JS-in-Python pattern, docx-js, PDF pipeline. 100% eval pass rate. |
| ✅ Done | iecc-meeting-workflow | Complete | Medium | Full staging flow, Go Live spec. 100% eval pass rate. |

---

## Useful Cowork Features for IECC

### Connectors (MCP)
Cowork supports enterprise connectors that could integrate with the IECC workflow:

- **Microsoft 365 / Outlook** — Alex's email for tracking committee communications, circ form submissions from chairs
- **SharePoint / OneDrive** — Direct integration with ICC's document management (the SharePoint upload service is already built but dormant)
- **Google Drive** — If any committee documents live there

### Scheduled Tasks
Cowork can run skills on a schedule. Potential uses:

- **Daily DB health check** — Run `iecc_preflight.py` every morning, alert if issues
- **Weekly status report** — Auto-generate proposal status summary for Alex
- **Meeting prep reminder** — Before scheduled meetings, generate agenda and verify all proposals are ready

### Cross-App Workflows
As of February 2026, Cowork can pass context between Excel and PowerPoint. This could be useful for:

- Generating committee status presentations from database exports
- Building meeting materials that combine spreadsheet data with slide decks

---

## IECC-Specific Opportunities

### Dynamic Context Injection for Startup

The `iecc-startup` skill could be enhanced with `!`command`` injection to embed live database stats directly:

```markdown
## Current database state
!`python3 iecc_preflight.py`

## Pending proposals requiring attention
!`python3 iecc_query.py --pending --summary`
```

This way the agent sees actual data before reading any docs.

### Argument-Driven Query Skill

The `iecc-query` skill could accept arguments for instant lookups:

```yaml
---
name: iecc-query
argument-hint: [proposal-id or question]
---
Look up: $ARGUMENTS
```

Usage: `/iecc-query CEPC28-25` or `/iecc-query how many pending residential proposals`

### Forked Research for Meeting Prep

A meeting prep skill with `context: fork` could research meeting data in isolation:

```yaml
---
name: iecc-meeting-prep
context: fork
agent: general-purpose
allowed-tools: Read, Grep, Bash(python3 *)
---
Prepare briefing for meeting $ARGUMENTS. Query DB for agenda items, pending proposals, and prior actions.
```

### Scheduled Tasks

Cowork scheduled tasks could automate recurring work:
- **Daily DB health check** — `iecc_preflight.py` every morning
- **Weekly status digest** — auto-generate proposal status summary
- **Pre-meeting prep** — generate agenda and verify proposals 24h before scheduled meetings

---

## References

### Official Anthropic Documentation
- [Extend Claude with skills — Claude Code Docs](https://code.claude.com/docs/en/skills) — The most comprehensive technical reference. Covers frontmatter, subagents, dynamic injection, everything.
- [Skill authoring best practices — Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Writing style, degrees of freedom, progressive disclosure, feedback loops, anti-patterns, testing methodology.
- [Agent Skills overview — Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — Architecture, three-layer loading, how skills work under the hood.
- [Skills explained — Claude Blog](https://claude.com/blog/skills-explained) — How skills compare to prompts, projects, MCP, and subagents.

### Help Center (UI-focused)
- [How to create custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) — Packaging, uploading, activating in Cowork.
- [Use Skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude) — Managing skills, toggling, troubleshooting.
- [Teach Claude your way of working](https://support.claude.com/en/articles/12580051-teach-claude-your-way-of-working-using-skills) — Patterns for capturing workflows as skills.

### Code and Examples
- [Official Anthropic Skills Repository](https://github.com/anthropics/skills) — Source code for all built-in skills (docx, xlsx, pptx, pdf, skill-creator).
- [Agent Skills Cookbook](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction) — Step-by-step tutorial for creating custom skills.
