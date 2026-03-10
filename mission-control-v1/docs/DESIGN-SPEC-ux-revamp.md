# Mission Control v1 — UX/UI Design Specification (Revamp)

**Author:** Mr Design  
**Date:** 2026-03-10  
**Applies to:** Streamlit app (`app.py`)  
**Reference PRD:** `docs/PRD-ux-revamp.md`

---

## 0) Objective

Create a cleaner, premium **command-center** UI for Mr Kai with:
- stronger visual hierarchy,
- fewer top-level tabs,
- consistent card/list/pill patterns,
- faster scanning for status and priorities,
- progressive disclosure (details only when needed).

This spec is intentionally **Streamlit-native** (custom CSS + standard Streamlit components), no React/custom JS frameworks required.

---

## 1) Color Palette (Exact Hex)

## Core neutrals
- `--bg-app: #F6F8FC` (page background)
- `--bg-surface: #FFFFFF` (cards, panels)
- `--bg-surface-soft: #F9FAFB` (subtle section backgrounds)
- `--bg-header: #1A1A2E` (sticky top shell / command strip)
- `--border-subtle: #E5E7EB`
- `--border-strong: #D1D5DB`

## Text
- `--text-primary: #111827`
- `--text-secondary: #4B5563`
- `--text-muted: #6B7280`
- `--text-on-dark: #F9FAFB`

## Brand accents
- `--accent-primary: #6C5CE7` (primary CTA / highlight)
- `--accent-primary-hover: #5B4BD6`
- `--accent-info: #0984E3`

## Status colors (global semantic)
- `--status-queued: #3B82F6` (blue)
- `--status-inprogress: #F59E0B` (amber)
- `--status-done: #10B981` (green)
- `--status-blocked: #EF4444` (red)

## Supporting state colors
- `--state-warning-bg: #FFFBEB`
- `--state-warning-border: #FCD34D`
- `--state-danger-bg: #FEF2F2`
- `--state-danger-border: #FCA5A5`
- `--state-success-bg: #ECFDF5`
- `--state-success-border: #86EFAC`
- `--state-info-bg: #EFF6FF`
- `--state-info-border: #93C5FD`

## Agent accent colors (already defined in app)
- Mr Brain `#6C5CE7`
- Mr Engineering `#0984E3`
- Mr Design `#E17055`
- Mr Marketing `#00B894`
- Mr Analytics `#6F42C1`
- Mr Support `#E84393`
- Mr Spatial `#00CEC9`
- Mr QA `#A29BFE`

---

## 2) Typography

## Font stack
```css
font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

## Type scale
- **H1:** 24px / 32px line-height / 700
- **H2:** 18px / 26px line-height / 650
- **Body:** 14px / 22px line-height / 400
- **Caption:** 12px / 18px line-height / 500

## Usage rules
- One H1 per page section (dashboard title).
- H2 for tab-level section headers and card group labels.
- Body for list rows and form text.
- Caption for metadata: timestamps, counts, helper notes.

---

## 3) Spacing System (8pt-based)

Use only this spacing scale across layout/components:
- `4px` (`--space-1`): micro gaps, icon-label gap
- `8px` (`--space-2`): chip/pill inner spacing, compact rows
- `16px` (`--space-3`): default card padding, block spacing
- `24px` (`--space-4`): section spacing

Optional for large desktop rhythm:
- `32px` (`--space-5`) between major zones (header → content)

---

## 4) Component Designs (Implementation-Oriented)

## 4.1 Agent Card (header cards)
**Purpose:** quick team scan + direct entry to agent page.

**Structure:** emoji → name → role → status meta row → full-width action.

**CSS properties:**
- Background: `#FFFFFF`
- Border: `1px solid #E5E7EB`
- Radius: `16px`
- Padding: `16px`
- Min-height: `148px`
- Hover: `transform: translateY(-2px)`, shadow `0 10px 24px rgba(17,24,39,0.10)`
- Active agent glow (if working): `box-shadow: 0 0 0 2px <agentColor>33, 0 10px 24px rgba(17,24,39,0.12)`

