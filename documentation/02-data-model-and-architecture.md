# ReelScope — Phase 1 (Part 2): Data Model & Technical Architecture

> **Status:** Design proposal — awaiting approval before implementation.
> Read `01-requirements.md` first.

---

## 1. Big picture (plain English)

ReelScope is a classic **server-rendered Django application**:

```
Browser
  ├── HTML pages (Django templates)
  ├── CSS (one stylesheet + small page styles)
  └── Vanilla JS (fetch calls for charts + rating widget)
        │
        ▼
Django
  ├── urls.py        → which page handles which address
  ├── views.py       → receive request, call services, choose a template
  ├── forms.py       → validate user input
  ├── services.py    → real business logic (tracking IDs, sentiment, email, stats)
  └── models.py      → database tables via the Django ORM
        │
        ▼
SQLite database (db.sqlite3)  +  media/posters/ (uploaded images)
```

**Why this split matters:** views stay short and readable; services are reusable
and testable (a retry button and a fresh submission call the same function);
models describe data only.

We use **no REST framework**. For charts, three tiny JSON views return
aggregates with `JsonResponse`. That is enough for Chart.js and keeps the
project beginner-friendly.

---

## 2. Proposed folder structure

```
ReelScope/
├── manage.py
├── requirements.txt
├── .env                      # local secrets (never committed)
├── .env.example              # documented variable names, no values
├── .gitignore
├── README.md
│
├── reelscope/                # project package (settings, root URLs)
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── movies/                   # Movie model, browsing + admin CRUD
│   ├── models.py
│   ├── forms.py
│   ├── views.py              # public + staff movie views
│   ├── admin_views.py        # (optional split) staff CRUD
│   ├── urls.py
│   └── services.py
│
├── feedback/                 # Feedback + SentimentAnalysis models and flow
│   ├── models.py
│   ├── forms.py
│   ├── views.py              # submit, success, track
│   ├── services/
│   │   ├── tracking.py       # Tracking ID generation
│   │   ├── sentiment.py      # VADER + aspect extraction
│   │   └── notifications.py  # tracking-ID email
│   ├── urls.py
│   └── tests.py
│
├── accounts/                 # registration, verification, login
│   ├── models.py             # EmailVerification
│   ├── forms.py
│   ├── views.py
│   ├── services.py           # token creation + verification email
│   └── urls.py
│
├── analytics/                # staff dashboard + chart JSON endpoints
│   ├── services.py           # all ORM aggregation queries
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── partials/             # nav, footer, movie card, star rating, messages
│   ├── movies/
│   │   ├── list.html
│   │   └── detail.html
│   ├── feedback/
│   │   ├── submit.html
│   │   ├── success.html
│   │   └── track.html
│   ├── accounts/
│   │   ├── register.html
│   │   ├── login.html
│   │   └── verify_result.html
│   └── staff/
│       ├── base_staff.html
│       ├── dashboard.html
│       ├── movie_list.html
│       ├── movie_form.html
│       ├── movie_confirm_delete.html
│       ├── movie_feedback.html
│       └── movie_analytics.html
│
├── static/
│   ├── css/style.css
│   ├── js/
│   │   ├── main.js           # nav, toasts, form helpers
│   │   ├── rating.js         # accessible star input
│   │   └── charts.js         # Chart.js dashboards
│   └── images/
│
├── media/
│   └── posters/
│
├── documentation/
│   ├── 01-requirements.md
│   ├── 02-data-model-and-architecture.md
│   └── (Phase 5) 03-testing-and-sentiment-evaluation.md
│
└── .venv/                    # local virtual environment (ignored)
```

**Two improvements over the brief, explained:**

1. `feedback/services/` instead of one `services.py` — tracking, sentiment and
   email are genuinely separate concerns; splitting keeps each file small and
   easy to read. If you prefer a single file, it can be flattened.
2. `staff/` templates live under `templates/staff/` (not `templates/admin/`)
   to avoid confusion with Django's built-in admin templates.

> Note: `accounts` uses Django's built-in `User` model (no custom user model),
> because registered accounts are independent of feedback. This keeps auth
> simple and reliable.

