# showoff_finished_4review/CLAUDE.md

Single-file showcase viewer for the LCC + Strong's Numbers AI transfer results, with authenticated review system.

## How to Start

```bash
# 1. Regenerate data bundle (if output files changed)
cd llm_direct_sn_unv2lcc && python generate_manifest.py && cd ..
python3 -c "..." # re-run bundling (see data_bundle.json section below)

# 2. Start server (uses start_server.py with review API)
./showoff_finished_4review/start.sh

# 3. Open browser
open http://localhost:8989/showoff_finished_4review/
```

No build step, no npm, no dependencies. Uses `start_server.py` (repo root) which serves static files + review API.

### Remote sharing via ngrok

```bash
ngrok http 8989
# Share the https://xxx.ngrok-free.dev/showoff_finished_4review/ URL
```

**ngrok free-tier gotcha**: The free tier injects an interstitial page for every HTTP request. JavaScript `fetch()` calls get intercepted and receive HTML instead of JSON, causing `載入失敗`. The fix is the `ngrok-skip-browser-warning: 1` header on all fetch requests (already applied in `FETCH_OPTS` and `authFetchOpts()`).

### SMTP Setup (for email OTP)

Create `showoff_finished_4review/smtp_config.json` (gitignored):

```json
{
  "gmail_user": "your@gmail.com",
  "gmail_app_password": "xxxx xxxx xxxx xxxx",
  "admin_email": "your@gmail.com"
}
```

Get an App Password at https://myaccount.google.com/apppasswords. Without this file, OTP codes are printed to the server console instead of emailed.

### Pre-approving Reviewers

Create `showoff_finished_4review/reviewers.json` (gitignored):

```json
{
  "approved": [
    {"email": "colleague@example.com", "name": "王大明", "added": "2026-02-28"}
  ],
  "pending": []
}
```

Pre-approved emails can request OTP directly. Others trigger an approval email to the admin.

## Review System

### Authentication Flow

```
"Enter Review Mode" button → Auth modal
  → Enter name + email → POST /api/auth/request-access
    → If pre-approved: OTP sent to email
    → If not: approval email sent to admin with clickable link
      → Admin clicks link (GET /api/approve?email=x&token=y)
      → Reviewer auto-approved, OTP sent
  → Enter 6-digit OTP → POST /api/auth/verify-otp
    → Session token stored in localStorage (7-day expiry)
    → Review mode enabled (form visible, can submit reviews)
```

### Review Types

| Type | Badge Color | Use Case |
|------|-------------|----------|
| `comment` | Blue | General feedback |
| `suggestion` | Orange | Suggest a specific SN change |
| `approval` | Green | Mark verse as correct |
| `needs_work` | Red | Flag verse for revision |

### API Endpoints (in `start_server.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/request-access` | No | Request OTP (body: `{email, name}`) |
| GET | `/api/approve?email=x&token=y` | No | Admin approval link (returns HTML) |
| POST | `/api/auth/verify-otp` | No | Verify OTP (body: `{email, otp}`) → session token |
| GET | `/api/auth/status` | Bearer | Check session validity |
| GET | `/api/reviews?book=Gen&chap=1` | No | Fetch reviews for chapter (public read) |
| POST | `/api/reviews` | Bearer | Create review (body: `{book, chap, sec, type, text}`) |
| DELETE | `/api/reviews?id=r_xxx` | Bearer | Delete own review (or admin can delete any) |

### Server-side Storage (all gitignored)

| File | Purpose |
|------|---------|
| `smtp_config.json` | Gmail SMTP credentials |
| `reviewers.json` | Approved + pending reviewer emails |
| `reviews.json` | All review entries |
| `sessions.json` | Active session tokens |
| `otp_pending.json` | Pending OTP codes + approval tokens |

## Data Source

All verse data is pre-bundled in `data_bundle.json` (1.5 MB) so the viewer works without access to `../llm_direct_sn_unv2lcc/output/`.

Each verse JSON contains:

| Field | Purpose |
|-------|---------|
| `unv_sn_reference` | UNV text with Strong's Numbers (left panel) |
| `lcc_sn` | LCC text with AI-inserted Strong's Numbers (right panel) |
| `lcc_original` | Plain LCC text without SN (shown in italic below right panel verses) |
| `confidence` | 0.0–1.0 AI confidence score |
| `notes` | Array of AI reasoning strings |
| `model` | LLM model used (`sonnet` or `opus`) |

## Architecture — Single File `index.html`

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ header: title | stats | auth-btn/badge | lang-select     │
├─────────────────────────────────────────────────────────┤
│ controls: book-select | chap-select                      │
├───────────────────────────┬─────────────────────────────┤
│ left panel (50%)          │ right panel (50%)            │
│ UNV+SN reference          │ LCC+SN AI output             │
│                           │ + confidence + review badges │
├───────────────────────────┴─────────────────────────────┤
│ notes-panel: AI notes + reviews + review form            │
└─────────────────────────────────────────────────────────┘
│ auth-modal (overlay): email → OTP → session              │
```

### i18n System

Three languages: 正體中文 (default), English, 简体中文. Controlled by `I18N` object with `t(key)` accessor. Includes auth and review strings.

### Key Functions

| Function | Purpose |
|----------|---------|
| `init()` | Load bundle + books.json, check existing session, populate UI |
| `checkAuthStatus()` | Validate stored session token via `/api/auth/status` |
| `requestAccess()` | POST email/name to `/api/auth/request-access` |
| `verifyOTP()` | POST OTP to `/api/auth/verify-otp`, store session token |
| `updateAuthUI()` | Toggle auth button / reviewer badge / review form visibility |
| `fetchReviews(book, chap)` | GET `/api/reviews`, cache in `reviewCache` |
| `showVerseReviews(book, chap, sec)` | Render review entries for selected verse |
| `submitReview()` | POST review with Bearer token, update cache + UI |
| `updateVerseBadges()` | Add review count/status badges on right panel verses |
| `onChapChange()` | Load verses from bundle, fetch reviews, render badges |
| `renderVerses(data, book, chap)` | Build HTML for both panels |
| `parseSN(text)` | Regex pipeline: 4 SN formats → `<span class="sn">` elements |
| `attachSNHandlers()` | Hover = temporary highlight, Click = sticky highlight |
| `attachVerseClickHandlers(data)` | Click verse → show AI notes + reviews |

## Files

| File | Purpose |
|------|---------|
| `index.html` | Single-file viewer (HTML + CSS + JS) with auth + review UI |
| `data_bundle.json` | Pre-bundled manifest + all verse data (1.5 MB) |
| `start.sh` | Convenience launcher (`python3 start_server.py --port 8989`) |
| `CLAUDE.md` | This file |
