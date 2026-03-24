// frontend/app.js - FinSight AI
// Full integration + CSV + Timeline

// Register Service Worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js")
      .then((reg) => console.log("SW registered:", reg.scope))
      .catch((err) => console.error("SW failed:", err));
  });
}

const API_BASE = window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "https://finsight-ai.vercel.app";
const PDF_BASE = "https://margaret-06-finsight-pdf.hf.space";
const IS_LOCALHOST = window.location.hostname === "localhost";
const ALLOW_MOCK_FALLBACK = IS_LOCALHOST;

// State
let currentResults = null;
let csvContent = null;
let pdfFile = null;
let activeTab = "sms";

// Demo data
const DEMO_SMS = `Access Bank: Your account credited with N150,000.00. Narration: Salary March 2026. Bal: N150,000.00
Acct 0123456789 debited with NGN5,000.00 on 01-Mar-26. Desc: UBER TRIP. Bal: NGN145,000.00
Acct 0123456789 debited with NGN4,500.00 on 02-Mar-26. Desc: KFC IKEJA. Bal: NGN140,500.00
Acct 0123456789 debited with NGN15,000.00 on 03-Mar-26. Desc: JUMIA ORDER. Bal: NGN125,500.00
Acct 0123456789 debited with NGN5,000.00 on 03-Mar-26. Desc: DSTV SUBSCRIPTION. Bal: NGN120,500.00
Acct 0123456789 debited with NGN3,000.00 on 05-Mar-26. Desc: AIRTEL DATA. Bal: NGN117,500.00
Acct 0123456789 debited with NGN12,000.00 on 07-Mar-26. Desc: CLUB OUTING LAGOS. Bal: NGN105,500.00
Acct 0123456789 debited with NGN8,500.00 on 08-Mar-26. Desc: CINEMA GENESIS. Bal: NGN97,000.00
Acct 0123456789 debited with NGN3,200.00 on 10-Mar-26. Desc: CHICKEN REPUBLIC. Bal: NGN93,800.00
Acct 0123456789 debited with NGN9,000.00 on 25-Mar-26. Desc: SLOT ELECTRONICS. Bal: NGN57,723.00`;

const DEMO_CSV = `Date,Description,Debit,Credit,Balance
01/03/2026,Salary March 2026,,150000,150000
01/03/2026,Uber Trip,5000,,145000
02/03/2026,KFC Ikeja,4500,,140500
03/03/2026,Jumia Order,15000,,125500
03/03/2026,DSTV Subscription,5000,,120500
05/03/2026,Airtel Data,3000,,117500
07/03/2026,Club Outing Lagos,12000,,105500
08/03/2026,Cinema Genesis,8500,,97000
10/03/2026,Chicken Republic,3200,,93800
25/03/2026,Slot Electronics,9000,,57723`;

function getEl(id) {
  return document.getElementById(id);
}

function switchTab(tab) {
  activeTab = tab === "csv" ? "csv" : (tab === "pdf" ? "pdf" : "sms");

  getEl("contentSMS")?.classList.toggle("hidden", activeTab !== "sms");
  getEl("contentCSV")?.classList.toggle("hidden", activeTab !== "csv");
  getEl("contentPDF")?.classList.toggle("hidden", activeTab !== "pdf");

  const tabSMS = getEl("tabSMS");
  const tabCSV = getEl("tabCSV");
  const tabPDF = getEl("tabPDF");
  tabSMS?.classList.toggle("active", activeTab === "sms");
  tabCSV?.classList.toggle("active", activeTab === "csv");
  tabPDF?.classList.toggle("active", activeTab === "pdf");
  tabSMS?.setAttribute("aria-selected", activeTab === "sms" ? "true" : "false");
  tabCSV?.setAttribute("aria-selected", activeTab === "csv" ? "true" : "false");
  tabPDF?.setAttribute("aria-selected", activeTab === "pdf" ? "true" : "false");
}

function loadDemoData() {
  const input = getEl("smsInput");
  if (input) input.value = DEMO_SMS;
  showToast("Demo SMS loaded. Click Analyze.");
}

function loadDemoCSV() {
  csvContent = DEMO_CSV;
  showCSVPreview("demo-statement.csv", 10);
  switchTab("csv");
  showToast("Demo CSV loaded. Click Analyze Statement.");
}

