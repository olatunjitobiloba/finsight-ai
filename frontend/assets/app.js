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

const host = window.location.hostname;
const IS_LOCALHOST = host === "localhost" || host === "127.0.0.1" || host === "[::1]";

// Optional override for cases where frontend and API are on different domains.
const API_BASE = window.FINSIGHT_API_BASE || (IS_LOCALHOST ? "http://localhost:8000" : "");
const ALLOW_MOCK_FALLBACK = IS_LOCALHOST;

// State
let currentResults = null;
let csvContent = null;
let csvFile = null;
let pdfFile = null;
let pdfDemoMode = false;
let activeTab = "sms";
let currentPillarExplanations = {};
let currentPillarWhyLines = {};

const AUTH_PENDING_ACTION_KEY = "finsight.pending.action";

const PILLAR_KEYS = [
  "income_stability",
  "spending_control",
  "savings_behavior",
  "bill_regularity",
  "category_diversity"
];

const PILLAR_LABELS = {
  income_stability: "Income Stability",
  spending_control: "Spending Control",
  savings_behavior: "Savings Behavior",
  bill_regularity: "Bill Regularity",
  category_diversity: "Category Diversity"
};

const PILLAR_MAXES = {
  income_stability: 25,
  spending_control: 25,
  savings_behavior: 20,
  bill_regularity: 15,
  category_diversity: 15
};

// Demo data - 3 months with multiple income, bills, savings, and diverse categories
const DEMO_SMS = `Access Bank: Your account credited with N200,000.00. Narration: Salary January 2026. Bal: N200,000.00
Acct 0123456789 debited with NGN75,000.00 on 02-Jan-26. Desc: RENT PAYMENT JAN. Bal: NGN125,000.00
Acct 0123456789 debited with NGN4,500.00 on 03-Jan-26. Desc: SHOPRITE GROCERIES. Bal: NGN120,500.00
Acct 0123456789 debited with NGN5,000.00 on 03-Jan-26. Desc: DSTV SUBSCRIPTION. Bal: NGN115,500.00
Acct 0123456789 debited with NGN3,000.00 on 05-Jan-26. Desc: AIRTEL DATA. Bal: NGN112,500.00
Acct 0123456789 debited with NGN25,000.00 on 05-Jan-26. Desc: PIGGYVEST SAVINGS. Bal: NGN87,500.00
Acct 0123456789 debited with NGN6,500.00 on 08-Jan-26. Desc: KFC IKEJA. Bal: NGN81,000.00
Acct 0123456789 debited with NGN8,000.00 on 10-Jan-26. Desc: UBER TRIPS. Bal: NGN73,000.00
Acct 0123456789 debited with NGN12,000.00 on 12-Jan-26. Desc: CLUB OUTING. Bal: NGN61,000.00
Acct 0123456789 credited with NGN35,000.00 on 15-Jan-26. Narration: Freelance project payment. Bal: NGN96,000.00
Acct 0123456789 debited with NGN7,200.00 on 18-Jan-26. Desc: CINEMA & DINNER. Bal: NGN88,800.00
Acct 0123456789 debited with NGN9,000.00 on 22-Jan-26. Desc: JUMIA SHOPPING. Bal: NGN79,800.00
Acct 0123456789 debited with NGN15,000.00 on 25-Jan-26. Desc: ELECTRICITY IKEDC. Bal: NGN64,800.00
Acct 0123456789 credited with N200,000.00 on 01-Feb-26. Narration: Salary February 2026. Bal: N264,800.00
Acct 0123456789 debited with NGN75,000.00 on 02-Feb-26. Desc: RENT PAYMENT FEB. Bal: NGN189,800.00
Acct 0123456789 debited with NGN5,500.00 on 03-Feb-26. Desc: SHOPRITE GROCERIES. Bal: NGN184,300.00
Acct 0123456789 debited with NGN5,000.00 on 03-Feb-26. Desc: GOTV SUBSCRIPTION. Bal: NGN179,300.00
Acct 0123456789 debited with NGN3,000.00 on 05-Feb-26. Desc: AIRTEL DATA. Bal: NGN176,300.00
Acct 0123456789 debited with NGN30,000.00 on 06-Feb-26. Desc: COWRYWISE INVESTMENT. Bal: NGN146,300.00
Acct 0123456789 debited with NGN5,800.00 on 08-Feb-26. Desc: CHICKEN REPUBLIC. Bal: NGN140,500.00
Acct 0123456789 debited with NGN7,500.00 on 10-Feb-26. Desc: BOLT RIDES. Bal: NGN133,000.00
Acct 0123456789 debited with NGN14,000.00 on 13-Feb-26. Desc: WEEKEND SHOPPING. Bal: NGN119,000.00
Acct 0123456789 credited with NGN32,000.00 on 16-Feb-26. Narration: Freelance consultation. Bal: NGN151,000.00
Acct 0123456789 debited with NGN8,500.00 on 19-Feb-26. Desc: RESTAURANT DINNER. Bal: NGN142,500.00
Acct 0123456789 debited with NGN16,000.00 on 22-Feb-26. Desc: FASHION NOVA STORE. Bal: NGN126,500.00
Acct 0123456789 debited with NGN12,000.00 on 24-Feb-26. Desc: ELECTRICITY IKEDC. Bal: NGN114,500.00
Acct 0123456789 credited with N200,000.00 on 01-Mar-26. Narration: Salary March 2026. Bal: N314,500.00
Acct 0123456789 debited with NGN75,000.00 on 02-Mar-26. Desc: RENT PAYMENT MAR. Bal: NGN239,500.00
Acct 0123456789 debited with NGN6,200.00 on 03-Mar-26. Desc: SHOPRITE GROCERIES. Bal: NGN233,300.00
Acct 0123456789 debited with NGN5,000.00 on 03-Mar-26. Desc: DSTV SUBSCRIPTION. Bal: NGN228,300.00
Acct 0123456789 debited with NGN3,000.00 on 05-Mar-26. Desc: AIRTEL DATA. Bal: NGN225,300.00
Acct 0123456789 debited with NGN25,000.00 on 05-Mar-26. Desc: PIGGYVEST SAVINGS. Bal: NGN200,300.00
Acct 0123456789 debited with NGN5,500.00 on 07-Mar-26. Desc: KFC IKEJA. Bal: NGN194,800.00
Acct 0123456789 debited with NGN7,800.00 on 09-Mar-26. Desc: UBER TRIPS. Bal: NGN187,000.00
Acct 0123456789 debited with NGN18,000.00 on 10-Mar-26. Desc: SHOPPING WEEKEND. Bal: NGN169,000.00
Acct 0123456789 credited with NGN30,000.00 on 14-Mar-26. Narration: Project bonus payment. Bal: NGN199,000.00
Acct 0123456789 debited with NGN9,000.00 on 17-Mar-26. Desc: CINEMA & DINNER. Bal: NGN190,000.00
Acct 0123456789 debited with NGN12,000.00 on 20-Mar-26. Desc: JUMIA ELECTRONICS. Bal: NGN178,000.00
Acct 0123456789 debited with NGN15,000.00 on 25-Mar-26. Desc: ELECTRICITY IKEDC. Bal: NGN163,000.00`;

