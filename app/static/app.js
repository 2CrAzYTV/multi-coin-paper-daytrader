const LANGUAGE_STORAGE_KEY = "multiCoinPaperDaytrader.language";
const supportedLanguages = new Set(["en", "de"]);
const state = {
  config: null,
  status: null,
  backtest: null,
  language: "en",
};

const translations = {
  en: {
    pageTitle: "Multi-Coin Paper Daytrader",
    edition: "Paper · Unraid Edition",
    paperOnly: "PAPER ONLY",
    language: "Language",
    languageAria: "Dashboard language",
    eyebrow: "Five markets. One shared risk budget.",
    heroTitle: "Crypto day trading.<br /><span>Without real money.</span>",
    heroCopy: "I scan liquid EUR pairs for 15-minute signals and compare long-only with simulated long/short leverage up to 10×. Every execution, margin value, and liquidation remains paper-only.",
    status: "Status",
    scanInterval: "Scan interval",
    dataSource: "Data source",
    riskLimitsAria: "My risk limits",
    virtualCapital: "Virtual capital",
    perStrategy: "per comparison strategy",
    riskPerTrade: "Risk per trade",
    portfolioWide: "I calculate it portfolio-wide",
    aggregateRisk: "Aggregate open risk",
    acrossCoins: "across every coin",
    dailyLimit: "Daily limit",
    acrossTrades: "across every trade",
    emergencyStop: "Emergency stop",
    untilReset: "until I reset manually",
    marketUniverse: "My market universe",
    selectedPairs: "Selected EUR pairs",
    runScan: "Run scan now",
    runBacktest: "Run multi-coin backtest",
    scanner: "Scanner",
    latestSignals: "My latest market signals",
    trendFilter: "15 min · 1 h trend filter",
    liveSimulation: "Live simulation",
    paperPortfolios: "My paper portfolios",
    notRun: "I have not run a scan yet",
    exposure: "Exposure",
    openPositionsTitle: "My open paper positions",
    strategy: "Strategy",
    pair: "Pair",
    side: "Side",
    notional: "Notional",
    leverage: "Leverage",
    maxLeverage: "Max. leverage",
    margin: "Paper margin",
    marginUsage: "Margin usage",
    liquidation: "Est. liquidation",
    stop: "Stop",
    target: "Target",
    openPnl: "Open P&L",
    noOpenPosition: "I have no open position.",
    performance: "Performance",
    paperEquity: "My paper equity",
    chartAria: "My simulated equity history",
    chartEmpty: "I start with a paper scan or backtest.",
    historicalSimulation: "Historical simulation",
    multiCoinBacktest: "My multi-coin backtest",
    backtestDisclaimer: "This backtest includes an exchange-agnostic paper liquidation estimate. It is not Bitpanda's exact margin formula and is not a return promise. Fees, gaps, execution and future conditions can differ substantially.",
    journal: "Journal",
    latestTrades: "My latest trades",
    result: "Result",
    tradeStatus: "Status",
    noTrades: "I have no trades yet.",
    safetyModel: "My safety model",
    portfolioBrakes: "Portfolio-wide brakes",
    allowAtMost: "I allow at most",
    simultaneousPositions: "simultaneous positions",
    newTradesPerDay: "new trades per day",
    closeDaily: "I close every open position each day",
    noOrderEndpoints: "I include no order, account, or transfer endpoint",
    paperLiquidationModel: "Liquidation prices are simulated estimates, not exchange quotes",
    system: "System",
    eventLog: "My event log",
    noEvents: "I have no events yet.",
    resetTitle: "Reset my paper accounts",
    resetCopy: "I delete only local simulations and start again with €1,000.",
    deleteData: "Delete paper data",
    loading: "Loading …",
    offlineDemo: "Offline demo",
    fusion: "Bitpanda Fusion",
    everySeconds: "every {count} seconds",
    simulationActive: "Simulation active",
    safetyError: "Safety error",
    sourceDemo: "I start safely with reproducible demo data. For Fusion, I provide an API key with Read permission only.",
    sourceFusion: "I use Fusion market data and never expose the API key to the dashboard.",
    waiting: "waiting",
    noClosedCandle: "I have not processed a closed candle yet.",
    longSetup: "Long setup",
    shortSetup: "Short setup",
    neutral: "Neutral",
    uptrend: "Uptrend",
    downtrend: "Downtrend",
    noTrend: "No confirmed trend",
    locked: "LOCKED",
    dailyStop: "DAILY STOP",
    cash: "Cash",
    openCount: "{count} open",
    openPositions: "Open positions",
    tradesToday: "Trades today",
    openRisk: "Open risk",
    effectiveLeverage: "Effective leverage",
    lastRun: "Last run",
    updated: "Updated {time}",
    long: "Long",
    short: "Short",
    open: "Open",
    closed: "Closed",
    backtestPeriod: "{from} to {to} · {bars} candles · {pairs} pairs",
    totalReturn: "Total return",
    maxDrawdown: "Max. drawdown",
    trades: "Trades",
    winRate: "Win rate",
    dailyStops: "Daily stops",
    liquidations: "Paper liquidations",
    maxPositions: "Max. positions",
    maxEffectiveLeverage: "Peak effective leverage",
    peakMarginUsage: "Peak margin usage",
    backtestChartTitle: "Multi-coin backtest",
    equalWeightHold: "Equal-weight hold",
    unavailable: "Unavailable",
    scanning: "I am scanning …",
    marketsProcessed: "{count} new markets processed.",
    backtesting: "I am running the backtest …",
    backtestDone: "I completed the multi-coin backtest.",
    resetConfirm: "Do I really want to delete every local multi-coin paper trade and balance?",
    resetDone: "I reset the paper accounts.",
    info: "info",
    warning: "warning",
    error: "error",
  },
  de: {
    pageTitle: "Multi-Coin Paper-Daytrader",
    edition: "Paper · Unraid-Ausgabe",
    paperOnly: "NUR PAPER",
    language: "Sprache",
    languageAria: "Sprache der Benutzeroberfläche",
    eyebrow: "Fünf Märkte. Ein gemeinsames Risikobudget.",
    heroTitle: "Krypto-Daytrading.<br /><span>Ohne Echtgeld.</span>",
    heroCopy: "Ich prüfe liquide EUR-Paare auf 15-Minuten-Signale und vergleiche Nur-Long mit simuliertem Long/Short-Hebel bis 10×. Ausführung, Margin und Liquidation bleiben vollständig Paper-only.",
    status: "Status",
    scanInterval: "Prüfintervall",
    dataSource: "Datenquelle",
    riskLimitsAria: "Meine Risikolimits",
    virtualCapital: "Virtuelles Kapital",
    perStrategy: "je Vergleichsstrategie",
    riskPerTrade: "Risiko je Trade",
    portfolioWide: "Ich berechne es portfolioweit",
    aggregateRisk: "Gesamtes offenes Risiko",
    acrossCoins: "über alle Coins",
    dailyLimit: "Tageslimit",
    acrossTrades: "über alle Trades",
    emergencyStop: "Not-Aus",
    untilReset: "bis zu meinem manuellen Reset",
    marketUniverse: "Mein Marktuniversum",
    selectedPairs: "Ausgewählte EUR-Paare",
    runScan: "Scan jetzt starten",
    runBacktest: "Multi-Coin-Backtest starten",
    scanner: "Scanner",
    latestSignals: "Meine neuesten Marktsignale",
    trendFilter: "15 Min. · 1-Std.-Trendfilter",
    liveSimulation: "Live-Simulation",
    paperPortfolios: "Meine Paper-Portfolios",
    notRun: "Ich habe noch keinen Scan ausgeführt",
    exposure: "Engagement",
    openPositionsTitle: "Meine offenen Paper-Positionen",
    strategy: "Strategie",
    pair: "Paar",
    side: "Richtung",
    notional: "Nominalwert",
    leverage: "Hebel",
    maxLeverage: "Max. Hebel",
    margin: "Paper-Margin",
    marginUsage: "Margin-Auslastung",
    liquidation: "Gesch. Liquidation",
    stop: "Stop",
    target: "Ziel",
    openPnl: "Offener G/V",
    noOpenPosition: "Ich habe keine offene Position.",
    performance: "Wertentwicklung",
    paperEquity: "Mein Paper-Kapital",
    chartAria: "Mein simulierter Kapitalverlauf",
    chartEmpty: "Ich beginne mit einem Paper-Scan oder Backtest.",
    historicalSimulation: "Historische Simulation",
    multiCoinBacktest: "Mein Multi-Coin-Backtest",
    backtestDisclaimer: "Dieser Backtest enthält eine börsenunabhängige Paper-Liquidationsschätzung. Sie ist nicht die exakte Bitpanda-Marginformel und kein Renditeversprechen. Gebühren, Gaps, Ausführung und künftige Marktbedingungen können erheblich abweichen.",
    journal: "Journal",
    latestTrades: "Meine neuesten Trades",
    result: "Ergebnis",
    tradeStatus: "Status",
    noTrades: "Ich habe noch keine Trades.",
    safetyModel: "Mein Sicherheitsmodell",
    portfolioBrakes: "Portfolioweite Bremsen",
    allowAtMost: "Ich erlaube höchstens",
    simultaneousPositions: "gleichzeitige Positionen",
    newTradesPerDay: "neue Trades pro Tag",
    closeDaily: "Ich schließe täglich jede offene Position",
    noOrderEndpoints: "Ich enthalte keinen Order-, Konto- oder Transfer-Endpunkt",
    paperLiquidationModel: "Liquidationspreise sind simulierte Schätzungen und keine Börsenkurse",
    system: "System",
    eventLog: "Mein Ereignisprotokoll",
    noEvents: "Ich habe noch keine Ereignisse.",
    resetTitle: "Meine Paper-Konten zurücksetzen",
    resetCopy: "Ich lösche nur lokale Simulationen und starte erneut mit 1.000 €.",
    deleteData: "Paper-Daten löschen",
    loading: "Wird geladen …",
    offlineDemo: "Offline-Demo",
    fusion: "Bitpanda Fusion",
    everySeconds: "alle {count} Sekunden",
    simulationActive: "Simulation aktiv",
    safetyError: "Sicherheitsfehler",
    sourceDemo: "Ich starte sicher mit reproduzierbaren Demo-Daten. Für Fusion verwende ich ausschließlich einen API-Schlüssel mit Leseberechtigung.",
    sourceFusion: "Ich verwende Fusion-Marktdaten und gebe den API-Schlüssel niemals an die WebUI weiter.",
    waiting: "wartet",
    noClosedCandle: "Ich habe noch keine abgeschlossene Kerze verarbeitet.",
    longSetup: "Long-Signal",
    shortSetup: "Short-Signal",
    neutral: "Neutral",
    uptrend: "Aufwärtstrend",
    downtrend: "Abwärtstrend",
    noTrend: "Kein bestätigter Trend",
    locked: "GESPERRT",
    dailyStop: "TAGESSTOPP",
    cash: "Cash",
    openCount: "{count} offen",
    openPositions: "Offene Positionen",
    tradesToday: "Trades heute",
    openRisk: "Offenes Risiko",
    effectiveLeverage: "Effektiver Hebel",
    lastRun: "Letzter Lauf",
    updated: "Aktualisiert {time}",
    long: "Long",
    short: "Short",
    open: "Offen",
    closed: "Geschlossen",
    backtestPeriod: "{from} bis {to} · {bars} Kerzen · {pairs} Paare",
    totalReturn: "Gesamtrendite",
    maxDrawdown: "Max. Drawdown",
    trades: "Trades",
    winRate: "Trefferquote",
    dailyStops: "Tagesstopps",
    liquidations: "Paper-Liquidationen",
    maxPositions: "Max. Positionen",
    maxEffectiveLeverage: "Spitzenwert eff. Hebel",
    peakMarginUsage: "Spitzenwert Margin-Auslastung",
    backtestChartTitle: "Multi-Coin-Backtest",
    equalWeightHold: "Gleichgewichtet halten",
    unavailable: "Nicht verfügbar",
    scanning: "Ich führe den Scan aus …",
    marketsProcessed: "{count} neue Märkte verarbeitet.",
    backtesting: "Ich führe den Backtest aus …",
    backtestDone: "Ich habe den Multi-Coin-Backtest abgeschlossen.",
    resetConfirm: "Möchte ich wirklich alle lokalen Multi-Coin-Paper-Trades und Kontostände löschen?",
    resetDone: "Ich habe die Paper-Konten zurückgesetzt.",
    info: "Info",
    warning: "Warnung",
    error: "Fehler",
  },
};

