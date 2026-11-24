# Time Tracker — Product Specification

**Version:** 0.3 (Draft)
**Date:** 2026-11-24

---

## 1. Overview

A self-hosted, desktop-based time-tracking application built for freelancers who need to share verifiable work evidence with their clients — without paying a monthly subscription to a third-party platform. Inspired by the Upwork Time Tracker, it records work sessions by combining periodic screenshots, keyboard activity metrics, and mouse activity metrics. The resulting data is surfaced through a lightweight web dashboard that the freelancer's client can access with a private link or login.

**Primary use case:** a single freelancer (the owner/operator) running the backend on their own server and sharing a client-facing dashboard URL. Scaling the platform to serve multiple independent freelancers is a planned future goal but is not a priority for the initial version.

---

## 2. Goals & Non-Goals

### Goals
- Accurate, tamper-evident time tracking per work contract / project.
- Periodic screenshots with configurable intervals.
- Keyboard and mouse activity metrics (keystrokes per minute, mouse distance / clicks).
- Local desktop agent for Windows (primary), macOS, Linux (secondary).
- Self-hosted backend deployable via Docker Compose on any VPS or home server.
- Live shareable link: client can view screenshots and activity in near real-time (no login required).
- Client dispute flow: client can flag time windows for removal via the shareable link.
- Invoice generation: produce a PDF invoice from billable hours for a chosen period.
- Offline-first agent: buffers data locally and syncs when connectivity is restored.

### Non-Goals
- Full screen-recording / video.
- Access to screenshot content by the agent itself (images are uploaded opaque).
- Payment processing (invoices are generated as PDFs; payment is handled outside the system).
- Mobile clients.

---

## 3. Target Platforms

| Platform | Priority | Notes |
|----------|----------|-------|
| Windows 10 / 11 | P0 | Primary target |
| macOS 13+ | P1 | Good-to-have; privacy permission handling differs |
| Ubuntu 22.04+ | P1 | Good-to-have; Wayland vs X11 considerations |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Desktop Agent                      │
│                                                     │
│  ┌───────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │ Screenshot│  │  Activity   │  │  Time Session│  │
│  │ Capturer  │  │  Sampler    │  │  Controller  │  │
│  └─────┬─────┘  └──────┬──────┘  └──────┬───────┘  │
│        │               │                │           │
│        └───────────────┴────────────────┘           │
│                        │                            │
│                 ┌──────▼──────┐                     │
│                 │  Local DB   │  (SQLite)            │
│                 └──────┬──────┘                     │
│                        │                            │
│                 ┌──────▼──────┐                     │
│                 │  Sync Agent │  (HTTP + queue)      │
│                 └──────┬──────┘                     │
└────────────────────────│────────────────────────────┘
                         │  HTTPS / REST + WebSocket
