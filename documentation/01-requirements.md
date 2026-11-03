# ReelScope — Phase 1: Requirements & System Design

> **Status:** Design proposal — awaiting approval before implementation.
> **Project:** ReelScope — Smart Movie Feedback Collection and Analysis System
> **Phase:** 1 of 5 (Requirements and System Design)

---

## 1. Purpose of this document

This document explains **what ReelScope will do, who uses it, and how it is
organised**, in plain English. It contains no application code. Its job is to
agree on the design before we build anything, so we do not waste work later.

Read this together with `02-data-model-and-architecture.md`.

---

## 2. Project summary

ReelScope is a movie platform where visitors can:

1. Browse a catalogue of movies.
2. Open a movie and submit a **star rating (1–5)** plus **written feedback**.
3. Receive a **unique Tracking ID** by email.
4. Use that Tracking ID later to see their own submission and its automatic
   **sentiment analysis** — without creating an account.

Admins get a private dashboard with real audience intelligence: average
ratings, positive/negative/neutral counts, common praise, common complaints,
and charts built from real database records.

**Important honesty note:** sentiment analysis is a best-effort estimate. VADER
and keyword rules handle sarcasm, irony and movie-specific slang imperfectly.
We will test and report measured accuracy in Phase 5 and never present results
as 100% correct.

---

## 3. Goals and non-goals

### Goals