let euro;
let preciseEuro;
let microEuro;
let number;

function locale() {
  return state.language === "de" ? "de-DE" : "en-GB";
}

function resetFormatters() {
  euro = new Intl.NumberFormat(locale(), { style: "currency", currency: "EUR" });
  preciseEuro = new Intl.NumberFormat(locale(), {
    style: "currency", currency: "EUR", minimumFractionDigits: 4, maximumFractionDigits: 4
  });
  microEuro = new Intl.NumberFormat(locale(), {
    style: "currency", currency: "EUR", minimumFractionDigits: 6, maximumFractionDigits: 6
  });
  number = new Intl.NumberFormat(locale(), { maximumFractionDigits: 2 });
}

function t(key, values = {}) {
  let message = translations[state.language][key] ?? translations.en[key] ?? key;
  Object.entries(values).forEach(([name, value]) => {
    message = message.replaceAll("{" + name + "}", String(value));
  });
  return message;
}

function getStoredLanguage() {
  try {
    const value = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return supportedLanguages.has(value) ? value : null;
  } catch (_) {
    return null;
  }
}

function applyStaticTranslations() {
  document.title = t("pageTitle");
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.busyKey || element.dataset.i18n;
    element.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-html]").forEach((element) => {
    element.innerHTML = t(element.dataset.i18nHtml);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAria));
  });
}

