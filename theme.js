// Light / dark theme toggle. The initial theme is set by a tiny script in base.html <head>.
(function () {
  var root = document.documentElement;

  function currentTheme() {
    return root.getAttribute("data-bs-theme") === "dark" ? "dark" : "light";
  }

  // Colours that Chart.js needs (it can't read CSS variables by itself)
  window.themeColors = function () {
    var css = getComputedStyle(root);
    var get = function (name) { return css.getPropertyValue(name).trim(); };
    return {
      text: get("--muted"), grid: get("--grid"),
      green: get("--green"), blue: get("--blue"), yellow: get("--yellow"), red: get("--red"),
    };
  };

  // Charts register themselves here so they can be recoloured on theme change
  window.themedCharts = window.themedCharts || [];
  window.applyChartTheme = function (chart) {
    var c = window.themeColors();
    if (chart.$recolor) chart.$recolor(c);   // optional per-chart hook (bar colours)
    var o = chart.options;
    if (o.plugins && o.plugins.legend && o.plugins.legend.labels) o.plugins.legend.labels.color = c.text;
    Object.keys(o.scales || {}).forEach(function (k) {
      var sc = o.scales[k];
      // Only change values that already exist (assigning the options proxy to itself causes recursion)
      if (sc.ticks) sc.ticks.color = c.text;
      if (sc.grid) sc.grid.color = c.grid;
      if (sc.title) sc.title.color = c.text;
    });
    chart.update();
  };

  function setTheme(t) {
    root.setAttribute("data-bs-theme", t);
    try { localStorage.setItem("theme", t); } catch (e) {}
    window.themedCharts.forEach(window.applyChartTheme);
  }

  var btn = document.getElementById("themeToggle");
  if (btn) {
    btn.addEventListener("click", function () {
      setTheme(currentTheme() === "dark" ? "light" : "dark");
    });
  }

  // Follow the system setting live, unless the user has picked a theme manually
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
      var saved = null;
      try { saved = localStorage.getItem("theme"); } catch (err) {}
      if (!saved) setTheme(e.matches ? "dark" : "light");
    });
  }
})();
