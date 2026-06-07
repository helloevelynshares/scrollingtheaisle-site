// Cloudflare Web Analytics
// Opt out of counting your own visits (run once in the browser console on scrollingtheaisle.com):
//   localStorage.setItem("sta_skip_analytics", "1")
// To count yourself again: localStorage.removeItem("sta_skip_analytics")
(function () {
  if (localStorage.getItem("sta_skip_analytics") === "1") return;

  var token = "5e190e6858da4e47a87e0ef2d69d339e";

  var script = document.createElement("script");
  script.defer = true;
  script.src = "https://static.cloudflareinsights.com/beacon.min.js";
  script.setAttribute("data-cf-beacon", JSON.stringify({ token: token }));
  document.head.appendChild(script);
})();