function setLanguage(value, options = {}) {
  const language = supportedLanguages.has(value) ? value : "en";
  state.language = language;
  document.documentElement.lang = language;
  document.getElementById("languageSelect").value = language;
  resetFormatters();
  applyStaticTranslations();
  if (options.persist !== false) {
    try {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch (_) {
      // The language still changes when browser storage is unavailable.
    }
  }
  if (options.render !== false) renderAll();
}

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
  if (!response.ok) throw new Error(payload.detail || "HTTP " + response.status);
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
  return Number.isNaN(date.valueOf()) ? escapeHtml(value) : date.toLocaleString(locale());
}

function toast(message, isError = false) {
  const element = document.getElementById("toast");
  element.textContent = message;
  element.className = "toast visible" + (isError ? " error" : "");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { element.className = "toast"; }, 4500);
}

function setBusy(button, busy, busyKey) {
  if (busy) button.dataset.busyKey = busyKey;
  else delete button.dataset.busyKey;
  button.textContent = t(button.dataset.busyKey || button.dataset.i18n);
  button.disabled = busy;
}

function strategyLabel(strategyId, fallback) {
  if (strategyId === "long_only_1x") {
    return state.language === "de" ? "Nur Long · 1×" : "Long-only · 1×";
  }
  const match = String(strategyId || "").match(/^long_short_([0-9]+(?:p[0-9]+)?)x$/);
  if (match) {
    const leverage = match[1].replace("p", ".");
    return "Long/Short · max. " + leverage + "×";
  }
  return fallback || strategyId;
}