┌────────────────────────▼────────────────────────────┐
│                   Backend Server                    │
│                                                     │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  REST API  │  │  Auth / IAM │  │  File Store │  │
│  │  (FastAPI) │  │  (JWT/OAuth)│  │  (S3-compat)│  │
│  └────────────┘  └─────────────┘  └─────────────┘  │
│                        │                            │
│                 ┌──────▼──────┐                     │
│                 │  PostgreSQL │                      │
│                 └─────────────┘                     │
└─────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                  Web Dashboard                      │
│              (React + TypeScript)                   │
└─────────────────────────────────────────────────────┘
```

---

## 5. Desktop Agent

### 5.1 Technology Stack

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Language | Python 3.11+ | Rich ecosystem for OS hooks, packaging |
| GUI / Tray | PyQt6 or PySide6 | Native look, system-tray support on all platforms |
| Installer | PyInstaller + Inno Setup (Win) / DMG (mac) | Single-binary distribution |
| Local storage | SQLite via SQLAlchemy | Zero-setup embedded DB |
| Screenshot | `mss` library | Fast, cross-platform, no extra deps |
| Input hooks | `pynput` | Keyboard + mouse events, cross-platform |
| Crypto / integrity | `hashlib` (SHA-256) + HMAC | Screenshot tamper detection |
| HTTP client | `httpx` with async | Async uploads, retry logic |

### 5.2 Core Components

#### 5.2.1 Time Session Controller
- Tracks start / pause / stop per contract.
- Maintains a running 10-minute "memo" window; each window produces one activity record.
- Saves session state to SQLite so a crash does not lose the current window.
- **Manual activity override:** the worker can mark any window as "manual" (e.g., *"in a meeting"*, *"watching a tutorial"*) before or during the window. Manual windows skip the activity-level calculation, display a fixed badge instead of a score, and require a short free-text reason. The override and its reason are visible to the client on the dashboard, maintaining full transparency.

#### 5.2.2 Screenshot Capturer
- Captures the primary monitor (and optionally additional monitors) at a random time within each configurable interval (default: once per 10-minute window, random offset within the window).
- Captures all connected monitors; each monitor image is stored separately.
- Resizes screenshot to a maximum of 1280 × 800 before storage to limit file size.
- Computes SHA-256 of the raw captured bytes and stores it alongside the image to detect post-capture tampering.
- Stores screenshots in a local spool directory until uploaded; purges them after confirmed upload.
- Allows the worker to preview and optionally delete the screenshot before it is uploaded (grace period: 60 seconds configurable). Deleted windows are logged as "deleted" and billed time for that window is forfeited.

#### 5.2.3 Activity Sampler
- Hooks global keyboard and mouse events using `pynput` without recording which keys are pressed (count only).
- Samples every 60 seconds and writes an aggregate row: `{window_id, sample_index, keystrokes, mouse_clicks, mouse_distance_px}`.
- Activity level for a window = aggregate across all 10 samples, normalized 0–10 (like Upwork's activity bar).
- Does **not** log key content, clipboard, or window titles.

#### 5.2.4 Sync Agent
- Runs as a background thread / asyncio task.
- Uploads pending screenshots and activity records via HTTPS.
- Uses an exponential back-off retry queue (max 72 hours retention for offline scenarios).
- Verifies server-side receipt acknowledgement before purging local records.

### 5.3 System Tray UI
- Icon states: Idle (grey), Tracking (green), Paused (yellow), Error (red).
- Menu: Start / Pause / Stop, Switch Contract, View Last Screenshot, Preferences, Quit.
- Notification on screenshot capture (optional, toggleable).
- Preferences dialog: screenshot interval, monitors to capture, server URL, proxy settings.

### 5.4 Security & Privacy
- All data is transmitted over TLS 1.2+.
- Screenshots are encrypted in transit (HTTPS) and at rest on the server (AES-256 via storage provider).
- Worker can delete a screenshot within the grace period; deletion is auditable.
- No key content, URLs, or application names are recorded by default.
- Agent binary is code-signed (Windows Authenticode). macOS notarization is deferred to a later phase.

---

## 6. Backend Server

### 6.1 Technology Stack

| Concern | Choice |
|---------|--------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL 15+ |
| File storage | S3-compatible (AWS S3 / MinIO for self-hosted) |
| Auth | JWT (access + refresh) + OAuth2 (Google, optional) |
| Task queue | Celery + Redis (async processing, thumbnail generation) |
| PDF generation | WeasyPrint (Jinja2 HTML template → PDF) |
| Deployment | Docker Compose (primary — self-hosted on any VPS); Kubernetes optional for future scale |

### 6.2 Data Models

```
User
  id, email, name, role (worker | client | admin), created_at

Organization
  id, name, owner_id, created_at

FreelancerProfile
  id, user_id, company_name, address, tax_id (nullable),
  logo_storage_key (nullable), payment_instructions (text)

Contract
  id, org_id, worker_id, title, hourly_rate, weekly_hour_limit,
  screenshot_interval_min, status (active | paused | closed),
  share_token (UUID, unique),   ← enables the client shareable link
  created_at

ClientProfile                   ← one per contract
  id, contract_id, name, company_name (nullable),
  billing_email, billing_address (nullable)

WorkSession
  id, contract_id, worker_id, started_at, ended_at, memo

TimeWindow
  id, session_id, started_at, ended_at, activity_level (0-10),
  is_manual (bool), manual_reason (nullable),
  screenshot_id (nullable),
  status (pending | submitted | deleted | disputed | accepted_dispute | rejected_dispute),
  disputed_at (nullable), dispute_reason (nullable), resolved_at (nullable)

Screenshot
  id, window_id, captured_at, storage_key, sha256, thumbnail_key,
  deleted_at (nullable)

ActivitySample
  id, window_id, sample_index, keystrokes, mouse_clicks,
  mouse_distance_px, sampled_at

Invoice
  id, contract_id, invoice_number, period_start, period_end,
  total_hours, hourly_rate, subtotal,
  tax_rate (default 0), tax_amount, total,
  status (draft | sent | paid | overdue),
  issued_at, due_at (nullable), paid_at (nullable), notes (nullable)

InvoiceLineItem
  id, invoice_id, description, hours, rate, amount