function handleCSVFile(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    csvContent = String(e.target?.result || "");
    const rows = Math.max(0, csvContent.split(/\r?\n/).filter(Boolean).length - 1);
    showCSVPreview(file.name, rows);
    showToast(`${file.name} loaded - ${rows} rows found.`);
  };
  reader.onerror = () => showToast("Unable to read CSV file.", "error");
  reader.readAsText(file);
}

function handleCSVDrop(event) {
  event.preventDefault();
  const file = event?.dataTransfer?.files?.[0];
  if (!file || !file.name.toLowerCase().endsWith(".csv")) {
    showToast("Please drop a .csv file.", "error");
    return;
  }

  const input = getEl("csvFileInput");
  if (input && event.dataTransfer?.files) {
    input.files = event.dataTransfer.files;
  }
  handleCSVFile({ target: { files: [file] } });
}

function handlePDFFile(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showToast("Please select a .pdf file.", "error");
    return;
  }

  pdfFile = file;
  const fileName = getEl("pdfFileName");
  const status = getEl("pdfStatus");
  if (fileName) fileName.textContent = file.name;
  if (status) status.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
  getEl("pdfPreview")?.classList.remove("hidden");
  getEl("pdfDropZone")?.classList.add("has-file");
  showToast(`${file.name} loaded.`);
}

function handlePDFDrop(event) {
  event.preventDefault();
  const file = event?.dataTransfer?.files?.[0];
  if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
    showToast("Please drop a .pdf file.", "error");
    return;
  }

  const input = getEl("pdfFileInput");
  if (input && event.dataTransfer?.files) {
    input.files = event.dataTransfer.files;
  }
  handlePDFFile({ target: { files: [file] } });
}

function showCSVPreview(name, rows) {
  const fileName = getEl("csvFileName");
  const rowCount = getEl("csvRowCount");
  if (fileName) fileName.textContent = name;
  if (rowCount) rowCount.textContent = `${rows} transactions`;
  getEl("csvPreview")?.classList.remove("hidden");
  getEl("csvDropZone")?.classList.add("has-file");
}

async function analyzeNow() {
  const smsText = String(getEl("smsInput")?.value || "").trim();
  if (!smsText) {
    showToast("Please paste your SMS alerts first.", "error");
    return;
  }
  await runAnalysis({ sms_text: smsText }, "/api/analyze");
}

async function analyzeCSV() {
  if (!csvContent) {
    showToast("Please upload or load a CSV file first.", "error");
    return;
  }

  showLoading(true);
  hideResults();

  try {
    await animateLoadingSteps();

    const form = new FormData();
    form.append("csv_text", csvContent);

    const parseResponse = await fetch(`${API_BASE}/api/parse/csv/text`, {
      method: "POST",
      body: form
    });

    if (!parseResponse.ok) {
      throw new Error(`CSV parse failed: ${parseResponse.status}`);
    }

    const parseResult = await parseResponse.json();
    const parsedTransactions = parseResult?.data?.parsed;
    if (!parseResult?.success || !Array.isArray(parsedTransactions) || parsedTransactions.length === 0) {
      throw new Error(parseResult?.error || "CSV parsing returned no transactions");
    }

    const analyzeResponse = await fetchJson(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sms_text: buildSMSFromTransactions(parsedTransactions)
      })
    });

    currentResults = analyzeResponse;
    showLoading(false);
    renderResults(analyzeResponse);
  } catch (err) {
    showLoading(false);
    const message = err?.message || "CSV analysis failed";

    if (ALLOW_MOCK_FALLBACK) {
      console.warn("CSV analysis error - using mock data:", message);
      showToast("CSV API unavailable in local mode. Showing demo data.", "warning");
      const mock = getMockResults();
      currentResults = mock;
      renderResults(mock);
      return;
    }

    console.warn("CSV analysis error:", message);
    showToast(`CSV analysis failed: ${message}`, "error");
  }
}

async function analyzePDF() {
  if (!pdfFile) {
    showToast("Please upload or load a PDF file first.", "error");
    return;
  }

  showLoading(true);
  hideResults();

  try {
    await animateLoadingSteps();

    const formData = new FormData();
    formData.append("file", pdfFile);

    const response = await fetch(`${API_BASE}/api/parse/pdf`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`PDF parse failed: ${response.status}`);
    }

    const parseResult = await response.json();

    if (!parseResult?.parsed || !Array.isArray(parseResult.parsed)) {
      throw new Error("PDF parsing returned invalid data");
    }

    const analyzeResponse = await fetchJson(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sms_text: buildSMSFromTransactions(parseResult.parsed)
      })
    });

    currentResults = analyzeResponse;
    showLoading(false);
    renderResults(analyzeResponse);
  } catch (err) {
    showLoading(false);
    const message = err?.message || "PDF analysis failed";

    if (ALLOW_MOCK_FALLBACK) {
      console.warn("PDF analysis error - using mock data:", message);
      showToast("PDF API unavailable in local mode. Showing demo data.", "warning");
      const mock = getMockResults();
      currentResults = mock;
      renderResults(mock);
      return;
    }

    console.warn("PDF analysis error:", message);
    showToast(`PDF analysis failed: ${message}`, "error");
  }
}