function backtestLabel(item) {
  if (item.strategy_id === "benchmark") return t("equalWeightHold");
  if (item.strategy_id) return strategyLabel(item.strategy_id, item.label);
  if (item.label === "Equal-weight hold" || item.label === "Gleichgewichtet halten") {
    return t("equalWeightHold");
  }
  return item.label;
}

function translateRuntimeText(value) {
  const text = String(value ?? "");
  if (state.language !== "de") return text;
  const exact = {
    "I do not have enough indicator data yet": "Ich habe noch nicht genügend Indikatordaten.",
    "Long setup": "Long-Signal",
    "Short setup": "Short-Signal",
    "Volume filter": "Volumenfilter",
    "I found no fresh EMA crossover": "Ich habe keine neue EMA-Kreuzung gefunden.",
    "I reset the multi-coin paper accounts.": "Ich habe die Multi-Coin-Paper-Konten zurückgesetzt.",
    "I reset only the local multi-coin paper accounts.": "Ich habe nur die lokalen Multi-Coin-Paper-Konten zurückgesetzt.",
    "I am already running a paper cycle.": "Ich führe bereits einen Paper-Zyklus aus.",
    "I have already processed every closed 15-minute candle.": "Ich habe bereits jede abgeschlossene 15-Minuten-Kerze verarbeitet.",
    "I received no market data for any configured pair.": "Ich habe für keines der konfigurierten Paare Marktdaten erhalten.",
    "I activated the daily limit": "Ich habe das Tageslimit aktiviert.",
    "I activated the emergency stop": "Ich habe den Not-Aus aktiviert.",
    "I activated the 10% emergency stop and require a reset.": "Ich habe den 10-%-Not-Aus aktiviert und benötige einen Reset.",
    "I reached the 10% total drawdown limit": "Ich habe das Gesamt-Drawdown-Limit von 10 % erreicht.",
    "Pair is not active on Bitpanda Fusion": "Das Paar ist auf Bitpanda Fusion nicht aktiv.",
    "Stop-Loss": "Stop-Loss",
    "Profit target": "Gewinnziel",
    "Daily position close": "Täglicher Positionsschluss",
    "EMA exit": "EMA-Ausstieg",
    "Overnight emergency exit": "Notausstieg vor dem Tageswechsel",
    "Simulated liquidation": "Simulierte Liquidation",
  };
  if (exact[text]) return exact[text];
  let match = text.match(/^I do not have enough candles for (.+)\.$/);
  if (match) return "Ich habe noch nicht genügend Kerzen für " + match[1] + ".";
  match = text.match(/^I activated the 2% daily limit on (.+)\.$/);
  if (match) return "Ich habe am " + match[1] + " das Tageslimit von 2 % aktiviert.";
  match = text.match(/^I could not load market data for (.+): (.+)$/);
  if (match) return "Ich konnte die Marktdaten für " + match[1] + " nicht laden: " + match[2];
  match = text.match(/^(.+) closed before the trading day$/);
  if (match) return match[1] + " vor dem Handelstag geschlossen";
  return text;
}

