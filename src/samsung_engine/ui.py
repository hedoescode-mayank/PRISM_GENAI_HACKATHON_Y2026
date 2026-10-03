"""Built-in Web UI for Samsung Smart Guided Troubleshooting Engine."""

from __future__ import annotations

UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Guided Troubleshooting</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    :root {
      --bg: #F7F8FA;
      --surface: #FFFFFF;
      --text-primary: #111111;
      --text-secondary: #6B7280;
      --border: #E5E7EB;
      --accent: #2563EB;
      --accent-hover: #1D4ED8;
      --success: #10B981;
      --warning: #F59E0B;
      --critical: #EF4444;
      
      --radius-page: 20px;
      --radius-card: 20px;
      --radius-input: 16px;
      --radius-btn: 14px;
      --radius-chip: 999px;
    }
    
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: 'Roboto', -apple-system, sans-serif;
      background-color: var(--bg);
      color: var(--text-primary);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      -webkit-font-smoothing: antialiased;
      line-height: 1.5;
    }

    /* Layout */
    .app-container {
      max-width: 1200px;
      margin: 0 auto;
      width: 100%;
      padding: 0 24px;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 24px 0;
      border-bottom: 1px solid var(--border);
      margin-bottom: 48px;
    }

    .header-left h1 {
      font-size: 18px;
      font-weight: 700;
    }
    .header-left p {
      font-size: 13px;
      color: var(--text-secondary);
    }
    .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      font-weight: 500;
      color: var(--text-secondary);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--success);
    }
    .btn-dev-mode {
      background: none;
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 13px;
      color: var(--text-secondary);
      cursor: pointer;
    }
    .btn-dev-mode:hover {
      background: #F3F4F6;
    }

    .main-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 40px;
    }
    @media (min-width: 900px) {
      .main-grid {
        grid-template-columns: 1fr 1fr;
      }
    }
    @media (max-width: 899px) {
      .main-grid {
        grid-template-columns: 1fr;
      }
      header {
        margin-bottom: 24px;
      }
    }

    /* Hero Section */
    .hero-section {
      max-width: 600px;
    }
    .hero-section h2 {
      font-size: 36px;
      font-weight: 700;
      margin-bottom: 8px;
      line-height: 1.2;
    }
    .hero-section p {
      font-size: 16px;
      color: var(--text-secondary);
      margin-bottom: 32px;
    }

    /* Input Area */
    .input-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-page);
      padding: 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }
    
    textarea {
      width: 100%;
      height: 160px;
      border: 1px solid var(--border);
      border-radius: var(--radius-input);
      padding: 16px;
      font-family: inherit;
      font-size: 16px;
      resize: none;
      outline: none;
      transition: border-color 0.2s;
    }
    textarea:focus {
      border-color: var(--accent);
    }
    
    .btn-primary {
      width: 100%;
      height: 48px;
      background-color: var(--accent);
      color: #FFF;
      border: none;
      border-radius: var(--radius-btn);
      font-size: 16px;
      font-weight: 600;
      margin-top: 16px;
      cursor: pointer;
      transition: background-color 0.2s;
    }
    .btn-primary:hover {
      background-color: var(--accent-hover);
    }
    .btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    /* Examples */
    .examples-section {
      margin-top: 32px;
    }
    .examples-section h3 {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: 12px;
    }
    .examples-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    @media (max-width: 600px) {
      .examples-grid {
        grid-template-columns: 1fr;
      }
    }
    .example-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .example-card:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .example-card i {
      color: var(--text-secondary);
      width: 20px;
      height: 20px;
    }
    .example-card span {
      font-size: 14px;
      font-weight: 500;
    }

    /* Loading State */
    #loadingState {
      display: none;
      padding: 40px 0;
    }
    .loading-title {
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 24px;
    }
    .loading-steps {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .loading-step {
      display: flex;
      align-items: center;
      gap: 12px;
      color: var(--text-secondary);
      font-size: 15px;
    }
    .loading-step.active {
      color: var(--accent);
      font-weight: 500;
    }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid var(--border);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      opacity: 0;
    }
    .loading-step.active .spinner { opacity: 1; }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Results */
    #resultState {
      display: none;
    }
    .result-header {
      margin-bottom: 32px;
    }
    .result-header h2 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .result-header p {
      font-size: 16px;
      color: var(--text-secondary);
    }

    .issue-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-card);
      padding: 24px;
      margin-bottom: 32px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }
    .issue-label {
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }
    .issue-title {
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 16px;
    }
    .issue-complaint {
      padding-top: 16px;
      border-top: 1px solid var(--border);
      font-size: 15px;
      color: var(--text-secondary);
      font-style: italic;
    }
    .source-badge {
      display: inline-block;
      margin-top: 12px;
      font-size: 12px;
      background: #F3F4F6;
      padding: 4px 8px;
      border-radius: 6px;
      color: var(--text-secondary);
    }

    /* Timeline */
    .timeline {
      position: relative;
    }
    .timeline::before {
      content: '';
      position: absolute;
      left: 14px;
      top: 0;
      bottom: 0;
      width: 2px;
      background: var(--border);
    }

    .action-node {
      position: relative;
      padding-left: 48px;
      margin-bottom: 40px;
    }
    .action-number {
      position: absolute;
      left: 0;
      top: 0;
      width: 30px;
      height: 30px;
      background: var(--surface);
      border: 2px solid var(--border);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 700;
      color: var(--text-secondary);
      z-index: 1;
    }
    
    .action-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-card);
      padding: 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }
    
    .action-type {
      display: inline-block;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 8px;
      border-radius: 6px;
      margin-bottom: 12px;
    }
    .type-auto { background: rgba(16, 185, 129, 0.1); color: var(--success); }
    .type-manual { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
    .type-critical { background: rgba(239, 68, 68, 0.1); color: var(--critical); }

    .action-title {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 4px;
    }
    .action-desc {
      font-size: 15px;
      color: var(--text-secondary);
      margin-bottom: 24px;
    }

    .step-list {
      list-style: none;
      margin-bottom: 24px;
    }
    .step-item {
      display: flex;
      gap: 12px;
      margin-bottom: 12px;
      font-size: 15px;
    }
    .step-num {
      width: 24px;
      height: 24px;
      background: #F3F4F6;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      flex-shrink: 0;
    }

    .btn-secondary {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--surface);
      border: 1px solid var(--border);
      padding: 10px 16px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-secondary:hover {
      background: #F9FAFB;
    }
    .btn-secondary i {
      width: 18px;
      height: 18px;
    }
    
    .fallback-message {
      margin-top: 12px;
      padding: 12px;
      background: #F9FAFB;
      border-radius: 8px;
      font-size: 13px;
      color: var(--text-secondary);
      display: none;
    }

    .validation-box {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }
    .val-header {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }
    .val-content {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: var(--success);
      font-weight: 500;
    }

    /* Developer Details Drawer */
    #devDetails {
      display: none;
      margin-top: 48px;
      padding: 24px;
      background: #F9FAFB;
      border: 1px solid var(--border);
      border-radius: var(--radius-card);
      font-size: 13px;
    }
    .dev-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .dev-box {
      background: var(--surface);
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
    }
    .dev-label {
      color: var(--text-secondary);
      margin-bottom: 4px;
    }
    .dev-value {
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
    }
    .json-pre {
      background: #111827;
      color: #A7F3D0;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
    }

    footer {
      padding: 40px 0;
      text-align: center;
      font-size: 13px;
      color: var(--text-secondary);
      margin-top: auto;
    }
    
    .hidden { display: none !important; }
  </style>