**Clickable behavior:**
- Entire card area should feel clickable; in Streamlit, place a full-width button at bottom (`use_container_width=True`) styled as subtle CTA.

---

## 4.2 Job Row/Card (AI Workers)
**Purpose:** dense scannable list with progressive details.

**Collapsed row design:**
- Display: ID, assigned agent, request snippet, status pill, priority.
- Row container: white background, `1px solid #E5E7EB`, radius `12px`, padding `12px 14px`.
- Request text: max 1 line with ellipsis.
- Hover: background to `#F9FAFB`.

**Expanded details (inside expander):**
- Two-column controls (status, assignment)
- Action row (Save / Clone / Delete)
- Output hidden in nested expander

---

## 4.3 Task Row/Card
**Purpose:** reduce noise while preserving quick actions.

**Card style:**
- Base: `background #FFFFFF`, border `1px solid #E5E7EB`, radius `12px`, padding `12px 14px`
- Left urgency stripe (`4px`) using urgency class:
  - Low `#10B981`
  - Medium `#F59E0B`
  - High `#F97316`
  - Critical `#EF4444`

**Primary row content:**
- Title + meta (company · owner · due date)
- Inline status pill
- Quick actions: Done, Snooze, Delete

**Edit behavior:**
- Hidden under “✏️ Edit” expander by default.

---

## 4.4 Status Pill Badges
**Base pill CSS:**
- Display: inline-flex; align-items center
- Height: `24px`
- Padding: `0 10px`
- Radius: `999px`
- Font: `12px`, `600`
- Border: `1px solid transparent`

**Variants:**
- Queued: bg `#EFF6FF`, text `#1D4ED8`, border `#BFDBFE`
- In Progress: bg `#FFFBEB`, text `#B45309`, border `#FCD34D`
- Done: bg `#ECFDF5`, text `#047857`, border `#86EFAC`
- Blocked: bg `#FEF2F2`, text `#B91C1C`, border `#FCA5A5`

---

## 4.5 KPI Metric Cards
Use Streamlit `st.metric` with CSS wrapper styling:
- Background: `#FFFFFF`
- Border: `1px solid #E5E7EB`
- Radius: `16px`
- Padding: `16px`
- Label: 12px uppercase (tracking 0.04em)
- Value: 28px, weight 700

---

## 4.6 Alert Banners
**Design:** full-width rounded banners with icon + concise message.

- Base: radius `12px`, padding `10px 12px`, border `1px solid`
- Danger: `bg #FEF2F2`, border `#FCA5A5`, text `#991B1B`
- Warning: `bg #FFFBEB`, border `#FCD34D`, text `#92400E`
- Info: `bg #EFF6FF`, border `#93C5FD`, text `#1E3A8A`
- Success: `bg #ECFDF5`, border `#86EFAC`, text `#065F46`

---

## 4.7 Quick Command Bar
**Placement:** directly below top header, above tabs.

**Container:**
- Background: gradient `linear-gradient(135deg, #1A1A2E 0%, #232347 100%)`
- Radius: `16px`
- Padding: `12px`
- Border: `1px solid rgba(255,255,255,0.08)`

**Input style:**
- Height: `42px`
- Radius: `10px`
- Border: `1px solid #D1D5DB`
- Focus ring: `0 0 0 3px rgba(108,92,231,0.20)`

**Send button:**
- Background `#6C5CE7`, text white, weight 600, radius `10px`
- Hover `#5B4BD6`

---

## 5) Layout Specification

## 5.1 Tab structure (reduce 9 → 5)
**New order (required):**
1. **🏢 Office**
2. **🤖 Jobs** (merge Team + AI Workers intent)
3. **📋 Tasks**
4. **📨 Inbox** (merge Escalations + Comms + Trends + Feedback)
5. **⚙️ Settings** (Automation + system controls)

