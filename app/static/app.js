const state = { config: null, status: null, backtest: null };

const euro = new Intl.NumberFormat("en-GB", { style: "currency", currency: "EUR" });
const preciseEuro = new Intl.NumberFormat("en-GB", {
  style: "currency", currency: "EUR", minimumFractionDigits: 4, maximumFractionDigits: 4
});
const microEuro = new Intl.NumberFormat("en-GB", {
  style: "currency", currency: "EUR", minimumFractionDigits: 6, maximumFractionDigits: 6
});
const number = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 });

function formatMarketPrice(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "–";
  const absolute = Math.abs(amount);
  if (absolute > 0 && absolute < 0.01) return microEuro.format(amount);
  if (absolute < 1) return preciseEuro.format(amount);
  return euro.format(amount);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
  return payload;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
}

function formatTime(value) {
  if (!value) return "–";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? escapeHtml(value) : date.toLocaleString("en-GB");
}

function toast(message, isError = false) {
  const element = document.getElementById("toast");
  element.textContent = message;
  element.className = `toast visible${isError ? " error" : ""}`;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { element.className = "toast"; }, 4500);
}

function setBusy(button, busy, busyText) {
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = busyText;
  } else if (button.dataset.label) {
    button.textContent = button.dataset.label;
  }
  button.disabled = busy;
}

function renderConfig() {
  const c = state.config;
  document.getElementById("capital").textContent = euro.format(c.starting_capital);
  document.getElementById("tradeRisk").textContent = `${number.format(c.risk_per_trade * 100)} % · ${euro.format(c.risk_amount)}`;
  document.getElementById("aggregateRisk").textContent = `${number.format(c.max_aggregate_risk * 100)} % · ${euro.format(c.aggregate_risk_amount)}`;
  document.getElementById("dailyRisk").textContent = `${number.format(c.max_daily_loss * 100)} % · ${euro.format(c.daily_loss_amount)}`;
  document.getElementById("hardStop").textContent = `${number.format(c.hard_drawdown * 100)} %`;
  document.getElementById("dataSource").textContent = c.data_source === "demo" ? "Offline demo" : "Bitpanda Fusion";
  document.getElementById("nextRun").textContent = `every ${c.poll_seconds} seconds`;
  document.getElementById("systemStatus").textContent = c.paper_only ? "Simulation active" : "Safety error";
  document.getElementById("maxPositions").textContent = c.max_open_positions;
  document.getElementById("maxTrades").textContent = c.max_trades_per_day;
  document.getElementById("pairChips").innerHTML = c.pairs.map((pair) => `<span>${escapeHtml(pair)}</span>`).join("");
  document.getElementById("sourceHint").textContent = c.data_source === "demo"
    ? "I start safely with reproducible demo data. For Fusion, I provide an API key with Read permission only."
    : "I use Fusion market data and never expose the API key to the dashboard.";
}

function renderMarkets() {
  const rows = state.status.markets || [];
  const byPair = Object.fromEntries(rows.map((item) => [item.pair, item]));
  document.getElementById("marketGrid").innerHTML = state.config.pairs.map((pair) => {
    const item = byPair[pair];
    if (!item) return `<article class="market-card pending"><div><strong>${escapeHtml(pair)}</strong><span>waiting</span></div><p>I have not processed a closed candle yet.</p></article>`;
    const signal = item.signal > 0 ? "Long setup" : item.signal < 0 ? "Short setup" : "Neutral";
    const trend = item.trend > 0 ? "Uptrend" : item.trend < 0 ? "Downtrend" : "No confirmed trend";
    const signalClass = item.signal > 0 ? "positive" : item.signal < 0 ? "negative" : "muted";
    return `<article class="market-card">
      <div><strong>${escapeHtml(pair)}</strong><span class="${signalClass}">${signal}</span></div>
      <b>${formatMarketPrice(item.price)}</b>
      <p>${trend} · RSI ${number.format(item.rsi)}</p>
      <small>${escapeHtml(item.reason)} · ${formatTime(item.candle_time)}</small>
    </article>`;
  }).join("");
}

