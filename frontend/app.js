(function () {
  const canvas = document.getElementById("nebula");
  const ctx = canvas.getContext("2d");
  let stars = [], clouds = [];

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    initScene();
  }

  function initScene() {
    stars = Array.from({ length: 220 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.3 + 0.15,
      o: Math.random() * 0.65 + 0.1,
      speed: Math.random() * 0.008 + 0.003,
      phase: Math.random() * Math.PI * 2,
    }));
    clouds = Array.from({ length: 4 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: 150 + Math.random() * 250,
      hue: [200, 220, 260, 280][Math.floor(Math.random() * 4)],
      o: 0.025 + Math.random() * 0.035,
    }));
  }

  function draw(t) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    clouds.forEach((c) => {
      const grad = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, c.r);
      grad.addColorStop(0, `hsla(${c.hue},80%,55%,${c.o})`);
      grad.addColorStop(1, "transparent");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
      ctx.fill();
    });

    stars.forEach((s) => {
      const o = s.o * (0.55 + 0.45 * Math.sin(t * s.speed + s.phase));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200,220,255,${o})`;
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resize);
  resize();
  requestAnimationFrame(draw);
})();

const API_BASE_URL = "https://ignite-ccyz.onrender.com";
const apiUrl = (path) => `${API_BASE_URL}${path}`;


document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
    btn.classList.add("active");
    document.getElementById(`view-${btn.dataset.view}`).classList.remove("hidden");
  });
});


function setRunLoading(btn, loading) {
  btn.disabled = loading;
  btn.classList.toggle("loading", loading);
  const inner = btn.querySelector(".run-btn-inner");
  inner.innerHTML = loading
    ? `<span style="display:inline-block;width:12px;height:12px;border:2px solid rgba(0,0,0,.3);border-top-color:#000;border-radius:50%;animation:spin 0.7s linear infinite"></span> Running…`
    : `<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Detection`;
  const prog = btn.querySelector(".run-progress");
  if (prog) { prog.style.width = loading ? "85%" : "0%"; }
}

function showLoading(id, show) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("hidden", !show);
}

function renderStats(container, data, typeMap = {}) {
  container.innerHTML = "";
  let delay = 0;
  Object.entries(data).forEach(([k, v]) => {
    const cls = typeMap[k] || "";
    const card = document.createElement("div");
    card.className = `stat-card ${cls}`;
    card.style.animationDelay = `${delay}ms`;
    card.innerHTML = `
      <div class="stat-k">${k.replace(/_/g, " ")}</div>
      <div class="stat-v">${v}</div>`;
    container.appendChild(card);
    delay += 40;
  });
}

function renderError(container, msg) {
  container.innerHTML = `<div class="error-box">⚠ ${msg}</div>`;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderMarkdown(content) {
  const source = String(content || "");
  if (window.marked?.parse) {
    return marked.parse(source, { breaks: true, gfm: true });
  }
  return `<p>${escapeHtml(source).replace(/\n/g, "<br>")}</p>`;
}

function updateMissionPill(text) {
  const pill = document.getElementById("mission-pill");
  const label = document.getElementById("mission-text");
  label.textContent = text || "No mission loaded";
  pill.classList.toggle("active", !!text);
}

function buildInteractiveChart(canvasId, rawData, existingChart) {
  if (existingChart) existingChart.destroy();

  const { time, flux, median_flux, anomaly_indices, transit_indices } = rawData;
  const anomalySet  = new Set(anomaly_indices);
  const transitSet  = new Set(transit_indices);

  const mainData = time.map((t, i) => ({ x: t, y: flux[i] }));
  const anomalyData = anomaly_indices.map((i) => ({ x: time[i], y: flux[i] }));
  const transitData = transit_indices.map((i) => ({ x: time[i], y: flux[i] }));

  const medianLine = [
    { x: time[0], y: median_flux },
    { x: time[time.length - 1], y: median_flux },
  ];

  return new Chart(document.getElementById(canvasId), {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Flux",
          data: mainData,
          showLine: true,
          borderColor: "#374151",
          borderWidth: 1,
          pointRadius: 0,
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "#374151",
          tension: 0.1,
          order: 3,
        },
        {
          label: "Median",
          data: medianLine,
          showLine: true,
          borderColor: "rgba(156,163,175,.9)",
          borderWidth: 0.9,
          borderDash: [4, 4],
          pointRadius: 0,
          order: 4,
        },
        {
          label: "Transit Dips",
          data: transitData,
          backgroundColor: "#065f46",
          pointRadius: 2.5,
          pointHoverRadius: 4,
          order: 2,
        },
        {
          label: "Anomalies",
          data: anomalyData,
          backgroundColor: "#b91c1c",
          pointRadius: 3,
          pointHoverRadius: 4.5,
          pointStyle: "crossRot",
          order: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      plugins: {
        legend: {
          labels: {
            color: "#6b7280",
            font: { family: "'Inter'", size: 11 },
            boxWidth: 12,
          },
        },
        tooltip: {
          backgroundColor: "#ffffff",
          borderColor: "#e5e7eb",
          borderWidth: 1,
          titleColor: "#111827",
          bodyColor: "#6b7280",
          callbacks: {
            label: (ctx) => {
              const x = ctx.parsed.x.toFixed(4);
              const y = ctx.parsed.y.toFixed(6);
              return ` Time: ${x}  Flux: ${y}`;
            },
          },
        },
        zoom: undefined,
      },
      scales: {
        x: {
          ticks: { color: "#6b7280", font: { family: "'Inter'", size: 10 } },
          grid:  { color: "rgba(229,231,235,.45)", lineWidth: 0.6 },
          border: { color: "rgba(209,213,219,.8)" },
          title: { display: true, text: "Time", color: "#6b7280",
                   font: { family: "'Inter'", size: 11 } },
        },
        y: {
          ticks: { color: "#6b7280", font: { family: "'Inter'", size: 10 } },
          grid:  { color: "rgba(229,231,235,.45)", lineWidth: 0.6 },
          border: { color: "rgba(209,213,219,.8)" },
          title: { display: true, text: "Normalized Flux", color: "#6b7280",
                   font: { family: "'Inter'", size: 11 } },
        },
      },
    },
  });
}


let selectedPlanet = null;
let selectedAuthor = null;
let exoChart = null;

Promise.all([
  fetch(apiUrl("/api/planets")).then((r) => r.json()),
  fetch(apiUrl("/api/telescopes")).then((r) => r.json()),
]).then(([{ planets }, { telescopes }]) => {
  const container = document.getElementById("planet-cards");
  planets.forEach((p) => {
    const card = document.createElement("div");
    card.className = "planet-card";
    card.dataset.planet = p;
    card.innerHTML = `<span class="planet-dot"></span>${p}`;
    card.addEventListener("click", () => selectPlanet(p, null));
    container.appendChild(card);
  });

  const sel = document.getElementById("telescope-select");
  telescopes.forEach(({ key, label }) => {
    const opt = document.createElement("option");
    opt.value = key; opt.textContent = label;
    sel.appendChild(opt);
  });
});

function selectPlanet(name, author) {
  selectedPlanet = name;
  selectedAuthor = author || null;

  document.querySelectorAll(".planet-card").forEach((c) => {
    c.classList.toggle("selected", c.dataset.planet === name);
  });

  const disp = document.getElementById("selected-planet-display");
  disp.textContent = name;
  disp.classList.add("has-value");

  document.getElementById("planet-search").value = name;
  document.getElementById("btn-run-exoplanet").disabled = false;
}

document.getElementById("btn-search").addEventListener("click", doSearch);
document.getElementById("planet-search").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch();
});

async function doSearch() {
  const query = document.getElementById("planet-search").value.trim();
  if (!query) return;

  const resultsBox = document.getElementById("search-results");
  resultsBox.innerHTML = `<div class="search-result-item dim-note">Searching…</div>`;
  resultsBox.classList.remove("hidden");

  try {
    const res = await fetch(apiUrl(`/api/search?target=${encodeURIComponent(query)}`));
    const data = await res.json();

    if (!res.ok) {
      resultsBox.innerHTML = `<div class="search-result-item" style="color:var(--red)">⚠ ${data.detail}</div>`;
      return;
    }

    if (!data.missions || data.missions.length === 0) {
      resultsBox.innerHTML = `<div class="search-result-item dim-note">No missions found.</div>`;
      return;
    }

    resultsBox.innerHTML = "";
    data.missions.forEach((m) => {
      const item = document.createElement("div");
      item.className = "search-result-item";
      item.innerHTML = `${data.target}
        <div class="search-result-mission">${m.label}</div>`;
      item.addEventListener("click", () => {
        selectPlanet(data.target, m.author);
        const sel = document.getElementById("telescope-select");
        for (const opt of sel.options) {
          if (opt.value !== "any") {
            if (m.label.toLowerCase().includes(opt.value.replace("_", " "))) {
              sel.value = opt.value;
              break;
            }
          }
        }
        resultsBox.classList.add("hidden");
      });
      resultsBox.appendChild(item);
    });
  } catch (e) {
    resultsBox.innerHTML = `<div class="search-result-item" style="color:var(--red)">Request failed</div>`;
  }
}

document.addEventListener("click", (e) => {
  if (!e.target.closest(".sidebar-section")) {
    document.getElementById("search-results").classList.add("hidden");
  }
});

document.querySelectorAll("#view-exoplanet .plot-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#view-exoplanet .plot-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll("#view-exoplanet .plot-panel").forEach((p) => {
      p.classList.remove("active"); p.classList.add("hidden");
    });
    tab.classList.add("active");
    const panel = document.getElementById(`plot-${tab.dataset.plot}`);
    panel.classList.add("active"); panel.classList.remove("hidden");
  });
});

document.getElementById("btn-run-exoplanet").addEventListener("click", async () => {
  if (!selectedPlanet) return;

  const telescope = document.getElementById("telescope-select").value;
  const showTransit = document.getElementById("transit-toggle").checked;
  const btn = document.getElementById("btn-run-exoplanet");

  setRunLoading(btn, true);
  showLoading("exo-loading", true);
  document.getElementById("exoplanet-results").classList.add("hidden");

  const loadingMessages = [
    "Contacting telescope array…",
    "Downloading light curve data…",
    "Running anomaly detection…",
    "Generating AI analysis…",
  ];
  let msgIdx = 0;
  const msgEl = document.getElementById("loading-text");
  const msgInterval = setInterval(() => {
    msgIdx = (msgIdx + 1) % loadingMessages.length;
    msgEl.textContent = loadingMessages[msgIdx];
  }, 2200);

  try {
    const body = new FormData();
    body.append("planet", selectedPlanet);
    body.append("telescope", telescope);
    if (selectedAuthor) body.append("author_override", selectedAuthor);
    body.append("show_transit_regions", showTransit ? "true" : "false");

    const res = await fetch(apiUrl("/api/exoplanet"), { method: "POST", body });
    const data = await res.json();

    if (!res.ok) {
      clearInterval(msgInterval);
      showLoading("exo-loading", false);
      setRunLoading(btn, false);
      document.getElementById("exoplanet-results").classList.remove("hidden");
      renderError(document.getElementById("exo-stats"), data.detail || "Unknown error.");
      return;
    }

    renderStats(
      document.getElementById("exo-stats"),
      data.summary,
      { anomalies_detected: "anomaly", transit_dips: "transit",
        planet: "info", mission: "info" }
    );

    const imgFull = document.getElementById("img-full");
    imgFull.src = `data:image/png;base64,${data.plot}`;
    const dlFull = document.getElementById("dl-full");
    dlFull.href = imgFull.src;

    const transitTabBtn = document.getElementById("transit-tab-btn");
    if (data.transit_plot) {
      const imgTransit = document.getElementById("img-transit");
      imgTransit.src = `data:image/png;base64,${data.transit_plot}`;
      document.getElementById("dl-transit").href = imgTransit.src;
      document.getElementById("no-transit-msg").classList.add("hidden");
      transitTabBtn.disabled = false;
    } else {
      document.getElementById("no-transit-msg").classList.remove("hidden");
      document.getElementById("img-transit").src = "";
      transitTabBtn.disabled = true;
    }

    if (data.raw_data) {
      exoChart = buildInteractiveChart("interactiveChart", data.raw_data, exoChart);
    }

    document.getElementById("exo-ai-body").innerHTML = renderMarkdown(data.ai_summary);

    updateMissionPill(`${selectedPlanet} — ${data.summary.mission || telescope.toUpperCase()}`);

    document.getElementById("chat-ctx-line").textContent =
      `Dataset: ${selectedPlanet} (${data.summary.mission || telescope})`;

    document.getElementById("exoplanet-results").classList.remove("hidden");

    document.querySelectorAll("#view-exoplanet .plot-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll("#view-exoplanet .plot-panel").forEach((p) => {
      p.classList.remove("active"); p.classList.add("hidden");
    });
    document.querySelector("#view-exoplanet .plot-tab[data-plot='full']").classList.add("active");
    document.getElementById("plot-full").classList.add("active"); 
    document.getElementById("plot-full").classList.remove("hidden");

  } catch (e) {
    renderError(document.getElementById("exo-stats"), `Request failed: ${e.message}`);
    document.getElementById("exoplanet-results").classList.remove("hidden");
  } finally {
    clearInterval(msgInterval);
    showLoading("exo-loading", false);
    setRunLoading(btn, false);
  }
});


let csvFile = null;
let csvChart = null;

const uploadZone    = document.getElementById("upload-zone");
const csvFileInput  = document.getElementById("csv-file");
const uploadTrigger = document.getElementById("upload-trigger");
const fileNameDisp  = document.getElementById("file-name-display");
const btnRunCsv     = document.getElementById("btn-run-csv");

uploadTrigger.addEventListener("click", (e) => { e.stopPropagation(); csvFileInput.click(); });
uploadZone.addEventListener("click", () => csvFileInput.click());

uploadZone.addEventListener("dragover", (e) => { e.preventDefault(); uploadZone.classList.add("dragover"); });
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
uploadZone.addEventListener("drop", (e) => {
  e.preventDefault(); uploadZone.classList.remove("dragover");
  const f = e.dataTransfer.files[0];
  if (f?.name.endsWith(".csv")) handleCsvSelected(f);
});

csvFileInput.addEventListener("change", () => {
  if (csvFileInput.files[0]) handleCsvSelected(csvFileInput.files[0]);
});

function handleCsvSelected(file) {
  csvFile = file;
  fileNameDisp.textContent = file.name;
  btnRunCsv.disabled = false;
  document.getElementById("col-row").classList.add("hidden");
}

document.querySelectorAll("#view-csv .plot-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#view-csv .plot-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll("#view-csv .plot-panel").forEach((p) => {
      p.classList.remove("active"); p.classList.add("hidden");
    });
    tab.classList.add("active");
    const panel = document.getElementById(`plot-${tab.dataset.plot}`);
    panel.classList.add("active"); panel.classList.remove("hidden");
  });
});

btnRunCsv.addEventListener("click", async () => {
  if (!csvFile) return;

  setRunLoading(btnRunCsv, true);
  showLoading("csv-loading", true);
  document.getElementById("csv-results").classList.add("hidden");

  try {
    const body = new FormData();
    body.append("file", csvFile);
    const colIdx = document.getElementById("col-select").selectedIndex;
    body.append("column_index", Math.max(0, colIdx));

    const res = await fetch(apiUrl("/api/csv"), { method: "POST", body });
    const data = await res.json();

    if (!res.ok) {
      showLoading("csv-loading", false);
      setRunLoading(btnRunCsv, false);
      document.getElementById("csv-results").classList.remove("hidden");
      renderError(document.getElementById("csv-stats"), data.detail || "Unknown error.");
      return;
    }

    if (data.columns?.length > 1) {
      const sel = document.getElementById("col-select");
      sel.innerHTML = data.columns.map((c, i) =>
        `<option value="${i}">${c}</option>`).join("");
      const usedIdx = data.columns.indexOf(data.summary.column);
      if (usedIdx >= 0) sel.selectedIndex = usedIdx;
      document.getElementById("col-row").classList.remove("hidden");
    }

    renderStats(
      document.getElementById("csv-stats"),
      data.summary,
      { anomalies_detected: "anomaly" }
    );

    const imgCsv = document.getElementById("img-csv");
    imgCsv.src = `data:image/png;base64,${data.plot}`;
    document.getElementById("dl-csv").href = imgCsv.src;

    if (data.raw_data) {
      csvChart = buildInteractiveChart("csvChart", data.raw_data, csvChart);
    }

    document.getElementById("csv-ai-body").innerHTML = renderMarkdown(data.ai_summary);
    updateMissionPill(`CSV: ${csvFile.name} — ${data.summary.column}`);
    document.getElementById("chat-ctx-line").textContent =
      `Dataset: CSV — ${data.summary.column}`;
    document.getElementById("csv-results").classList.remove("hidden");

    document.querySelectorAll("#view-csv .plot-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll("#view-csv .plot-panel").forEach((p) => {
      p.classList.remove("active"); p.classList.add("hidden");
    });
    document.querySelector("#view-csv .plot-tab[data-plot='csv-full']").classList.add("active");
    document.getElementById("plot-csv-full").classList.add("active");
    document.getElementById("plot-csv-full").classList.remove("hidden");

  } catch (e) {
    renderError(document.getElementById("csv-stats"), `Request failed: ${e.message}`);
    document.getElementById("csv-results").classList.remove("hidden");
  } finally {
    showLoading("csv-loading", false);
    setRunLoading(btnRunCsv, false);
  }
});


const chatMessages = document.getElementById("chat-messages");
const chatInput    = document.getElementById("chat-input");
const btnSend      = document.getElementById("btn-send");

function appendMsg(role, text) {
  const wrap = document.createElement("div");
  wrap.className = `chat-msg ${role}`;
  const safeText = escapeHtml(text);
  const bodyHtml = role === "assistant"
    ? `<div class="chat-bubble markdown-body">${renderMarkdown(text)}</div>`
    : `<div class="chat-bubble">${safeText.replace(/\n/g, "<br>")}</div>`;
  wrap.innerHTML = `
    <div class="chat-role">${role === "user" ? "You" : "Groq AI"}</div>
    ${bodyHtml}`;
  chatMessages.appendChild(wrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendThinking() {
  const wrap = document.createElement("div");
  wrap.className = "chat-msg assistant";
  wrap.innerHTML = `
    <div class="chat-role">Groq AI</div>
    <div class="chat-thinking"><span></span><span></span><span></span></div>`;
  chatMessages.appendChild(wrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return wrap;
}

async function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg) return;

  if (["exit", "quit", "back"].includes(msg.toLowerCase())) {
    chatInput.value = "";
    return;
  }

  chatInput.value = "";
  btnSend.disabled = true;
  appendMsg("user", msg);
  const thinking = appendThinking();

  try {
    const res = await fetch(apiUrl("/api/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });
    const data = await res.json();
    thinking.remove();
    appendMsg("assistant", res.ok ? data.response : `⚠ ${data.detail || "Error"}`);
    if (data.dataset_context) updateMissionPill(data.dataset_context);
  } catch (e) {
    thinking.remove();
    appendMsg("assistant", `⚠ Request failed: ${e.message}`);
  } finally {
    btnSend.disabled = false;
    chatInput.focus();
  }
}

btnSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.ctrlKey) { e.preventDefault(); sendChat(); }
});

document.getElementById("btn-clear-chat").addEventListener("click", async () => {
  await fetch(apiUrl("/api/chat/clear"), { method: "POST" });
  chatMessages.innerHTML = `
    <div class="chat-intro">
      <p>Ask about anomalies, transit dips, exoplanet science, or your loaded dataset.</p>
      <p class="dim-note" style="margin-top:.4rem">Type <kbd>exit</kbd> or <kbd>back</kbd> to clear input</p>
    </div>`;
});

fetch(apiUrl("/api/chat/context"))
  .then((r) => r.json())
  .then(({ source }) => {
    if (source) {
      updateMissionPill(source);
      document.getElementById("chat-ctx-line").textContent = `Dataset: ${source}`;
    }
  });
