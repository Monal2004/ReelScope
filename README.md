# ReelScope — Smart Movie Feedback Collection and Analysis System

ReelScope is a Django-based web application that collects movie feedback from
visitors, performs automatic sentiment analysis on the written reviews, and
provides staff with a comprehensive analytics dashboard to understand audience
opinion.

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Main Features](#2-main-features)
3. [Technology Stack](#3-technology-stack)
4. [Project Folder Structure](#4-project-folder-structure)
5. [System Requirements](#5-system-requirements)
6. [Installation and Setup Guide — Windows](#6-installation-and-setup-guide--windows)
7. [Staff Account Creation Guide](#7-staff-account-creation-guide)
8. [Important Website URLs](#8-important-website-urls)
9. [How to Use ReelScope](#9-how-to-use-reelscope)
10. [Database Information](#10-database-information)
11. [Testing](#11-testing)
12. [Troubleshooting](#12-troubleshooting)
13. [Project Limitations and Future Improvements](#13-project-limitations-and-future-improvements)

---

## 1. Project Overview

### What ReelScope Is

ReelScope is a Smart Movie Feedback Collection and Analysis System. It is a
server-rendered Django web application that lets visitors browse a catalogue of
movies, submit star ratings and written feedback without creating an account,
and receive a unique Tracking ID to revisit their submission later.

Staff members can log in to a private dashboard to manage the movie catalogue
(add, edit, publish, unpublish, delete movies), view all submitted feedback,
see real-time sentiment analysis results, and explore movie rankings based on
audience appreciation.

### Why It Was Developed

ReelScope was developed to solve a common problem: collecting audience feedback
on movies and turning raw ratings and written reviews into clear, actionable
insights. Star ratings alone do not tell the whole story — a 5-star rating
with a comment like "the story was boring" reveals a mismatch between the
rating and the written opinion. ReelScope pairs every star rating with
automatic sentiment analysis to surface these insights.

### How Visitors Submit Movie Feedback

1. A visitor browses the public movie catalogue.
2. They select a movie and open its detail page.
3. They click "Rate this movie" to open the feedback form.
4. They enter their username, email address, a star rating (1–5), and a written
   feedback message.
5. They submit the form. No account or login is required.
6. The feedback is saved to the database, sentiment analysis runs
   automatically, and the visitor receives a unique Tracking ID (e.g.
   `RS-2026-A8K92`) on a confirmation page.

### How Sentiment Analysis Works

Every submitted feedback message is analysed using VADER (Valence Aware
Dictionary and sEntiment Reasoner), a lexicon-based sentiment analysis tool
tuned for English text. The analysis:

- Classifies the written feedback as Positive, Neutral, or Negative based on
  the VADER compound score (>= 0.05 = positive, <= -0.05 = negative,
  otherwise neutral).
- Classifies the star rating separately (4–5 stars = positive, 3 stars =
  neutral, 1–2 stars = negative).
- Detects mismatches when the written sentiment disagrees with the star rating
  (e.g. 5 stars but a negative written comment).
- Stores the result in a `SentimentAnalysis` record linked to the feedback.

If analysis fails, the feedback is still saved and the analysis record is
marked as "failed". Staff can retry failed analyses later.

### How Staff Use the Analytics Dashboard

Staff log in through the Login page and access the staff dashboard at
`/staff/`. The dashboard shows:

- Key performance indicators: total movies, total feedback, average rating,
  sentiment breakdown.
- Interactive charts: feedback trends, sentiment distribution, movie ratings,
  praise vs complaints.
- A movie ranking table showing audience appreciation scores.
- A list of recent feedback submissions.

Staff can also manage movies through `/staff/movies/` (add, edit, publish,
unpublish, delete).

---

## 2. Main Features

### Public Features

| Feature | Description |
|---------|-------------|
| Browse published movies | Visitors can see all published movies on the home page and movie listing page, with posters, titles, genres, languages, release dates, and average ratings. |
| View movie details | Each movie has a dedicated page showing full metadata (director, cast, description), average rating, feedback count, sentiment breakdown, and recent audience feedback. |
| Submit feedback without registration | No account or login is required. Visitors provide username, email, star rating (1–5), and a written message. |
| Receive a unique Tracking ID | Every submission gets a unique ID (format: `RS-YYYY-XXXXX`) shown on the confirmation page. |
| Track submitted feedback | Visitors can enter their Tracking ID at `/track/` to revisit their submission and see its sentiment result. |
| Submission confirmation page | After submitting, visitors see a confirmation page with their Tracking ID, movie title, rating, and a copy button. |

### Staff Features

| Feature | Description |
|---------|-------------|
| Secure staff login | Staff log in through `/accounts/login/`. Only users with staff status can access staff pages. |
| Add movies | Staff can add new movies with title, poster image, description, genre, release date, director, cast, and language. |
| Edit movies | Staff can edit any movie's details and replace its poster. |
| Delete movies | Staff can delete movies with a confirmation screen showing how many feedback submissions will also be removed. |
| Publish/unpublish movies | New movies are unpublished by default. Staff can toggle publication status so only published movies appear publicly. |
| View submitted feedback | Staff can see all feedback submissions with tracking ID, movie, username, rating, sentiment, and submission date. |
| View movie rankings | Staff see a ranked table of movies based on audience appreciation (ratings, sentiment, and feedback volume). |
| View rating and sentiment analytics | Charts and KPIs show rating distribution, sentiment split, feedback trends, and praise vs complaints. |
| Manage staff accounts | Staff accounts are created and managed through Django Admin at `/django-admin/`. |

> **Important:** Public staff registration is disabled. Staff accounts can only
> be created by an administrator through Django's superuser system or Django
> Admin. There is no public "Create account" or "Register" option on the
> website.

### Sentiment Analysis

- **Classification:** Written feedback is classified as Positive, Neutral, or Negative using VADER compound score thresholds (>= 0.05 positive, <= -0.05 negative, otherwise neutral).
- **Rating-based sentiment:** Star ratings are mapped separately: 4–5 stars = positive, 3 stars = neutral, 1–2 stars = negative.
- **Mismatch detection:** When text sentiment and rating sentiment disagree (e.g. 5 stars but negative written feedback), `is_mismatch` is flagged. Staff can see mismatch counts on the dashboard.
- **Failure handling:** If sentiment analysis fails, the feedback row is never lost. The analysis record is marked "failed" with an error message, and staff can retry it later using the `retry_failed_sentiment` management command.
- **Limitations:** VADER is primarily designed for English text. Malayalam and mixed-language feedback may not be classified accurately. Sarcasm, irony, and indirect opinions are not reliably detected. Results are best-effort estimates, not ground truth.

### Movie Ranking

The ranking system uses a transparent weighted formula. All values are
computed from live SQLite database records — nothing is hardcoded or stored
as a stale score.

**Formula:**

```
Final Score = (Rating Score × 0.50)
            + (Positive Sentiment Percentage × 0.30)
            + (Feedback Confidence × 0.20)
```

**Components:**

| Component | Formula | Range |
|-----------|---------|-------|
| Rating Score | (Average Rating / 5) × 100 | 0–100 |
| Positive Sentiment % | (Positive Analyzed Feedback / Total Analyzed Feedback) × 100 | 0–100 |
| Feedback Confidence | min(Feedback Count / 20, 1) × 100 | 0–100 |

**Thresholds:**

- `MIN_FEEDBACK_FOR_RANKING = 5`: A movie must have at least 5 feedback
  submissions to appear in the reliable ranking. Movies with fewer than 5
  submissions show an "Insufficient data" label.
- `CONFIDENCE_DENOMINATOR = 20`: Feedback confidence caps at 100% when a
  movie has 20 or more submissions.

**Example calculation** for a movie with 8 feedback submissions, average
rating 4.625, and 8 out of 8 successfully analysed as positive:

- Rating Score = (4.625 / 5) × 100 = 92.5
- Positive Sentiment % = (8 / 8) × 100 = 100.0
- Feedback Confidence = min(8 / 20, 1) × 100 = 40.0
- Final Score = (92.5 × 0.50) + (100.0 × 0.30) + (40.0 × 0.20)
  = 46.25 + 30.0 + 8.0 = **84.25**

---

## 3. Technology Stack

| Technology | Purpose |
|------------|---------|
| HTML5 | Semantic page structure for all public and staff pages. |
| CSS3 | Styling with a dark cinematic theme, responsive layouts, and modern typography (Inter + Bebas Neue). |
| JavaScript (Vanilla) | Interactive UI behaviour: mobile navigation, staff sidebar, star rating widget, character counter, copy-to-clipboard, and Chart.js integration. |
| Python 3 | Backend programming language. |
| Django 6.1.2 | Web framework handling routing, templates, forms, database ORM, authentication, and admin. |
| SQLite | File-based relational database (`db.sqlite3`). No separate database server required. |
| VADER (vaderSentiment) | Lexicon-based sentiment analysis for English text, producing compound scores in [-1.0, 1.0]. |
| Chart.js | Interactive charts for the staff dashboard (line, doughnut, bar charts). |

No Node.js, MongoDB, React, or external AI APIs are used or required.

---

## 4. Project Folder Structure

```
ReelScope/
├── manage.py                 # Django command-line utility
├── requirements.txt          # Python dependencies
├── .env                      # Local environment variables (not committed)
├── .env.example              # Documented environment variable template
├── .gitignore                # Git ignore rules
├── db.sqlite3                # SQLite database file
├── _verify_phase3.py         # Temporary verification script
│
├── accounts/                 # Staff authentication app
│   ├── models.py             # EmailVerification model
│   ├── forms.py              # RegisterForm (legacy, no longer used publicly)
│   ├── views.py              # Login, logout, register-redirect views
│   ├── urls.py               # /accounts/login/, /accounts/logout/, /accounts/register/
│   ├── admin.py              # EmailVerification admin registration
│   ├── migrations/
│   └── tests.py
│
├── analytics/                # Staff analytics dashboard app
│   ├── models.py             # (empty placeholder)
│   ├── views.py              # Dashboard, chart JSON endpoints (staff-only)
│   ├── urls.py               # /staff/, /staff/data/summary/, etc.
│   ├── admin.py
│   ├── services/
│   │   ├── __init__.py       # overall_stats, sentiment_breakdown, dashboard_context, chart functions
│   │   └── ranking.py        # Movie ranking service (weighted formula)
│   ├── migrations/
│   └── tests.py
│
├── feedback/                 # Feedback collection and sentiment analysis app
│   ├── models.py             # Feedback, SentimentAnalysis models
│   ├── forms.py              # FeedbackForm (username, email, rating, message)
│   ├── views.py              # Submit feedback, success page, tracking page
│   ├── urls.py               # /feedback/success/<tracking_id>/
│   ├── tracking.py           # Tracking ID generation (RS-YYYY-XXXXX)
│   ├── services/
│   │   ├── __init__.py
│   │   └── sentiment.py      # VADER sentiment analysis service + retry command
│   ├── management/
│   │   └── commands/
│   │       └── retry_failed_sentiment.py
│   ├── migrations/
│   └── tests.py
│
├── movies/                   # Movie catalogue app
│   ├── models.py             # Movie model (title, poster, genre, release_date, etc.)
│   ├── forms.py              # MovieForm (staff add/edit)
│   ├── views.py              # Public home/list/detail + staff movie CRUD
│   ├── urls.py               # Public movie URLs
│   ├── staff_urls.py         # Staff movie management URLs (/staff/movies/)
│   ├── validators.py         # Poster size and release date validators
│   ├── admin.py              # Movie admin registration
│   ├── migrations/
│   └── tests.py
│
├── reelscope/                # Django project configuration
│   ├── settings.py           # Django settings (loads .env, SQLite, email, etc.)
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── templates/                # HTML templates (shared and app-specific)
│   ├── base.html             # Base template with header, footer, messages
│   ├── home.html             # Public home page
│   ├── partials/             # Reusable template fragments (movie card, pagination, sentiment badge)
│   ├── movies/               # Public movie pages (list, detail)
│   ├── feedback/             # Feedback pages (submit, success, track)
│   ├── accounts/             # Auth pages (login, verify_result)
│   └── staff/                # Staff pages (base_staff, dashboard, movie CRUD)
│
├── static/                   # Static assets (CSS, JS, images)
│   ├── css/style.css         # Main stylesheet (dark cinematic theme, responsive)
│   ├── js/main.js            # Shared UI behaviour (nav, toasts, forms, stars)
│   ├── js/charts.js          # Chart.js dashboard charts
│   └── images/               # Logo and placeholder images
│
├── media/                    # User-uploaded files (movie posters)
│   └── posters/
│
├── documentation/            # Design documents
│   ├── 01-requirements.md
│   └── 02-data-model-and-architecture.md
│
├── .dist/                    # Build artifacts
├── .freebuff/                # Tooling artifacts
├── .venv/                    # Virtual environment (local, not committed)
└── .git/                     # Git version control
```

---

## 5. System Requirements

### Required Software

- **Python 3** — Compatible with Django 6.1.2 (Python 3.10+ recommended).
- **pip** — Python package installer (comes with Python).
- **A modern web browser** — Chrome, Firefox, Edge, or Safari for viewing the application.
- **VS Code** (recommended) — Code editor with Python extension.

### Not Required

- **Node.js** — Not used. No frontend build step.
- **MongoDB** — Not used. SQLite is the only database.
- **External AI APIs** — Not used. Sentiment analysis runs locally with VADER.

---

## 6. Installation and Setup Guide — Windows

Follow these steps to set up and run ReelScope on Windows.

### Step 1: Open the Project Folder

1. Open **File Explorer**.
2. Navigate to `C:\Users\Admin\Desktop\monal\ReelScope` (or wherever you cloned/copied the project).
3. Right-click inside the folder and select **Open with Code Editor** (or open VS Code and choose `File > Open Folder` and select this folder).

### Step 2: Open the Terminal

In VS Code:
1. Press `Ctrl + `` (backtick) or select **Terminal > New Terminal** from the menu.
2. A PowerShell terminal opens at the project root.

### Step 3: Create a Virtual Environment

```powershell
python -m venv venv
```

This creates a `venv/` folder containing an isolated Python environment.

### Step 4: Activate the Virtual Environment

```powershell
.\venv\Scripts\Activate
```

You will see `(venv)` at the start of your command prompt, indicating the virtual environment is active.

### Step 5: Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs Django 6.1.2, Pillow, python-dotenv, and vaderSentiment.

### Step 6: Configure Environment Variables

ReelScope loads secrets from a `.env` file in the project root. A template is provided at `.env.example`.

1. Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

2. Open `.env` in a text editor and update the values as needed:

```
DJANGO_SECRET_KEY=replace-with-a-long-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-address@example.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=ReelScope <no-reply@example.com>

EMAIL_VERIFICATION_HOURS=24
```

**Important:** Never commit `.env` to version control. It is listed in `.gitignore`. Do not expose real SMTP passwords or secret keys in `.env.example` or in the README.

For development, the console email backend prints emails to the terminal, so you can test the Tracking ID delivery flow without real SMTP credentials.

### Step 7: Apply Database Migrations

```powershell
python manage.py migrate
```

This creates or updates all SQLite database tables defined in the project's migrations. The database file `db.sqlite3` is created in the project root.

### Step 8: Create the First Superuser

```powershell
python manage.py createsuperuser
```

You will be prompted for:

- **Username:** Choose a staff username (e.g. `admin`).
- **Email:** Enter an email address (can be left blank for local development).
- **Password:** Enter a secure password. **The password will not be visible while typing** — this is normal terminal behaviour.

This superuser has full staff access and can log in to the website and Django Admin.

### Step 9: Run the Project

```powershell
python manage.py runserver
```

You should see output like:

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).

Django version 6.1.2, using settings 'reelscope.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Step 10: Open the Website

Open your browser and navigate to:

```
http://127.0.0.1:8000/
```

You will see the ReelScope home page with published movies (if any exist).

---

## 7. Staff Account Creation Guide

Public staff registration is **disabled**. Staff accounts must be created through Django's superuser/admin system.

### First Staff Account — Superuser

Run the createsuperuser command:

```powershell
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password. After creating the superuser:

1. Start the server: `python manage.py runserver`
2. Open `http://127.0.0.1:8000/accounts/login/`
3. Log in with your superuser credentials.
4. You can now access the staff dashboard at `http://127.0.0.1:8000/staff/`.

### Creating Additional Staff Accounts

1. Start the server and log in to Django Admin:
   `http://127.0.0.1:8000/django-admin/`
2. Use your superuser credentials.
3. In the Django Admin sidebar, click **Users** under the "Auth" section.
4. Click **Add User** in the top-right corner.
5. Enter the username and password for the new staff member.
6. Click **Save**.
7. Click on the newly created user's name to edit their details.
8. Under "Permissions", check the **Staff status** (`is_staff`) checkbox.
9. Assign any additional permissions as needed (e.g. "Can add movie", "Can change movie").
10. Click **Save**.

The new staff member can now log in at `http://127.0.0.1:8000/accounts/login/` and access staff pages.

> Public visitors cannot create staff accounts through the website. The registration page redirects to the login page with a message that public registration is disabled.

---

## 8. Important Website URLs

| URL | Page | Access |
|-----|------|--------|
| `/` | Home page | Public |
| `/movies/` | Movie listing (search, filter, paginate) | Public |
| `/movies/<slug>/` | Movie detail page | Public (published movies only) |
| `/movies/<slug>/feedback/` | Feedback submission form | Public |
| `/feedback/success/<tracking_id>/` | Feedback confirmation page | Public (owner with tracking ID) |
| `/track/` | Feedback tracking lookup | Public |
| `/accounts/login/` | Staff login | Public (login form) |
| `/accounts/logout/` | Logout | Authenticated users |
| `/accounts/register/` | Registration (disabled, redirects to login) | Redirects to login |
| `/staff/` | Staff dashboard | Staff only (`is_staff`) |
| `/staff/data/summary/` | Summary stats JSON | Staff only |
| `/staff/data/ratings/` | Movie ratings chart JSON | Staff only |
| `/staff/data/sentiment/` | Sentiment by movie JSON | Staff only |
| `/staff/data/trends/` | Feedback trends JSON | Staff only |
| `/staff/movies/` | Staff movie management list | Staff only |
| `/staff/movies/add/` | Add movie | Staff only |
| `/staff/movies/<pk>/edit/` | Edit movie | Staff only |
| `/staff/movies/<pk>/delete/` | Delete movie | Staff only |
| `/staff/movies/<pk>/toggle-publish/` | Publish/unpublish | Staff only |
| `/django-admin/` | Django Admin | Staff/superuser only |

---

## 9. How to Use ReelScope

### Visitor Workflow

1. **Open the home page** at `http://127.0.0.1:8000/`.
2. **Browse available movies** — published movies appear as cards with posters, titles, genres, and ratings.
3. **Select a movie** — click a movie card to view its details.
4. **Submit feedback** — click "Rate this movie" and enter your username, email, star rating (1–5), and written message. No account required.
5. **Receive the tracking ID** — after submission, you see a confirmation page with your unique Tracking ID (e.g. `RS-2026-A8K92`). Copy it or note it down.
6. **Track your submission** — go to `/track/`, enter your Tracking ID, and view your submission details and sentiment result.

### Staff Workflow

1. **Log in** at `http://127.0.0.1:8000/accounts/login/` using staff credentials.
2. **Open the dashboard** at `http://127.0.0.1:8000/staff/` to see KPIs, charts, and recent feedback.
3. **Add movies** — go to `/staff/movies/add/` and fill in the movie details.
4. **Publish movies** — new movies are unpublished by default. Toggle the "Publish publicly" checkbox or use the Publish button in the movie list.
5. **View feedback** — see all submissions in the dashboard's recent feedback panel or manage movies to see per-movie feedback.
6. **Review sentiment analysis** — check sentiment breakdown, mismatch counts, and per-movie sentiment data.
7. **View movie rankings** — see the ranked table of movies based on audience appreciation scores.

---

## 10. Database Information

### Database Type

ReelScope uses **SQLite**, a file-based relational database. The database file is stored at:

```
db.sqlite3
```

No separate database server (e.g. PostgreSQL, MySQL, MongoDB) is required or used.

### Main Database Models

#### Movie (`movies` app)

| Field | Type | Description |
|-------|------|-------------|
| `title` | CharField | Movie title |
| `slug` | SlugField | URL-friendly identifier (auto-generated) |
| `description` | TextField | Movie description |
| `poster` | ImageField | Movie poster image (uploaded to `media/posters/`) |
| `genre` | CharField (choices) | Action, Comedy, Drama, Sci-Fi, Thriller, Horror, Romance, Animation, Documentary |
| `release_date` | DateField | Release date (cannot be in the future) |
| `director` | CharField | Director name |
| `cast` | TextField | Comma-separated cast list |
| `language` | CharField | Movie language |
| `is_published` | BooleanField | Whether the movie is visible to public visitors (default: False) |
| `created_at`, `updated_at` | DateTimeField | Automatic timestamps |

#### Feedback (`feedback` app)

| Field | Type | Description |
|-------|------|-------------|
| `movie` | ForeignKey → Movie | The movie being reviewed |
| `username` | CharField | Visitor's name |
| `email` | EmailField | Visitor's email (never shown publicly) |
| `rating` | PositiveSmallIntegerField | Star rating (1–5) |
| `message` | TextField | Written feedback (10–2000 characters) |
| `tracking_id` | CharField | Unique ID (format: `RS-YYYY-XXXXX`) |
| `email_sent_at` | DateTimeField | When tracking email was sent |
| `created_at` | DateTimeField | Submission timestamp |

#### SentimentAnalysis (`feedback` app)

| Field | Type | Description |
|-------|------|-------------|
| `feedback` | OneToOneField → Feedback | Linked feedback record |
| `text_sentiment` | CharField | Positive / Neutral / Negative |
| `text_score` | FloatField | VADER compound score (−1.0 to 1.0) |
| `rating_sentiment` | CharField | Rating-based sentiment (Positive / Neutral / Negative) |
| `is_mismatch` | BooleanField | True when text and rating sentiment disagree |
| `positive_aspects` | JSONField | List of detected positive aspects |
| `negative_aspects` | JSONField | List of detected negative aspects |
| `status` | CharField | Pending / Success / Failed |
| `error_message` | TextField | Error message if analysis failed |
| `attempts` | PositiveSmallIntegerField | Number of analysis attempts |
| `analyzed_at` | DateTimeField | When analysis was completed |

#### EmailVerification (`accounts` app)

| Field | Type | Description |
|-------|------|-------------|
| `user` | OneToOneField → User | Linked Django user |
| `token` | CharField | Unique verification token |
| `created_at` | DateTimeField | Token creation time |
| `expires_at` | DateTimeField | Token expiry (24 hours by default) |
| `used_at` | DateTimeField | When token was used (nullable) |

### Relationships

- **Movie → Feedback:** One movie can have many feedback submissions (one-to-many, CASCADE delete).
- **Feedback → SentimentAnalysis:** One feedback has one sentiment analysis (one-to-one, CASCADE delete).
- **User → EmailVerification:** One user has one email verification record (one-to-one, CASCADE delete).

---

## 11. Testing

ReelScope uses Django's built-in test framework. Run the following commands from the project root (with the virtual environment activated):

### System Check

```powershell
python manage.py check
```

This verifies that Django's configuration, models, URLs, and database connections are valid. It does not require a database migration.

### Run Tests

```powershell
python manage.py test
```

This runs all test cases defined in the `tests.py` files of each Django app.

> **Note:** Currently, all `tests.py` files contain only stub imports (`from django.test import TestCase`) with no actual test cases. The test command will run 0 tests. Comprehensive automated tests should be added as part of future development.

---

## 12. Troubleshooting

### Python command not recognized

**Problem:** `python` is not recognised as a command.

**Solution:** Use `py` instead (Windows Python launcher):

```powershell
py -m venv venv
.\venv\Scripts\Activate
py -m pip install -r requirements.txt
py manage.py runserver
```

Or ensure Python is installed and added to your system PATH during installation.

### Virtual environment activation problems

**Problem:** `.\venv\Scripts\Activate` fails with a script execution policy error.

**Solution:** Run PowerShell as Administrator and execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry activation.

### Missing Django modules

**Problem:** `ModuleNotFoundError: No module named 'django'`.

**Solution:** Ensure the virtual environment is activated (look for `(venv)` in the prompt) and install dependencies:

```powershell
pip install -r requirements.txt
```

### Migration errors

**Problem:** Errors when running `python manage.py migrate`.

**Solution:** Ensure the virtual environment is activated and all dependencies are installed. If the database is corrupted, delete `db.sqlite3` and re-run migrations:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### Port 8000 already in use

**Problem:** `Address already in use` when running `runserver`.

**Solution:** Use a different port:

```powershell
python manage.py runserver 8001
```

Then open `http://127.0.0.1:8001/`.

### Unable to log in

**Problem:** Login fails with incorrect credentials.

**Solution:**
- Ensure you created a superuser with `python manage.py createsuperuser`.
- Passwords are case-sensitive.
- The user must have `is_staff=True` to access staff pages. Check this in Django Admin at `/django-admin/`.

### Staff dashboard access denied

**Problem:** Redirect to login when accessing `/staff/`.

**Solution:** Your user account does not have staff status. Log in to Django Admin, edit your user, and enable the **Staff status** checkbox.

### Static files not loading

**Problem:** CSS or images appear broken.

**Solution:** In development (`DEBUG=True`), Django serves static files automatically. Ensure `python manage.py runserver` is running. For production, run `python manage.py collectstatic` and configure a web server to serve static files.

### SQLite database problems

**Problem:** Database locked or corrupted.

**Solution:** Ensure no other process is using `db.sqlite3`. Close any database browser tools. For development, you can delete `db.sqlite3` and re-run migrations and createsuperuser.

### Sentiment analysis failures

**Problem:** Feedback submitted but sentiment analysis shows "failed".

**Solution:** This can happen if VADER encounters an unexpected error. Staff can retry failed analyses:

```powershell
python manage.py retry_failed_sentiment
```

Or retry individual failed records through the Django Admin at `/django-admin/`.

### `/health` returning 404

ReelScope does not define a `/health` endpoint. A 404 response for `/health` is expected and not a problem for local development unless your deployment environment specifically requires that endpoint.

---

## 13. Project Limitations and Future Improvements

### Current Limitations

- **VADER is English-only:** Sentiment analysis is tuned for English text. Malayalam and mixed-language feedback may not be classified accurately.
- **Sarcasm and irony:** VADER is a lexicon-based tool and does not reliably detect sarcasm, irony, or indirect opinions.
- **Aspect-based analysis is not implemented:** The system detects overall sentiment but does not extract specific aspects (acting, story, direction, etc.) from feedback text.
- **Email delivery depends on configuration:** By default, the console email backend prints emails to the terminal. Real email delivery requires SMTP configuration in `.env`.
- **Public registration is disabled:** Staff accounts can only be created through Django Admin or the createsuperuser command.
- **No feedback editing or deletion:** Visitors cannot edit or delete submitted feedback after submission.
- **No CSV/PDF export:** Analytics data cannot be exported from the dashboard.

### Future Improvements (Not Yet Implemented)

- Aspect-based sentiment analysis (extracting opinions about acting, story, direction, etc.)
- Movie recommendation engine based on audience preferences
- Genre-wise and language-wise audience preference analysis
- CSV/PDF export of analytics reports
- Advanced tracking and notification features
- Public user profiles and activity history
- Email delivery of Tracking IDs (currently console backend only in development)

---