function renderPortfolios() {
  const portfolios = state.status.portfolios || [];
  document.getElementById("portfolioGrid").innerHTML = portfolios.map((item) => {
    const resultClass = item.pnl >= 0 ? "positive" : "negative";
    const locked = Boolean(item.hard_locked);
    const dayLocked = Boolean(item.daily_locked);
    const badge = locked ? "LOCKED" : dayLocked ? "DAILY STOP" : item.position;
    return `<article class="portfolio-card" style="--accent:${escapeHtml(item.color)}">
      <div class="portfolio-top"><strong>${escapeHtml(item.label)}</strong><span class="position-tag">${escapeHtml(badge)}</span></div>
      <div class="portfolio-value">${euro.format(item.equity)}</div>
      <div class="portfolio-return ${resultClass}">${item.pnl >= 0 ? "+" : ""}${euro.format(item.pnl)} · ${number.format(item.return_pct)} %</div>
      <div class="portfolio-details">
        <div><small>Open positions</small><strong>${item.position_count}/${state.config.max_open_positions}</strong></div>
        <div><small>Trades today</small><strong>${item.trades_today}/${state.config.max_trades_per_day}</strong></div>
        <div><small>Notional</small><strong>${euro.format(item.notional)}</strong></div>
        <div><small>Open risk</small><strong>${euro.format(item.open_risk)}</strong></div>
        <div><small>Effective leverage</small><strong>${number.format(item.effective_leverage)}×</strong></div>
        <div><small>Last run</small><strong>${formatTime(item.last_run_at)}</strong></div>
      </div>
      ${locked ? `<p class="negative">${escapeHtml(item.lock_reason)}</p>` : ""}
    </article>`;
  }).join("");
  const dated = portfolios.map((item) => item.last_run_at).filter(Boolean).sort();
  document.getElementById("lastUpdate").textContent = dated.length ? `Updated ${formatTime(dated.at(-1))}` : "I have not run a scan yet";
}

function renderPositions() {
  const positions = state.status.positions || [];
  const labels = Object.fromEntries((state.status.portfolios || []).map((p) => [p.strategy_id, p.label]));
  document.getElementById("positionRows").innerHTML = positions.length ? positions.map((item) => {
    const pnlClass = item.unrealized_pnl >= 0 ? "positive" : "negative";
    return `<tr><td>${escapeHtml(labels[item.strategy_id] || item.strategy_id)}</td><td>${escapeHtml(item.pair)}</td><td>${item.side === "long" ? "Long" : "Short"}</td><td>${euro.format(item.notional)}</td><td>${euro.format(item.stop_price)}</td><td>${euro.format(item.take_profit)}</td><td class="${pnlClass}">${euro.format(item.unrealized_pnl)}</td></tr>`;
  }).join("") : `<tr><td colspan="7" class="muted">I have no open position.</td></tr>`;
}

function renderTrades() {
  const rows = state.status.trades || [];
  const labels = Object.fromEntries((state.status.portfolios || []).map((p) => [p.strategy_id, p.label]));
  document.getElementById("tradeRows").innerHTML = rows.length ? rows.slice(0, 16).map((trade) => {
    const pnl = trade.pnl == null ? "–" : euro.format(trade.pnl);
    const pnlClass = trade.pnl == null ? "" : trade.pnl >= 0 ? "positive" : "negative";
    return `<tr><td>${escapeHtml(labels[trade.strategy_id] || trade.strategy_id)}</td><td>${escapeHtml(trade.pair)}</td><td>${trade.side === "long" ? "Long" : "Short"}</td><td class="${pnlClass}">${pnl}</td><td>${escapeHtml(trade.status)}</td></tr>`;
  }).join("") : `<tr><td colspan="5" class="muted">I have no trades yet.</td></tr>`;
}

function renderEvents() {
  const events = state.status.events || [];
  document.getElementById("eventList").innerHTML = events.length ? events.slice(0, 18).map((event) =>
    `<div class="event"><span class="event-level ${escapeHtml(event.level)}">${escapeHtml(event.level)}</span><span>${escapeHtml(event.message)}</span><time>${formatTime(event.created_at)}</time></div>`
  ).join("") : `<p class="muted">I have no events yet.</p>`;
}

function renderBacktest() {
  const result = state.backtest;
  if (!result || result.status !== "ok") return;
  document.getElementById("backtestSection").hidden = false;
  document.getElementById("backtestPeriod").textContent = `${formatTime(result.from)} to ${formatTime(result.to)} · ${result.bars} candles · ${result.pairs.length} pairs`;
  const cards = [...result.strategies, result.benchmark];
  document.getElementById("backtestGrid").innerHTML = cards.map((item) => {
    const returnClass = item.total_return_pct >= 0 ? "positive" : "negative";
    return `<article class="backtest-card" style="border-top:2px solid ${escapeHtml(item.color)}">
      <span>${escapeHtml(item.label)}</span><strong>${euro.format(item.final_equity)}</strong>
      <div class="mini-stats">
        <div><span>Total return</span><b class="${returnClass}">${number.format(item.total_return_pct)} %</b></div>
        <div><span>Max. drawdown</span><b class="negative">${number.format(item.max_drawdown_pct)} %</b></div>
        <div><span>Trades</span><b>${item.trades ?? "–"}</b></div>
        <div><span>Win rate</span><b>${item.win_rate_pct == null ? "–" : `${number.format(item.win_rate_pct)} %`}</b></div>
        <div><span>Daily stops</span><b>${item.daily_limit_hits ?? "–"}</b></div>
        <div><span>Max. positions</span><b>${item.max_positions ?? "–"}</b></div>
      </div>
    </article>`;
  }).join("");
  const series = cards.map((item) => ({ label: item.label, color: item.color, points: item.curve }));
  document.getElementById("chartTitle").textContent = "Multi-coin backtest";
  drawChart(series);
}