---

## 3. Database design

### 3.1 ERD (text diagram)

```
┌─────────────────────┐
│ Movie               │
│---------------------│
│ id (PK)             │
│ title               │
│ slug (unique)       │
│ description         │
│ poster              │
│ genre               │
│ release_date        │
│ director            │
│ cast                │
│ language            │
│ created_at          │
└─────────┬───────────┘
          │ 1
          │
          │ N
┌─────────▼───────────┐          ┌───────────────────────┐
│ Feedback            │ 1      1 │ SentimentAnalysis     │
│---------------------│──────────│-----------------------│
│ id (PK)             │          │ id (PK)               │
│ movie_id (FK)       │          │ feedback_id (FK,uniq) │
│ username            │          │ text_sentiment        │
│ email               │          │ text_score            │
│ rating (1–5)        │          │ rating_sentiment      │
│ message             │          │ is_mismatch           │
│ tracking_id (uniq)  │          │ positive_aspects JSON │
│ status              │          │ negative_aspects JSON │
│ email_sent_at       │          │ status                │
│ created_at          │          │ error_message         │
│                     │          │ attempts              │
│                     │          │ analyzed_at           │
└─────────────────────┘          └───────────────────────┘

┌─────────────────────┐
│ User (Django)       │ 1      1 ┌──────────────────────┐
│ id, username,       │──────────│ EmailVerification    │
│ email, password,    │          │ id (PK)              │
│ is_active, is_staff │          │ user_id (FK, unique) │
└─────────────────────┘          │ token (unique)       │
                                 │ created_at           │
                                 │ expires_at           │
                                 │ used_at (nullable)   │
                                 └──────────────────────┘
```

### 3.2 `Movie` (app: `movies`)

| Field | Type | Rules |
|---|---|---|
| `title` | CharField(200) | required |
| `slug` | SlugField(200) | unique, auto-generated from title, collision-safe |
| `description` | TextField | required, 30–3000 chars |
| `poster` | ImageField | `upload_to="posters/"`, JPEG/PNG/WebP, ≤ 5 MB |
| `genre` | CharField(20, choices) | Action, Comedy, Drama, Sci-Fi, Thriller, Horror, Romance, Animation, Documentary |
| `release_date` | DateField | cannot be in the future |
| `director` | CharField(150) | required |
| `cast` | TextField | comma-separated names, required |
| `language` | CharField(50) | required |
| `created_at` / `updated_at` | DateTime | automatic |
| `average_rating` | computed | `Avg("feedback__rating")`, never stored (avoids stale data) |

Deleting a movie cascades to its feedback and analyses. The confirmation page
shows the count first.

### 3.3 `Feedback` (app: `feedback`)

| Field | Type | Rules |
|---|---|---|
| `movie` | FK → Movie | `on_delete=CASCADE`, `related_name="feedback"` |
| `username` | CharField(100) | 2–100 chars, required |
| `email` | EmailField | required, **never shown publicly** |
| `rating` | PositiveSmallIntegerField | validator: 1–5 |
| `message` | TextField | 10–2000 chars |
| `tracking_id` | CharField(16) | unique, indexed, format `RS-YYYY-XXXXX` |
| `email_sent_at` | DateTimeField(null) | set when the tracking email is sent |
| `created_at` | DateTimeField | auto, indexed (used for trend charts) |

`status` is **not duplicated** here; the submission status shown to visitors is
derived from the related `SentimentAnalysis.status` (see below). Indexes:
`tracking_id`, `created_at`, `movie`.

### 3.4 `SentimentAnalysis` (app: `feedback`)

| Field | Type | Rules |
|---|---|---|
| `feedback` | OneToOne → Feedback | `on_delete=CASCADE`, `related_name="analysis"` |
| `text_sentiment` | CharField(10, choices) | positive / neutral / negative |
| `text_score` | FloatField | VADER compound, −1.0 … 1.0 |
| `rating_sentiment` | CharField(10, choices) | 4–5 positive, 3 neutral, 1–2 negative |
| `is_mismatch` | BooleanField | true when text and stars disagree |
| `positive_aspects` | JSONField(list) | e.g. `["storyline", "acting"]` |
| `negative_aspects` | JSONField(list) | e.g. `["pacing", "character development"]` |
| `status` | CharField(10, choices) | pending / success / failed |
| `error_message` | TextField(blank) | technical reason for admin retry |
| `attempts` | PositiveSmallIntegerField | incremented per analysis run |
| `analyzed_at` | DateTimeField(null) | completion time |