const DEMO_CSV = `Date,Description,Debit,Credit,Balance
01/01/2026,Salary January 2026,,200000,200000
02/01/2026,Rent Payment Jan,75000,,125000
03/01/2026,Shoprite Groceries,4500,,120500
03/01/2026,DSTV Subscription,5000,,115500
05/01/2026,Airtel Data,3000,,112500
05/01/2026,Piggyvest Savings,25000,,87500
08/01/2026,KFC Ikeja,6500,,81000
10/01/2026,Uber Trips,8000,,73000
12/01/2026,Club Outing,12000,,61000
15/01/2026,Freelance project payment,,35000,96000
18/01/2026,Cinema & Dinner,7200,,88800
22/01/2026,Jumia Shopping,9000,,79800
25/01/2026,Electricity IKEDC,15000,,64800
01/02/2026,Salary February 2026,,200000,264800
02/02/2026,Rent Payment Feb,75000,,189800
03/02/2026,Shoprite Groceries,5500,,184300
03/02/2026,GoTV Subscription,5000,,179300
05/02/2026,Airtel Data,3000,,176300
06/02/2026,Cowrywise Investment,30000,,146300
08/02/2026,Chicken Republic,5800,,140500
10/02/2026,Bolt Rides,7500,,133000
13/02/2026,Weekend Shopping,14000,,119000
16/02/2026,Freelance consultation,,32000,151000
19/02/2026,Restaurant Dinner,8500,,142500
22/02/2026,Fashion Nova Store,16000,,126500
24/02/2026,Electricity IKEDC,12000,,114500
01/03/2026,Salary March 2026,,200000,314500
02/03/2026,Rent Payment Mar,75000,,239500
03/03/2026,Shoprite Groceries,6200,,233300
03/03/2026,DSTV Subscription,5000,,228300
05/03/2026,Airtel Data,3000,,225300
05/03/2026,Piggyvest Savings,25000,,200300
07/03/2026,KFC Ikeja,5500,,194800
09/03/2026,Uber Trips,7800,,187000
10/03/2026,Shopping Weekend,18000,,169000
14/03/2026,Project bonus payment,,30000,199000
17/03/2026,Cinema & Dinner,9000,,190000
20/03/2026,Jumia Electronics,12000,,178000
25/03/2026,Electricity IKEDC,15000,,163000`;

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
  csvFile = null;
  showCSVPreview("demo-statement.csv", 10);
  switchTab("csv");
  showToast("Demo CSV loaded. Click Analyze Statement.");
}

function handleCSVFile(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;

  csvFile = file;

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
  pdfDemoMode = false;
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
  const bankType = String(getEl("smsBankType")?.value || "").trim();

  if (!bankType) {
    showToast("Please select your bank before analyzing SMS alerts.", "error");
    return;
  }

  if (!smsText) {
    showToast("Please paste your SMS alerts first.", "error");
    return;
  }
  await runAnalysis({ sms_text: smsText, bank_type: bankType }, "/api/analyze");
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

    let parseResponse;
    if (csvFile) {
      const fileForm = new FormData();
      fileForm.append("file", csvFile);
      parseResponse = await fetch(`${API_BASE}/api/parse/csv`, {
        method: "POST",
        body: fileForm
      });
    } else {
      const textForm = new FormData();
      textForm.append("csv_text", csvContent);
      parseResponse = await fetch(`${API_BASE}/api/parse/csv/text`, {
        method: "POST",
        body: textForm
      });
    }

    if (!parseResponse.ok) {
      let detail = "";
      try {
        const errBody = await parseResponse.json();
        if (typeof errBody?.detail === "string") {
          detail = errBody.detail;
        } else if (errBody?.detail?.message) {
          detail = errBody.detail.message;
        } else if (typeof errBody?.error === "string") {
          detail = errBody.error;
        }
      } catch {
        // Keep status-only fallback if body is not JSON.
      }
      const suffix = detail ? ` - ${detail}` : "";
      throw new Error(`CSV parse failed: ${parseResponse.status}${suffix}`);
    }

    const parseResult = await parseResponse.json();
    const parsedTransactions = parseResult?.data?.parsed || parseResult?.parsed;
    if (!parseResult?.success || !Array.isArray(parsedTransactions) || parsedTransactions.length === 0) {
      const firstFailure = parseResult?.data?.failed?.[0] || parseResult?.failed?.[0];
      throw new Error(parseResult?.error || firstFailure || "CSV parsing returned no transactions");
    }

    const analyzeResponse = await fetchJson(`${API_BASE}/api/analyze/transactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transactions: parsedTransactions
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
  if (pdfDemoMode) {
    await analyzeDemoPDF();
    return;
  }

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
    const pdfPassword = String(getEl("pdfPassword")?.value || "").trim();
    if (pdfPassword) {
      formData.append("password", pdfPassword);
    }

    const response = await fetch(`${API_BASE}/api/parse/pdf`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      let detail = "";
      try {
        const errBody = await response.json();
        if (typeof errBody?.detail === "string") {
          detail = errBody.detail;
        } else if (errBody?.detail?.message) {
          detail = errBody.detail.message;
        }
      } catch {
        // Ignore parse errors and use status text fallback.
      }
      const suffix = detail ? ` - ${detail}` : "";
      throw new Error(`PDF parse failed: ${response.status}${suffix}`);
    }

    const parseResult = await response.json();

    if (!parseResult?.parsed || !Array.isArray(parseResult.parsed)) {
      throw new Error("PDF parsing returned invalid data");
    }

    // Send parsed transactions directly to analysis endpoint (skip SMS conversion)
    const analyzeResponse = await fetchJson(`${API_BASE}/api/analyze/transactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transactions: parseResult.parsed
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
  pdfFile = null;
  pdfDemoMode = true;
  const fileName = getEl("pdfFileName");
  const status = getEl("pdfStatus");
  const passwordInput = getEl("pdfPassword");
  if (fileName) fileName.textContent = "demo-statement.pdf";
  if (status) status.textContent = "Uses built-in sample transactions";
  if (passwordInput) passwordInput.value = "";
  getEl("pdfPreview")?.classList.remove("hidden");
  getEl("pdfDropZone")?.classList.add("has-file");
  switchTab("pdf");
  showToast("Demo PDF loaded. Click Extract & Analyze.");
}

async function analyzeDemoPDF() {
  await runAnalysis({ sms_text: DEMO_SMS, bank_type: "access" }, "/api/analyze");
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
  currentPillarWhyLines = buildPillarWhyLines(
    data.score?.pillars || {},
    data.transactions || []
  );
  currentPillarExplanations = buildPillarExplanations(
    data.score?.pillars || {},
    data.transactions || [],
    currentPillarWhyLines
  );
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
  if (msg) {
    // Backward-compatible cleanup in case older API responses still include [TOKEN] prefixes.
    msg.textContent = String(d.message || "-").replace(/^\s*\[[^\]]+\]\s*/u, "");
  }

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
    const count = Number(p.count || patterns.length || 0);
    patternCount.textContent = `${count} pattern${count !== 1 ? "s" : ""} found`;
  }

  const list = getEl("patternsList");
  if (!list) return;

  if (patterns.length === 0) {
    list.innerHTML = '<div class="pattern-empty">No concerning patterns detected.</div>';
    return;
  }

  list.innerHTML = patterns.map((pat, i) => {
    const severity = ["low", "medium", "high"].includes(String(pat.severity || "").toLowerCase())
      ? String(pat.severity).toLowerCase()
      : "low";
    const title = escapeHtml(pat.title || "Pattern detected");
    const detail = escapeHtml(pat.detail || "No details available.");
    return `
    <div class="pattern-item severity-${severity}" style="animation-delay:${i * 150}ms">
      <div class="pattern-top">
        <span class="pattern-title">${title}</span>
        <span class="pattern-badge ${severity}">${severity}</span>
      </div>
      <div class="pattern-detail">${detail}</div>
    </div>
  `;
  }).join("");
}

