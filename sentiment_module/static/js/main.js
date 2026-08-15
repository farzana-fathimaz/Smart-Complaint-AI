/* ════════════════════════════════════════════
   SENTIMENT IQ — FRONTEND LOGIC
═══════════════════════════════════════════════ */

// Set today's date in topbar
document.getElementById("topbar-date").textContent = new Date().toLocaleDateString("en-IN", {
  weekday: "long", year: "numeric", month: "long", day: "numeric"
});

// Character counter
document.getElementById("complaint-text").addEventListener("input", function () {
  document.getElementById("char-count").textContent = this.value.length;
});

/* ─── TOAST ──────────────────────────────────── */
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

/* ─── BADGE HELPERS ──────────────────────────── */
function labelBadge(label) {
  const map = { Positive: "badge-pos", Negative: "badge-neg", Neutral: "badge-neu" };
  return `<span class="badge ${map[label] || "badge-neu"}">${label}</span>`;
}

function toneBadge(tone) {
  const map = { Angry: "badge-ang", Frustrated: "badge-frus", Neutral: "badge-neu", Positive: "badge-pos" };
  return `<span class="badge ${map[tone] || "badge-neu"}">${tone}</span>`;
}

/* ─── LOAD STATS ─────────────────────────────── */
async function loadStats() {
  const res  = await fetch("/stats");
  const data = await res.json();

  document.getElementById("s-total").textContent    = data.total;
  document.getElementById("s-positive").textContent = data.positive;
  document.getElementById("s-negative").textContent = data.negative;
  document.getElementById("s-angry").textContent    = data.angry;
}

/* ─── LOAD HISTORY ───────────────────────────── */
async function loadHistory() {
  const res  = await fetch("/history");
  const list = await res.json();
  const tbody = document.getElementById("history-tbody");

  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-muted);">No history yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(r => `
    <tr>
      <td style="color:var(--text-muted);font-weight:600;">#${r.id}</td>
      <td class="truncate" title="${r.text}">${r.text}</td>
      <td style="font-weight:600;">${r.polarity.toFixed(3)}</td>
      <td>${r.subjectivity.toFixed(3)}</td>
      <td>${labelBadge(r.label)}</td>
      <td>${r.emoji} ${toneBadge(r.tone)}</td>
      <td style="color:var(--text-muted);font-size:12px;">${r.created_at}</td>
    </tr>
  `).join("");
}

/* ─── ANALYZE ────────────────────────────────── */
async function analyzeText() {
  const text = document.getElementById("complaint-text").value.trim();

  if (!text) { toast("Please enter complaint text."); return; }
  if (text.length < 5) { toast("Text is too short to analyze."); return; }

  const btn = document.getElementById("analyze-btn");
  btn.textContent = "Analyzing...";
  btn.disabled    = true;

  try {
    const res  = await fetch("/analyze", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ text })
    });
    const data = await res.json();

    if (data.error) { toast("⚠️ " + data.error); return; }

    // ── Show result card ──────────────────────────
    const card = document.getElementById("result-card");
    card.style.display = "block";

    document.getElementById("result-emoji").textContent = data.emoji;
    document.getElementById("result-tone").textContent  = data.tone + " Complaint";
    document.getElementById("result-label").textContent = `Sentiment: ${data.label}`;

    document.getElementById("metric-polarity").textContent    = data.polarity.toFixed(3);
    document.getElementById("metric-subjectivity").textContent = data.subjectivity.toFixed(3);

    // Polarity bar: map -1..+1 to 0%..100%
    const polPct = Math.round(((data.polarity + 1) / 2) * 100);
    const subPct = Math.round(data.subjectivity * 100);

    document.getElementById("bar-polarity").style.width     = polPct + "%";
    document.getElementById("bar-subjectivity").style.width  = subPct + "%";

    document.getElementById("result-text-display").textContent = `"${text}"`;

    // Color the polarity bar based on sentiment
    const polBar = document.getElementById("bar-polarity");
    if (data.polarity > 0.1)       polBar.style.background = "var(--green)";
    else if (data.polarity < -0.1) polBar.style.background = "var(--red)";
    else                            polBar.style.background = "var(--amber)";

    // Scroll result into view
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });

    // Refresh stats and history
    loadStats();
    loadHistory();

  } catch (e) {
    toast("Error connecting to server.");
  } finally {
    btn.textContent = "Analyze Sentiment";
    btn.disabled    = false;
  }
}

/* ─── CLEAR HISTORY ──────────────────────────── */
async function clearHistory() {
  if (!confirm("Clear all analysis history?")) return;
  await fetch("/history/clear", { method: "POST" });
  toast("✅ History cleared.");
  loadHistory();
  loadStats();
}

/* ─── INIT ───────────────────────────────────── */
loadStats();
loadHistory();