**Why a separate table instead of fields on Feedback?**

- The feedback row is created and committed first. If the analyser crashes, the
  feedback is safe and the analysis row says `failed`. That directly satisfies
  "feedback must remain saved if analysis fails".
- Retrying updates only the analysis row — the visitor's original submission,
  tracking ID and timestamp are never touched.
- Status is in exactly one place, so it cannot contradict itself.

`rating_sentiment` is stored, not just computed, because dashboards filter and
count it (for example, "star ratings vs text sentiment mismatch" reports).

### 3.5 `EmailVerification` (app: `accounts`)

| Field | Type | Rules |
|---|---|---|
| `user` | OneToOne → User | `on_delete=CASCADE` |
| `token` | CharField(64) | unique, generated with `secrets.token_urlsafe(32)` |
| `created_at` | DateTimeField | auto |
| `expires_at` | DateTimeField | created + 24 hours |
| `used_at` | DateTimeField(null) | set on successful verification |

Registration creates a `User(is_active=False)` and the token in one transaction.
The verification view validates expiry and single use, then flips
`is_active=True`. Django's login form already refuses inactive users, so no
custom login rule is needed.

---

## 4. URL map (pages and endpoints)

### Public

| Method | URL | View | Template / response |
|---|---|---|---|
| GET | `/` | `home` | `home.html` |
| GET | `/movies/` | `movie_list` | `movies/list.html` (paginated, `?q=`, `?genre=`) |
| GET | `/movies/<slug>/` | `movie_detail` | `movies/detail.html` |
| GET/POST | `/movies/<slug>/feedback/` | `submit_feedback` | `feedback/submit.html` |
| GET | `/feedback/success/<tracking_id>/` | `feedback_success` | `feedback/success.html` |
| GET/POST | `/track/` | `track_feedback` | `feedback/track.html` |
| GET | `/about/` (optional) | `about` | static page |

### Accounts

| Method | URL | View |
|---|---|---|
| GET/POST | `/accounts/register/` | `register` |
| GET/POST | `/accounts/login/` | `login` |
| POST | `/accounts/logout/` | `logout` |
| GET | `/accounts/verify/<token>/` | `verify_email` (result page) |
| POST | `/accounts/verify/resend/` | `resend_verification` (optional) |

### Staff (all require `is_staff`; unauthorised users get 403 or login redirect)

| Method | URL | View |
|---|---|---|
| GET/POST | `/staff/login/` | staff login (redirects to dashboard) |
| GET | `/staff/` | dashboard |
| GET | `/staff/movies/` | manage movies (search, pagination) |
| GET/POST | `/staff/movies/add/` | add movie |
| GET/POST | `/staff/movies/<int:pk>/edit/` | edit movie |
| GET/POST | `/staff/movies/<int:pk>/delete/` | confirm delete |
| GET | `/staff/movies/<int:pk>/feedback/` | feedback table for one movie |
| GET | `/staff/movies/<int:pk>/analytics/` | movie-wise analytics + charts |
| POST | `/staff/feedback/<int:pk>/retry-analysis/` | retry sentiment analysis |
| POST | `/staff/feedback/<int:pk>/resend-email/` | retry tracking-ID email |

### Chart data (staff-only JSON)

| URL | Returns |
|---|---|
| `/staff/data/summary/` | totals, average rating, sentiment counts |
| `/staff/data/movies/` | `[{title, average_rating, feedback_count}]` |
| `/staff/data/sentiment-by-movie/` | positive/negative/neutral counts per movie |
| `/staff/data/trends/?days=30` | daily feedback counts, positive vs negative |

All values come from ORM aggregation with `Count`, `Avg`, `TruncDate`; nothing
is hardcoded.

---

## 5. Key workflows

