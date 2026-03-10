# PRD: Mission Control UX/UI Revamp
**Product Owner:** Mr Brain | **Date:** 2026-03-10 | **Status:** Draft

## Background
Mission Control is a Streamlit dashboard managing 8 AI agents. Current UI was built functionally but lacks polish — buttons are scattered, tables overflow, edit forms are cluttered, and it doesn't feel like a premium command center.

## User
- **Mr Kai** — Marketing & IT Director, manages 2 companies
- Uses dashboard on desktop (Mac) and occasionally mobile
- Wants quick glance at agent status, fast task creation, easy job management
- Values: clean, modern, professional — not cluttered or overwhelming

## Current Problems
1. **Agent cards** — clickable but "Open" button feels bolted on, not integrated
2. **Tables** — too many columns, overflow horizontally, hard to scan
3. **AI Workers tab** — was 8 emoji reassign buttons on one row, now per-job expanders but still dense
4. **Tasks tab** — expandable cards are functional but visually noisy
5. **Virtual Office** — isometric view is cool but small on screen, not responsive
6. **Overall** — inconsistent spacing, no clear visual hierarchy, too many exposed controls
7. **No dark mode** — should match Mr Kai's preference for modern aesthetic
8. **9 tabs** — too many, some rarely used (Trends, Feedback, Comms could consolidate)

## Goals
1. **Clean, modern command center feel** — think Linear, Notion, or Vercel dashboard
2. **Information hierarchy** — most important info visible first, details on demand
3. **Consistent component patterns** — same card style, same button layout everywhere
4. **Responsive** — works well on 1440px+ screens
5. **Reduce cognitive load** — fewer tabs, progressive disclosure

## Requirements

### R1: Navigation & Layout
- Reduce tabs from 9 to 5-6 max (merge Trends+Feedback+Comms into "Inbox")
- Tab order: Office → Jobs → Tasks → Inbox → Settings
- Sticky header with key metrics always visible

### R2: Agent Cards (Home/Header)
- Cards should be the entire clickable area (not a separate button)
- Show: emoji, name, status dot (green/grey), active job count
- Hover: subtle lift + shadow
- Consider 1 row of 8 smaller cards instead of 2 rows of 4

### R3: Job Management
- Primary view: clean list/table with status pills (colored badges)
- Click row → slide-out or expander with full details
- Reassign via dropdown, not multiple buttons
- Bulk actions: select multiple → mark done / delete

### R4: Task Management  
- Clean list with urgency color stripe on left
- Inline status toggle (click to cycle: Open → In Progress → Done)
- Edit fields hidden behind "Edit" button
- Quick action: swipe-to-done feel (single click)

### R5: Virtual Office
- Larger, more prominent in Office tab
- Clicking desk navigates to agent page
- Status reflected in real-time (green glow = working)

### R6: Visual Design
- Color palette: dark header (#1a1a2e or similar), white content cards
- Accent colors per agent (already defined)
- Rounded corners (16px for cards, 8px for buttons)
- Consistent 8px spacing grid
- Status pills: colored rounded badges (not just text)
- Typography: system font stack, clear hierarchy (24/18/14/12px)

### R7: Components to Design
- Agent card component
- Job row component  
- Task row component
- Status pill (Queued=blue, In Progress=yellow, Done=green, Blocked=red)
- Quick Command bar (redesigned)
- Metric card (KPI)
- Alert banner

## Out of Scope
- Mobile-first design (desktop priority)
- Real-time WebSocket updates (Streamlit limitation)
- Complete framework change (staying on Streamlit)

## Success Criteria
- Mr Kai says "this looks good" ✅
- All existing features preserved
- Page loads in < 3 seconds
- No horizontal overflow on 1440px screen

## Pipeline
1. 🧠 Mr Brain → PRD (this document)
2. 🎨 Mr Design → UX/UI design spec (CSS, layout, component guide)
3. 💻 Mr Engineering → Build implementation
4. 🧪 Mr QA → Test and validate
5. 👔 Mr Kai → Final approval