function portfolioPosition(value) {
  if (value === "Cash") return t("cash");
  const match = String(value ?? "").match(/^(\d+) open$/);
  return match ? t("openCount", { count: match[1] }) : translateRuntimeText(value);
}

function tradeStatus(value) {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized === "open") return t("open");
  if (normalized === "closed") return t("closed");
  return translateRuntimeText(value);
}

function renderConfig() {
  const c = state.config;
  if (!c) return;
  document.getElementById("capital").textContent = euro.format(c.starting_capital);
  document.getElementById("tradeRisk").textContent = number.format(c.risk_per_trade * 100) + " % · " + euro.format(c.risk_amount);
  document.getElementById("aggregateRisk").textContent = number.format(c.max_aggregate_risk * 100) + " % · " + euro.format(c.aggregate_risk_amount);
  document.getElementById("dailyRisk").textContent = number.format(c.max_daily_loss * 100) + " % · " + euro.format(c.daily_loss_amount);
  document.getElementById("hardStop").textContent = number.format(c.hard_drawdown * 100) + " %";
  document.getElementById("dataSource").textContent = c.data_source === "demo" ? t("offlineDemo") : t("fusion");
  document.getElementById("nextRun").textContent = t("everySeconds", { count: c.poll_seconds });
  document.getElementById("systemStatus").textContent = c.paper_only ? t("simulationActive") : t("safetyError");
  document.getElementById("maxPositions").textContent = c.max_open_positions;
  document.getElementById("maxTrades").textContent = c.max_trades_per_day;
  document.getElementById("pairChips").innerHTML = c.pairs.map((pair) => "<span>" + escapeHtml(pair) + "</span>").join("");
  document.getElementById("sourceHint").textContent = c.data_source === "demo" ? t("sourceDemo") : t("sourceFusion");
}

function renderMarkets() {
  if (!state.status || !state.config) return;
  const rows = state.status.markets || [];
  const byPair = Object.fromEntries(rows.map((item) => [item.pair, item]));
  document.getElementById("marketGrid").innerHTML = state.config.pairs.map((pair) => {
    const item = byPair[pair];
    if (!item) {
      return "<article class=\"market-card pending\"><div><strong>" + escapeHtml(pair) +
        "</strong><span>" + escapeHtml(t("waiting")) + "</span></div><p>" +
        escapeHtml(t("noClosedCandle")) + "</p></article>";
    }
    const signal = item.signal > 0 ? t("longSetup") : item.signal < 0 ? t("shortSetup") : t("neutral");
    const trend = item.trend > 0 ? t("uptrend") : item.trend < 0 ? t("downtrend") : t("noTrend");
    const signalClass = item.signal > 0 ? "positive" : item.signal < 0 ? "negative" : "muted";
    return "<article class=\"market-card\">" +
      "<div><strong>" + escapeHtml(pair) + "</strong><span class=\"" + signalClass + "\">" + escapeHtml(signal) + "</span></div>" +
      "<b>" + escapeHtml(formatMarketPrice(item.price)) + "</b>" +
      "<p>" + escapeHtml(trend) + " · RSI " + escapeHtml(number.format(item.rsi)) + "</p>" +
      "<small>" + escapeHtml(translateRuntimeText(item.reason)) + " · " + escapeHtml(formatTime(item.candle_time)) + "</small>" +
      "</article>";
  }).join("");
}