function drawChart(series) {
  const svg = document.getElementById("equityChart");
  const empty = document.getElementById("chartEmpty");
  const valid = series.filter((item) => item.points && item.points.length > 1);
  if (!valid.length) {
    svg.style.display = "none";
    empty.style.display = "grid";
    document.getElementById("chartLegend").innerHTML = "";
    return;
  }
  const values = valid.flatMap((item) => item.points.map((point) => Number(point.equity))).filter(Number.isFinite);
  let min = Math.min(...values);
  let max = Math.max(...values);
  const padding = Math.max((max - min) * .12, 5);
  min -= padding; max += padding;
  const x0 = 62, x1 = 980, y0 = 18, y1 = 282;
  const y = (value) => y1 - ((value - min) / (max - min || 1)) * (y1 - y0);
  const parts = [];
  for (let i = 0; i <= 4; i += 1) {
    const yy = y0 + ((y1 - y0) * i / 4);
    const label = max - ((max - min) * i / 4);
    parts.push(`<line class="chart-grid" x1="${x0}" y1="${yy}" x2="${x1}" y2="${yy}"/><text class="chart-label" x="0" y="${yy + 5}">${Math.round(label)} €</text>`);
  }
  valid.forEach((item) => {
    const coordinates = item.points.map((point, index) => {
      const xx = x0 + (index / (item.points.length - 1)) * (x1 - x0);
      return `${xx.toFixed(2)},${y(Number(point.equity)).toFixed(2)}`;
    }).join(" ");
    parts.push(`<polyline class="chart-line" stroke="${escapeHtml(item.color)}" points="${coordinates}"/>`);
  });
  svg.innerHTML = parts.join("");
  svg.style.display = "block";
  empty.style.display = "none";
  document.getElementById("chartLegend").innerHTML = valid.map((item) => `<span><i style="background:${escapeHtml(item.color)}"></i>${escapeHtml(item.label)}</span>`).join("");
}

function renderPaperChart() {
  const labels = Object.fromEntries((state.status.portfolios || []).map((p) => [p.strategy_id, p]));
  const series = Object.entries(state.status.curves || {}).map(([id, points]) => ({
    label: labels[id]?.label || id,
    color: labels[id]?.color || "#fff",
    points,
  }));
  document.getElementById("chartTitle").textContent = "My paper equity";
  drawChart(series);
}

async function refreshStatus() {
  state.status = await requestJson("/api/status");
  renderMarkets();
  renderPortfolios();
  renderPositions();
  renderTrades();
  renderEvents();
  if (!state.backtest) renderPaperChart();
}

async function initialize() {
  try {
    [state.config, state.status] = await Promise.all([
      requestJson("/api/config"), requestJson("/api/status")
    ]);
    renderConfig();
    renderMarkets();
    renderPortfolios();
    renderPositions();
    renderTrades();
    renderEvents();
    renderPaperChart();
  } catch (error) {
    document.getElementById("systemStatus").textContent = "Unavailable";
    toast(error.message, true);
  }
}

document.getElementById("runButton").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  setBusy(button, true, "I am scanning …");
  try {
    const result = await requestJson("/api/paper/run", { method: "POST" });
    toast(result.status === "ok" ? `${result.new_pairs.length} new markets processed.` : result.message);
    state.backtest = null;
    document.getElementById("backtestSection").hidden = true;
    await refreshStatus();
  } catch (error) { toast(error.message, true); }
  finally { setBusy(button, false); }
});

document.getElementById("backtestButton").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  setBusy(button, true, "I am running the backtest …");
  try {
    state.backtest = await requestJson("/api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bars: Math.min(1000, state.config.backtest_bars) }),
    });
    renderBacktest();
    toast("I completed the multi-coin backtest.");
  } catch (error) { toast(error.message, true); }
  finally { setBusy(button, false); }
});

document.getElementById("resetButton").addEventListener("click", async () => {
  if (!window.confirm("Do I really want to delete every local multi-coin paper trade and balance?")) return;
  try {
    await requestJson("/api/reset?confirm=RESET", { method: "POST" });
    state.backtest = null;
    document.getElementById("backtestSection").hidden = true;
    await refreshStatus();
    toast("I reset the paper accounts.");
  } catch (error) { toast(error.message, true); }
});

initialize();
window.setInterval(() => refreshStatus().catch(() => {}), 30_000);