function renderPillars(pillars) {
  if (!pillars) return;

  const pillarsList = getEl("pillarsList");
  if (!pillarsList) return;

  pillarsList.innerHTML = PILLAR_KEYS
    .filter((k) => Object.prototype.hasOwnProperty.call(pillars, k))
    .map((k) => {
      const v = pillars[k];
    const max = PILLAR_MAXES[k] || 25;
    const pct = Math.max(0, Math.min(100, Math.round((Number(v || 0) / max) * 100)));

    return `
      <div class="pillar-item">
        <div class="pillar-top">
          <span class="pillar-label">${PILLAR_LABELS[k] || k}</span>
          <span class="pillar-value">${v}/${max}</span>
        </div>
        <div class="pillar-why">${escapeHtml(currentPillarWhyLines[k] || "Threshold branch unavailable.")}</div>
        <button class="pillar-explain-btn" type="button" onclick="openScoreDrawer('${k}')">
          Show transactions used
        </button>
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

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMoney(amount) {
  return `\u20a6${Number(amount || 0).toLocaleString("en-NG", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function formatTxnForDrawer(txn) {
  const date = escapeHtml(txn.transaction_date || "-");
  const desc = escapeHtml(txn.description || "Transaction");
  const cat = escapeHtml(txn.category || "Uncategorized");
  const amount = formatMoney(txn.amount || 0);
  const typeClass = txn.type === "credit" ? "credit" : "debit";
  const typeLabel = txn.type === "credit" ? "Credit" : "Debit";

  return `
    <li class="drawer-txn-item">
      <div class="drawer-txn-main">
        <span class="drawer-txn-desc">${desc}</span>
        <span class="drawer-txn-meta">${date} · ${cat} · ${typeLabel}</span>
      </div>
      <span class="drawer-txn-amount ${typeClass}">${amount}</span>
    </li>
  `;
}

function isFeeOrTaxLine(text) {
  const content = String(text || "").toLowerCase();
  return /\b(vat|stamp\s*duty|levy|charge|commission|fee|sms\s*alert\s*fee)\b/.test(content);
}

function isSavingsTxn(txn) {
  const keywords = [
    "savings", "piggyvest", "cowrywise",
    "investment", "stash", "target", "save"
  ];
  const desc = String(txn.description || "").toLowerCase();
  const cat = String(txn.category || "").toLowerCase();
  return keywords.some((kw) => desc.includes(kw) || cat.includes(kw));
}

function isBillTxn(txn) {
  const billKeywords = [
    "dstv", "gotv", "electricity", "water",
    "rent", "airtime", "data", "subscription",
    "ikedc", "ekedc", "aedc", "phcn"
  ];
  const desc = String(txn.description || "").toLowerCase();
  const cat = String(txn.category || "").toLowerCase();
  if (isFeeOrTaxLine(desc)) {
    return false;
  }
  return billKeywords.some((kw) => desc.includes(kw) || cat.includes(kw));
}

function findSavingsMatch(transactions) {
  const keywords = [
    "savings", "piggyvest", "cowrywise",
    "investment", "stash", "target", "save"
  ];

  for (const txn of transactions) {
    const desc = String(txn.description || "").toLowerCase();
    const cat = String(txn.category || "").toLowerCase();
    for (const kw of keywords) {
      if (desc.includes(kw) || cat.includes(kw)) {
        return { kw, txn };
      }
    }
  }

  return null;
}

function buildPillarWhyLines(_pillars, transactions) {
  const credits = transactions.filter((t) => t.type === "credit");
  const debits = transactions.filter((t) => t.type === "debit");
  const incomeCount = credits.length;
  const totalIncome = credits.reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const totalSpending = debits.reduce((sum, t) => sum + Number(t.amount || 0), 0);

  let incomeWhy = "Branch: no credits detected, so 0/25.";
  if (incomeCount >= 3) {
    incomeWhy = `Branch: income count >= 3 (${incomeCount}), so 25/25.`;
  } else if (incomeCount === 2) {
    incomeWhy = "Branch: income count == 2, so 18/25.";
  } else if (incomeCount === 1) {
    incomeWhy = "Branch: single income entry, so 10/25.";
  }

  let spendingWhy;
  if (totalSpending <= 0) {
    spendingWhy = "Branch: spending <= 0, so 25/25.";
  } else if (totalIncome <= 0) {
    spendingWhy = "Branch: income <= 0 with spending present, so 0/25.";
  } else {
    const ratio = totalSpending / totalIncome;
    const ratioText = `${(ratio * 100).toFixed(1)}%`;
    if (ratio <= 0.35) {
      spendingWhy = `Branch: ratio <= 35% (${ratioText}), so 25/25.`;
    } else if (ratio <= 0.5) {
      spendingWhy = `Branch: ratio <= 50% (${ratioText}), so 18/25.`;
    } else if (ratio <= 0.7) {
      spendingWhy = `Branch: ratio <= 70% (${ratioText}), so 13/25.`;
    } else if (ratio <= 0.9) {
      spendingWhy = `Branch: ratio <= 90% (${ratioText}), so 9/25.`;
    } else if (ratio <= 1.0) {
      spendingWhy = `Branch: ratio <= 100% (${ratioText}), so 8/25.`;
    } else if (ratio <= 1.1) {
      spendingWhy = `Branch: ratio <= 110% (${ratioText}), so 6/25.`;
    } else if (ratio <= 1.25) {
      spendingWhy = `Branch: ratio <= 125% (${ratioText}), so 4/25.`;
    } else if (ratio <= 1.5) {
      spendingWhy = `Branch: ratio <= 150% (${ratioText}), so 2/25.`;
    } else if (ratio <= 1.75) {
      spendingWhy = `Branch: ratio <= 175% (${ratioText}), so 1/25.`;
    } else {
      spendingWhy = `Branch: ratio > 175% (${ratioText}), so 0/25.`;
    }
  }

  const savingsMatch = findSavingsMatch(transactions);
  const savingsWhy = savingsMatch
    ? `Branch: matched savings keyword '${savingsMatch.kw}', so 20/20.`
    : "Branch: no savings keyword matched, so 0/20.";

  const billTxns = debits.filter(isBillTxn);
  const billCount = billTxns.length;
  let billWhy = "Branch: bill count == 0, so 0/15.";
  if (billCount >= 3) {
    billWhy = `Branch: bill count >= 3 (${billCount}), so 15/15.`;
  } else if (billCount === 2) {
    billWhy = "Branch: bill count == 2, so 10/15.";
  } else if (billCount === 1) {
    billWhy = "Branch: bill count == 1, so 5/15.";
  }

  const spendingByCategory = new Map();
  debits.forEach((txn) => {
    const category = txn.category || "Uncategorized";
    const current = spendingByCategory.get(category) || 0;
    spendingByCategory.set(category, current + Number(txn.amount || 0));
  });

  let diversityWhy;
  if (totalSpending <= 0) {
    diversityWhy = "Branch: total debit spend <= 0, so 0/15.";
  } else {
    const qualifyingCount = Array.from(spendingByCategory.values())
      .filter((amount) => (amount / totalSpending) >= 0.03)
      .length;
    if (qualifyingCount >= 5) {
      diversityWhy = `Branch: qualifying categories >= 5 (${qualifyingCount}), so 15/15.`;
    } else if (qualifyingCount >= 3) {
      diversityWhy = `Branch: qualifying categories >= 3 (${qualifyingCount}), so 10/15.`;
    } else if (qualifyingCount >= 2) {
      diversityWhy = `Branch: qualifying categories >= 2 (${qualifyingCount}), so 5/15.`;
    } else {
      diversityWhy = `Branch: qualifying categories < 2 (${qualifyingCount}), so 0/15.`;
    }
  }

  return {
    income_stability: incomeWhy,
    spending_control: spendingWhy,
    savings_behavior: savingsWhy,
    bill_regularity: billWhy,
    category_diversity: diversityWhy
  };
}

function buildPillarExplanations(pillars, transactions, pillarWhyLines = {}) {
  const credits = transactions.filter((t) => t.type === "credit");
  const debits = transactions.filter((t) => t.type === "debit");
  const savingsTxns = transactions.filter(isSavingsTxn);
  const billTxns = debits.filter(isBillTxn);
  const totalIncome = credits.reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const totalSpending = debits.reduce((sum, t) => sum + Number(t.amount || 0), 0);

  const spendingByCategory = new Map();
  debits.forEach((txn) => {
    const category = txn.category || "Uncategorized";
    const current = spendingByCategory.get(category) || 0;
    spendingByCategory.set(category, current + Number(txn.amount || 0));
  });

  const qualifyingCategories = new Set(
    Array.from(spendingByCategory.entries())
      .filter(([, amount]) => totalSpending > 0 && (amount / totalSpending) >= 0.03)
      .map(([category]) => category)
  );

  const diversityTxns = debits.filter((txn) => qualifyingCategories.has(txn.category || "Uncategorized"));

  const spendingRatio = totalIncome > 0 ? (totalSpending / totalIncome) : null;
  const ratioText = spendingRatio === null
    ? "No income transactions were found, so spending control is capped."
    : `Spent ${(spendingRatio * 100).toFixed(1)}% of income (${formatMoney(totalSpending)} of ${formatMoney(totalIncome)}).`;

  return {
    income_stability: {
      title: PILLAR_LABELS.income_stability,
      score: Number(pillars.income_stability || 0),
      max: PILLAR_MAXES.income_stability,
      reason: pillarWhyLines.income_stability || "Threshold branch unavailable.",
      sections: [
        {
          title: `Income entries (${credits.length})`,
          txns: credits,
          emptyText: "No credit transactions were found."
        }
      ]
    },
    spending_control: {
      title: PILLAR_LABELS.spending_control,
      score: Number(pillars.spending_control || 0),
      max: PILLAR_MAXES.spending_control,
      reason: pillarWhyLines.spending_control || ratioText,
      sections: [
        {
          title: `Credits counted (${credits.length})`,
          txns: credits,
          emptyText: "No credits were counted."
        },
        {
          title: `Debits counted (${debits.length})`,
          txns: debits,
          emptyText: "No debits were counted."
        }
      ]
    },
    savings_behavior: {
      title: PILLAR_LABELS.savings_behavior,
      score: Number(pillars.savings_behavior || 0),
      max: PILLAR_MAXES.savings_behavior,
      reason: pillarWhyLines.savings_behavior || "Threshold branch unavailable.",
      sections: [
        {
          title: `Savings-related transactions (${savingsTxns.length})`,
          txns: savingsTxns,
          emptyText: "No savings-related transactions matched."
        }
      ]
    },
    bill_regularity: {
      title: PILLAR_LABELS.bill_regularity,
      score: Number(pillars.bill_regularity || 0),
      max: PILLAR_MAXES.bill_regularity,
      reason: pillarWhyLines.bill_regularity || "Threshold branch unavailable.",
      sections: [
        {
          title: `Bill transactions counted (${billTxns.length})`,
          txns: billTxns,
          emptyText: "No qualifying bill transactions were found."
        }
      ]
    },
    category_diversity: {
      title: PILLAR_LABELS.category_diversity,
      score: Number(pillars.category_diversity || 0),
      max: PILLAR_MAXES.category_diversity,
      reason: pillarWhyLines.category_diversity || "Threshold branch unavailable.",
      sections: [
        {
          title: `Transactions in qualifying categories (${diversityTxns.length})`,
          txns: diversityTxns,
          emptyText: "No categories met the 3% contribution threshold."
        }
      ]
    }
  };
}

function openScoreDrawer(pillarKey) {
  const drawer = getEl("scoreDrawer");
  const title = getEl("scoreDrawerTitle");
  const body = getEl("scoreDrawerBody");
  const explanation = currentPillarExplanations[pillarKey];
  if (!drawer || !title || !body || !explanation) return;

  title.textContent = `${explanation.title} (${explanation.score}/${explanation.max})`;

  body.innerHTML = `
    <p class="score-drawer-reason">${escapeHtml(explanation.reason)}</p>
    ${explanation.sections.map((section) => `
      <section class="drawer-section">
        <h4 class="drawer-section-title">${escapeHtml(section.title)}</h4>
        ${section.txns.length
          ? `<ul class="drawer-txn-list">${section.txns.map(formatTxnForDrawer).join("")}</ul>`
          : `<p class="drawer-empty">${escapeHtml(section.emptyText)}</p>`}
      </section>
    `).join("")}
  `;

  drawer.classList.remove("hidden");
  drawer.setAttribute("aria-hidden", "false");
  window.requestAnimationFrame(() => {
    drawer.classList.add("is-open");
  });
}

function closeScoreDrawer() {
  const drawer = getEl("scoreDrawer");
  if (!drawer) return;

  drawer.classList.remove("is-open");
  drawer.setAttribute("aria-hidden", "true");
  window.setTimeout(() => {
    drawer.classList.add("hidden");
  }, 220);
}

function setupScoreDrawerBehavior() {
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const drawer = getEl("scoreDrawer");
    if (!drawer || drawer.classList.contains("hidden")) return;
    closeScoreDrawer();
  });
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

function queuePendingAuthAction(actionFn) {
  const name = String(actionFn?.name || "").trim();
  const mapped = name === "_doSave"
    ? "simulateSave"
    : (name === "_doBill" ? "simulateBill" : "");
  if (mapped) {
    sessionStorage.setItem(AUTH_PENDING_ACTION_KEY, mapped);
  }
}

function goToLogin() {
  const next = `${window.location.pathname.split("/").pop() || "dashboard.html"}${window.location.search || ""}`;
  window.location.href = `./login.html?next=${encodeURIComponent(next)}`;
}

async function runPendingAuthActionIfAny() {
  const actionName = sessionStorage.getItem(AUTH_PENDING_ACTION_KEY);
  if (!actionName) return;

  const session = await getSupabaseSession();
  if (!session) return;

  sessionStorage.removeItem(AUTH_PENDING_ACTION_KEY);
  const action = window[actionName];
  if (typeof action === "function") {
    action().catch(() => {
      showToast("Signed in, but we could not resume the previous action.", "warning");
    });
  }
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

function setupExecuteModalBehavior() {
  const modal = getEl("executeModal");
  if (!modal) return;

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeExecuteFlow(false);
    }
  });
}

function openExecuteFlow() {
  const modal = getEl("executeModal");
  if (!modal) return;

  const amountInput = getEl("executeAmount");
  if (amountInput && !amountInput.value) {
    amountInput.value = "500";
  }

  const status = getEl("executeStatus");
  if (status) {
    status.className = "execute-status hidden";
    status.innerHTML = "";
  }

  modal.classList.remove("hidden");
  loadExecuteBillers();
  checkExecuteIntegrationStatus();
}

function closeExecuteFlow(clearFields = false) {
  const modal = getEl("executeModal");
  if (!modal) return;

  modal.classList.add("hidden");

  if (clearFields) {
    const customer = getEl("executeCustomerId");
    const amount = getEl("executeAmount");
    const paymentCode = getEl("executePaymentItemId");
    if (customer) customer.value = "";
    if (amount) {
      amount.value = "";
      amount.readOnly = false;
    }
    if (paymentCode) paymentCode.value = "";
  }
}

function setExecuteStatus(kind, message, details = "") {
  const status = getEl("executeStatus");
  if (!status) return;

  status.className = `execute-status ${kind}`;
  status.classList.remove("hidden");
  status.innerHTML = `
    <div class="execute-status-title">${message}</div>
    ${details ? `<div class="execute-status-detail">${details}</div>` : ""}
  `;
}

function isSandboxPendingResponse(payload) {
  const message = String(payload?.message || payload?.provider_message || "").toLowerCase();
  return payload?.status === "sandbox_pending"
    || message.includes("access denied")
    || message.includes("permission")
    || message.includes("entitle")
    || message.includes("unauthorized");
}

async function checkExecuteIntegrationStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/bills/billers`);
    const data = await response.json();

    const statusBefore = getEl("executeStatusBefore");
    if (!statusBefore) return;

    if (response.ok && data?.status === "success") {
      statusBefore.classList.add("hidden");
      return;
    }

    const message = `Integration not ready: ${data?.message || `HTTP ${response.status}`}`;

    statusBefore.innerHTML = `
      <div style="color: #d4a574; padding: 12px; background: rgba(212, 165, 116, 0.1); border-left: 3px solid #d4a574; border-radius: 4px;">
        <strong>⚠️ Integration Health Check:</strong> ${message}
      </div>
    `;
    statusBefore.classList.remove("hidden");
  } catch (err) {
    console.warn("Integration status check failed:", err);
  }
}

function isValidBillerName(name) {
  if (!name) return false;
  const normalized = String(name).trim();
  if (!normalized) return false;
  // Skip likely sandbox artifacts like "10159au8".
  if (/^[0-9a-z]{6,}$/i.test(normalized) && !/\s/.test(normalized)) return false;
  return true;
}

async function loadExecuteBillers() {
  try {
    const dropdown = getEl("executeBillerId");
    if (!dropdown) return;

    dropdown.innerHTML = '<option value="">Loading billers...</option>';
    dropdown.disabled = true;

    const response = await fetch(`${API_BASE}/api/bills/billers`);
    const data = await response.json();

    if (!response.ok || data?.status === "error") {
      dropdown.innerHTML = '<option value="">-- Error loading billers --</option>';
      return;
    }

    const billerCategories = data?.data || [];
    if (!Array.isArray(billerCategories) || billerCategories.length === 0) {
      dropdown.innerHTML = '<option value="">-- No billers available --</option>';
      return;
    }

    let html = '<option value="">-- Select a biller --</option>';
    billerCategories.forEach((category) => {
      if (category?.billers && Array.isArray(category.billers)) {
        category.billers.forEach((biller) => {
          const id = biller?.id;
          const displayName = String(biller?.name || biller?.shortName || "").trim();
          if (id && isValidBillerName(displayName)) {
            html += `<option value="${escapeHtml(String(id))}">${escapeHtml(displayName)}</option>`;
          }
        });
      }
    });

    if (html === '<option value="">-- Select a biller --</option>') {
      dropdown.innerHTML = '<option value="">-- No valid billers available --</option>';
      dropdown.disabled = true;
      return;
    }

    dropdown.innerHTML = html;
    dropdown.disabled = false;
  } catch (err) {
    console.error("Failed to load billers:", err);
    const dropdown = getEl("executeBillerId");
    if (dropdown) {
      dropdown.innerHTML = '<option value="">-- Error loading billers --</option>';
    }
  }
}

async function onExecuteBillerSelected() {
  const billerId = String(getEl("executeBillerId")?.value || "").trim();
  const paymentItemDropdown = getEl("executePaymentItemId");
  const amountInput = getEl("executeAmount");

  if (!paymentItemDropdown) return;

  if (!billerId) {
    paymentItemDropdown.innerHTML = '<option value="">-- Select a biller first --</option>';
    paymentItemDropdown.disabled = true;
    if (amountInput) amountInput.readOnly = false;
    return;
  }

  try {
    paymentItemDropdown.innerHTML = '<option value="">Loading payment types...</option>';
    paymentItemDropdown.disabled = true;

    const paymentItemRequests = [
      () => fetch(`${API_BASE}/api/bills/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ biller_id: Number(billerId) })
      }),
      () => fetch(`${API_BASE}/api/execute/payment-items?biller_id=${encodeURIComponent(billerId)}`),
    ];

    let items = [];

    for (const request of paymentItemRequests) {
      const response = await request();
      const data = await response.json();

      if (response.ok && data?.status !== "error" && Array.isArray(data?.data)) {
        items = data.data;
        break;
      }
    }
    
    if (items.length === 0) {
      paymentItemDropdown.innerHTML = '<option value="">-- No payment types available --</option>';
      return;
    }

    let html = '<option value="">-- Select payment type --</option>';
    items.forEach((item) => {
      const code = item?.paymentCode || item?.code || "";
      const name = item?.paymentitemname || item?.name || item?.itemName || "Unknown";
      const amount = item?.amount ?? "";
      const isAmountFixed = item?.isAmountFixed ?? "";
      const fee = item?.itemFee ?? "";
      if (code) {
        html += `<option value="${escapeHtml(code)}" data-amount="${escapeHtml(String(amount))}" data-fixed="${escapeHtml(String(isAmountFixed))}" data-fee="${escapeHtml(String(fee))}">${escapeHtml(name)}</option>`;
      }
    });

    paymentItemDropdown.innerHTML = html;
    paymentItemDropdown.disabled = false;
    onExecutePaymentItemSelected();
  } catch (err) {
    console.error("Failed to load payment items:", err);
    paymentItemDropdown.innerHTML = '<option value="">-- Error loading payment types --</option>';
  }
}