```

### 6.3 API Surface (v1)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/auth/login` | Username + password → JWT |
| POST | `/v1/auth/refresh` | Refresh access token |
| GET | `/v1/contracts` | List contracts for current user |
| POST | `/v1/sessions` | Start a work session |
| PATCH | `/v1/sessions/{id}` | Pause / stop a session |
| POST | `/v1/windows` | Submit a completed time window |
| POST | `/v1/screenshots` | Upload a screenshot (multipart) |
| DELETE | `/v1/screenshots/{id}` | Worker deletes screenshot (grace period) |
| GET | `/v1/contracts/{id}/windows` | Worker reviews their own windows |
| GET | `/v1/screenshots/{id}/image` | Serve screenshot image (worker) |
| PATCH | `/v1/windows/{id}/dispute/resolve` | Worker accepts or rejects a dispute |
| POST | `/v1/invoices` | Create a draft invoice for a date range |
| GET | `/v1/invoices` | List invoices |
| PATCH | `/v1/invoices/{id}` | Update invoice status (sent, paid) |
| GET | `/v1/invoices/{id}/pdf` | Download PDF |
| — | — | — |
| GET | `/share/{token}` | Client: live view of contract (no auth) |
| GET | `/share/{token}/screenshots/{id}` | Client: full-size screenshot |
| PATCH | `/share/{token}/windows/{id}/dispute` | Client: dispute a time window |

---

## 7. Web Dashboard

### 7.1 Technology Stack

| Concern | Choice |
|---------|--------|
| Language | TypeScript |
| Framework | React 18 + Vite |
| UI library | shadcn/ui + Tailwind CSS |
| State | Zustand |
| Data fetching | TanStack Query |
| Charts | Recharts |

### 7.2 Views

#### Worker Dashboard
- Current session timer with live activity bar.
- Recent screenshots (blurred by default, click to preview).
- Weekly hours summary vs. contract limit.
- History of time windows with activity levels; disputed windows highlighted.
- Accept / reject dispute actions on flagged windows.
- Invoice management: create draft, view history, download PDF, mark as sent / paid.
- Copy shareable client link button (regenerate token to revoke).

#### Client Shared View (no login — accessed via `/share/{token}`)
- Live feed of work sessions, auto-refreshing every 60 seconds; "last updated X min ago" indicator.
- Timeline of time windows with date, duration, and activity level badge.
- Screenshot thumbnails (blurred); click to view full size.
- Total billable hours (excluding deleted and accepted-dispute windows).
- **Dispute button** on each window: client adds an optional note and submits; worker is notified by email.
- Disputed windows show a yellow ⚠ badge; resolved disputes show green ✓ (accepted) or grey ✗ (rejected).

#### Admin Panel
- User management (invite, deactivate).
- Organization and contract management.
- Audit log viewer.

---

## 8. Activity Tracking Details

### 8.1 Keyboard Tracking
- Count total keystrokes per 60-second sample.
- Do not record which keys were pressed.
- Do not record key combinations or shortcuts.

### 8.2 Mouse Tracking
- Count left / right / middle clicks per sample.
- Compute total mouse movement distance in pixels per sample.
- Do not record cursor absolute position or trajectory.

### 8.3 Activity Level Calculation

The scale factor is **fixed** (not auto-calibrated):

```
activity_level = min(10, round((keystrokes + clicks * 5) / SCALE_FACTOR))
```

`SCALE_FACTOR` is a single constant calibrated so that normal coding/writing activity produces a level of 6–8. It is set at the application level and not adjustable per worker or organization.

**Manual override:** a worker can bypass the activity level for any window by marking it as "manual" (see §5.2.1). The override reason is recorded and visible to the client. Typical bypass scenarios include:
- Attending a video call or meeting.
- Watching a tutorial, documentation video, or screen-share.
- Reading long documents with minimal interaction.

### 8.4 Idle Detection

After **5 consecutive minutes** of zero keyboard and mouse activity during an active session, the agent displays a prompt:

> *"No activity detected for 5 minutes. Are you still working?"*
> **[Yes, keep tracking]** | **[Pause]**

- If the worker confirms, tracking continues normally and the low-activity period is included in the current window (it will register a low activity score unless a manual override is applied).
- If the worker clicks Pause, or dismisses the prompt without responding within 2 minutes, the session is auto-paused and the idle period is excluded from billable time.
- The idle threshold (default 5 min) is configurable in Preferences.

---

## 9. Invoicing

