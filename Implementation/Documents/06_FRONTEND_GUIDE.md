# Frontend Guide

**Location:** `Implementation/frontend/`  
**Framework:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Recharts  
**Dev server:** `npm run dev` → http://localhost:3000

---

## Project Structure

```
frontend/
├── app/                        Next.js App Router pages
│   ├── layout.tsx              Root layout: Sidebar + page slot
│   ├── page.tsx                Home → renders UnifiedDashboard
│   ├── alerts/page.tsx         Security threats list
│   ├── logs/page.tsx           Access log + enrolled people
│   ├── falls/page.tsx          Fall detection analytics
│   ├── objects/page.tsx        Object detection analytics
│   ├── compliance/page.tsx     Audit trail
│   ├── demo/page.tsx           Demo Center (start/stop camera scripts)
│   ├── globals.css             Tailwind base + custom styles
│   └── icon.png                Browser tab favicon (DoorFace logo)
│
├── components/
│   ├── Sidebar.tsx             Navigation + demo mode toggle
│   ├── PageHero.tsx            Page header with title/actions slot
│   ├── dashboard/
│   │   └── UnifiedDashboard.tsx  Main dashboard component
│   └── icons/
│       └── DoorIcons.tsx       SVG icon components
│
├── lib/
│   ├── api.ts                  All API fetch functions + TypeScript types
│   ├── demoData.ts             Synthetic demo fixtures + emptyOrDemo helper
│   ├── useDemoMode.ts          Demo mode toggle hook (localStorage)
│   ├── chartPrep.ts            Data transformation for charts
│   ├── insightChartData.ts     Dashboard insight chart helpers
│   ├── dashboardHelpers.ts     KPI computation
│   ├── objectAnalytics.ts      Object category/severity analytics
│   ├── reportExport.ts         Client-side CSV export
│   ├── theme.ts                Recharts colour palette
│   └── timeRange.ts            Time-range filter utilities
│
├── public/
│   ├── doorface-icon.png       Logo used in Sidebar
│   └── models/                 MediaPipe pose model (downloaded on npm install)
│       └── pose_landmarker.task
│
├── scripts/
│   └── download-pose-model.mjs  Postinstall script for pose model
│
├── next.config.ts              API proxy + config
├── tailwind.config.ts          Colour tokens, content paths
├── tsconfig.json
└── package.json
```

---

## Pages

### Home — Dashboard (`/`)

**File:** `app/page.tsx` → renders `components/dashboard/UnifiedDashboard.tsx`

The main landing page. Polls 5 APIs every **10 seconds**:
- `getStats()` → KPI cards (total entries, active alerts, falls today)
- `getAccessLogs(280)` → recent activity feed
- `getFallEvents(150)` → fall events for charts
- `getObjectEvents(150)` → object events for charts
- `getThreats()` → recent threats for alert ticker

**Sections:**
- KPI stat cards (total people, entries today, active alerts, falls today)
- Recent access activity log
- Threat/alert summary
- Fall events quick overview
- Object detection summary

---

### Alerts (`/alerts`)

**File:** `app/alerts/page.tsx`

All security threats, filterable by severity. No polling interval — loads once on mount. Includes a client-side CSV export button.

**API:** `getThreats(?severity=)`

---

### Access Logs (`/logs`)

**File:** `app/logs/page.tsx`

Door access history with a modal to view and delete enrolled people.

**APIs:** `getAccessLogs()`, `getUsers()`, `deleteUser(userId)`

**Special demo logic:** If the API returns logs but none have a real `person_id` (only `Unknown`), and demo mode is ON, demo logs are shown instead. If real named logs exist, they always take priority regardless of demo toggle.

---

### Fall Detection (`/falls`)

**File:** `app/falls/page.tsx`  
**Polling:** every 15 seconds

Two charts + events table:
1. **Confidence histogram** — bucketed by confidence score ranges
2. **Events by day** — area chart of fall events over last ~30 days

Also shows: falls today, total in buffer, last fall time, latest event confidence bar.

**APIs:** `getFallEvents(100)`, `getFallStatus()`, `resetFallDetector()`

---

### Object Detection (`/objects`)

**File:** `app/objects/page.tsx`  
**Polling:** every 15 seconds

**APIs:** `getObjectEvents(280)`, `getObjectStatus()`

Filters by category and severity. Includes stacked bar chart of events by hour and donut chart of category distribution.

---

### Compliance (`/compliance`)

**File:** `app/compliance/page.tsx`

PIPEDA audit log. Server-side CSV export (`/api/compliance/audit?format=csv`) and client-side export both available.

**API:** `getAuditLog(limit)`

---

### Demo Center (`/demo`)

**File:** `app/demo/page.tsx`  
**Polling:** every 2.5 seconds (tool process status only)

Start and stop live camera scripts via the backend subprocess API. Face registration requires a form (Person ID, name, role, photo count).

**APIs:** `getDemoTools()`, `startDemoTool()`, `startDemoToolWithPayload()`, `stopDemoTool()`

---

## Key Library Files

### `lib/api.ts`

Central API client. All functions return typed data or `null` on error.

```typescript
// Usage example
const data = await getFallEvents(100);
if (data) {
  console.log(data.events);  // FallEvent[]
}
```

The `fetchAPI<T>()` helper catches all errors and returns `null` — pages must handle `null` responses.