</head>
<body>

  <div class="app-container">
    <header>
      <div class="header-left">
        <h1>Smart Guided Troubleshooting</h1>
        <p>Source-backed guidance for Galaxy device issues</p>
      </div>
      <div class="header-right">
        <div class="status" id="statusBadge">
          <div class="status-dot" id="statusDot"></div>
          <span id="statusText">Checking...</span>
        </div>
        <button class="btn-dev-mode" onclick="toggleDevMode()">Developer details</button>
      </div>
    </header>

    <div class="main-grid" id="mainLayout">
      
      <!-- Left Column / Hero & Input -->
      <div>
        <div class="hero-section">
          <h2>What’s wrong with your Galaxy device?</h2>
          <p>Describe the problem in your own words.<br>We’ll turn it into clear troubleshooting steps.</p>
        </div>

        <div class="input-card">
          <textarea id="queryInput" placeholder="Tell us what is happening...&#10;Example: My screen is cracked and flashes intermittently."></textarea>
          <button class="btn-primary" id="submitBtn" onclick="submitQuery()">Create troubleshooting plan</button>
        </div>

        <div class="examples-section">
          <h3>Try an example</h3>
          <div class="examples-grid">
            <div class="example-card" onclick="setPreset('cracked')">
              <i data-lucide="smartphone"></i> <span>Cracked screen</span>
            </div>
            <div class="example-card" onclick="setPreset('swipe')">
              <i data-lucide="move"></i> <span>Navigation issue</span>
            </div>
            <div class="example-card" onclick="setPreset('blank')">
              <i data-lucide="monitor-x"></i> <span>Screen won't turn on</span>
            </div>
            <div class="example-card" onclick="setPreset('battery')">
              <i data-lucide="battery-warning"></i> <span>Battery drains quickly</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Right Column / Results & Loading -->
      <div>
        
        <!-- Loading State -->
        <div id="loadingState">
          <div class="loading-title">Understanding your problem</div>
          <div class="loading-steps">
            <div class="loading-step active" id="step1"><div class="spinner"></div>Understanding complaint</div>
            <div class="loading-step" id="step2"><div class="spinner"></div>Retrieving trusted guidance</div>
            <div class="loading-step" id="step3"><div class="spinner"></div>Finding relevant device actions</div>
            <div class="loading-step" id="step4"><div class="spinner"></div>Validating troubleshooting plan</div>
          </div>
        </div>

        <!-- Result State -->
        <div id="resultState">
          <div class="result-header">
            <h2>Troubleshooting plan</h2>
            <p>We found a guided path for your issue.</p>
          </div>

          <div class="issue-card" id="issueCard">
            <div class="issue-label">Issue identified</div>
            <div class="issue-title" id="issueTitle"></div>
            <div class="issue-complaint">
              " <span id="issueComplaintText"></span> "
            </div>
            <div class="source-badge">Source-backed</div>
          </div>

          <div class="timeline" id="timelineContainer">
            <!-- Actions inserted here -->
          </div>
        </div>

      </div>
    </div>
    
    <!-- Developer Details -->
    <div id="devDetails">
      <h3 style="margin-bottom:16px; font-size:16px;">Developer Details</h3>
      <div class="dev-grid">
        <div class="dev-box">
          <div class="dev-label">Cache</div>
          <div class="dev-value" id="devCache">-</div>
        </div>
        <div class="dev-box">
          <div class="dev-label">Latency</div>
          <div class="dev-value" id="devLatency">-</div>
        </div>
        <div class="dev-box">
          <div class="dev-label">Model</div>
          <div class="dev-value" id="devModel">-</div>
        </div>
        <div class="dev-box">
          <div class="dev-label">Catalog</div>
          <div class="dev-value" id="devCatalog">-</div>
        </div>
      </div>
      
      <h4 style="margin-bottom:8px;">Query Variations</h4>
      <div id="devVariations" style="margin-bottom:24px; color:var(--text-secondary); line-height:1.6;"></div>
      
      <h4 style="margin-bottom:8px;">Raw Response JSON</h4>
      <pre class="json-pre" id="devJson"></pre>
    </div>

    <footer>
      &copy; 2026 Samsung Electronics. All rights reserved.
    </footer>
  </div>

  <script>
    lucide.createIcons();

    const PRESETS = {
      cracked: "The mobile phone screen is cracked and flashes intermittently.",
      swipe: "The mobile phone swipe navigation moves up or down instead of left or right after downloading an app",
      blank: "My Samsung Galaxy A15/A16 screen suddenly went completely black on its own after about a month of use. It doesn't display anything, even when I try to turn it on.",
      battery: "My phone battery drains very fast when using background apps."
    };

    let devMode = false;
    let catalogCount = 0;

    function setPreset(key) {
      document.getElementById('queryInput').value = PRESETS[key] || '';
    }

    function toggleDevMode() {
      devMode = !devMode;
      document.getElementById('devDetails').style.display = devMode ? 'block' : 'none';
      if(devMode) {
         window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }
    }

    async function checkHealth() {
      try {
        const res = await fetch('/health');
        if (res.ok) {
          const data = await res.json();
          catalogCount = data.catalog_entries || 0;
          document.getElementById('statusText').innerText = "Service ready";
          document.getElementById('devCatalog').innerText = `${catalogCount} URIs`;
        } else {
          document.getElementById('statusText').innerText = "Degraded";
          document.getElementById('statusDot').style.backgroundColor = 'var(--warning)';
        }
      } catch (err) {
        document.getElementById('statusText').innerText = "Offline";
        document.getElementById('statusDot').style.backgroundColor = 'var(--critical)';
      }
    }
    checkHealth();

    // Fake loading sequence simulation
    async function runLoadingSequence() {
      const steps = ['step1', 'step2', 'step3', 'step4'];
      for(let i=0; i<steps.length; i++) {
        steps.forEach(s => document.getElementById(s).classList.remove('active'));
        document.getElementById(steps[i]).classList.add('active');
        // Wait 300-600ms per step just to show sequence
        await new Promise(r => setTimeout(r, 400 + Math.random()*200)); 
      }
    }

    function fallbackBtn(btn) {
      const fb = btn.nextElementSibling;
      fb.style.display = 'block';
    }

    async function submitQuery() {
      const q = document.getElementById('queryInput').value.trim();
      if (!q) return;

      const submitBtn = document.getElementById('submitBtn');
      const resultState = document.getElementById('resultState');
      const loadingState = document.getElementById('loadingState');
      
      submitBtn.disabled = true;
      resultState.style.display = 'none';
      loadingState.style.display = 'block';
      
      // We run the fetch and the loading animation concurrently, 
      // but await the animation to ensure smooth UX before showing results.
      const fetchPromise = fetch('/v1/troubleshoot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q })
      }).then(res => res.json()).catch(err => ({ error: err.message }));

      const [data] = await Promise.all([fetchPromise, runLoadingSequence()]);
      
      loadingState.style.display = 'none';
      
      if (data.error) {
        alert("Failed to query service: " + data.error);
        submitBtn.disabled = false;
        return;
      }

      // Populate Developer Details
      document.getElementById('devLatency').innerText = `${data.meta.latency_ms} ms`;
      document.getElementById('devCache').innerText = data.meta.cache_hit ? "HIT" : "MISS";
      document.getElementById('devModel').innerText = data.meta.model;
      
      document.getElementById('devVariations').innerHTML = (data.query_variations || []).map(v => `<div>• ${v}</div>`).join('');
      document.getElementById('devJson').innerText = JSON.stringify(data, null, 2);

      // Populate Results
      const timeline = document.getElementById('timelineContainer');
      timeline.innerHTML = '';
      document.getElementById('issueComplaintText').innerText = q;

      if (data.fallback === 'no_match' || !data.response.contexts || data.response.contexts.length === 0) {
        document.getElementById('issueTitle').innerText = "No specific match found";
        timeline.innerHTML = `
          <div style="padding: 24px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; text-align: center;">
            <p style="color: var(--text-secondary);">We couldn't find a source-backed plan for this issue in the current catalog.</p>
          </div>
        `;
      } else {
        const ctx = data.response.contexts[0];
        document.getElementById('issueTitle').innerText = ctx.title;
        
        let actionsHtml = '';
        (ctx.actions || []).forEach((act, actIdx) => {
          
          let typeLabel = act.category === 'auto' ? 'Recommended action' : act.category === 'manual' ? 'Manual step' : 'Important safety step';
          let typeClass = act.category === 'auto' ? 'type-auto' : act.category === 'manual' ? 'type-manual' : 'type-critical';

          let stepsHtml = '';
          (act.stepGroups || []).forEach(sg => {
            (sg.steps || []).forEach((st, idx) => {
              stepsHtml += `
                <li class="step-item">
                  <div class="step-num">${idx + 1}</div>
                  <div>${st}</div>
                </li>
              `;
            });
            
            if (sg.actionableDeeplink) {
              stepsHtml += `
                <div style="margin-top: 16px;">
                  <button class="btn-secondary" onclick="fallbackBtn(this)">
                    <i data-lucide="external-link"></i> Open setting
                  </button>
                  <div class="fallback-message">
                    <strong>This setting can't be opened here</strong><br>
                    You're viewing the troubleshooting plan in a browser that doesn't support this device action.<br>
                    <div style="font-family:'JetBrains Mono',monospace; color:var(--accent); margin-top:6px;">URI: ${sg.actionableDeeplink.deeplink}</div>
                  </div>
                </div>
              `;
            }
            if (sg.validationDeeplink) {
              stepsHtml += `
                <div class="validation-box">
                  <div class="val-header">Verification ready</div>
                  <div class="val-content">
                    <i data-lucide="check-circle-2" style="width:16px; height:16px;"></i>
                    This step can be verified when device-state access is available.
                  </div>
                </div>
              `;
            }
          });

          let actionNum = (actIdx + 1).toString().padStart(2, '0');

          actionsHtml += `
            <div class="action-node">
              <div class="action-number">${actionNum}</div>
              <div class="action-card">
                <div class="action-type ${typeClass}">${typeLabel}</div>
                <div class="action-title">${act.actionName}</div>
                <div class="action-desc">${act.description}</div>
                <ul class="step-list">${stepsHtml}</ul>
              </div>
            </div>
          `;
        });
        timeline.innerHTML = actionsHtml;
      }
      
      lucide.createIcons(); // Refresh icons inside the new HTML
      resultState.style.display = 'block';
      submitBtn.disabled = false;
      
      // Auto-scroll on mobile
      if(window.innerWidth < 900) {
        resultState.scrollIntoView({behavior: "smooth"});
      }
    }
  </script>
</body>
</html>
"""
