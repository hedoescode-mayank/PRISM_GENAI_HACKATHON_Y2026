"""Built-in Web UI for Samsung Smart Guided Troubleshooting Engine."""

from __future__ import annotations

UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Samsung Smart Guided Troubleshooting Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07090e;
      --card-bg: rgba(18, 24, 38, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #3b82f6;
      --primary-glow: rgba(59, 130, 246, 0.35);
      --cyan: #06b6d4;
      --emerald: #10b981;
      --amber: #f59e0b;
      --rose: #f43f5e;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.5;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.10) 0%, transparent 40%);
    }

    .container {
      max-width: 1100px;
      margin: 0 auto;
      padding: 2.5rem 1.5rem;
    }

    /* Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2.5rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--card-border);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .logo-badge {
      background: linear-gradient(135deg, var(--primary), var(--cyan));
      width: 42px;
      height: 42px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.25rem;
      box-shadow: 0 0 20px var(--primary-glow);
    }
    .brand h1 {
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand p {
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .status-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.25);
      color: var(--emerald);
      padding: 0.4rem 0.85rem;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 500;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--emerald);
      box-shadow: 0 0 10px var(--emerald);
    }

    /* Main Grid */
    .grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 2rem;
    }

    /* Query Box */
    .query-card {
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.75rem;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .query-card h2 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .presets {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1.25rem;
    }
    .preset-btn {
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 0.45rem 0.85rem;
      border-radius: 8px;
      font-size: 0.82rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .preset-btn:hover {
      background: rgba(59, 130, 246, 0.12);
      border-color: rgba(59, 130, 246, 0.3);
      color: var(--text);
    }

    textarea {
      width: 100%;
      height: 100px;
      background: rgba(0,0,0,0.3);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1rem;
      color: var(--text);
      font-family: inherit;
      font-size: 0.95rem;
      resize: vertical;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 15px var(--primary-glow);
    }

    .action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1.25rem;
    }
    .btn-submit {
      background: linear-gradient(135deg, var(--primary), var(--cyan));
      color: #fff;
      border: none;
      padding: 0.75rem 1.75rem;
      border-radius: 10px;
      font-weight: 600;
      font-size: 0.95rem;
      cursor: pointer;
      box-shadow: 0 4px 20px var(--primary-glow);
      transition: transform 0.15s, opacity 0.15s;
    }
    .btn-submit:hover {
      transform: translateY(-1px);
      opacity: 0.95;
    }
    .btn-submit:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Results */
    .results-card {
      display: none;
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.75rem;
    }
    .meta-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
      padding-bottom: 1.25rem;
      margin-bottom: 1.5rem;
      border-bottom: 1px solid var(--card-border);
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .meta-item { display: flex; align-items: center; gap: 0.4rem; }
    .meta-value { font-weight: 600; color: var(--text); }
    .pill {
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .pill-hit { background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }
    .pill-miss { background: rgba(244, 63, 94, 0.15); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }

    /* Goal & Actions */
    .goal-header {
      margin-bottom: 1.5rem;
    }
    .goal-header h3 {
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 0.35rem;
      color: #fff;
    }
    .goal-subtitle {
      font-size: 0.88rem;
      color: var(--cyan);
    }

    .action-list {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .action-item {
      background: rgba(255,255,255,0.02);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
    }
    .action-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }
    .action-title {
      font-size: 1rem;
      font-weight: 600;
    }
    .cat-auto { background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }
    .cat-manual { background: rgba(245, 158, 11, 0.15); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); }
    .cat-critical { background: rgba(244, 63, 94, 0.15); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }

    .action-desc {
      font-size: 0.88rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }

    .steps-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    .steps-list li {
      display: flex;
      gap: 0.6rem;
      font-size: 0.9rem;
      color: var(--text);
    }
    .step-num {
      background: rgba(255,255,255,0.07);
      width: 20px;
      height: 20px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 600;
      flex-shrink: 0;
      color: var(--cyan);
    }

    .deeplink-box {
      background: rgba(0,0,0,0.35);
      border: 1px dashed rgba(59, 130, 246, 0.25);
      border-radius: 8px;
      padding: 0.75rem 1rem;
      margin-top: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      color: var(--cyan);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }
    .deeplink-info { word-break: break-all; }
    .btn-copy {
      background: rgba(255,255,255,0.06);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 0.25rem 0.6rem;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
    }
    .btn-copy:hover { color: var(--text); background: rgba(255,255,255,0.12); }

    /* Fallback Banner */
    .fallback-banner {
      background: rgba(245, 158, 11, 0.08);
      border: 1px solid rgba(245, 158, 11, 0.25);
      border-radius: 12px;
      padding: 1.25rem;
      color: var(--amber);
      display: flex;
      align-items: flex-start;
      gap: 0.85rem;
    }

    /* Variations Accordion */
    .variations-section {
      margin-top: 1.5rem;
      border-top: 1px solid var(--card-border);
      padding-top: 1.25rem;
    }
    summary {
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 500;
      color: var(--text-muted);
    }
    summary:hover { color: var(--text); }
    .variations-list {
      margin-top: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      padding-left: 1rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    /* JSON Drawer */
    .json-box {
      background: #030508;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      color: #a7f3d0;
      max-height: 250px;
      overflow-y: auto;
      margin-top: 0.75rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="logo-badge">S</div>
        <div>
          <h1>Samsung Smart Guided Troubleshooting</h1>
          <p>Theme 02 Engine — Local Source-Backed REST Service</p>
        </div>
      </div>
      <div class="status-badge" id="statusBadge">
        <div class="status-dot"></div>
        <span id="statusText">Checking status...</span>
      </div>
    </header>

    <div class="grid">
      <div class="query-card">
        <h2>Describe Complaint / Device Symptom</h2>
        <div class="presets">
          <button class="preset-btn" onclick="setPreset('cracked')">📱 Cracked & Flashing Screen</button>
          <button class="preset-btn" onclick="setPreset('swipe')">📐 Swipe Gestures Wrong Axis</button>
          <button class="preset-btn" onclick="setPreset('blank')">⬛ Blank Display / Won't Turn On</button>
          <button class="preset-btn" onclick="setPreset('battery')">🔋 Battery Drain (Fallback Test)</button>
        </div>
        <textarea id="queryInput" placeholder="e.g. The mobile phone screen is cracked and flashes intermittently."></textarea>
        <div class="action-bar">
          <span style="font-size:0.8rem; color: var(--text-dim);">Engine: Local catalog & SIIS evidence</span>
          <button class="btn-submit" id="submitBtn" onclick="submitQuery()">Troubleshoot Symptom</button>
        </div>
      </div>

      <div class="results-card" id="resultsCard">
        <div class="meta-bar">
          <div class="meta-item">Latency: <span class="meta-value" id="metaLatency">-</span></div>
          <div class="meta-item">Cache: <span class="pill" id="metaCache">-</span></div>
          <div class="meta-item">Model: <span class="meta-value" id="metaModel">-</span></div>
          <div class="meta-item">Cost: <span class="meta-value">$0.00</span></div>
        </div>

        <div id="planContainer"></div>

        <details class="variations-section">
          <summary>View Generated Query Variations (9 Paraphrases)</summary>
          <div class="variations-list" id="variationsList"></div>
        </details>

        <details class="variations-section">
          <summary>Inspect Raw JSON API Response</summary>
          <pre class="json-box" id="jsonBox"></pre>
        </details>
      </div>
    </div>
  </div>

  <script>
    const PRESETS = {
      cracked: "The mobile phone screen is cracked and flashes intermittently.",
      swipe: "The mobile phone swipe navigation moves up or down instead of left or right after downloading an app",
      blank: "My Samsung Galaxy A15/A16 screen suddenly went completely black on its own after about a month of use. It doesn't display anything, even when I try to turn it on.",
      battery: "My phone battery drains very fast when using background apps."
    };

    function setPreset(key) {
      document.getElementById('queryInput').value = PRESETS[key] || '';
    }

    async function checkHealth() {
      try {
        const res = await fetch('/health');
        if (res.ok) {
          const data = await res.json();
          document.getElementById('statusText').innerText = `Online (${data.catalog_entries} catalog URIs)`;
        } else {
          document.getElementById('statusText').innerText = "Degraded / Off-line";
        }
      } catch (err) {
        document.getElementById('statusText').innerText = "Service Error";
      }
    }
    checkHealth();

    async function submitQuery() {
      const q = document.getElementById('queryInput').value.trim();
      if (!q) return;

      const submitBtn = document.getElementById('submitBtn');
      const resultsCard = document.getElementById('resultsCard');
      const planContainer = document.getElementById('planContainer');

      submitBtn.disabled = true;
      submitBtn.innerText = "Processing Engine...";

      try {
        const res = await fetch('/v1/troubleshoot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: q })
        });
        const data = await res.json();

        resultsCard.style.display = 'block';
        document.getElementById('metaLatency').innerText = `${data.meta.latency_ms} ms`;
        
        const cachePill = document.getElementById('metaCache');
        if (data.meta.cache_hit) {
          cachePill.innerText = "Hit";
          cachePill.className = "pill pill-hit";
        } else {
          cachePill.innerText = "Miss";
          cachePill.className = "pill pill-miss";
        }
        document.getElementById('metaModel').innerText = data.meta.model;

        // Render Plan or Fallback
        planContainer.innerHTML = '';
        if (data.fallback === 'no_match' || !data.response.contexts || data.response.contexts.length === 0) {
          planContainer.innerHTML = `
            <div class="fallback-banner">
              <span style="font-size: 1.2rem;">⚠️</span>
              <div>
                <strong>Fallback: Explicit No-Match</strong>
                <p style="font-size:0.85rem; margin-top:0.2rem;">No source-backed troubleshooting plan found for this symptom in the Theme 02 evidence catalog. (Explicit contractual fallback returned)</p>
              </div>
            </div>
          `;
        } else {
          const ctx = data.response.contexts[0];
          let actionsHtml = '';
          (ctx.actions || []).forEach(act => {
            const catClass = act.category === 'auto' ? 'cat-auto' : act.category === 'manual' ? 'cat-manual' : 'cat-critical';
            let stepsHtml = '';
            (act.stepGroups || []).forEach(sg => {
              (sg.steps || []).forEach((st, idx) => {
                stepsHtml += `<li><span class="step-num">${idx + 1}</span><span>${st}</span></li>`;
              });
              if (sg.actionableDeeplink) {
                stepsHtml += `
                  <div class="deeplink-box">
                    <div class="deeplink-info">
                      <div><strong>Bixby Actionable Deep Link:</strong> ${sg.actionableDeeplink.deeplink}</div>
                      <div style="color:var(--text-muted); font-size:0.75rem;">${sg.actionableDeeplink.description}</div>
                    </div>
                    <button class="btn-copy" onclick="navigator.clipboard.writeText('${sg.actionableDeeplink.deeplink}')">Copy</button>
                  </div>
                `;
              }
              if (sg.validationDeeplink) {
                stepsHtml += `
                  <div class="deeplink-box" style="border-color: rgba(16, 185, 129, 0.3); color: var(--emerald);">
                    <div class="deeplink-info">
                      <div><strong>Validation Link:</strong> ${sg.validationDeeplink.deeplink} (Key: ${sg.validationDeeplink.key})</div>
                    </div>
                  </div>
                `;
              }
            });

            actionsHtml += `
              <div class="action-item">
                <div class="action-head">
                  <span class="action-title">${act.actionName}</span>
                  <span class="pill ${catClass}">${act.category.toUpperCase()}</span>
                </div>
                <div class="action-desc">${act.description}</div>
                <ul class="steps-list">${stepsHtml}</ul>
              </div>
            `;
          });

          planContainer.innerHTML = `
            <div class="goal-header">
              <h3>${ctx.title}</h3>
              <div class="goal-subtitle">${ctx.goal}</div>
            </div>
            <div class="action-list">${actionsHtml}</div>
          `;
        }

        // Render Variations
        const varList = document.getElementById('variationsList');
        varList.innerHTML = (data.query_variations || []).map(v => `<div>• ${v}</div>`).join('');

        // Render JSON
        document.getElementById('jsonBox').innerText = JSON.stringify(data, null, 2);

      } catch (err) {
        alert("Failed to query service: " + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Troubleshoot Symptom";
      }
    }
  </script>
</body>
</html>
"""