function renderPortfolios() {
  if (!state.status || !state.config) return;
  const portfolios = state.status.portfolios || [];
  document.getElementById("portfolioGrid").innerHTML = portfolios.map((item) => {
    const resultClass = item.pnl >= 0 ? "positive" : "negative";
    const locked = Boolean(item.hard_locked);
    const dayLocked = Boolean(item.daily_locked);
    const badge = locked ? t("locked") : dayLocked ? t("dailyStop") : portfolioPosition(item.position);
    const label = strategyLabel(item.strategy_id, item.label);
    return "<article class=\"portfolio-card\" style=\"--accent:" + escapeHtml(item.color) + "\">" +
      "<div class=\"portfolio-top\"><strong>" + escapeHtml(label) + "</strong><span class=\"position-tag\">" + escapeHtml(badge) + "</span></div>" +
      "<div class=\"portfolio-value\">" + escapeHtml(euro.format(item.equity)) + "</div>" +
      "<div class=\"portfolio-return " + resultClass + "\">" + (item.pnl >= 0 ? "+" : "") + escapeHtml(euro.format(item.pnl)) + " · " + escapeHtml(number.format(item.return_pct)) + " %</div>" +
      "<div class=\"portfolio-details\">" +
        "<div><small>" + escapeHtml(t("openPositions")) + "</small><strong>" + item.position_count + "/" + state.config.max_open_positions + "</strong></div>" +
        "<div><small>" + escapeHtml(t("tradesToday")) + "</small><strong>" + item.trades_today + "/" + state.config.max_trades_per_day + "</strong></div>" +
        "<div><small>" + escapeHtml(t("notional")) + "</small><strong>" + escapeHtml(euro.format(item.notional)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("openRisk")) + "</small><strong>" + escapeHtml(euro.format(item.open_risk)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("effectiveLeverage")) + "</small><strong>" + escapeHtml(number.format(item.effective_leverage)) + "× / " + escapeHtml(number.format(item.max_leverage)) + "×</strong></div>" +
        "<div><small>" + escapeHtml(t("margin")) + "</small><strong>" + escapeHtml(euro.format(item.margin_required)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("marginUsage")) + "</small><strong>" + escapeHtml(number.format(item.margin_utilization_pct)) + " %</strong></div>" +
        "<div><small>" + escapeHtml(t("lastRun")) + "</small><strong>" + escapeHtml(formatTime(item.last_run_at)) + "</strong></div>" +
      "</div>" +
      (locked ? "<p class=\"negative\">" + escapeHtml(translateRuntimeText(item.lock_reason)) + "</p>" : "") +
      "</article>";
  }).join("");
  const dated = portfolios.map((item) => item.last_run_at).filter(Boolean).sort();
  document.getElementById("lastUpdate").textContent = dated.length
    ? t("updated", { time: formatTime(dated.at(-1)) })
    : t("notRun");
}

function renderPositions() {
  if (!state.status) return;
  const positions = state.status.positions || [];
  const labels = Object.fromEntries((state.status.portfolios || []).map((p) => [
    p.strategy_id,
    strategyLabel(p.strategy_id, p.label),
  ]));
  document.getElementById("positionRows").innerHTML = positions.length ? positions.map((item) => {
    const pnlClass = item.unrealized_pnl >= 0 ? "positive" : "negative";
    const liquidation = item.liquidation_price == null ? "–" : formatMarketPrice(item.liquidation_price);
    return "<tr><td>" + escapeHtml(labels[item.strategy_id] || item.strategy_id) +
      "</td><td>" + escapeHtml(item.pair) +
      "</td><td>" + escapeHtml(item.side === "long" ? t("long") : t("short")) +
      "</td><td>" + escapeHtml(euro.format(item.notional)) +
      "</td><td>" + escapeHtml(number.format(item.max_leverage)) + "×" +
      "</td><td>" + escapeHtml(euro.format(item.margin_required)) +
      "</td><td>" + escapeHtml(liquidation) +
      "</td><td>" + escapeHtml(formatMarketPrice(item.stop_price)) +
      "</td><td>" + escapeHtml(formatMarketPrice(item.take_profit)) +
      "</td><td class=\"" + pnlClass + "\">" + escapeHtml(euro.format(item.unrealized_pnl)) + "</td></tr>";
  }).join("") : "<tr><td colspan=\"10\" class=\"muted\">" + escapeHtml(t("noOpenPosition")) + "</td></tr>";
}

