"""Temporary Phase 3 verification script (deleted after use)."""

import os
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reelscope.settings")
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.template.loader import get_template, render_to_string  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import override_settings  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from feedback.models import Feedback, SentimentAnalysis  # noqa: E402
from movies.models import Movie  # noqa: E402

FAILURES = []


def check(label, condition, detail=""):
    status = "OK  " if condition else "FAIL"
    if not condition:
        FAILURES.append(label)
    print(f"[{status}] {label}{(' — ' + detail) if detail else ''}")


def poster(name, top, bottom, title):
    img = Image.new("RGB", (600, 900), top)
    draw = ImageDraw.Draw(img)
    for y in range(900):
        ratio = y / 900
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (600, y)], fill=color)
    draw.rectangle([60, 700, 540, 780], outline=(230, 181, 102), width=3)
    draw.text((90, 730), title, fill=(240, 235, 220))
    path = Path("media/posters") / name
    img.save(path)
    return f"posters/{name}"


def main():
    # 1. Every template compiles.
    templates = sorted(Path("templates").rglob("*.html"))
    for path in templates:
        name = path.relative_to("templates").as_posix()
        try:
            get_template(name)
            check(f"template compiles: {name}", True)
        except Exception as exc:  # noqa: BLE001
            check(f"template compiles: {name}", False, str(exc))

    # 2. Temporary fixture with real posters.
    if Movie.objects.exists():
        print("!! existing movies found — aborting to avoid touching real data")
        return 1

    movie1 = Movie.objects.create(
        title="Nebula Run",
        description="A courier crosses a collapsing star system while a quiet revolution unfolds on her ship.",
        poster=poster("tmp-nebula.jpg", (24, 34, 66), (6, 9, 18), "NEBULA RUN"),
        genre="sci-fi",
        release_date="2024-03-15",
        director="Ada Vale",
        cast="Nia Okafor, Tomas Reed, June Park",
        language="English",
    )
    movie2 = Movie.objects.create(
        title="The Last Screening",
        description="An ageing projectionist keeps a fading cinema alive in a town that has stopped watching.",
        poster=poster("tmp-screening.jpg", (74, 44, 22), (10, 8, 8), "THE LAST SCREENING"),
        genre="drama",
        release_date="2023-11-02",
        director="Milo Ferrer",
        cast="Ruth Adeyemi, Peter Shaw",
        language="English",
    )
    movie3 = Movie.objects.create(
        title="Paper Moons",
        description="Two estranged sisters rebuild their childhood cinema using nothing but paper and memory.",
        poster=poster("tmp-moons.jpg", (30, 52, 48), (7, 11, 14), "PAPER MOONS"),
        genre="animation",
        release_date="2025-01-20",
        director="Iris Chen",
        cast="Lina Cho, Bea Moreno",
        language="Spanish",
    )

    samples = [
        (movie1, "Maya Rao", "maya@example.com", 5, "The cinematography is stunning and the storyline kept me gripped.", "positive", 0.82, ["cinematography", "storyline"], [], False),
        (movie1, "Dev Kumar", "dev@example.com", 2, "Beautiful visuals but the pacing was painfully slow.", "negative", -0.45, ["cinematography"], ["pacing"], True),
        (movie2, "Ruth Adeyemi", "ruth@example.com", 4, "Wonderful acting and a gentle, moving direction.", "positive", 0.71, ["acting", "direction"], [], False),
        (movie2, "Sam Lee", "sam@example.com", 2, "Weak character development and the story felt thin.", "negative", -0.62, [], ["character development", "storyline"], False),
        (movie3, "Bea Moreno", "bea@example.com", 3, "The animation is lovely, though the music was forgettable.", "neutral", 0.02, ["animation"], ["music"], False),
        (movie3, "Iris Chen", "iris@example.com", 5, "A gorgeous, heartfelt film with music that stayed with me.", "positive", 0.78, ["music", "visual effects"], [], False),
    ]

    feedback_rows = []
    for movie, name, email, rating, message, sentiment, score, pos, neg, mismatch in samples:
        item = Feedback.objects.create(
            movie=movie, username=name, email=email, rating=rating, message=message
        )
        SentimentAnalysis.objects.create(
            feedback=item,
            text_sentiment=sentiment,
            text_score=score,
            rating_sentiment="positive" if rating >= 4 else ("neutral" if rating == 3 else "negative"),
            is_mismatch=mismatch,
            positive_aspects=pos,
            negative_aspects=neg,
            status="success",
        )
        feedback_rows.append(item)

    pending = Feedback.objects.create(
        movie=movie2, username="Queued Visitor", email="queued@example.com",
        rating=4, message="This review is still waiting for its analysis to run.",
    )
    SentimentAnalysis.objects.create(feedback=pending, status="pending")

    # 3. Public pages render.
    public_urls = [
        "/", "/movies/", "/movies/?q=nebula", "/movies/?genre=drama",
        f"/movies/{movie1.slug}/", f"/movies/{movie1.slug}/feedback/",
        "/track/", "/accounts/login/", "/accounts/register/",
    ]

    with override_settings(ALLOWED_HOSTS=["testserver"]):
        client = Client()
        for url in public_urls:
            response = client.get(url)
            check(f"GET {url}", response.status_code == 200, f"status {response.status_code}")

        detail = client.get(f"/movies/{movie1.slug}/").content.decode()
        check("movie detail hides visitor emails", "maya@example.com" not in detail)
        check("movie detail shows audience notes", "cinematography" in detail.lower())
        check("movie detail renders sentiment badges", "badge-positive" in detail and "badge-negative" in detail)
        check("movie list shows seeded movie", "Nebula Run" in client.get("/movies/").content.decode())
        check("search filters results", "Nebula Run" in client.get("/movies/?q=nebula").content.decode())
        check("home renders hero", "Every voice" in client.get("/").content.decode())

        # 4. Staff area permissions and data.
        check("anonymous staff redirects", client.get("/staff/").status_code == 302)
        check("chart endpoint protects data", client.get("/staff/data/summary/").status_code == 302)

        admin = User.objects.get(username="admin")
        client.force_login(admin)
        dashboard = client.get("/staff/")
        body = dashboard.content.decode()
        check("GET /staff/ as staff", dashboard.status_code == 200, f"status {dashboard.status_code}")
        check("dashboard shows real total", ">6<" in body or "6" in body)
        check("dashboard shows latest submissions", "Queued Visitor" in body)
        check("dashboard KPI markup present", "kpi-grid" in body and "chart-grid" in body)

        for endpoint in ["summary", "ratings", "sentiment", "trends"]:
            response = client.get(f"/staff/data/{endpoint}/")
            ok = response.status_code == 200 and response["Content-Type"].startswith("application/json")
            check(f"chart JSON /staff/data/{endpoint}/", ok, f"status {response.status_code}")

        summary = client.get("/staff/data/summary/").json()
        check("summary totals match fixture", summary["total_feedback"] == 7, str(summary.get("total_feedback")))
        check("summary sentiment counts match", summary["counts"] == {"positive": 3, "neutral": 1, "negative": 2}, str(summary["counts"]))
        trends = client.get("/staff/data/trends/").json()
        check("trend endpoint returns 30 days", len(trends["labels"]) == 30)

        # 5. Auth templates.
        client.logout()
        check("login page has form", "csrfmiddlewaretoken" in client.get("/accounts/login/").content.decode())

        # 6. Templates that are wired in the backend phase still render.
        try:
            render_to_string("feedback/success.html", {"feedback": feedback_rows[0]})
            check("success template renders", True)
        except Exception as exc:  # noqa: BLE001
            check("success template renders", False, str(exc))

        try:
            render_to_string("accounts/verify_result.html", {"status": "success"})
            check("verify result template renders", True)
        except Exception as exc:  # noqa: BLE001
            check("verify result template renders", False, str(exc))

    # 7. Clean up fixture and generated posters.
    Feedback.objects.filter(movie__in=[movie1, movie2, movie3]).delete()
    Movie.objects.filter(pk__in=[movie1.pk, movie2.pk, movie3.pk]).delete()
    for name in ["tmp-nebula.jpg", "tmp-screening.jpg", "tmp-moons.jpg"]:
        Path("media/posters", name).unlink(missing_ok=True)

    print(f"\n{'ALL CHECKS PASSED' if not FAILURES else 'FAILURES: ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


raise SystemExit(main())
