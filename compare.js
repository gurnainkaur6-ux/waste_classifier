// Bar chart of model accuracy. `names` and `accuracy` are defined in compare.html.
const tc = window.themeColors();
const accChart = new Chart(document.getElementById("accChart"), {
  type: "bar",
  data: {
    labels: names,
    datasets: [{
      label: "Accuracy (%)",
      data: accuracy,
      backgroundColor: [tc.green, tc.blue, tc.yellow, tc.red],   // the four theme colours
      borderRadius: 8,
    }],
  },
  options: {
    plugins: { legend: { display: false } },
    scales: {
      y: {
        min: Math.max(0, Math.floor(Math.min(...accuracy) - 10)),
        max: 100,
        ticks: { color: tc.text },
        grid: { color: tc.grid },
        title: { display: true, text: "Accuracy (%)", color: tc.text },
      },
      x: { ticks: { color: tc.text }, grid: { display: false } },
    },
  },
});

// Recolour when the light/dark theme is switched (theme.js calls this)
accChart.$recolor = function (c) {
  accChart.data.datasets[0].backgroundColor = [c.green, c.blue, c.yellow, c.red];
};
window.themedCharts.push(accChart);