### 5.1 Submit feedback

```
Visitor fills form
   → FeedbackForm.is_valid() (server-side)
   → spam checks (honeypot empty, form age > 3 s, rate limit OK)
   → generate tracking ID (retry on collision)
   → save Feedback (commit)
   → create SentimentAnalysis(status="pending")
   → send tracking email (on_commit; failures logged, not fatal)
   → run analysis service in the same request (fast, local)
       ├── success → update analysis row (sentiment, score, aspects)
       └── failure → mark analysis failed with error, feedback untouched
   → redirect to /feedback/success/<tracking_id>/
```

**Why the same request?** VADER is local and takes milliseconds, so no Celery
or background worker is needed. If analysis ever became slow, the pending row
already exists and a management command or retry button could process it later.
This is a deliberate simplicity trade-off for a beginner project.

### 5.2 Track feedback

```
POST /track/ with ID
  → normalise to uppercase, rate-limit
  → Feedback.objects.filter(tracking_id=...).first()
  → not found: generic error (no hint)
  → found: render all fields except email + analysis results
```

### 5.3 Register / verify

```
POST register → validate → User(is_active=False) + EmailVerification
              → send signed-token link (24 h expiry)
GET verify/<token> → valid & unused & unexpired?
                     → is_active=True, used_at=now → success page
                     → else → explained failure page
```

### 5.4 Admin analytics request

```
GET /staff/ → analytics.services.dashboard_context()
  → aggregate totals, sentiment counts, recent submissions
GET /staff/data/*.json → JsonResponse (fetch from charts.js)
```

---

## 6. Sentiment analysis design (the important part)

### 6.1 Overall sentiment

