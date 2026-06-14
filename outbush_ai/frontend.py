FRONTEND_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Outbush AI</title>
  <style>
    :root {
      --bg: #f5f0e6;
      --ink: #17231d;
      --muted: #647268;
      --panel: #fffdf7;
      --line: #d8cfbd;
      --gum: #246958;
      --gum-dark: #173f36;
      --sun: #c97824;
      --sky: #426f91;
      --rust: #964934;
      --soft: #f9f5ec;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        linear-gradient(160deg, rgba(36, 105, 88, .13), transparent 42%),
        linear-gradient(24deg, rgba(201, 120, 36, .14), transparent 44%),
        var(--bg);
    }
    .app { width: min(980px, 100%); margin: 0 auto; min-height: 100vh; padding: 18px; }
    header { padding: 10px 0 16px; }
    .brand { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    .brand h1 {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(38px, 11vw, 74px);
      line-height: .9;
      letter-spacing: 0;
    }
    .status {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      background: rgba(255, 255, 255, .72);
      font-weight: 850;
      font-size: 13px;
      white-space: nowrap;
    }
    .lede { max-width: 720px; margin: 12px 0 0; color: #34433b; font-size: 17px; }
    nav {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding: 8px 0 14px;
      position: sticky;
      top: 0;
      z-index: 2;
      background: rgba(245, 240, 230, .94);
      backdrop-filter: blur(10px);
    }
    nav button, .suggestions button {
      flex: 0 0 auto;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 999px;
      padding: 10px 13px;
      font-weight: 850;
      cursor: pointer;
    }
    nav button.active { background: var(--gum); color: #fff; border-color: var(--gum); }
    main { display: grid; gap: 14px; }
    .panel {
      display: none;
      background: rgba(255, 253, 247, .88);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 18px 45px rgba(26, 35, 29, .12);
    }
    .panel.active { display: block; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .stack { display: grid; gap: 12px; }
    .toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .suggestions { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; }
    .suggestions button { background: #edf4ed; border-color: #c6d8cb; color: var(--gum-dark); }
    label { display: block; font-weight: 850; margin: 0 0 7px; }
    input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      padding: 12px;
      font: inherit;
    }
    textarea { min-height: 116px; resize: vertical; }
    .action {
      border: 0;
      border-radius: 8px;
      background: var(--gum);
      color: #fff;
      padding: 12px 14px;
      font-weight: 900;
      cursor: pointer;
      min-height: 44px;
    }
    .action.secondary { background: var(--sky); }
    .action.rust { background: var(--rust); }
    .output {
      min-height: 150px;
      white-space: pre-wrap;
      background: var(--soft);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      overflow-wrap: anywhere;
    }
    .cards { display: grid; gap: 10px; }
    .card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fffdf7;
      padding: 13px;
    }
    .card h3 { margin: 0 0 7px; font-size: 18px; }
    .card p { margin: 7px 0; }
    .pill {
      display: inline-flex;
      align-items: center;
      margin: 0 5px 6px 0;
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 12px;
      font-weight: 900;
      background: #e7efe7;
      color: var(--gum-dark);
    }
    .critical { background: #fff1eb; border-color: #e1ad9d; }
    .high { background: #fff8e6; border-color: #e2c77a; }
    .normal { background: #fffdf7; }
    .small { color: var(--muted); font-size: 13px; }
    .answer { font-size: 16px; line-height: 1.45; }
    .split { display: grid; grid-template-columns: minmax(0, 1fr) minmax(220px, .6fr); gap: 12px; }
    .preview {
      display: grid;
      place-items: center;
      min-height: 180px;
      border: 1px dashed var(--line);
      border-radius: 8px;
      background: #fbf8ef;
      overflow: hidden;
    }
    .preview img { max-width: 100%; max-height: 280px; display: block; }
    .day-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 8px; }
    .day { padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
    .day strong { display: block; margin-bottom: 4px; }
    ul.clean { margin: 8px 0 0 20px; padding: 0; }
    .checklist-card label { display: flex; align-items: flex-start; gap: 9px; font-weight: 650; }
    .checklist-card input { width: 18px; height: 18px; flex: 0 0 auto; margin-top: 2px; }
    footer { color: var(--muted); font-size: 13px; padding: 20px 0 8px; }
    footer strong { color: var(--ink); }
    footer details {
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 253, 247, .82);
      padding: 10px;
    }
    footer summary { cursor: pointer; color: var(--ink); font-weight: 900; }
    .dev-log { display: grid; gap: 7px; margin-top: 10px; }
    .dev-log div { border-top: 1px solid var(--line); padding-top: 7px; }
    pre {
      max-height: 220px;
      overflow: auto;
      background: #18231d;
      color: #f5f0e6;
      border-radius: 8px;
      padding: 10px;
      font-size: 12px;
      white-space: pre-wrap;
    }
    @media (max-width: 720px) {
      .app { padding: 12px; }
      .brand { align-items: flex-start; flex-direction: column; }
      .grid, .split { grid-template-columns: 1fr; }
      .panel { padding: 13px; }
      .action { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="brand">
        <h1>Outbush AI</h1>
        <div class="status" id="status">checking...</div>
      </div>
      <p class="lede">Offline field help for Australian bushwalkers, built for a phone connected to the Pi in places with no service.</p>
    </header>

    <nav aria-label="Outbush tools">
      <button class="active" data-tab="chat">Ask</button>
      <button data-tab="photo">Photo</button>
      <button data-tab="firstaid">First Aid</button>
      <button data-tab="encyclopedia">Encyclopedia</button>
      <button data-tab="weather">Weather</button>
      <button data-tab="danger">Danger</button>
      <button data-tab="checklist">Checklist</button>
    </nav>

    <main>
      <section class="panel active" id="chat">
        <div class="stack">
          <div>
            <label for="region">Region</label>
            <input id="region" value="General Australia" autocomplete="off">
          </div>
          <div class="suggestions" aria-label="Suggested questions">
            <button type="button" data-question="What should I check before a Blue Mountains day walk?">Blue Mountains prep</button>
            <button type="button" data-question="I saw a snake near the track. What should I do?">Snake nearby</button>
            <button type="button" data-question="We lost the track and the group is getting tired. What now?">Lost track</button>
            <button type="button" data-question="How should I think about orange fungus on a fallen log?">Orange fungus</button>
            <button type="button" data-question="What should I do for heat stress on a remote walk?">Heat stress</button>
          </div>
          <div>
            <label for="message">Question</label>
            <textarea id="message" placeholder="Ask about wildlife, plants, first aid, survival, weather, or gear..."></textarea>
          </div>
          <button class="action" id="askBtn">Ask Outbush</button>
          <div class="output answer" id="chatOut">Answers will appear here.</div>
        </div>
      </section>

      <section class="panel" id="photo">
        <div class="split">
          <div class="stack">
            <div>
              <label for="image">Photo</label>
              <input id="image" type="file" accept="image/*">
            </div>
            <div>
              <label for="photoNote">Field notes</label>
              <textarea id="photoNote" placeholder="Example: brown snake on track, orange fungus under eucalypt, dark anvil cloud..."></textarea>
            </div>
            <button class="action rust" id="photoBtn">Check Photo</button>
          </div>
          <div class="preview" id="photoPreview"><span class="small">Image preview</span></div>
        </div>
        <div class="cards" id="photoOut" style="margin-top: 12px;"></div>
      </section>

      <section class="panel" id="firstaid">
        <div class="stack">
          <label for="firstTopic">First aid topic</label>
          <input id="firstTopic" value="snake bite" autocomplete="off">
          <button class="action rust" id="firstBtn">Get Flow</button>
          <div class="output" id="firstOut"></div>
        </div>
      </section>

      <section class="panel" id="encyclopedia">
        <div class="stack">
          <label for="encyQuery">Search local Australia field pack</label>
          <input id="encyQuery" value="Australian snakes" autocomplete="off">
          <button class="action secondary" id="encyBtn">Search Encyclopedia</button>
          <div class="output answer" id="encyAnswer">RAG answer will appear here.</div>
          <div class="cards" id="encyOut"></div>
        </div>
      </section>

      <section class="panel" id="weather">
        <div class="stack">
          <div class="grid">
            <div>
              <label for="weatherRegion">Region</label>
              <input id="weatherRegion" value="Blue Mountains" autocomplete="off">
            </div>
            <div>
              <label for="cloudNote">Cloud note</label>
              <input id="cloudNote" placeholder="dark anvil cloud building west" autocomplete="off">
            </div>
          </div>
          <div class="toolbar">
            <button class="action secondary" id="weatherBtn">Get Weather</button>
            <button class="action" id="weatherSyncBtn">Sync 10-day Pack</button>
          </div>
          <div class="output" id="weatherOut"></div>
          <div class="cards" id="weatherPackOut"></div>
        </div>
      </section>

      <section class="panel" id="danger">
        <div class="cards" id="dangerOut"><article class="card">Loading field reference...</article></div>
      </section>

      <section class="panel" id="checklist">
        <div class="stack">
          <button class="action" id="copyChecklistBtn">Copy Checklist Text</button>
          <textarea id="checkExport" readonly placeholder="Checklist export text will appear here."></textarea>
          <div class="cards" id="checkOut"><article class="card">Loading checklist...</article></div>
        </div>
      </section>
    </main>

    <footer>
      <p><strong>Field disclaimer.</strong> Outbush AI is uncertain field support, not medical care, an official forecast, or species certification. Do not use it to decide a wild thing is safe to eat or touch. For life-threatening symptoms call 000; for suspected poisoning call Poisons Information Centre on 13 11 26.</p>
      <p><strong>Offline models.</strong> Text answers use a local GGUF model through llama.cpp when enabled; photo checks use SmolVLM2 through llama.cpp mtmd when installed, with local image heuristics as fallback.</p>
      <details>
        <summary>Dev mode</summary>
        <div class="dev-log" id="devLog"></div>
        <pre id="devState">No requests yet.</pre>
      </details>
    </footer>
  </div>

  <script>
    const $ = (id) => document.getElementById(id);
    const devEntries = [];
    let lastChecklistText = "";

    function escapeHTML(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#039;"
      }[char]));
    }

    function devLog(label, data = {}) {
      const entry = { time: new Date().toLocaleTimeString(), label, data };
      devEntries.unshift(entry);
      devEntries.splice(8);
      $("devLog").innerHTML = devEntries.map((item) => (
        `<div><strong>${escapeHTML(item.time)}</strong> ${escapeHTML(item.label)}</div>`
      )).join("");
      $("devState").textContent = JSON.stringify(entry.data, null, 2);
    }

    async function postJSON(url, payload) {
      const started = performance.now();
      devLog(`POST ${url}`, payload);
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      data._duration_ms = Math.round(performance.now() - started);
      devLog(`DONE ${url}`, data);
      return data;
    }

    async function getJSON(url) {
      const started = performance.now();
      devLog(`GET ${url}`);
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      data._duration_ms = Math.round(performance.now() - started);
      devLog(`DONE ${url}`, data);
      return data;
    }

    function setTab(tabId) {
      document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("active", b.dataset.tab === tabId));
      document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === tabId));
    }

    document.querySelectorAll("nav button").forEach((btn) => {
      btn.addEventListener("click", () => setTab(btn.dataset.tab));
    });

    document.querySelectorAll(".suggestions button").forEach((btn) => {
      btn.addEventListener("click", () => {
        $("message").value = btn.dataset.question;
        $("message").focus();
      });
    });

    $("message").addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        $("askBtn").click();
      }
    });

    $("image").addEventListener("change", () => {
      const file = $("image").files[0];
      if (!file) {
        $("photoPreview").innerHTML = "<span class=\"small\">Image preview</span>";
        return;
      }
      const url = URL.createObjectURL(file);
      $("photoPreview").innerHTML = `<img alt="Uploaded field photo preview" src="${url}">`;
    });

    function renderSources(sources = []) {
      if (!sources.length) return "";
      return `<p class="small">Sources: ${sources.map((source) => escapeHTML(source.title)).join(" / ")}</p>`;
    }

    function renderDanger(cards) {
      $("dangerOut").innerHTML = cards.map((card) => `
        <article class="card ${escapeHTML(card.severity)}">
          <span class="pill">${escapeHTML(card.severity)}</span>
          <h3>${escapeHTML(card.title)}</h3>
          <p>${escapeHTML(card.signals)}</p>
          <ul class="clean">${card.actions.map((item) => `<li>${escapeHTML(item)}</li>`).join("")}</ul>
          ${renderSources([card.source])}
        </article>
      `).join("");
    }

    function renderChecklist(data) {
      lastChecklistText = data.export_text;
      $("checkExport").value = data.export_text;
      $("checkOut").innerHTML = data.sections.map((section) => `
        <article class="card checklist-card">
          <h3>${escapeHTML(section.title)}</h3>
          <div class="stack">
            ${section.items.map((item) => `<label><input type="checkbox"> <span>${escapeHTML(item)}</span></label>`).join("")}
          </div>
        </article>
      `).join("");
    }

    function renderPhoto(data) {
      const analysis = data.image_analysis || {};
      const candidateCards = (data.candidates || []).map((candidate) => `
        <article class="card ${escapeHTML(data.risk_level)}">
          <span class="pill">${escapeHTML(candidate.confidence)}</span>
          <h3>${escapeHTML(candidate.label)}</h3>
          <p>${escapeHTML(candidate.reason)}</p>
        </article>
      `).join("");
      const notes = (data.care_notes || []).map((item) => `<li>${escapeHTML(item)}</li>`).join("");
      $("photoOut").innerHTML = `
        <article class="card">
          <span class="pill">${escapeHTML(data.model_backend)}</span>
          <h3>${escapeHTML(data.identification_status)}</h3>
          <p>${escapeHTML(analysis.summary || "Image check complete.")}</p>
          <ul class="clean">${notes}</ul>
          ${renderSources(data.sources)}
        </article>
        ${candidateCards}
      `;
    }

    function renderEncyclopedia(data) {
      $("encyAnswer").textContent = data.answer || "No local answer generated.";
      $("encyOut").innerHTML = (data.results || []).map((item) => `
        <article class="card ${escapeHTML(item.risk)}">
          <span class="pill">${escapeHTML(item.risk)}</span>
          <h3>${escapeHTML(item.title)}</h3>
          <p>${escapeHTML(item.text)}</p>
          ${renderSources([item.source])}
        </article>
      `).join("") || "<article class=\"card\">No local results.</article>";
    }

    function renderWeatherPack(pack) {
      if (!pack) {
        $("weatherPackOut").innerHTML = "";
        return;
      }
      const dayCards = (pack.days || []).map((day) => `
        <div class="day">
          <strong>${escapeHTML(day.date)}</strong>
          <span>${escapeHTML(day.summary)}</span><br>
          <span>${escapeHTML(day.min_c)}-${escapeHTML(day.max_c)} C</span><br>
          <span>${escapeHTML(day.rain_mm)} mm / ${escapeHTML(day.rain_probability)}%</span>
        </div>
      `).join("");
      $("weatherPackOut").innerHTML = `
        <article class="card">
          <span class="pill">${pack.online ? "online sync" : (pack.cached ? "cached pack" : "offline only")}</span>
          <h3>${escapeHTML(pack.location?.matched || "Weather pack")}</h3>
          <p>${escapeHTML(pack.rain_summary)}</p>
          <ul class="clean">${(pack.expected_events || []).map((item) => `<li>${escapeHTML(item)}</li>`).join("")}</ul>
          <p class="small">${escapeHTML(pack.provider || "")}</p>
        </article>
        <div class="day-grid">${dayCards}</div>
      `;
    }

    async function refreshHealth() {
      try {
        const data = await getJSON("/api/health");
        $("status").textContent = data.llama_configured ? "llama.cpp ready" : "offline ready";
      } catch (err) {
        $("status").textContent = "offline";
        devLog("Health check failed", { error: err.message });
      }
    }

    async function loadStaticReferences() {
      try {
        const [danger, checklist] = await Promise.all([getJSON("/api/dangers"), getJSON("/api/checklist")]);
        renderDanger(danger.cards);
        renderChecklist(checklist);
      } catch (err) {
        devLog("Reference load failed", { error: err.message });
      }
    }

    $("askBtn").addEventListener("click", async () => {
      $("chatOut").textContent = "Thinking locally...";
      try {
        const data = await postJSON("/api/chat", { message: $("message").value, region: $("region").value });
        const sourceLine = data.sources?.length ? "\n\nSources: " + data.sources.map((s) => s.title).join(" / ") : "";
        $("chatOut").textContent = data.answer + sourceLine;
      } catch (err) {
        $("chatOut").textContent = err.message;
        devLog("Chat failed", { error: err.message });
      }
    });

    $("photoBtn").addEventListener("click", async () => {
      $("photoOut").innerHTML = "<article class=\"card\">Checking locally...</article>";
      const started = performance.now();
      const form = new FormData();
      if ($("image").files[0]) form.append("image", $("image").files[0]);
      form.append("note", $("photoNote").value);
      devLog("POST /api/photo", { file: $("image").files[0]?.name || null, note: $("photoNote").value });
      try {
        const res = await fetch("/api/photo", { method: "POST", body: form });
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const data = await res.json();
        data._duration_ms = Math.round(performance.now() - started);
        renderPhoto(data);
        devLog("DONE /api/photo", data);
      } catch (err) {
        $("photoOut").innerHTML = `<article class="card">${escapeHTML(err.message)}</article>`;
        devLog("Photo failed", { error: err.message });
      }
    });

    $("firstBtn").addEventListener("click", async () => {
      $("firstOut").textContent = "Searching local notes...";
      try {
        const data = await postJSON("/api/firstaid", { topic: $("firstTopic").value });
        $("firstOut").textContent = data.banner + "\n\nSteps:\n" + data.steps.map((s) => `- ${s}`).join("\n") + "\n\nAvoid:\n" + data.do_not.map((s) => `- ${s}`).join("\n");
      } catch (err) {
        $("firstOut").textContent = err.message;
        devLog("First aid failed", { error: err.message });
      }
    });

    $("encyBtn").addEventListener("click", async () => {
      $("encyAnswer").textContent = "Searching local pack...";
      $("encyOut").innerHTML = "";
      try {
        const data = await postJSON("/api/encyclopedia", { query: $("encyQuery").value, limit: 6 });
        renderEncyclopedia(data);
      } catch (err) {
        $("encyAnswer").textContent = err.message;
        devLog("Encyclopedia failed", { error: err.message });
      }
    });

    $("weatherBtn").addEventListener("click", async () => {
      $("weatherOut").textContent = "Checking weather notes...";
      try {
        const data = await postJSON("/api/weather", { region: $("weatherRegion").value, cloud_note: $("cloudNote").value, refresh_live: false });
        $("weatherOut").textContent = data.profile + "\n\n" + data.cloud_read + "\n\n" + data.pre_trip_note;
        renderWeatherPack(data.weather_pack);
      } catch (err) {
        $("weatherOut").textContent = err.message;
        devLog("Weather failed", { error: err.message });
      }
    });

    $("weatherSyncBtn").addEventListener("click", async () => {
      $("weatherOut").textContent = "Syncing the 10-day pack...";
      try {
        const data = await postJSON("/api/weather-pack", { region: $("weatherRegion").value, refresh: true });
        $("weatherOut").textContent = data.online ? "10-day weather pack synced to this device." : "No live connection; showing cached/offline data if available.";
        renderWeatherPack(data);
      } catch (err) {
        $("weatherOut").textContent = err.message;
        devLog("Weather sync failed", { error: err.message });
      }
    });

    $("copyChecklistBtn").addEventListener("click", async () => {
      if (!lastChecklistText) return;
      try {
        await navigator.clipboard.writeText(lastChecklistText);
        $("copyChecklistBtn").textContent = "Copied";
        setTimeout(() => { $("copyChecklistBtn").textContent = "Copy Checklist Text"; }, 1200);
      } catch (err) {
        $("checkExport").focus();
        $("checkExport").select();
      }
    });

    refreshHealth();
    loadStaticReferences();
  </script>
</body>
</html>"""