### 9.1 Invoice Generation Flow
1. Worker selects a contract and a date range (e.g., "1 Nov – 30 Nov 2026").
2. System calculates billable hours: all `submitted` windows in that range, **excluding** `deleted` and `accepted_dispute` windows.
3. A single summary line item is generated: *"November 2026 — 60 hrs @ $X/hr"*.
4. Worker reviews the draft: total hours, rate, subtotal, optional tax, optional notes.
5. Worker clicks **Download PDF** — a formatted PDF is generated server-side and returned.
6. Worker emails the PDF to the client manually.
7. Worker marks the invoice as **Sent**, then later **Paid** when payment is received.

### 9.2 PDF Content
The generated PDF includes:

| Section | Content |
|---|---|
| Header | Freelancer name / company, logo (if set), invoice number, issue date, due date |
| Bill To | Client name, company, billing address |
| Line Item | Period description, total hours, hourly rate, amount |
| Totals | Subtotal, tax (if rate > 0), **Total** |
| Footer | Payment instructions (bank details, PayPal link, etc.) |
| Appendix | Link to the shareable tracker page for the same period |

### 9.3 Invoice Numbering
Auto-incremented per freelancer profile: `INV-0001`, `INV-0002`, … Prefix is configurable in Freelancer Profile settings.

### 9.4 Tax Handling
- `tax_rate` defaults to `0` (no tax).
- Worker can set a tax rate (e.g., `20` for 20% VAT) on the draft before downloading.
- Tax label (e.g., "VAT", "GST") is configurable in Freelancer Profile settings.
- No automatic jurisdiction-based tax calculation.

### 9.5 Invoice Statuses
```
Draft → Sent → Paid
              └→ Overdue  (due_at is set and today > due_at and status is still Sent)
```
Overdue is computed on read; it is not stored as a separate status transition.

---

## 10. Offline Behavior

1. Agent continues tracking and stores everything locally.
2. Sync attempts every 5 minutes with exponential back-off.
3. Local SQLite + spool directory retains up to 72 hours of unsynced data.
4. After 72 hours without sync, the agent warns the user and pauses tracking.
5. On reconnect, all buffered data is uploaded in chronological order.

---

## 11. Privacy & Compliance Considerations

- Workers must explicitly consent before tracking starts (shown at first run and each new contract).
- Screenshots are blurred in thumbnail view on the dashboard by default; client must click to view full size (audit-logged).
- Personal data retention policy: configurable per organization (default 1 year), with automated purge.
- GDPR: workers can request data export and deletion.
- Screenshots of sensitive applications (e.g., password managers) can be blurred via an application blocklist (v2 feature).

---

## 12. Phased Delivery

### Phase 1 — MVP (self-hosted: Windows agent + API + basic dashboard)
- [ ] Desktop agent: session control, screenshots, activity sampling, manual override, idle-detection prompt, sync
- [ ] Backend: auth, contracts, windows, screenshots API, shareable link, dispute flow — Docker Compose deployment
- [ ] Dashboard: worker view + client shareable live view
- [ ] Invoicing: draft, PDF download, sent/paid tracking

### Phase 2 — Cross-platform & polish
- [ ] macOS and Linux agent support
- [ ] Screenshot deletion grace period UI
- [ ] Admin panel
- [ ] CSV export of hours + activity

### Phase 3 — Advanced features
- [ ] Application blocklist (blur sensitive apps in screenshots)
- [ ] Multiple monitor support
- [ ] Real-time activity push (WebSocket)
- [ ] Mobile companion app (view-only)
- [ ] Multi-tenant mode: allow multiple independent freelancers to self-register and use the same hosted instance

---

## 13. Decisions Log

| # | Question | Decision |
|---|----------|----------|
| 1 | Self-hosted vs. SaaS? | **Self-hosted.** Docker Compose on a VPS. Multi-tenant SaaS is a Phase 3 goal. |
| 2 | Screenshot resolution? | **Keep default** (max 1280 × 800). |
| 3 | Activity level scale factor? | **Fixed** constant. Workers can bypass via manual override with a required reason. |
| 4 | Idle detection behavior? | **Prompt** after 5 min of zero activity. Auto-pause if no response within 2 min. Configurable. |
| 5 | Code signing? | **Windows Authenticode only.** macOS notarization deferred. |
| 6 | Client access model? | **Shareable read-only link** (`/share/{token}`). No client login required for v1. |
| 7 | Client dispute deadline? | **Open-ended.** Client can dispute any window at any time. |
| 8 | Invoice delivery? | **PDF download only.** Worker emails it manually. |
| 9 | Invoice line items? | **One summary line** per invoice (e.g., "November 2026 — 60 hrs @ $X/hr"). |
| 10 | Invoice tax? | **Optional.** `tax_rate` defaults to 0; worker sets it manually per invoice. |
