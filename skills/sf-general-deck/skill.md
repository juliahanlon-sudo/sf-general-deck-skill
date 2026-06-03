---
name: sf-general-deck
description: Build a general-purpose Salesforce-branded presentation using the Salesforce Corporate Template 2026. Asks for title, sections, content, links, and photo folders before building. Researches unknown topics from the web to populate slide content. Auto-detects the current user for the cover. Always ends with a Thank You slide. Opens the finished deck when done.
---

# Salesforce General Slide Deck

Build a branded Salesforce presentation using the **Salesforce Corporate Template 2026** (`15bBgTADtCxDmXeh4PJX3fZBz2yloMkzRepVU2KJoe6M`). Script-first: all content is researched and planned before any Slides API call.

## Phase 0 — Verify template access

1. Call `get_presentation(presentation_id="15bBgTADtCxDmXeh4PJX3fZBz2yloMkzRepVU2KJoe6M")`.
2. If it fails with an auth error, tell the user to run `/salesforce-trust-foundations:mcp-auth` and stop.
3. On success, confirm at least one cover slide, one agenda slide, one segue, one content slide, and one thank-you slide are present (the template is versioned and IDs may change — just verify the types exist by reading slide text patterns).

## Phase 0.5 — Detect author

Run this command to get the author name for the cover:

```bash
git config user.name 2>/dev/null || echo ""
```

If the result is a non-empty real name (not a username/email), use it as `author`. Otherwise, extract the name from the Google account email returned by `get_presentation` (the "for julia.hanlon@salesforce.com" prefix — capitalize "Julia Hanlon" from "julia.hanlon"). Trim to ≤ 30 chars. Never use an email address or Unix login directly on the slide.

## Phase 1 — Intake (ask the user)

Ask **all four questions in a single `AskUserQuestion` batch**. Never ask them one at a time.

| # | Field | Question |
|---|---|---|
| 1 | **Title** | "What is the title of your presentation?" |
| 2 | **Sections** | "List the sections or topics you want to cover (e.g. Overview, Q3 Priorities, Roadmap, Next Steps)." |
| 3 | **Content** | "For each section, what are the key points, data, or narrative you want on the slides? Leave blank for any section you'd like me to research." |
| 4 | **Links & Photos** | "Any URLs to include or photo folders (local paths or Google Drive links)? Leave blank if none." |

Parse all answers before proceeding. If the user leaves content blank for a section, mark it for research in Phase 1.5.

**Exit:** `intake = {title, author, sections[], content{}, links[], photo_sources[]}`

## Phase 1.5 — Research missing content

For any section where the user left content blank (or provided only a vague name), research it to write real slide body copy.

**Research strategy — apply in order, stop when you have enough:**

1. **User-provided links:** if the user gave a URL for this section, `WebFetch` it first and extract the key points.
2. **Web search:** use the `search` MCP tool (or `WebFetch` on a well-known URL) to find a concise description of the topic. Search query format: `"<section name> overview site:salesforce.com OR site:autodesk.com OR <relevant domain>"`. For BIM/AEC tools (Forma, Navisworks, Revit, etc.) use `site:autodesk.com`. For Salesforce products use `site:salesforce.com`. For partner companies (e.g. Symetri) search directly.
3. **Known product facts:** if the topic is a well-known product and search is unavailable, use your training knowledge to write accurate body copy — but flag to the user that it should be verified.

**From research, produce for each section:**
- `title` — the section name (≤ 40 chars)
- `body` — 3–5 punchy bullet points summarizing what the product/service does, written in plain language (≤ 400 chars total). No marketing fluff.
- `layout_hint` — `single-title` for narrative/bullets, `cards-three-up` for exactly 3 discrete items, `two-column` for comparisons.

**Sections that already have user-provided content:** use that content as-is — do not replace with research.

**Exit:** all sections have body copy and a layout_hint. Show a one-line summary per section to the user before proceeding (e.g. "Forma Cloud: researched from autodesk.com — 4 bullets").

## Phase 2 — Deck plan

Using the intake + research, produce a `slide-plan` array. Each entry has:
- `index` — 0-based position
- `layout` — one of: `title`, `agenda`, `segue`, `single-title`, `two-column`, `three-column`, `cards-three-up`, `thank-you`
- `template_slide_id` — resolved from the live template (see Phase 0)
- `roles` — content map for that layout