## 5.2 Section ordering (top to bottom)
1. Sticky command header (title + global KPIs)
2. Agent cards strip (single row of 8 on desktop)
3. Quick Command bar
4. Alerts block
5. Tab content area

## 5.3 Header design
- Sticky top wrapper with dark background (`#1A1A2E`), soft shadow.
- Left: app title + subtitle.
- Right: 4 KPI cards (Open, Escalations, Overdue, Due Today).
- Keep header compact (no more than ~148px visual height).

---

## 6) Streamlit-Specific CSS (Copy/Paste Ready)

Use exactly this block via:
```python
st.markdown(CSS, unsafe_allow_html=True)
```

```css
<style>
:root {
  --bg-app: #F6F8FC;
  --bg-surface: #FFFFFF;
  --bg-surface-soft: #F9FAFB;
  --bg-header: #1A1A2E;
  --border-subtle: #E5E7EB;
  --border-strong: #D1D5DB;
  --text-primary: #111827;
  --text-secondary: #4B5563;
  --text-muted: #6B7280;
  --text-on-dark: #F9FAFB;
  --accent-primary: #6C5CE7;
  --accent-primary-hover: #5B4BD6;
  --status-queued: #3B82F6;
  --status-inprogress: #F59E0B;
  --status-done: #10B981;
  --status-blocked: #EF4444;
  --radius-card: 16px;
  --radius-md: 12px;
  --radius-sm: 8px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
}

html, body, [class*="css"]  {
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text-primary);
}

.stApp {
  background: var(--bg-app);
}

.main .block-container {
  max-width: 1440px;
  padding-top: 1rem;
  padding-bottom: 2rem;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, [data-testid="stSidebar"], [data-testid="collapsedControl"] {
  visibility: hidden;
  display: none !important;
}

/* Sticky top header wrapper: apply class via st.markdown html wrapper */
.mc-sticky-header {
  position: sticky;
  top: 0;
  z-index: 90;
  background: linear-gradient(135deg, #1A1A2E 0%, #232347 100%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 12px 16px;
  margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(17,24,39,0.18);
}

.mc-title {
  font-size: 24px;
  line-height: 32px;
  font-weight: 700;
  color: var(--text-on-dark);
  margin: 0;
}

.mc-subtitle {
  font-size: 12px;
  line-height: 18px;
  font-weight: 500;
  color: #D1D5DB;
  margin: 2px 0 0;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background: transparent;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 0 8px 0;
}

.stTabs [data-baseweb="tab"] {
  height: 36px;
  border-radius: 10px;
  padding: 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: #EEF2FF;
  color: #3730A3;
}

/* KPI metric cards */
[data-testid="stMetric"] {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  padding: 14px 16px !important;
  box-shadow: 0 2px 8px rgba(17,24,39,0.04);
}

[data-testid="stMetricLabel"] {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

[data-testid="stMetricValue"] {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

/* Cards / containers */
div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px;
}

.mc-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 16px;
}

.mc-agent-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 16px;
  min-height: 148px;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}

.mc-agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(17,24,39,0.10);
  border-color: var(--border-strong);
}

/* Row cards for jobs/tasks */
.mc-row-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 12px 14px;
}

.mc-row-card:hover {
  background: var(--bg-surface-soft);
}

.mc-urgency-low { border-left: 4px solid #10B981; }
.mc-urgency-medium { border-left: 4px solid #F59E0B; }
.mc-urgency-high { border-left: 4px solid #F97316; }
.mc-urgency-critical { border-left: 4px solid #EF4444; }

/* Pills */
.mc-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}

.mc-pill-queued { background: #EFF6FF; color: #1D4ED8; border-color: #BFDBFE; }
.mc-pill-inprogress { background: #FFFBEB; color: #B45309; border-color: #FCD34D; }
.mc-pill-done { background: #ECFDF5; color: #047857; border-color: #86EFAC; }
.mc-pill-blocked { background: #FEF2F2; color: #B91C1C; border-color: #FCA5A5; }

/* Alerts */
.mc-alert {
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid;
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 20px;
}

.mc-alert-danger { background:#FEF2F2; border-color:#FCA5A5; color:#991B1B; }
.mc-alert-warning { background:#FFFBEB; border-color:#FCD34D; color:#92400E; }
.mc-alert-info { background:#EFF6FF; border-color:#93C5FD; color:#1E3A8A; }
.mc-alert-success { background:#ECFDF5; border-color:#86EFAC; color:#065F46; }

/* Quick command strip */
.mc-command-bar {
  background: linear-gradient(135deg, #1A1A2E 0%, #232347 100%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 12px;
  margin: 8px 0 16px;
}

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
  border-radius: 10px !important;
  border: 1px solid var(--border-strong) !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent-primary) !important;
  box-shadow: 0 0 0 3px rgba(108,92,231,.20) !important;
}

.stButton > button {
  border-radius: 10px !important;
  border: 1px solid var(--border-subtle) !important;
  height: 38px;
  font-weight: 600;
}

/* Primary action button if wrapped in class context */
.mc-primary-btn .stButton > button {
  background: var(--accent-primary) !important;
  color: #fff !important;
  border-color: var(--accent-primary) !important;
}

.mc-primary-btn .stButton > button:hover {
  background: var(--accent-primary-hover) !important;
  border-color: var(--accent-primary-hover) !important;
}

/* Dataframe readability */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  overflow: hidden;
}

.streamlit-expanderHeader {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}
</style>
```

