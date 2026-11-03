/* ReelScope — staff dashboard charts (Chart.js).
   All values come from database-backed JSON endpoints. Nothing is hardcoded. */
(() => {
  "use strict";

  const root = document.getElementById("dashboard-charts");
  if (!root) return;

  const COLORS = {
    positive: "#4ade80",
    neutral: "#fbbf24",
    negative: "#f87171",
    gold: "#e6b566",
    goldSoft: "rgba(230, 181, 102, 0.18)",
    grid: "rgba(255, 255, 255, 0.05)",
    text: "#98a1b5",
  };

  const charts = {};

  const urls = {
    summary: root.dataset.summaryUrl,
    ratings: root.dataset.ratingsUrl,
    sentiment: root.dataset.sentimentUrl,
    trends: root.dataset.trendsUrl,
  };

  async function getJson(url) {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    return response.json();
  }

  function setupDefaults() {
    if (!window.Chart) return false;
    Chart.defaults.color = COLORS.text;
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
    Chart.defaults.font.size = 11;
    Chart.defaults.borderColor = COLORS.grid;
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(8, 13, 24, 0.95)";
    Chart.defaults.plugins.tooltip.borderColor = "rgba(255, 255, 255, 0.1)";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.titleFont = { weight: "600" };
    return true;
  }

  function toggleEmpty(canvasId, isEmpty) {
    const canvas = document.getElementById(canvasId);
    const empty = document.querySelector(`[data-chart-empty="${canvasId}"]`);
    if (canvas) canvas.hidden = isEmpty;
    if (empty) empty.hidden = !isEmpty;
  }

  function formatDay(iso) {
    const date = new Date(`${iso}T00:00:00`);
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  function renderTrend(data) {
    const hasData = data.total.some((value) => value > 0);
    toggleEmpty("trendLine", !hasData);
    if (!hasData) return;

    charts.trend?.destroy();
    charts.trend = new Chart(document.getElementById("trendLine"), {
      type: "line",
      data: {
        labels: data.labels.map(formatDay),
        datasets: [
          {
            label: "All feedback",
            data: data.total,
            borderColor: COLORS.gold,
            backgroundColor: COLORS.goldSoft,
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            pointHoverBackgroundColor: COLORS.gold,
          },
          {
            label: "Positive",
            data: data.positive,
            borderColor: COLORS.positive,
            borderWidth: 1.5,
            tension: 0.35,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
          {
            label: "Negative",
            data: data.negative,
            borderColor: COLORS.negative,
            borderWidth: 1.5,
            tension: 0.35,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 8, boxHeight: 8, usePointStyle: true, padding: 18 },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 8 },
          },
          y: {
            beginAtZero: true,
            ticks: { precision: 0, maxTicksLimit: 5 },
            grid: { color: COLORS.grid },
          },
        },
      },
    });
  }

  function renderSentiment(data) {
    const counts = data.counts || { positive: 0, neutral: 0, negative: 0 };
    const total = counts.positive + counts.neutral + counts.negative;
    toggleEmpty("sentimentPie", total === 0);
    if (total === 0) return;

    charts.sentiment?.destroy();
    charts.sentiment = new Chart(document.getElementById("sentimentPie"), {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [
          {
            data: [counts.positive, counts.neutral, counts.negative],
            backgroundColor: [COLORS.positive, COLORS.neutral, COLORS.negative],
            borderColor: "#0a0f1c",
            borderWidth: 4,
            hoverOffset: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const percent = total ? Math.round((context.parsed / total) * 100) : 0;
                return ` ${context.label}: ${context.parsed} (${percent}%)`;
              },
            },
          },
        },
      },
    });
  }

  function renderRatings(data) {
    const hasData = data.labels.length > 0;
    toggleEmpty("ratingsBar", !hasData);
    if (!hasData) return;

    charts.ratings?.destroy();
    charts.ratings = new Chart(document.getElementById("ratingsBar"), {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Average rating",
            data: data.ratings,
            backgroundColor: COLORS.gold,
            hoverBackgroundColor: "#f6d79b",
            borderRadius: 4,
            barThickness: 16,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const count = data.counts[context.dataIndex];
                return ` ${context.parsed.x.toFixed(1)} / 5 from ${count} review${count === 1 ? "" : "s"}`;
              },
            },
          },
        },
        scales: {
          x: {
            min: 0,
            max: 5,
            ticks: { stepSize: 1 },
            grid: { color: COLORS.grid },
          },
          y: { grid: { display: false } },
        },
      },
    });
  }

  function renderPolarity(data) {
    const hasData = data.labels.length > 0;
    toggleEmpty("polarityBar", !hasData);
    if (!hasData) return;

    charts.polarity?.destroy();
    charts.polarity = new Chart(document.getElementById("polarityBar"), {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Positive",
            data: data.positive,
            backgroundColor: COLORS.positive,
            borderRadius: 3,
            barThickness: 10,
          },
          {
            label: "Negative",
            data: data.negative,
            backgroundColor: COLORS.negative,
            borderRadius: 3,
            barThickness: 10,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 8, boxHeight: 8, usePointStyle: true, padding: 16 },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: COLORS.grid },
          },
          y: { grid: { display: false } },
        },
      },
    });
  }

  function updateKpis(summary) {
    Object.entries(summary.counts || {}).forEach(([key, value]) => {
      const countEl = document.querySelector(`[data-sentiment-count="${key}"]`);
      if (countEl) countEl.textContent = value;
    });
    Object.entries(summary.percentages || {}).forEach(([key, value]) => {
      document.querySelectorAll(`[data-sentiment-percent="${key}"]`).forEach((el) => {
        el.textContent = `${value}%`;
      });
    });
  }

  async function load() {
    if (!setupDefaults()) return;

    const tasks = [
      getJson(urls.trends).then(renderTrend).catch((error) => console.error("trend chart:", error)),
      getJson(urls.sentiment).then(renderPolarity).catch((error) => console.error("polarity chart:", error)),
      getJson(urls.ratings).then(renderRatings).catch((error) => console.error("ratings chart:", error)),
      getJson(urls.summary)
        .then((data) => {
          updateKpis(data);
          renderSentiment(data);
        })
        .catch((error) => console.error("sentiment chart:", error)),
    ];

    await Promise.allSettled(tasks);
  }

  document.addEventListener("DOMContentLoaded", load);
})();