function renderTrades() {
  if (!state.status) return;
  const rows = state.status.trades || [];
  const labels = Object.fromEntries((state.status.portfolios || []).map((p) => [
    p.strategy_id,
    strategyLabel(p.strategy_id, p.label),
  ]));
  document.getElementById("tradeRows").innerHTML = rows.length ? rows.slice(0, 16).map((trade) => {
    const pnl = trade.pnl == null ? "–" : euro.format(trade.pnl);
    const pnlClass = trade.pnl == null ? "" : trade.pnl >= 0 ? "positive" : "negative";
    return "<tr><td>" + escapeHtml(labels[trade.strategy_id] || trade.strategy_id) +
      "</td><td>" + escapeHtml(trade.pair) +
      "</td><td>" + escapeHtml(trade.side === "long" ? t("long") : t("short")) +
      "</td><td class=\"" + pnlClass + "\">" + escapeHtml(pnl) +
      "</td><td>" + escapeHtml(tradeStatus(trade.status)) + "</td></tr>";
  }).join("") : "<tr><td colspan=\"5\" class=\"muted\">" + escapeHtml(t("noTrades")) + "</td></tr>";
}

function renderEvents() {
  if (!state.status) return;
  const events = state.status.events || [];
  document.getElementById("eventList").innerHTML = events.length ? events.slice(0, 18).map((event) =>
    "<div class=\"event\"><span class=\"event-level " + escapeHtml(event.level) + "\">" +
    escapeHtml(t(event.level)) + "</span><span>" + escapeHtml(translateRuntimeText(event.message)) +
    "</span><time>" + escapeHtml(formatTime(event.created_at)) + "</time></div>"
  ).join("") : "<p class=\"muted\">" + escapeHtml(t("noEvents")) + "</p>";
}

function renderBacktest() {
  const result = state.backtest;
  if (!result || result.status !== "ok") return;
  document.getElementById("backtestSection").hidden = false;
  document.getElementById("backtestPeriod").textContent = t("backtestPeriod", {
    from: formatTime(result.from),
    to: formatTime(result.to),
    bars: result.bars,
    pairs: result.pairs.length,
  });
  const cards = [...result.strategies, result.benchmark];
  document.getElementById("backtestGrid").innerHTML = cards.map((item) => {
    const returnClass = item.total_return_pct >= 0 ? "positive" : "negative";
    return "<article class=\"backtest-card\" style=\"border-top:2px solid " + escapeHtml(item.color) + "\">" +
      "<span>" + escapeHtml(backtestLabel(item)) + "</span><strong>" + escapeHtml(euro.format(item.final_equity)) + "</strong>" +
      "<div class=\"mini-stats\">" +
        "<div><span>" + escapeHtml(t("totalReturn")) + "</span><b class=\"" + returnClass + "\">" + escapeHtml(number.format(item.total_return_pct)) + " %</b></div>" +
        "<div><span>" + escapeHtml(t("maxDrawdown")) + "</span><b class=\"negative\">" + escapeHtml(number.format(item.max_drawdown_pct)) + " %</b></div>" +
        "<div><span>" + escapeHtml(t("maxLeverage")) + "</span><b>" + escapeHtml(number.format(item.max_leverage ?? 1)) + "×</b></div>" +
        "<div><span>" + escapeHtml(t("maxEffectiveLeverage")) + "</span><b>" + (item.max_effective_leverage == null ? "–" : escapeHtml(number.format(item.max_effective_leverage)) + "×") + "</b></div>" +
        "<div><span>" + escapeHtml(t("peakMarginUsage")) + "</span><b>" + (item.max_margin_utilization_pct == null ? "–" : escapeHtml(number.format(item.max_margin_utilization_pct)) + " %") + "</b></div>" +
        "<div><span>" + escapeHtml(t("trades")) + "</span><b>" + (item.trades ?? "–") + "</b></div>" +
        "<div><span>" + escapeHtml(t("winRate")) + "</span><b>" + (item.win_rate_pct == null ? "–" : escapeHtml(number.format(item.win_rate_pct)) + " %") + "</b></div>" +
        "<div><span>" + escapeHtml(t("liquidations")) + "</span><b>" + (item.liquidations ?? "–") + "</b></div>" +
        "<div><span>" + escapeHtml(t("dailyStops")) + "</span><b>" + (item.daily_limit_hits ?? "–") + "</b></div>" +
        "<div><span>" + escapeHtml(t("maxPositions")) + "</span><b>" + (item.max_positions ?? "–") + "</b></div>" +
      "</div></article>";
  }).join("");
  const series = cards.map((item) => ({
    label: backtestLabel(item),
    color: item.color,
    points: item.curve,
  }));
  document.getElementById("chartTitle").textContent = t("backtestChartTitle");
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
  const padding = Math.max((max - min) * 0.12, 5);
  min -= padding;
  max += padding;
  const x0 = 62;
  const x1 = 980;
  const y0 = 18;
  const y1 = 282;
  const y = (value) => y1 - ((value - min) / (max - min || 1)) * (y1 - y0);
  const parts = [];
  for (let i = 0; i <= 4; i += 1) {
    const yy = y0 + ((y1 - y0) * i / 4);
    const label = max - ((max - min) * i / 4);
    parts.push("<line class=\"chart-grid\" x1=\"" + x0 + "\" y1=\"" + yy + "\" x2=\"" + x1 + "\" y2=\"" + yy + "\"/>" +
      "<text class=\"chart-label\" x=\"0\" y=\"" + (yy + 5) + "\">" + Math.round(label) + " €</text>");
  }
  valid.forEach((item) => {
    const coordinates = item.points.map((point, index) => {
      const xx = x0 + (index / (item.points.length - 1)) * (x1 - x0);
      return xx.toFixed(2) + "," + y(Number(point.equity)).toFixed(2);
    }).join(" ");
    parts.push("<polyline class=\"chart-line\" stroke=\"" + escapeHtml(item.color) + "\" points=\"" + coordinates + "\"/>");
  });
  svg.innerHTML = parts.join("");
  svg.style.display = "block";
  empty.style.display = "none";
  document.getElementById("chartLegend").innerHTML = valid.map((item) =>
    "<span><i style=\"background:" + escapeHtml(item.color) + "\"></i>" + escapeHtml(item.label) + "</span>"
  ).join("");
}