function onExecutePaymentItemSelected() {
  const paymentItemDropdown = getEl("executePaymentItemId");
  const amountInput = getEl("executeAmount");

  if (!paymentItemDropdown || !amountInput) return;

  const selectedOption = paymentItemDropdown.options[paymentItemDropdown.selectedIndex];
  if (!selectedOption || !selectedOption.value) {
    amountInput.readOnly = false;
    return;
  }

  const rawFixed = String(selectedOption.dataset.fixed || "").toLowerCase();
  const isFixed = ["true", "1", "yes"].includes(rawFixed);
  const amount = Number(String(selectedOption.dataset.amount || "").trim());

  if (isFixed && Number.isFinite(amount) && amount > 0) {
    amountInput.value = String(amount);
    amountInput.readOnly = true;
    return;
  }

  amountInput.readOnly = false;
}

async function confirmExecutePayment() {
  const customerId = String(getEl("executeCustomerId")?.value || "").trim();
  const amountRaw = String(getEl("executeAmount")?.value || "").trim();
  const paymentCode = String(getEl("executePaymentItemId")?.value || "").trim();
  const amountNGN = Number(amountRaw);
  const amountKobo = Math.round(amountNGN * 100);

  if (!customerId) {
    showToast("Enter customer ID.", "error");
    return;
  }
  if (!Number.isFinite(amountNGN) || amountNGN <= 0) {
    showToast("Enter a valid amount.", "error");
    return;
  }
  if (amountKobo < 20000) {
    showToast("Minimum amount is ₦200.00", "error");
    return;
  }
  if (!paymentCode) {
    showToast("Select a payment type.", "error");
    return;
  }

  setExecuteStatus("loading", "Validating customer...", "Step 1 of 2: Validate customer");

  try {
    const validateRes = await fetch(`${API_BASE}/api/bills/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customerId: customerId,
        paymentCode: paymentCode
      })
    });

    const validateData = await validateRes.json();

    if (!validateRes.ok || !validateData?.valid) {
      const reason = validateData?.message || "Customer validation failed";
      setExecuteStatus("error", "Validation failed.", reason);
      showToast(reason, "error");
      return;
    }

    setExecuteStatus("loading", "Processing payment...", "Step 2 of 2: Initiate payment");
    await sleep(500);

    const payRes = await fetch(`${API_BASE}/api/bills/pay`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customerId: customerId,
        paymentCode: paymentCode,
        amount: amountKobo,
        customerMobile: "",
        customerEmail: ""
      })
    });

    const payData = await payRes.json();

    if (!payRes.ok) {
      const reason = payData?.message || `Payment failed (${payRes.status})`;
      setExecuteStatus("error", "Payment error.", reason);
      showToast(reason, "error");
      return;
    }

    const reference = payData?.reference || "N/A";
    const responseCode = payData?.response_code || "Unknown";

    if (responseCode === "90009") {
      setExecuteStatus(
        "pending",
        "Payment initiated successfully.",
        `Reference: ${reference} | Amount: ₦${amountNGN.toLocaleString("en-NG")} | Status: Processing`
      );
      showToast(`Payment initiated. Reference: ${reference}`);
      return;
    }

    if (responseCode === "90000") {
      setExecuteStatus(
        "success",
        "Payment completed successfully.",
        `Reference: ${reference} | Amount: ₦${amountNGN.toLocaleString("en-NG")}`
      );
      showToast("Payment completed successfully.");
      return;
    }

    setExecuteStatus(
      "warning",
      "Payment status unclear.",
      `Response: ${responseCode} | Reference: ${reference}`
    );
    showToast(`Payment processed with status: ${responseCode}`, "warning");
  } catch (err) {
    const msg = String(err?.message || "Network error");
    setExecuteStatus(
      "error",
      "Network error.",
      "Unable to complete payment. Check your connection and try again."
    );
    showToast(msg, "error");
  }
}

// ===== Bank Verification Flow =====

function setupBankVerifyModalBehavior() {
  const modal = getEl("bankVerifyModal");
  if (!modal) return;

  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeBankVerifyFlow(false);
    }
  });
}

async function openBankVerifyFlow() {
  const modal = getEl("bankVerifyModal");
  if (!modal) return;

  const dropdown = getEl("bankSelectDropdown");
  const accountInput = getEl("bankAccountNumber");
  const status = getEl("bankVerifyStatus");

  if (status) {
    status.className = "execute-status hidden";
    status.innerHTML = "";
  }

  // Load banks
  if (dropdown) {
    dropdown.innerHTML = '<option value="">-- Loading banks --</option>';
    try {
      const bankEndpoints = [
        `${API_BASE}/api/bank-verify/banks`,
        `${API_BASE}/api/execute/banks`,
      ];

      let banks = [];
      let reason = "";

      for (const endpoint of bankEndpoints) {
        const response = await fetch(endpoint);
        const data = await response.json();

        if (response.ok && (data?.status === "success" || data?.success) && Array.isArray(data?.data)) {
          banks = data.data;
          break;
        }

        reason = String(data?.message || `Request failed (${response.status})`).trim();
      }

      if (banks.length > 0) {
        dropdown.innerHTML = '<option value="">-- Select a bank --</option>';
        banks.forEach((bank) => {
          const opt = document.createElement("option");
          opt.value = bank.code;
          opt.textContent = `${bank.name} (${bank.code})`;
          dropdown.appendChild(opt);
        });
      } else {
        dropdown.innerHTML = '<option value="">Bank list unavailable</option>';
        setBankVerifyStatus(
          "pending",
          "Unable to load banks right now.",
          reason || "No bank list endpoint returned usable data."
        );
      }
    } catch (err) {
      dropdown.innerHTML = '<option value="">Network error</option>';
      setBankVerifyStatus(
        "pending",
        "Network error while loading banks.",
        String(err?.message || "Check your connection and try again.")
      );
    }
  }

  if (accountInput) accountInput.value = "";
  modal.classList.remove("hidden");
}

function closeBankVerifyFlow(clearFields = false) {
  const modal = getEl("bankVerifyModal");
  if (!modal) return;

  modal.classList.add("hidden");

  if (clearFields) {
    const dropdown = getEl("bankSelectDropdown");
    const account = getEl("bankAccountNumber");
    if (dropdown) dropdown.value = "";
    if (account) account.value = "";
  }
}

function setBankVerifyStatus(kind, message, details = "") {
  const status = getEl("bankVerifyStatus");
  if (!status) return;

  status.className = `execute-status ${kind}`;
  status.classList.remove("hidden");
  status.innerHTML = `
    <div class="execute-status-title">${message}</div>
    ${details ? `<div class="execute-status-detail">${details}</div>` : ""}
  `;
}

function onBankSelected() {
  const status = getEl("bankVerifyStatus");
  if (status) {
    status.className = "execute-status hidden";
    status.innerHTML = "";
  }
}

async function confirmBankVerify() {
  const bankCode = String(getEl("bankSelectDropdown")?.value || "").trim();
  const accountNumber = String(getEl("bankAccountNumber")?.value || "").trim();

  if (!bankCode) {
    showToast("Select a bank.", "error");
    return;
  }
  if (!accountNumber || accountNumber.length < 10) {
    showToast("Enter a valid account number (10+ digits).", "error");
    return;
  }

  setBankVerifyStatus("loading", "Verifying account...", "Connecting to bank...");

  try {
    const response = await fetch(`${API_BASE}/api/bank-verify/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        account_number: accountNumber,
        bank_code: bankCode,
      }),
    });

    const payload = await response.json();

    if (response.ok && payload?.status === "success") {
      const name = payload?.account_name || "N/A";
      setBankVerifyStatus(
        "success",
        "Account verified successfully.",
        `Account Name: ${name} | Account No: ${accountNumber}`
      );
      showToast(`Account verified: ${name}`);
      return;
    }

    const message = payload?.message || `Verification failed (${response.status})`;
    setBankVerifyStatus("error", "Verification failed.", message);
    showToast(message, "error");
  } catch (err) {
    const msg = String(err?.message || "Network error");
    setBankVerifyStatus("error", "Network error.", msg);
    showToast(msg, "error");
  }
}