| # | Goal |
|---|------|
| G1 | Let anyone submit movie feedback in under a minute, without registering. |
| G2 | Automatically analyse every feedback message and store the result. |
| G3 | Give visitors a private, trackable receipt (Tracking ID) for their submission. |
| G4 | Give admins real, database-derived analytics and Chart.js visualisations. |
| G5 | Keep visitor data private (no email exposure, no browsing others' feedback). |
| G6 | Teach good structure: thin views, service layer, Django ORM, tests. |

### Non-goals (out of scope for this build)

- Public user reviews shown to other visitors.
- Editing feedback after submission (explicitly forbidden by the brief).
- Social login (Google/Facebook), payments, or mobile apps.
- Frontend frameworks (React/Vue) or REST frameworks (DRF).
- Machine-learning model training (we use an existing NLP library + rules).
- Multi-language sentiment analysis (English only in this version).

---

## 4. Users and permissions

There are three roles. **Feedback authorship is always anonymous in terms of
accounts** — a visitor does not need to log in, and registered accounts are
never linked to feedback rows.

### 4.1 Public Visitor (no account)

Can: browse movies, view movie details, submit feedback, receive a Tracking ID
by email, look up their own feedback with that ID.

Cannot: see other visitors' feedback, see any email addresses, edit/delete
feedback, access admin pages.

### 4.2 Registered User (verified account)

Can: everything a visitor can, plus log in to a simple account page.

Registered accounts exist **separately** from feedback. Creating an account is
optional and never required to submit feedback. The account's only purpose in
this version is identity/verification practice and a future "my activity"
feature; no feedback rows are attached to it.

### 4.3 Admin (staff)

Can: log in to the staff area, add/edit/delete movies, view all feedback per
movie, see average ratings and sentiment counts, inspect common positive
aspects and negative complaints, view charts and movie-wise analytics,
re-run failed sentiment analysis, and retry failed tracking-ID emails.

Admin accounts are created with `createsuperuser` (or promoted with
`is_staff=True`). They are **not** created through public registration.

### Permission matrix

| Capability | Visitor | Registered | Admin |
|---|:--:|:--:|:--:|
| Browse movies / details | ✅ | ✅ | ✅ |
| Submit feedback | ✅ | ✅ | ✅ |
| Track feedback by ID | ✅ | ✅ | ✅ |
| Register / verify email | ✅ | — | — |
| Log in to account area | — | ✅ | ✅ |
| Staff dashboard | — | — | ✅ |
| Manage movies (CRUD) | — | — | ✅ |
| View all feedback | — | — | ✅ |
| Retry failed analysis / email | — | — | ✅ |

---

## 5. Functional requirements

Requirement IDs are used later in tests (Phase 5).

### Module 1 — Movie management (admin)

| ID | Requirement |
|---|---|
| FR-1.1 | Admin can add a movie with title, poster image, description, genre, release date, director, cast, language. |
| FR-1.2 | Admin can list, search and edit any movie. |
| FR-1.3 | Admin can delete a movie, with a confirmation screen that warns how much feedback will also be deleted. |
| FR-1.4 | Poster uploads are validated (file type JPEG/PNG/WebP, max 5 MB) and stored under `media/posters/`. |
| FR-1.5 | Movie URLs are human-readable slugs generated from the title, kept unique. |

### Module 2 — Movie browsing (public)

| ID | Requirement |
|---|---|
| FR-2.1 | Home page shows a cinematic hero, the latest movies and top-rated movies. |
| FR-2.2 | Explore page lists movie cards (poster, title, genre, year, average rating) with pagination. |
| FR-2.3 | Movie detail page shows full metadata, average rating, rating count and recent feedback **without emails**. |
| FR-2.4 | Only the movie's title/metadata plus analysis themes are public; no personal data is ever shown. |

### Module 3 — Feedback submission (public)

| ID | Requirement |
|---|---|
| FR-3.1 | Form collects username, email, star rating (1–5), and written feedback. |
| FR-3.2 | No login and no email verification are required to submit. |
| FR-3.3 | Server-side validation is mandatory (never trust the browser): valid email, rating in 1–5, message length 10–2000 characters. |
| FR-3.4 | Multiple submissions for the same movie are allowed; each is stored as a separate row. |
| FR-3.5 | Submitted feedback cannot be edited or deleted by visitors. |
| FR-3.6 | Basic spam protection: hidden honeypot field, minimum time-on-form, and per-IP rate limiting. |
| FR-3.7 | On success, the visitor sees a confirmation page with their Tracking ID and movie title. |

### Module 4 — Tracking ID generation & email

| ID | Requirement |
|---|---|
| FR-4.1 | Every submission gets its own unique Tracking ID in the form `RS-2026-A8K92`. |
| FR-4.2 | IDs are generated with a cryptographically secure random source (`secrets`), not sequential numbers. |
| FR-4.3 | The alphabet excludes confusing characters (no `O/0`, `I/1`), giving 32⁵ ≈ 33.5 million combinations per year. |
| FR-4.4 | Uniqueness is enforced by a database `UNIQUE` constraint and a retry loop on collision. |
| FR-4.5 | The Tracking ID is emailed to the visitor's address. |
| FR-4.6 | If email sending fails, the feedback is **still saved** and the ID is shown on the confirmation page; the failure is logged and visible to admins. |

### Module 5 — Automatic sentiment analysis

| ID | Requirement |
|---|---|
| FR-5.1 | Analysis runs automatically after each submission. |
| FR-5.2 | Overall text sentiment is classified as Positive, Neutral or Negative, with a numeric confidence score. |
| FR-5.3 | Star rating and written-text sentiment are analysed **separately**, and a "mismatch" flag is stored when they disagree. |
| FR-5.4 | Positive aspects (e.g. storyline, acting, cinematography, music, direction, VFX) are extracted from the text. |
| FR-5.5 | Negative aspects (e.g. slow pacing, weak story, poor acting, long duration, weak characters) are extracted from the text. |
| FR-5.6 | Aspect names are **not a fixed list**; the vocabulary is extensible and unmatched topics are ignored rather than invented. |
| FR-5.7 | Feedback is saved even if analysis crashes or times out. |
| FR-5.8 | A failed or pending analysis can be retried by an admin without re-submitting the feedback. |
| FR-5.9 | Analysis results are stored in SQLite. |
| FR-5.10 | Accuracy is evaluated with a hand-labelled test set; results are reported, never claimed as 100%. |

### Module 6 — Feedback tracking (public)

| ID | Requirement |
|---|---|
| FR-6.1 | A dedicated Track Feedback page accepts a Tracking ID. |
| FR-6.2 | A valid ID displays: Tracking ID, movie title, username, submission date, star rating, written feedback, submission status, sentiment result, positive aspects, negative aspects. |
| FR-6.3 | The page never displays an email address. |
| FR-6.4 | Invalid IDs produce a generic "not found" message that does not reveal whether an ID nearly matched. |
| FR-6.5 | Tracking lookups are rate-limited to slow down guessing. |
| FR-6.6 | Query strings in links are avoided (ID is submitted by POST) so the secret ID does not sit in browser history or server logs. |

### Module 7 — Admin analytics dashboard

| ID | Requirement |
|---|---|
| FR-7.1 | Dashboard shows total movies, total feedback, overall average rating, and positive/negative/neutral counts. |
| FR-7.2 | Every figure is computed from database records at request time — nothing hardcoded. |
| FR-7.3 | Per-movie view shows average rating, feedback count, sentiment distribution, common positive aspects and common complaints. |
| FR-7.4 | Chart.js renders: pie chart (sentiment split), bar chart (movie-wise average rating), bar chart (positive vs negative counts), line chart (feedback trend over time). |
| FR-7.5 | Charts read JSON from small Django endpoints, so they update as the database changes. |
| FR-7.6 | Dashboard and chart data are staff-only and return 404/403 for everyone else. |

### Module 8 — Accounts & email verification

| ID | Requirement |
|---|---|
| FR-8.1 | Visitors can register with username, email and password. |
| FR-8.2 | Passwords are hashed by Django (`PBKDF2` by default); plain passwords are never stored. |
| FR-8.3 | Registration sends a verification link containing a signed, expiring token. |
| FR-8.4 | Accounts are inactive until the link is used; inactive users cannot log in. |
| FR-8.5 | Verification links expire after 24 hours and can be used once. |
| FR-8.6 | Verification result page clearly reports success, already-verified, or expired-link states. |
| FR-8.7 | Email addresses are unique across accounts. |
| FR-8.8 | No feedback or tracking data is attached to registered accounts. |

---

## 6. Non-functional requirements

| Area | Requirement |
|---|---|
| **Security** | CSRF protection on all forms; server-side validation; hashed passwords; staff-only admin views; secret key and SMTP credentials in `.env`; `.env` git-ignored. |
| **Privacy** | Emails never rendered publicly; tracking requires the secret ID; analytics shows aggregates, not identities. |
| **Performance** | Movie list and dashboards use `select_related`/`annotate` to avoid N+1 queries; pagination on listings; dashboard queries target < 500 ms on SQLite with a few thousand rows. |
| **Usability** | Responsive from 360 px phones to desktop; keyboard-accessible forms; clear error messages; loading states on AJAX actions. |
| **Accessibility** | Semantic HTML, labels tied to inputs, visible focus states, colour-independent sentiment labels (text + icon), chart summaries in text. |
| **Maintainability** | Thin views; business logic in `services.py`; templates per app; small helper functions; English code comments. |
| **Reliability** | Analysis and email failures never lose the feedback row; failures are recorded and retryable. |
| **Testing** | Automated Django tests for permissions, validation, tracking, ID uniqueness, failure handling, analytics correctness, plus a sentiment evaluation script. |

---

## 7. Assumptions and open decisions

These are design choices I recommend. Each is open to change before Phase 2.

1. **VADER over TextBlob.** VADER is already installed, is tuned for short
   informal text and social-style opinions, and gives a compound score. TextBlob
   is polarity-only and weaker on slang. We will still use TextBlob optionally
   in evaluation if you want a comparison, but VADER is the production engine.
2. **Aspect extraction is rule-based** on top of VADER (keyword groups +
   sentence-level polarity + negation handling), not a trained ML model. This is
   appropriate for a beginner project and is explainable; its limits will be
   documented.
3. **Anonymous feedback stores name + email on the feedback row**, not as a
   user account. Registered accounts stay separate, as the brief requires.
4. **Admin uses Django staff auth**, with a custom-branded `/staff/` area.
   Django's built-in `/django-admin/` remains available as a low-level backup
   unless you prefer it disabled.
5. **Genre** is a choice field (Action, Comedy, Drama, Sci-Fi, Thriller, Horror,
   Romance, Animation, Documentary) rather than a separate Genre table. Simpler
   for now; can be normalised later.
6. **Tracking lookup is POST-only** to keep secret IDs out of URLs and logs.
7. **Images** require `Pillow` (not yet installed). We will add it in Phase 2.
8. **Email in development** uses Django's console backend so the flow is
   testable without real SMTP credentials; real SMTP is enabled through `.env`.

---

## 8. Phase plan (what happens next)

| Phase | Deliverable | Code? |
|---|---|---|
| 0 ✅ | Project inspection report | No |
| 1 (this) | Requirements + data model + architecture + URL map | Docs only |
| 2 | Project skeleton, apps, models, migrations, settings, git init | Yes |
| 3 | Templates, CSS, vanilla JS, charts, responsive cinematic UI | Yes |
| 4 | Submission flow, tracking, email, sentiment service, admin CRUD, analytics | Yes |
| 5 | Tests, sentiment evaluation report, polish, run instructions | Yes |

No implementation starts until you approve Phase 1.