- Engine: **VADER** (`vaderSentiment`), already installed.
- Output: `compound` in −1.0…1.0.
- Mapping (VADER's recommended thresholds):
  - `>= 0.05` → **positive**
  - `<= -0.05` → **negative**
  - otherwise → **neutral**
- Star rating is mapped separately: 4–5 positive, 3 neutral, 1–2 negative.
- If the two disagree, `is_mismatch=True` and the dashboard reports the count.
  We do **not** overwrite either value — that would hide real disagreement.

### 6.2 Aspect extraction (rule-based)

VADER scores emotion, not topics. Aspects come from a curated, extensible
dictionary of keyword groups, for example:

| Aspect | Keywords (examples) |
|---|---|
| storyline | story, plot, script, writing, narrative, predictable, twist |
| acting | acting, actor, actress, performance, cast, chemistry |
| cinematography | cinematography, visuals, shots, camera, beautiful, frames |
| music | music, soundtrack, score, songs, sound |
| direction | direction, director, pacing, editing |
| visual effects | vfx, cgi, effects, animation |
| pacing | pacing, slow, dragged, boring, rushed, long |
| duration | runtime, duration, too long, three hours |
| character development | character, characters, shallow, depth, development |

Algorithm (per message):

1. Split the message into sentences, then clauses on `, but, however, although`.
2. Score each sentence with VADER.
3. Match aspect keywords per sentence (word-boundary matching, lowercase).
4. Assign an aspect to `positive_aspects` if the containing sentence is
   positive, or to `negative_aspects` if it is negative. Sentences that are
   neutral fall back to the overall sentiment.
5. De-duplicate and keep a stable order. Unmentioned aspects are never added.

**Limitations we will document honestly:** sarcasm ("great, another 3-hour
movie"), mixed opinions in one sentence, and unusual vocabulary can be
misclassified. Aspect extraction is keyword-driven, so it only understands
topics it knows about.

### 6.3 Evaluation plan (Phase 5)

- Hand-label 50 real feedback samples across the three classes and aspect tags.
- Measure accuracy and macro-F1 for overall sentiment; report per-class
  precision/recall and a confusion matrix.
- Report aspect precision on a smaller sample.
- Target: useful signal, not perfection. Any claim in the README will quote the
  measured numbers from this evaluation, not a guess.

### 6.4 Failure handling and retry

- Analysis runs inside `try/except Exception`.
- On failure: `status="failed"`, `error_message` recorded, `attempts += 1`,
  feedback row untouched.
- Admin sees a "Failed" badge and a **Retry analysis** button.
- Retry calls the same service with the stored message; on success the row
  transitions to `success`.

---

## 7. Email design

Two emails:

1. **Verification link** (accounts) — subject "Verify your ReelScope account",
   link `/accounts/verify/<token>/`, 24-hour expiry.
2. **Tracking ID receipt** (feedback) — subject "Your ReelScope feedback
   receipt", includes movie title, star rating and Tracking ID.

Configuration via environment variables loaded with `python-dotenv`:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | `True` locally, `False` in production |
| `EMAIL_HOST`, `EMAIL_PORT` | SMTP server |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP credentials |
| `EMAIL_USE_TLS` | usually `True` |
| `DEFAULT_FROM_EMAIL` | sender address |

Development behaviour: `EMAIL_BACKEND=console` prints emails to the terminal so
the whole flow is testable without credentials. Production switches to SMTP
through `.env` only. `.env` is git-ignored; `.env.example` documents the keys.

Sending happens with `transaction.on_commit` so a mail failure cannot roll back
a saved feedback row. Every send is wrapped in try/except and logged.

---

## 8. Spam protection and privacy measures

| Threat | Mitigation |
|---|---|
| Bots filling forms | Hidden honeypot field (must stay empty) + minimum 3 s form age via signed timestamp |
| Flooding submissions | Cache-based rate limit: `5 submissions / 10 min / IP` |
| Tracking-ID guessing | 33.5M combinations per year + 10 lookups / 10 min / IP + generic errors |
| Email harvesting | Emails never rendered in public templates or chart endpoints; excluded from admin feedback tables by default |
| XSS | Django template auto-escaping; no `safe` on user input |
| CSRF | `{% csrf_token %}` on every POST form + middleware |
| Secret leakage | `.env` ignored, no keys in JS, SMTP logs avoid credentials |
| Unauthorised admin access | `staff_member_required` on every staff view and JSON endpoint |
| Password theft | Django hashing, no custom password storage |

---

## 9. Testing strategy (Phase 5 preview)

**Automated (Django `TestCase`):**

- Movie slug uniqueness, future release date rejected, poster validation.
- Feedback validation: rating bounds, message length, email format.
- Tracking ID format, uniqueness under simulated collisions, unpredictability
  smoke check (not sequential).
- Feedback saved when the sentiment service raises; analysis marked failed.
- Retry flips failed → success.
- Tracking page: shows own data, hides email, rejects unknown IDs, rate-limits.
- Verification: valid/expired/reused tokens; inactive user cannot log in.
- Permissions: anonymous/registered blocked from all staff URLs and JSON.
- Analytics maths: seed known rows, assert exact averages/counts per movie.
- Chart endpoints return correct JSON shape.

**Manual/visual:** responsive checks at 360 px, 768 px, 1440 px; keyboard-only
navigation; chart readability.

**Sentiment quality:** labelled evaluation set with reported accuracy and
macro-F1 (never a 100% claim).

---

## 10. Dependencies to add in Phase 2

| Package | Why |
|---|---|
| Django 6.1.2 | already installed |
| `vaderSentiment` 3.3.2 | already installed |
| `Pillow` | required by Django `ImageField` for posters |
| `python-dotenv` | load `.env` securely into settings |

Optional: `TextBlob` (only if we decide to compare engines in evaluation).

---

## 11. Decisions I need you to confirm

1. Separate `SentimentAnalysis` table (recommended) vs fields directly on
   `Feedback`.
2. Genre as a fixed choice list vs a separate `Genre` table.
3. Tracking lookup by POST on `/track/` (recommended, keeps IDs out of URLs) vs
   a shareable `/track/<id>/` URL.
4. Keep Django's built-in `/django-admin/` enabled alongside the custom
   `/staff/` area (recommended), or disable it.
5. Use Django's default `User` model (recommended) rather than a custom user
   model.
6. VADER as the sentiment engine (recommended) with rule-based aspect
   extraction.

Once you approve these (or tell me what to change), Phase 2 will create the
project skeleton, models, migrations and settings — still no page design or
business logic.