async function signInWithGoogle() {
  if (!window.finsightAuth) {
    showToast("Auth bootstrap is not loaded.", "error");
    return;
  }

  await window.finsightAuth.fetchPublicConfig();
  const config = window.finsightAuth.getConfig();
  if (!config.configured) {
    showToast("Sign-in is not configured on the server yet.", "warning");
    goToLogin();
    return;
  }

  const redirectTo = window.location.href.split("#")[0];
  const { error } = await window.finsightAuth.signInWithGoogle(redirectTo, "./dashboard.html");

  if (error) showToast(`Sign-in failed: ${error.message}`, "error");
}

async function getSupabaseSession() {
  if (window.finsightAuth?.getSession) {
    return window.finsightAuth.getSession();
  }
  if (!window.supabase?.auth) return null;
  const { data } = await window.supabase.auth.getSession();
  return data?.session || null;
}

function getSessionAvatarUrl(session) {
  const meta = session?.user?.user_metadata || {};
  const candidates = [meta.avatar_url, meta.picture, meta.photo_url, session?.user?.avatar_url];
  for (const candidate of candidates) {
    const url = String(candidate || "").trim();
    if (url.startsWith("http://") || url.startsWith("https://")) {
      return url;
    }
  }
  return "";
}

function setHeaderAvatar(session) {
  const avatar = getEl("userAvatar");
  const avatarImg = getEl("userAvatarImg");
  const avatarFallback = getEl("userAvatarFallback");
  const brandMark = getEl("headerBrandMark");
  if (!avatar || !avatarImg || !avatarFallback) return;

  if (!session?.user) {
    avatar.classList.add("hidden");
    avatarImg.classList.add("hidden");
    avatarImg.removeAttribute("src");
    avatarFallback.textContent = "U";
    brandMark?.classList.remove("hidden");
    return;
  }

  const email = String(session.user.email || "").trim();
  const name = String(session.user.user_metadata?.full_name || session.user.user_metadata?.name || "").trim();
  const seed = name || email || "User";
  avatarFallback.textContent = seed.charAt(0).toUpperCase();
  avatar.classList.remove("hidden");
  brandMark?.classList.add("hidden");

  const avatarUrl = getSessionAvatarUrl(session);
  if (!avatarUrl) {
    avatarImg.classList.add("hidden");
    avatarImg.removeAttribute("src");
    return;
  }

  avatarImg.onload = () => {
    avatarImg.classList.remove("hidden");
  };
  avatarImg.onerror = () => {
    avatarImg.classList.add("hidden");
    avatarImg.removeAttribute("src");
  };
  avatarImg.src = avatarUrl;
}