function renderPaperChart() {
  if (!state.status) return;
  const labels = Object.fromEntries((state.status.portfolios || []).map((p) => [p.strategy_id, p]));
  const series = Object.entries(state.status.curves || {}).map(([id, points]) => ({
    label: strategyLabel(id, labels[id]?.label || id),
    color: labels[id]?.color || "#fff",
    points,
  }));
  document.getElementById("chartTitle").textContent = t("paperEquity");
  drawChart(series);
}

function renderAll() {
  renderConfig();
  renderMarkets();
  renderPortfolios();
  renderPositions();
  renderTrades();
  renderEvents();
  if (state.backtest) renderBacktest();
  else renderPaperChart();
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
      requestJson("/api/config"),
      requestJson("/api/status"),
    ]);
    const selectedLanguage = getStoredLanguage() || state.config.app_language || "en";
    setLanguage(selectedLanguage, { persist: false, render: false });
    renderAll();
  } catch (error) {
    document.getElementById("systemStatus").textContent = t("unavailable");
    toast(translateRuntimeText(error.message), true);
  }
}

document.getElementById("languageSelect").addEventListener("change", (event) => {
  setLanguage(event.currentTarget.value);
});

document.getElementById("runButton").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  setBusy(button, true, "scanning");
  try {
    const result = await requestJson("/api/paper/run", { method: "POST" });
    toast(result.status === "ok"
      ? t("marketsProcessed", { count: result.new_pairs.length })
      : translateRuntimeText(result.message));
    state.backtest = null;
    document.getElementById("backtestSection").hidden = true;
    await refreshStatus();
  } catch (error) {
    toast(translateRuntimeText(error.message), true);
  } finally {
    setBusy(button, false);
  }
});

document.getElementById("backtestButton").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  setBusy(button, true, "backtesting");
  try {
    state.backtest = await requestJson("/api/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bars: Math.min(1000, state.config.backtest_bars) }),
    });
    renderBacktest();
    toast(t("backtestDone"));
  } catch (error) {
    toast(translateRuntimeText(error.message), true);
  } finally {
    setBusy(button, false);
  }
});

document.getElementById("resetButton").addEventListener("click", async () => {
  if (!window.confirm(t("resetConfirm"))) return;
  try {
    await requestJson("/api/reset?confirm=RESET", { method: "POST" });
    state.backtest = null;
    document.getElementById("backtestSection").hidden = true;
    await refreshStatus();
    toast(t("resetDone"));
  } catch (error) {
    toast(translateRuntimeText(error.message), true);
  }
});

setLanguage(getStoredLanguage() || "en", { persist: false, render: false });
initialize();
window.setInterval(() => refreshStatus().catch(() => {}), 30_000);