function loadDemoPDF() {
  pdfFile = { name: "demo-statement.pdf" };
  const fileName = getEl("pdfFileName");
  const status = getEl("pdfStatus");
  if (fileName) fileName.textContent = "demo-statement.pdf";
  if (status) status.textContent = "Ready to analyze";
  getEl("pdfPreview")?.classList.remove("hidden");
  getEl("pdfDropZone")?.classList.add("has-file");
  switchTab("pdf");
  showToast("Demo PDF loaded. Click Extract & Analyze.");
}

function buildSMSFromTransactions(transactions) {
  return transactions.map((t) => {
    const type = t.type === "credit" ? "credited" : "debited";
    const amount = Number(t.amount || 0).toFixed(2);
    const balance = Number(t.balance || 0).toFixed(2);
    return `Acct ${type} with NGN${amount} on ${t.transaction_date}. Desc: ${t.description}. Bal: NGN${balance}`;
  }).join("\n");
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  return response.json();
}

async function runAnalysis(payload, endpoint, transformer = null) {
  showLoading(true);
  hideResults();

  try {
    await animateLoadingSteps();

    let data;
    if (transformer) {
      const firstData = await fetchJson(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      data = await transformer(firstData);
    } else {
      data = await fetchJson(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    currentResults = data;
    showLoading(false);
    renderResults(data);
  } catch (err) {
    showLoading(false);
    const message = err?.message || "Analysis failed";

    if (ALLOW_MOCK_FALLBACK) {
      console.warn("API unavailable in local mode - using mock data:", message);
      showToast("Local demo mode - API not connected.", "warning");
      const mock = getMockResults();
      currentResults = mock;
      renderResults(mock);
      return;
    }

    console.warn("Analysis failed:", message);
    showToast(`Analysis failed: ${message}`, "error");
  }
}

async function animateLoadingSteps() {
  const steps = ["step1", "step2", "step3", "step4"];
  const msgs = [
    "Reading your financial data...",
    "Calculating health score...",
    "Predicting your financial future...",
    "Generating action plan..."
  ];

  for (let i = 0; i < steps.length; i += 1) {
    const loadingText = getEl("loadingText");
    if (loadingText) loadingText.textContent = msgs[i];

    steps.forEach((step, idx) => {
      getEl(step)?.classList.toggle("active", idx <= i);
    });

    await sleep(550);
  }
}

function renderResults(data) {
  getEl("resultsPanel")?.classList.remove("hidden");
  renderScore(data.score || {});
  renderDaysToZero(data.days_to_zero || {});
  renderPatterns(data.patterns || {});
  renderPillars(data.score?.pillars || null);
  renderTimeline(data.transactions || []);

  getEl("resultsPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderScore(s) {
  const score = Number(s.score || 0);
  animateNumber("scoreNumber", 0, score, 1200);

  const scoreLabel = getEl("scoreLabel");
  const scoreMessage = getEl("scoreMessage");
  if (scoreLabel) scoreLabel.textContent = s.label || "-";
  if (scoreMessage) scoreMessage.textContent = s.message || "-";

  getEl("scoreCard")?.setAttribute("data-color", s.color || "gray");

  window.setTimeout(() => {
    const ring = getEl("ringFill");
    if (!ring) return;
    ring.style.strokeDashoffset = String(314 - (score / 100) * 314);
    ring.setAttribute("data-color", s.color || "gray");
  }, 300);
}

function renderDaysToZero(d) {
  const days = d.days_remaining;
  getEl("daysCard")?.setAttribute("data-urgency", d.urgency || "low");

  if (days !== null && days !== undefined) {
    animateNumber("daysNumber", 0, Number(days), 1500);
  } else {
    const daysNumber = getEl("daysNumber");
    if (daysNumber) daysNumber.textContent = "N/A";
  }

  const msg = getEl("daysMessage");
  if (msg) msg.textContent = d.message || "-";

  const burn = getEl("dailyBurn");
  if (burn) {
    burn.textContent = `₦${Number(d.daily_burn_rate || 0).toLocaleString("en-NG", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  }
}

function renderPatterns(p) {
  const patterns = Array.isArray(p.patterns) ? p.patterns : [];
  const patternCount = getEl("patternCount");
  if (patternCount) {
    const count = Number(p.count || 0);
    patternCount.textContent = `${count} pattern${count !== 1 ? "s" : ""} found`;
  }

  const list = getEl("patternsList");
  if (!list) return;

  if (patterns.length === 0) {
    list.innerHTML = '<div class="pattern-empty">No concerning patterns detected.</div>';
    return;
  }

  list.innerHTML = patterns.map((pat, i) => `
    <div class="pattern-item severity-${pat.severity}" style="animation-delay:${i * 150}ms">
      <div class="pattern-top">
        <span class="pattern-title">${pat.title}</span>
        <span class="pattern-badge ${pat.severity}">${pat.severity}</span>
      </div>
      <div class="pattern-detail">${pat.detail}</div>
    </div>
  `).join("");
}

function renderPillars(pillars) {
  if (!pillars) return;

  const labels = {
    income_stability: "Income Stability",
    spending_control: "Spending Control",
    savings_behavior: "Savings Behavior",
    bill_regularity: "Bill Regularity",
    category_diversity: "Category Diversity"
  };

  const maxes = {
    income_stability: 25,
    spending_control: 25,
    savings_behavior: 20,
    bill_regularity: 15,
    category_diversity: 15
  };

  const pillarsList = getEl("pillarsList");
  if (!pillarsList) return;

  pillarsList.innerHTML = Object.entries(pillars).map(([k, v]) => {
    const max = maxes[k] || 25;
    const pct = Math.round((Number(v || 0) / max) * 100);

    return `
      <div class="pillar-item">
        <div class="pillar-top">
          <span class="pillar-label">${labels[k] || k}</span>
          <span class="pillar-value">${v}/${max}</span>
        </div>
        <div class="pillar-bar-bg">
          <div class="pillar-bar-fill" style="width:0" data-target="${pct}"></div>
        </div>
      </div>
    `;
  }).join("");

  window.setTimeout(() => {
    document.querySelectorAll(".pillar-bar-fill").forEach((bar) => {
      const target = bar.getAttribute("data-target") || "0";
      bar.style.width = `${target}%`;
    });
  }, 400);
}

function renderTimeline(transactions) {
  const list = getEl("timelineList");
  const count = getEl("timelineCount");
  if (!list) return;

  if (!transactions || transactions.length === 0) {
    list.innerHTML = '<div class="timeline-empty">No transactions to display.</div>';
    if (count) count.textContent = "0 total";
    return;
  }

  const recent = [...transactions]
    .sort((a, b) => new Date(b.transaction_date) - new Date(a.transaction_date))
    .slice(0, 8);

  if (count) count.textContent = `${transactions.length} total`;

  list.innerHTML = recent.map((t) => {
    const isCredit = t.type === "credit";
    const sign = isCredit ? "+" : "-";
    const cls = isCredit ? "txn-credit" : "txn-debit";

    return `
      <div class="timeline-item">
        <div class="txn-left">
          <div class="txn-dot ${cls}"></div>
          <div class="txn-info">
            <div class="txn-desc">${t.description || "Transaction"}</div>
            <div class="txn-meta">${t.transaction_date} · ${t.category || "Uncategorized"}</div>
          </div>
        </div>
        <div class="txn-amount ${cls}">
          ${sign}₦${Number(t.amount || 0).toLocaleString("en-NG")}
        </div>
      </div>
    `;
  }).join("");
}

function fixThis() {
  if (!currentResults) {
    showToast("Run analysis first.", "error");
    return;
  }

  const card = getEl("actionsCard");
  if (!card) return;

  card.classList.remove("hidden");
  card.scrollIntoView({ behavior: "smooth", block: "start" });
  renderActions(currentResults.actions || getMockActions());
}

function renderActions(actions) {
  const actionsList = getEl("actionsList");
  if (!actionsList) return;

  actionsList.innerHTML = actions.map((a, i) => `
    <div class="action-item impact-${a.impact}" style="animation-delay:${i * 200}ms">
      <div class="action-number">${i + 1}</div>
      <div class="action-body">
        <div class="action-title">${a.title}</div>
        <div class="action-detail">${a.detail}</div>
        <span class="action-impact impact-${a.impact}">${a.impact} impact</span>
      </div>
    </div>
  `).join("");
}

// Auth gate before any Interswitch action.
async function requireAuth(actionFn) {
  const session = await getSupabaseSession();
  if (!session) {
    showAuthModal(actionFn);
    return;
  }
  await actionFn();
}

function showAuthModal(pendingAction) {
  const modal = getEl("authModal");
  if (!modal) {
    showToast("Sign-in modal not available.", "error");
    return;
  }

  modal.classList.remove("hidden");
  modal._pendingAction = pendingAction;
}

function closeAuthModal(clearPending = true) {
  const modal = getEl("authModal");
  if (!modal) return;

  modal.classList.add("hidden");
  if (clearPending) {
    modal._pendingAction = null;
  }
}

function setupAuthModalBehavior() {
  const modal = getEl("authModal");
  if (!modal) return;

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeAuthModal(true);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.classList.contains("hidden")) {
      closeAuthModal(true);
    }
  });
}

async function signInWithGoogle() {
  if (!window.supabase?.auth) {
    showToast("Supabase is not configured.", "error");
    return;
  }

  const { error } = await window.supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.href }
  });

  if (error) showToast(`Sign-in failed: ${error.message}`, "error");
}

async function getSupabaseSession() {
  if (!window.supabase?.auth) return null;
  const { data } = await window.supabase.auth.getSession();
  return data?.session || null;
}

async function showHistoryModal() {
  const session = await getSupabaseSession();
  if (!session) {
    showToast("Please sign in to view your history.", "info");
    return;
  }

  const modal = getEl("historyModal");
  if (!modal) {
    showToast("History modal not available.", "error");
    return;
  }

  modal.classList.remove("hidden");
  await loadHistory(session.user.id);
}

function closeHistoryModal() {
  const modal = getEl("historyModal");
  if (!modal) return;
  modal.classList.add("hidden");
}

async function loadHistory(userId) {
  const loading = getEl("historyLoading");
  const list = getEl("historyList");
  const empty = getEl("historyEmpty");

  if (!loading || !list || !empty) return;

  loading.classList.remove("hidden");
  list.classList.add("hidden");
  empty.classList.add("hidden");

  try {
    const response = await fetchJson(`${API_BASE}/api/history/${userId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });

    if (response?.analyses && Array.isArray(response.analyses) && response.analyses.length > 0) {
      renderHistoryList(response.analyses);
      list.classList.remove("hidden");
    } else {
      empty.classList.remove("hidden");
    }
  } catch (err) {
    console.warn("Failed to load history:", err?.message || err);
    empty.classList.remove("hidden");
    showToast("Unable to load history.", "warning");
  } finally {
    loading.classList.add("hidden");
  }
}

function renderHistoryList(analyses) {
  const list = getEl("historyList");
  if (!list) return;

  list.innerHTML = analyses.slice(0, 20).map((analysis, idx) => {
    const date = new Date(analysis.timestamp || Date.now());
    const dateStr = date.toLocaleDateString("en-NG", { 
      month: "short", 
      day: "numeric", 
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
    const score = analysis.score?.score || "-";
    const label = analysis.score?.label || "Unknown";
    const color = analysis.score?.color || "gray";

    return `
      <div class="history-item" style="animation-delay:${idx * 100}ms">
        <div class="history-item-left">
          <div class="history-score ${color}">${score}</div>
          <div class="history-info">
            <div class="history-label">${label}</div>
            <div class="history-date">${dateStr}</div>
          </div>
        </div>
        <div class="history-actions">
          <button class="btn btn-ghost history-view-btn" onclick="viewAnalysis('${analysis.id}')" type="button">
            View
          </button>
        </div>
      </div>
    `;
  }).join("");

  list.classList.remove("hidden");
}

function viewAnalysis(analysisId) {
  showToast(`Loading analysis ${analysisId}...`);
  closeHistoryModal();
  // TODO: Implement loading and displaying saved analysis
}

async function simulateSave() {
  await requireAuth(_doSave);
}

async function simulateBill() {
  await requireAuth(_doBill);
}

async function _doSave() {
  const result = getEl("interswitchResult");
  if (!result) return;

  result.classList.remove("hidden");
  result.innerHTML = '<div class="interswitch-loading">Connecting to Interswitch...</div>';

  try {
    const data = await fetchJson(`${API_BASE}/api/action/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: 5000, user_id: "demo-user" })
    });

    result.innerHTML = `
      <div class="interswitch-success">
        <strong>${data.message}</strong><br/>
        Reference: <code>${data.reference}</code><br/>
        Provider: ${data.provider}<br/>
        Status: <span class="status-success">Simulated Successfully</span>
      </div>
    `;
  } catch {
    await sleep(1500);
    result.innerHTML = `
      <div class="interswitch-success">
        <strong>₦5,000 savings initiated via Quickteller</strong><br/>
        Reference: QT-${Math.random().toString(36).slice(2, 10).toUpperCase()}<br/>
        Status: <span class="status-success">Simulated Successfully</span>
      </div>
    `;
  }

  showToast("₦5,000 savings simulated via Interswitch.");
}

async function _doBill() {
  const result = getEl("interswitchResult");
  if (!result) return;

  result.classList.remove("hidden");
  result.innerHTML = '<div class="interswitch-loading">Optimizing bills via Interswitch...</div>';

  try {
    const data = await fetchJson(`${API_BASE}/api/action/bills`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: 0, user_id: "demo-user" })
    });

    result.innerHTML = `
      <div class="interswitch-success">
        <strong>${data.message}</strong><br/>
        Reference: <code>${data.reference}</code><br/>
        Monthly Saving: <strong>₦${Number(data.monthly_saving || 0).toLocaleString()}</strong><br/>
        Status: <span class="status-success">Simulated Successfully</span>
      </div>
    `;
  } catch {
    await sleep(1500);
    result.innerHTML = `
      <div class="interswitch-success">
        <strong>Bill optimization complete. Save ₦1,200/month</strong><br/>
        Reference: BI-${Math.random().toString(36).slice(2, 10).toUpperCase()}<br/>
        Status: <span class="status-success">Simulated Successfully</span>
      </div>
    `;
  }

  showToast("Bill optimization simulated via Interswitch.");
}

function getMockResults() {
  return {
    score: {
      score: 52,
      label: "Financially Unstable",
      color: "orange",
      message: "Your spending patterns are concerning. Act now.",
      pillars: {
        income_stability: 25,
        spending_control: 7,
        savings_behavior: 0,
        bill_regularity: 10,
        category_diversity: 10
      },
      summary: {
        total_income: 170000,
        total_spending: 65400,
        net: 104600,
        transaction_count: 10
      }
    },
    days_to_zero: {
      days_remaining: 8,
      daily_burn_rate: 7215.38,
      current_balance: 57723,
      urgency: "high",
      message: "At your current burn rate, you will run out of money in 8 days."
    },
    patterns: {
      count: 3,
      patterns: [
        {
          id: "post_salary_spike",
          title: "Post-Income Spending Spike",
          detail: "You spend 48% of your money within 3 days of receiving income.",
          severity: "high"
        },
        {
          id: "weekend_overspend",
          title: "Weekend Overspending",
          detail: "You spend 67% more on weekends than weekdays.",
          severity: "high"
        },
        {
          id: "food_overspend",
          title: "High Food Spending",
          detail: "Food accounts for 38% of your total spending.",
          severity: "medium"
        }
      ]
    },
    actions: getMockActions(),
    transactions: [
      {
        amount: 150000,
        type: "credit",
        category: "Income",
        description: "Salary March 2026",
        transaction_date: "2026-03-01"
      },
      {
        amount: 15000,
        type: "debit",
        category: "Shopping",
        description: "Jumia Order",
        transaction_date: "2026-03-03"
      },
      {
        amount: 12000,
        type: "debit",
        category: "Entertainment",
        description: "Club Outing Lagos",
        transaction_date: "2026-03-07"
      },
      {
        amount: 8500,
        type: "debit",
        category: "Entertainment",
        description: "Cinema Genesis",
        transaction_date: "2026-03-08"
      },
      {
        amount: 5000,
        type: "debit",
        category: "Bills",
        description: "DSTV Subscription",
        transaction_date: "2026-03-03"
      },
      {
        amount: 4500,
        type: "debit",
        category: "Food",
        description: "KFC Ikeja",
        transaction_date: "2026-03-02"
      }
    ]
  };
}

function getMockActions() {
  return [
    {
      title: "Reduce Daily Spending Immediately",
      detail: "Cut daily spending by ₦2,164 to extend your runway by 3+ days.",
      impact: "high"
    },
    {
      title: "Lock 30% of Income on Payday",
      detail: "Move 30% to savings the moment salary lands.",
      impact: "high"
    },
    {
      title: "Start a ₦500/day Savings Habit",
      detail: "₦500/day = ₦15,000/month = ₦180,000/year.",
      impact: "medium"
    }
  ];
}

function showLoading(show) {
  getEl("loadingPanel")?.classList.toggle("hidden", !show);
  getEl("inputPanel")?.classList.toggle("hidden", show);
}

function hideResults() {
  getEl("resultsPanel")?.classList.add("hidden");
  getEl("actionsCard")?.classList.add("hidden");
  getEl("interswitchResult")?.classList.add("hidden");
}

function animateNumber(id, from, to, duration) {
  const el = getEl(id);
  if (!el) return;

  const start = performance.now();
  const target = Number(to) || 0;

  function update(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = String(Math.round(from + (target - from) * eased));
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

function showToast(msg, type = "success") {
  const toast = getEl("toast");
  if (!toast) return;

  toast.textContent = msg;
  toast.className = `toast toast-${type}`;
  toast.classList.remove("hidden");
  window.setTimeout(() => toast.classList.add("hidden"), 3500);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function prefersReducedMotion() {
  return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function updateThemeColorMeta() {
  const meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) return;
  meta.setAttribute("content", "#f8f4ee");
}

function setupPageTransitions() {
  if (!document.body || prefersReducedMotion()) return;

  document.body.classList.add("is-entering");
  window.setTimeout(() => {
    document.body.classList.remove("is-entering");
  }, 420);

  const splashCta = document.querySelector('.cta-block a[href*="dashboard.html"]');
  if (!splashCta) return;

  splashCta.addEventListener("click", (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    document.body.classList.add("page-out");
    window.setTimeout(() => {
      window.location.href = splashCta.href;
    }, 220);
  });
}

function setupBrandMarkTilt() {
  if (prefersReducedMotion()) return;
  if (!window.matchMedia || !window.matchMedia("(pointer: fine)").matches) return;

  const mark = document.querySelector(".brand-mark");
  if (!mark) return;

  let rafId = 0;

  const applyTilt = (event) => {
    const rect = mark.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const x = (event.clientX - centerX) / (rect.width / 2);
    const y = (event.clientY - centerY) / (rect.height / 2);
    const clampX = Math.max(-1, Math.min(1, x));
    const clampY = Math.max(-1, Math.min(1, y));

    mark.style.transform = `perspective(220px) rotateX(${(-clampY * 2).toFixed(2)}deg) rotateY(${(clampX * 2.4).toFixed(2)}deg)`;
  };

  mark.addEventListener("mousemove", (event) => {
    if (rafId) return;
    rafId = window.requestAnimationFrame(() => {
      applyTilt(event);
      rafId = 0;
    });
  });

  mark.addEventListener("mouseleave", () => {
    mark.style.transform = "perspective(220px) rotateX(0deg) rotateY(0deg)";
  });
}

function setupMouseHoverEffects() {
  if (prefersReducedMotion()) return;
  if (!window.matchMedia || !window.matchMedia("(pointer: fine)").matches) return;

  const interactiveElements = Array.from(document.querySelectorAll(".btn, .card"));
  if (!interactiveElements.length) return;

  let mouseX = 0;
  let mouseY = 0;
  let rafId = 0;

  document.addEventListener("mousemove", (event) => {
    mouseX = event.clientX;
    mouseY = event.clientY;

    if (rafId) return;
    rafId = window.requestAnimationFrame(() => {
      interactiveElements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const distX = mouseX - centerX;
        const distY = mouseY - centerY;
        const distance = Math.sqrt(distX * distX + distY * distY);
        const maxDistance = 250;
        const influence = Math.max(0, 1 - distance / maxDistance);
        const shiftX = (distX / maxDistance) * 4 * influence;
        const shiftY = (distY / maxDistance) * 4 * influence;

        el.style.transform = `translate3d(${shiftX.toFixed(2)}px, ${shiftY.toFixed(2)}px, 0)`;
      });
      rafId = 0;
    });
  });

  document.addEventListener("mouseleave", () => {
    interactiveElements.forEach((el) => {
      el.style.transform = "translate3d(0, 0, 0)";
    });
  });
}

function setupBackgroundObjects() {
  if (prefersReducedMotion()) return;

  const body = document.body;
  if (!body) return;

  const container = document.createElement("div");
  container.className = "bg-objects-container";

  const objectCount = 16;
  for (let i = 0; i < objectCount; i += 1) {
    const obj = document.createElement("div");
    obj.className = "naira-note";

    obj.textContent = "₦";
    obj.style.left = `${Math.random() * 100}%`;
    obj.style.top = `${Math.random() * 100}%`;
    obj.style.animationDuration = `${Math.random() * 25 + 20}s`;
    obj.style.animationDelay = `${Math.random() * 5}s`;
    obj.style.transform = `rotate(${Math.random() * 360}deg)`;

    container.appendChild(obj);
  }

  body.insertBefore(container, body.firstChild);
}

function setupParallaxCards() {
  if (prefersReducedMotion()) return;
  if (window.innerWidth < 820) return;

  const cards = Array.from(document.querySelectorAll(".main .panel, .main .card"));
  if (!cards.length) return;

  let ticking = false;
  const maxShift = 14;

  const render = () => {
    const viewportCenter = window.innerHeight * 0.5;
    cards.forEach((card, index) => {
      const rect = card.getBoundingClientRect();
      const distance = rect.top + rect.height * 0.5 - viewportCenter;
      const normalized = Math.max(-1, Math.min(1, distance / viewportCenter));
      const depth = Math.min(maxShift, 8 + index * 1.1);
      const translateY = normalized * -depth;
      const rotateX = normalized * -1.8;
      card.style.transform = `translate3d(0, ${translateY.toFixed(2)}px, 0) rotateX(${rotateX.toFixed(2)}deg)`;
    });
    ticking = false;
  };

  const onScroll = () => {
    if (!ticking) {
      window.requestAnimationFrame(render);
      ticking = true;
    }
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  onScroll();
}

function setupThemeToggle() {
  const toggle = getEl("themeToggle");
  if (!toggle) return;

  const savedTheme = localStorage.getItem("finsight-theme") || "cleo";
  const isDark = savedTheme === "dark";
  
  document.body.setAttribute("data-theme", isDark ? "dark" : "light");
  document.body.classList.toggle("cleo-mode", !isDark);
  updateThemeIcon();

  toggle.addEventListener("click", () => {
    const currentTheme = document.body.getAttribute("data-theme") || "light";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.body.setAttribute("data-theme", newTheme);
    document.body.classList.toggle("cleo-mode", newTheme !== "dark");
    localStorage.setItem("finsight-theme", newTheme);
    updateThemeIcon();
    showToast(`Switched to ${newTheme === "dark" ? "dark" : "light"} mode.`);
  });
}

function updateThemeIcon() {
  const toggle = getEl("themeToggle");
  const icon = toggle?.querySelector("i");
  if (!toggle || !icon) return;
  const isDark = document.body.getAttribute("data-theme") === "dark";
  icon.className = isDark ? "fa-solid fa-sun" : "fa-solid fa-moon";
  toggle.title = isDark ? "Switch to light mode" : "Switch to dark mode";
}

window.addEventListener("DOMContentLoaded", () => {
  updateThemeColorMeta();
  switchTab("sms");
  setupThemeToggle();

  if (window.supabase?.auth) {
    window.supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) return;
      const modal = getEl("authModal");
      const pendingAction = modal?._pendingAction;
      if (typeof pendingAction === "function") {
        closeAuthModal(true);
        pendingAction().catch(() => {
          showToast("Unable to continue action after sign-in.", "error");
        });
      }
    });
  }

  setupAuthModalBehavior();

  setupPageTransitions();
  setupBrandMarkTilt();
  setupParallaxCards();
  setupBackgroundObjects();
  setupMouseHoverEffects();
});

// Ensure inline HTML handlers can call these methods reliably.
window.switchTab = switchTab;
window.loadDemoData = loadDemoData;
window.loadDemoCSV = loadDemoCSV;
window.loadDemoPDF = loadDemoPDF;
window.handleCSVFile = handleCSVFile;
window.handleCSVDrop = handleCSVDrop;
window.handlePDFFile = handlePDFFile;
window.handlePDFDrop = handlePDFDrop;
window.analyzeNow = analyzeNow;
window.analyzeCSV = analyzeCSV;
window.analyzePDF = analyzePDF;
window.fixThis = fixThis;
window.simulateSave = simulateSave;
window.simulateBill = simulateBill;
window.signInWithGoogle = signInWithGoogle;
window.closeAuthModal = closeAuthModal;
window.showHistoryModal = showHistoryModal;
window.closeHistoryModal = closeHistoryModal;
window.viewAnalysis = viewAnalysis;