async function showHistoryModal() {
  const session = await getSupabaseSession();
  if (!session) {
    sessionStorage.setItem(AUTH_PENDING_ACTION_KEY, "showHistoryModal");
    showToast("Please sign in to view your history.", "info");
    goToLogin();
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
  closeScoreDrawer();
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

function setupInteractiveTiles() {
  const tileEntries = [
    {
      selector: ".hero-card-a, .media-a, .flow-media-a, .story-1",
      label: "Spending Pattern Pulse",
      title: "Spending Pattern Pulse",
      summary: "Your spend profile clusters around convenience and impulse windows, especially right after income inflow.",
      points: [
        "Highest risk window is typically within 72 hours of salary credit.",
        "Recurring small debits are compounding faster than planned categories.",
        "Pre-committing budget caps can reduce unplanned spend velocity."
      ],
      metricLabel: "Signal Strength",
      metricValue: "High",
      actionLabel: "Review patterns",
      actionTarget: "resultsPanel",
      fallbackTarget: "inputPanel",
      fallbackMessage: "Run analysis first, then review your spending patterns."
    },
    {
      selector: ".hero-card-b, .media-b, .flow-media-b, .story-2",
      label: "Runway Pressure Map",
      title: "Runway Pressure Map",
      summary: "Liquidity pressure follows a predictable arc and can be surfaced early before balance stress intensifies.",
      points: [
        "Mid-cycle expenses are pulling runway down disproportionately.",
        "Your fixed-cost density leaves limited buffer in low-cash weeks.",
        "A weekly burn checkpoint materially improves forecast accuracy."
      ],
      metricLabel: "Runway Outlook",
      metricValue: "Watch",
      actionLabel: "Check runway",
      actionTarget: "resultsPanel",
      fallbackTarget: "inputPanel",
      fallbackMessage: "Run analysis first to unlock runway and risk insights."
    },
    {
      selector: ".hero-card-c, .media-c, .flow-media-c, .story-3",
      label: "Savings Momentum Lens",
      title: "Savings Momentum Lens",
      summary: "Small repeatable behavior shifts produce the fastest score lift when applied consistently.",
      points: [
        "Automating micro-savings improves consistency more than one-off transfers.",
        "Rounding-up spend events can create low-friction reserve growth.",
        "Momentum increases when savings are triggered on income day."
      ],
      metricLabel: "Momentum Grade",
      metricValue: "Building",
      actionLabel: "Open actions",
      actionTarget: "actionsCard",
      fallbackTarget: "inputPanel",
      fallbackMessage: "Run analysis first, then execute recommended actions."
    }
  ];

  const layer = document.createElement("div");
  layer.className = "tile-insight-layer hidden";
  layer.innerHTML = `
    <article class="tile-insight-card" role="dialog" aria-modal="true" aria-label="Tile insight" tabindex="-1">
      <button class="tile-insight-close" type="button" aria-label="Close insight">
        <i class="fa-solid fa-xmark" aria-hidden="true"></i>
      </button>
      <p class="tile-insight-kicker">Insight</p>
      <h4 class="tile-insight-title"></h4>
      <p class="tile-insight-summary"></p>
      <ul class="tile-insight-list"></ul>
      <div class="tile-insight-metric">
        <span class="tile-insight-metric-label"></span>
        <strong class="tile-insight-metric-value"></strong>
      </div>
      <button class="tile-insight-action" type="button">
        <i class="fa-solid fa-bolt" aria-hidden="true"></i>
        <span class="tile-insight-action-label">Take action</span>
      </button>
    </article>
  `;
  document.body.appendChild(layer);

  const card = layer.querySelector(".tile-insight-card");
  const closeBtn = layer.querySelector(".tile-insight-close");
  const titleEl = layer.querySelector(".tile-insight-title");
  const summaryEl = layer.querySelector(".tile-insight-summary");
  const listEl = layer.querySelector(".tile-insight-list");
  const metricLabelEl = layer.querySelector(".tile-insight-metric-label");
  const metricValueEl = layer.querySelector(".tile-insight-metric-value");
  const actionBtn = layer.querySelector(".tile-insight-action");
  const actionLabelEl = layer.querySelector(".tile-insight-action-label");
  let activeTile = null;
  let activeEntry = null;

  const closeInsight = () => {
    layer.classList.remove("is-open");
    window.setTimeout(() => {
      layer.classList.add("hidden");
    }, 180);

    if (activeTile) {
      activeTile.setAttribute("aria-expanded", "false");
      activeTile.focus({ preventScroll: true });
      activeTile = null;
    }

    activeEntry = null;
  };

  const flashSection = (section) => {
    section.classList.add("section-jump-highlight");
    window.setTimeout(() => {
      section.classList.remove("section-jump-highlight");
    }, 1200);
  };

  const jumpToActionTarget = (entry) => {
    const target = getEl(entry.actionTarget);
    const fallback = getEl(entry.fallbackTarget || "inputPanel");

    if (target && !target.classList.contains("hidden")) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      flashSection(target);
      closeInsight();
      return;
    }

    if (fallback) {
      fallback.scrollIntoView({ behavior: "smooth", block: "start" });
      flashSection(fallback);
    }

    closeInsight();
    if (entry.fallbackMessage) showToast(entry.fallbackMessage, "warning");
  };

  const placeCardNearTile = (tileRect) => {
    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;
    const cardWidth = Math.min(360, viewportW - 24);
    const cardHeight = 330;

    let left = tileRect.right + 12;
    let top = tileRect.top;

    if (left + cardWidth > viewportW - 12) {
      left = tileRect.left - cardWidth - 12;
    }

    if (left < 12) {
      left = Math.max(12, (viewportW - cardWidth) / 2);
    }

    if (top + cardHeight > viewportH - 12) {
      top = Math.max(12, viewportH - cardHeight - 12);
    }

    card.style.left = `${Math.round(left)}px`;
    card.style.top = `${Math.round(top)}px`;
  };

  const openInsight = (tile, entry) => {
    tile.classList.add("is-burst");
    window.setTimeout(() => tile.classList.remove("is-burst"), 260);

    titleEl.textContent = entry.title;
    summaryEl.textContent = entry.summary;
    listEl.innerHTML = entry.points.map((point) => `<li>${point}</li>`).join("");
    metricLabelEl.textContent = entry.metricLabel;
    metricValueEl.textContent = entry.metricValue;
    actionLabelEl.textContent = entry.actionLabel || "Take action";

    const rect = tile.getBoundingClientRect();
    placeCardNearTile(rect);

    layer.classList.remove("hidden");
    requestAnimationFrame(() => {
      layer.classList.add("is-open");
      card.focus();
    });

    if (activeTile) activeTile.setAttribute("aria-expanded", "false");
    activeTile = tile;
    activeTile.setAttribute("aria-expanded", "true");
    activeEntry = entry;
  };

  layer.addEventListener("click", (event) => {
    if (event.target === layer) closeInsight();
  });

  closeBtn?.addEventListener("click", closeInsight);
  actionBtn?.addEventListener("click", () => {
    if (!activeEntry) return;
    jumpToActionTarget(activeEntry);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !layer.classList.contains("hidden")) {
      closeInsight();
    }
  });

  window.addEventListener("resize", () => {
    if (!activeTile || layer.classList.contains("hidden")) return;
    placeCardNearTile(activeTile.getBoundingClientRect());
  });

  const activateTile = (tile, entry) => openInsight(tile, entry);

  tileEntries.forEach((entry) => {
    const nodes = document.querySelectorAll(entry.selector);
    nodes.forEach((tile) => {
      tile.classList.add("interactive-tile");
      tile.setAttribute("role", "button");
      tile.setAttribute("tabindex", "0");
      tile.setAttribute("aria-label", `${entry.label}. Click for insight.`);
      tile.setAttribute("aria-expanded", "false");
      tile.setAttribute("title", entry.label);

      tile.addEventListener("click", () => activateTile(tile, entry));
      tile.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        activateTile(tile, entry);
      });
    });
  });
}