**Key functions:**
| Function | Method | Endpoint |
|----------|--------|----------|
| `getStats()` | GET | `/api/stats` |
| `getAccessLogs(limit, personId?)` | GET | `/api/logs` |
| `getThreats(severity?)` | GET | `/api/threats` |
| `getUsers()` | GET | `/api/users` |
| `deleteUser(userId)` | DELETE | `/api/users/:id` |
| `getAuditLog(limit)` | GET | `/api/compliance/audit` |
| `getFallEvents(limit)` | GET | `/api/fall/events` |
| `getFallStatus()` | GET | `/api/fall/status` |
| `resetFallDetector()` | POST | `/api/fall/reset` |
| `getObjectEvents(limit, cat?, sev?)` | GET | `/api/objects/events` |
| `getObjectStatus()` | GET | `/api/objects/status` |
| `getDemoTools()` | GET | `/api/demo/tools` |
| `startDemoTool(toolId)` | POST | `/api/demo/tools/:id/start` |
| `stopDemoTool(toolId)` | POST | `/api/demo/tools/:id/stop` |

---

### `lib/demoData.ts`

All synthetic demo fixtures for every dashboard page. Also exports the key helper functions.

**Demo data exports:**
- `DEMO_THREATS` — ~20 threat records spanning 30 days
- `DEMO_AUDIT` — ~25 audit log entries
- `DEMO_LOGS` — ~50 access log entries (named residents, 30 days)
- `DEMO_FALL_EVENTS` — 48 fall events with full 30-day coverage
- `DEMO_OBJECT_EVENTS` — ~30 object detection events
- `DEMO_USERS` — demo user roster
- `DEMO_FALL_STATUS` — detector status with `detector_ready: true`
- `DEMO_OBJECT_STATUS` — detector status object

**Timestamp helpers** (timestamps relative to current time so charts always look recent):
```typescript
ago(minutes)           // minutes ago
hoursAgo(h)
daysAgo(d, h?, m?)     // d days ago at optional hour:minute
todayAt(h, m)          // today at hour:minute
```

**Core helpers:**

```typescript
emptyOrDemo(apiData, demoData, demoEnabled?)
// Returns demoData if demoEnabled === true
// Returns apiData if demoEnabled === false
// Falls back to localStorage when demoEnabled not passed

nullOrDemo(apiItem, demoItem, demoEnabled?)
// Same logic for single items (not arrays)
```

---

### `lib/useDemoMode.ts`

React hook for the demo mode toggle.

```typescript
const { demoEnabled, toggle } = useDemoMode();
```

**State persistence:** `localStorage["facedoor_demo_mode"]` (`"true"` / `"false"`)

**Default:** ON (`true`) on first visit (key not yet in localStorage)

**Sync mechanism:** The hook dispatches a `facedoor-demo-change` custom event when toggled, and listens for `storage` events — so multiple tabs stay in sync.

**Toggle location in UI:** Sidebar, next to the admin name, above the navigation links.

---

## Sidebar & Layout

**File:** `components/Sidebar.tsx`

The sidebar renders on all pages via `app/layout.tsx`. It contains:
- DoorFace logo and brand name
- Demo mode toggle (purple = ON, grey = OFF)
- Navigation links to all 7 pages
- Admin info footer

The demo toggle uses `useDemoMode()` and is positioned at the top of the nav section.

---

## API Proxy

**File:** `next.config.ts`

```typescript
rewrites: async () => [
  {
    source: "/api/:path*",
    destination: "http://localhost:5001/api/:path*",
  },
]
```

All fetch calls in the frontend use `/api/...` (relative). Next.js forwards them to Flask. **If you change the Flask port, update `destination` here.**

---

## Tailwind Theme

**File:** `tailwind.config.ts`

Custom colour tokens used throughout:

| Token | Usage |
|-------|-------|
| `violet-*` | Primary: demo toggle, active states |
| `rose-*` | Falls page, critical alerts |
| `orange-*` | Object detection events |
| `fuchsia-*` | Fall confidence charts |
| `slate-*` | Text, borders, backgrounds |
| `emerald-*` | Success / access granted |
| `amber-*` | Warnings |

Chart-specific colours are in `lib/theme.ts` (`chart` export).

---

## Adding a New Page

1. Create `app/your-page/page.tsx`
2. Add `"use client"` at the top (all dashboard pages are client components)
3. Import `useDemoMode` if you need demo data support
4. Import relevant functions from `lib/api.ts`
5. Add demo data to `lib/demoData.ts` if needed
6. Add the route to the nav links in `components/Sidebar.tsx`

---

## Build for Production

```bash
cd Implementation/frontend
npm run build
npm run start     # serves the built app on :3000
```

The build output is in `.next/`. In production, set `NODE_ENV=production` and point the API rewrite to the production Flask URL.

---

## Environment Variables

All frontend env vars must be prefixed `NEXT_PUBLIC_` to be accessible in the browser.

| Variable | Default | Effect |
|----------|---------|--------|
| `NEXT_PUBLIC_USE_DEMO_DATA` | `true` | Fallback to demo when API empty; set `"false"` to disable |
| `NEXT_PUBLIC_FORCE_DEMO_DATA` | unset | Set `"true"` to always show demo data (no toggle) |
| `SKIP_POSE_MODEL_DOWNLOAD` | unset | Set `"1"` to skip MediaPipe model download on `npm install` |

Create a `.env.local` file in `Implementation/frontend/` to set these.
