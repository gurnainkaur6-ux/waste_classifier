// Charts for the admin dashboard. perDay, categories and catColors are set in admin.html.
const c0 = window.themeColors();

const dailyChart = new Chart(document.getElementById("dailyChart"), {
  type: "bar",
  data: {
    labels: perDay.labels.map(d => d.slice(5)),   // MM-DD
    datasets: [{ label: "Predictions", data: perDay.values, backgroundColor: c0.green, borderRadius: 6 }],
  },
  options: {
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, ticks: { color: c0.text, precision: 0 }, grid: { color: c0.grid } },
      x: { ticks: { color: c0.text }, grid: { display: false } },
    },
  },
});
dailyChart.$recolor = c => { dailyChart.data.datasets[0].backgroundColor = c.green; };

// Bars use each category's own bin colour
const names = Object.keys(categories);
const catChart = new Chart(document.getElementById("catChart"), {
  type: "bar",
  data: {
    labels: names,
    datasets: [{
      label: "Predictions",
      data: names.map(n => categories[n]),
      backgroundColor: names.map(n => catColors[n].color),
      borderRadius: 6,
    }],
  },
  options: {
    indexAxis: "y",
    plugins: { legend: { display: false } },
    scales: {
      x: { beginAtZero: true, ticks: { color: c0.text, precision: 0 }, grid: { color: c0.grid } },
      y: { ticks: { color: c0.text }, grid: { display: false } },
    },
  },
});

window.themedCharts.push(dailyChart, catChart);