window.addEventListener("DOMContentLoaded", () => {
  updateThemeColorMeta();
  switchTab("sms");

  getSupabaseSession().then((session) => {
    setHeaderAvatar(session);
  }).catch(() => {
    setHeaderAvatar(null);
  });

  if (window.supabase?.auth) {
    window.supabase.auth.onAuthStateChange((_event, session) => {
      setHeaderAvatar(session || null);
      if (!session) return;
      const modal = getEl("authModal");
      const pendingAction = modal?._pendingAction;
      if (typeof pendingAction === "function") {
        closeAuthModal(true);
        pendingAction().catch(() => {
          showToast("Unable to continue action after sign-in.", "error");
        });
      }

      runPendingAuthActionIfAny().catch(() => {
        // no-op
      });
    });
  }

  runPendingAuthActionIfAny().catch(() => {
    // no-op
  });

  setupAuthModalBehavior();
  setupExecuteModalBehavior();
  setupBankVerifyModalBehavior();
  setupScoreDrawerBehavior();

  setupPageTransitions();
  setupBrandMarkTilt();
  setupParallaxCards();
  setupBackgroundObjects();
  setupMouseHoverEffects();
  setupInteractiveTiles();
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
window.openExecuteFlow = openExecuteFlow;
window.closeExecuteFlow = closeExecuteFlow;
window.confirmExecutePayment = confirmExecutePayment;
window.onExecutePaymentItemSelected = onExecutePaymentItemSelected;
window.openBankVerifyFlow = openBankVerifyFlow;
window.closeBankVerifyFlow = closeBankVerifyFlow;
window.confirmBankVerify = confirmBankVerify;
window.onBankSelected = onBankSelected;
window.simulateSave = simulateSave;
window.simulateBill = simulateBill;
window.signInWithGoogle = signInWithGoogle;
window.goToLogin = goToLogin;
window.closeAuthModal = closeAuthModal;
window.showHistoryModal = showHistoryModal;
window.closeHistoryModal = closeHistoryModal;
window.viewAnalysis = viewAnalysis;
window.openScoreDrawer = openScoreDrawer;
window.closeScoreDrawer = closeScoreDrawer;