---

## 7) Interaction Patterns

## 7.1 Hover states
- Cards: lift by 2px + stronger shadow.
- Row cards: background shifts to `#F9FAFB`.
- Buttons: 120–180ms ease transition, clear contrast increase on hover.

## 7.2 Click targets
- Minimum target size: **44x44px** for primary controls.
- For agent cards, the bottom full-width Open button remains explicit while card itself is visually clickable.
- Status pills are non-primary controls unless explicitly used as toggles.

## 7.3 Progressive disclosure
- Default view = summary only.
- Details/edit controls hidden in expanders.
- Nested expanders only for secondary content (e.g., output logs).
- Limit simultaneous expanded cards to reduce visual noise.

## 7.4 Task status quick flow
- One-click quick action for “Done”.
- Inline cycle interaction allowed only if state model is predictable (`Open → In Progress → Done`); otherwise keep explicit buttons.
- Destructive actions (Delete) remain separated and visually de-emphasized.

## 7.5 Feedback and loading behavior
- On action: immediate toast (`st.success`) + rerun.
- Preserve filter state across reruns (existing Streamlit session state behavior).

---

## 8) Mapping from Current App → New IA

- **Office** tab: keep virtual office + agent state panes.
- **Team + AI Workers** → **Jobs** tab.
- **Escalations + Comms + Trends + Feedback** → **Inbox** tab with segmented sections.
- **Automation** → **Settings**.

This removes low-frequency top-level clutter while preserving all features.

---

## 9) Engineering Handoff Notes

1. Inject CSS block early (right after `st.set_page_config`).
2. Add minimal HTML wrappers using `st.markdown` classes:
   - `.mc-sticky-header`
   - `.mc-command-bar`
   - `.mc-agent-card`
   - `.mc-pill-*`
3. Keep Streamlit-native widgets (buttons/selectboxes/expanders/dataframe).
4. Avoid horizontal overflow by:
   - truncating long text in list tables,
   - reducing visible columns,
   - using detail expanders for secondary fields.
5. Desktop-first at 1440px, with graceful wrap at smaller widths.

---

## 10) QA Acceptance Criteria (Design)

- No horizontal overflow at 1440px width.
- Top-level tabs reduced to 5 in required order.
- Status represented as color pills consistently across Jobs/Tasks/Inbox.
- Agent cards visually consistent and discoverable as entry points.
- Forms no longer expose all controls by default (progressive disclosure applied).
- Overall visual style reads as modern command center (dark control strip + clean white cards).