### Layout selection rules

- **Slide 0:** always `title`. Roles: `title` (≤ 35 chars), `subtitle` (blank unless given), `author_block` (from Phase 0.5, ≤ 30 chars).
- **Slide 1:** always `agenda`. One item per section, max 6. Group minor sections if needed.
- **Segue before each section** (if 2+ sections). Roles: `title` (section name ≤ 40 chars), `subtitle` (one-line context ≤ 80 chars — use a researched tagline if available).
- **Content slides:** use the `layout_hint` from Phase 1.5 research.
  - `single-title`: title + body bullets
  - `two-column`: title + two column headings + two column bodies
  - `cards-three-up`: title + 3 cards each as `"Heading\n\nBody."` (heading ≤ 4 words)
- **Last slide:** always `thank-you`. Roles: `{}`. Do NOT add any text — master renders it.

### Character budgets (enforce before Phase 3)

| Role | Limit |
|---|---|
| Cover `title` | 35 chars |
| Cover `author_block` | 30 chars |
| Segue `title` | 40 chars |
| Segue `subtitle` | 80 chars |
| Content `title` | 40 chars |
| Content `body` | 500 chars |
| Each column body | 200 chars |
| Each card (heading + body) | 120 chars total |
| Agenda item | 60 chars |

Trim copy to fit. Never pass oversize text to Phase 3.

Show the user a compact plan preview: `N. [layout] Title — first line of body`. Ask: **proceed / edit / cancel**. Don't continue until approved.

**Exit:** approved `slide-plan[]` persisted to `/tmp/sf-deck/slide-plan.json`.

## Phase 3 — Build the deck

1. `copy_drive_file(file_id="15bBgTADtCxDmXeh4PJX3fZBz2yloMkzRepVU2KJoe6M", new_name=intake.title)`. Capture `new_presentation_id`. On failure, surface the error and stop.
2. `get_presentation(presentation_id=new_presentation_id)`. Collect all `slides[].objectId`.
3. Identify slides to keep: one cover (text contains "Title of" or "presentation"), one agenda (text contains "Agenda" + "01"), one segue (2 elements, text "Segue"), one single-title content (4 elements, text "Title, single line"), one closing thank-you (text "Closing Thank You"). Keep these 5; delete all others.
4. Duplicate segue and content slides as needed (one per section each), then reorder: cover → agenda → [segue + content] × N sections → thank-you.
5. **Fill slides one at a time** (one `batch_update_presentation` per slide):
   - `get_page(new_presentation_id, slide_id)` → get shape objectIds
   - Fill by resolved objectId: `deleteText` (type ALL) + `insertText` at index 0
   - Skip `deleteText` if shape has no text; skip fill entirely for thank-you slide
   - For agenda: shapes with text matching `^0[1-6]$` are badges — skip them. Delete unused item shapes + their paired badges.
   - For cover: shape index 0 = title, index 1 = subtitle, index 2 = first author block (fill with `author`), remaining author shapes = clear text.

**Exit:** deck URL + `/tmp/sf-deck/resolution-log.json`.

## Phase 4 — Verify and open

1. `get_presentation(new_presentation_id)`. Flag any slides still containing placeholder text (`"Title, single line"`, `"Placeholder text"`, `"Subtitle"` as the entire content, `"Lorem ipsum"`).
2. Auto-delete any stray "Thank you" text box added to the closing slide.
3. Get shareable link: `get_drive_shareable_link(file_id=new_presentation_id)`.
4. Open the deck:
   ```bash
   open "https://docs.google.com/presentation/d/<new_presentation_id>/edit"
   ```
5. Tell the user the deck is open, give the link, and list any flagged issues by slide number.

## Do / Don't

**Do**
- Auto-detect the author name from git config or the Google account — never leave cover author blank or use a placeholder.
- Research any section the user left blank — pull real content from the web before planning slides.
- Show a one-line research summary per section before the plan preview.
- Enforce character budgets before Phase 3.
- Open the deck automatically.

**Don't**
- Don't put "Add key points here" or any placeholder body on a content slide — always fill with real content.
- Don't add a "Thank you" text box to the closing slide.
- Don't put raw URLs > 40 chars in a title or heading.
- Don't use `replaceAllText` — always fill by resolved `objectId`.
- Don't invent statistics or customer names not found in research.
