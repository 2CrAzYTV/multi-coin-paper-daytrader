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
    pageTitle: "Multi-Coin Paper Trader",
    edition: "Paper · Unraid Edition",
    paperOnly: "PAPER ONLY",
    language: "Language",
    languageAria: "Dashboard language",
    eyebrow: "Spot only. Real fees. One strategy.",
    heroTitle: "Crypto trend following.<br /><span>Without real money.</span>",
    heroCopy: "I check the most liquid EUR pairs once per daily candle. I buy a close above the 55-day high and sell a close below the 20-day low - long only, no leverage, with Bitpanda Fusion fees and order-book prices.",
    status: "Status",
    scanInterval: "Scan interval",
    dataSource: "Data source",
    riskLimitsAria: "My trading costs and rules",
    virtualCapital: "Virtual capital",
    oneAccount: "one spot account",
    feePerOrder: "Fee per order",
    fusionTier: "Fusion entry tier",
    roundTrip: "Round-trip cost",
    feesAndSlippage: "fees + slippage, buy and sell",
    positionSize: "Position size",
    ofEquity: "of equity, min. exchange order",
    channels: "Channels",
    entryExit: "entry high / exit low",
    marketUniverse: "My market universe",
    selectedPairs: "Selected EUR pairs",
    runScan: "Run scan now",
    runBacktest: "Run 4-year backtest",
    scanner: "Scanner",
    latestSignals: "My latest market signals",
    intervalHint: "{interval} candles · {entry}/{exit} channel",
    liveSimulation: "Live simulation",
    paperPortfolios: "My paper account",
    notRun: "I have not run a scan yet",
    exposure: "Exposure",
    openPositionsTitle: "My open paper positions",
    pair: "Pair",
    entryPrice: "Entry",
    exitPrice: "Exit",
    lastPrice: "Last",
    notional: "Value",
    exitBelow: "Sell below",
    openPnl: "Open P&L",
    since: "Since",
    noOpenPosition: "I have no open position.",
    performance: "Performance",
    paperEquity: "My paper equity",
    chartAria: "My simulated equity history",
    chartEmpty: "I start with a paper scan or backtest.",
    historicalSimulation: "Historical simulation",
    multiCoinBacktest: "My backtest with real costs",
    backtestDisclaimer: "I do not treat a backtest as a return promise. Four years contain only a few dozen trades, and future market conditions can differ substantially. The tax model is simplified and not tax advice.",
    journal: "Journal",
    latestTrades: "My latest trades",
    result: "Result",
    tradeStatus: "Status",
    noTrades: "I have no trades yet.",
    safetyModel: "My safety model",
    portfolioBrakes: "How I stay realistic",
    ruleSpot: "Spot only: no short selling, no leverage, never more than the cash I hold",
    ruleFees: "Fees on every order and prices from the real order book",
    ruleMinOrder: "Exchange minimum order sizes and size increments",
    allowAtMost: "I hold at most",
    simultaneousPositions: "positions at the same time",
    noOrderEndpoints: "I include no order, account, or transfer endpoint",
    system: "System",
    eventLog: "My event log",
    noEvents: "I have no events yet.",
    resetTitle: "Reset my paper account",
    resetCopy: "I delete only local simulations and start again with {capital}.",
    deleteData: "Delete paper data",
    loading: "Loading …",
    offlineDemo: "Offline demo",
    fusion: "Bitpanda Fusion",
    everySeconds: "every {count} seconds",
    simulationActive: "Simulation active",
    safetyError: "Safety error",
    sourceDemo: "I start safely with reproducible demo data. For Fusion, I provide an API key with Read permission only.",
    sourceFusion: "I use Fusion market data and the read-only order book, and never expose the API key to the dashboard.",
    waiting: "waiting",
    noClosedCandle: "I have not processed a closed candle yet.",
    buySignal: "Buy signal",
    sellSignal: "Sell signal",
    neutral: "No signal",
    breakoutAbove: "Buy above {price} ({distance})",
    exitUnder: "Sell below {price}",
    cash: "Cash",
    invested: "Invested",
    openPositions: "Positions",
    feesPaid: "Fees paid",
    drawdownNow: "Drawdown",
    closedTrades: "Closed trades",
    winRate: "Win rate",
    lastRun: "Last run",
    taxYear: "Tax {year} (estimate)",
    afterTax: "After tax",
    taxFreeFrom: "Tax-free from",
    taxable: "taxable",
    taxFree: "tax-free",
    heldDays: "{days} days",
    preTax: "Before tax",
    taxesPaid: "Taxes paid",
    cagrAfterTax: "Per year after tax",
    ruleTax: "German tax: sales within 1 year at {rate}, Freigrenze {limit} per year, loss carryforward; after 1 year tax-free",
    updated: "Updated {time}",
    open: "Open",
    closed: "Closed",
    backtestPeriod: "{from} to {to} · {bars} candles · {pairs} pairs · fee {fee} per order",
    totalReturn: "Total return",
    cagr: "Per year",
    maxDrawdown: "Max. drawdown",
    trades: "Trades",
    timeInvested: "Time invested",
    backtestChartTitle: "Backtest equity",
    equalWeightHold: "Buy and hold (equal weight)",
    strategyName: "Trend following · {entry}/{exit} breakout",
    unavailable: "Unavailable",
    scanning: "I am scanning …",
    marketsProcessed: "{count} new candles processed.",
    backtesting: "I am running the backtest …",
    backtestDone: "I completed the backtest.",
    resetConfirm: "Do I really want to delete every local paper trade and balance?",
    resetDone: "I reset the paper account.",
    info: "info",
    warning: "warning",
    error: "error",
  },
  de: {
    pageTitle: "Multi-Coin Paper-Trader",
    edition: "Paper · Unraid-Ausgabe",
    paperOnly: "NUR PAPER",
    language: "Sprache",
    languageAria: "Sprache der Benutzeroberfläche",
    eyebrow: "Nur Spot. Echte Gebühren. Eine Strategie.",
    heroTitle: "Krypto-Trendfolge.<br /><span>Ohne Echtgeld.</span>",
    heroCopy: "Ich prüfe die liquidesten EUR-Paare einmal pro Tageskerze. Ich kaufe, wenn der Kurs über dem 55-Tage-Hoch schließt, und verkaufe, wenn er unter dem 20-Tage-Tief schließt – nur Long, ohne Hebel, mit Bitpanda-Fusion-Gebühren und Orderbuch-Preisen.",
    status: "Status",
    scanInterval: "Prüfintervall",
    dataSource: "Datenquelle",
    riskLimitsAria: "Meine Kosten und Regeln",
    virtualCapital: "Virtuelles Kapital",
    oneAccount: "ein Spot-Konto",
    feePerOrder: "Gebühr je Order",
    fusionTier: "Fusion-Einstiegsstufe",
    roundTrip: "Kosten Kauf + Verkauf",
    feesAndSlippage: "Gebühren + Slippage, beide Seiten",
    positionSize: "Positionsgröße",
    ofEquity: "des Kapitals, mind. Börsenminimum",
    channels: "Kanäle",
    entryExit: "Einstiegs-Hoch / Ausstiegs-Tief",
    marketUniverse: "Mein Marktuniversum",
    selectedPairs: "Ausgewählte EUR-Paare",
    runScan: "Scan jetzt starten",
    runBacktest: "4-Jahres-Backtest starten",
    scanner: "Scanner",
    latestSignals: "Meine neuesten Marktsignale",
    intervalHint: "{interval}-Kerzen · Kanal {entry}/{exit}",
    liveSimulation: "Live-Simulation",
    paperPortfolios: "Mein Paper-Konto",
    notRun: "Ich habe noch keinen Scan ausgeführt",
    exposure: "Engagement",
    openPositionsTitle: "Meine offenen Paper-Positionen",
    pair: "Paar",
    entryPrice: "Einstieg",
    exitPrice: "Ausstieg",
    lastPrice: "Aktuell",
    notional: "Wert",
    exitBelow: "Verkauf unter",
    openPnl: "Offener G/V",
    since: "Seit",
    noOpenPosition: "Ich habe keine offene Position.",
    performance: "Wertentwicklung",
    paperEquity: "Mein Paper-Kapital",
    chartAria: "Mein simulierter Kapitalverlauf",
    chartEmpty: "Ich beginne mit einem Paper-Scan oder Backtest.",
    historicalSimulation: "Historische Simulation",
    multiCoinBacktest: "Mein Backtest mit echten Kosten",
    backtestDisclaimer: "Ich behandle einen Backtest nicht als Renditeversprechen. Vier Jahre enthalten nur einige Dutzend Trades, und künftige Marktbedingungen können erheblich abweichen. Das Steuermodell ist vereinfacht und keine Steuerberatung.",
    journal: "Journal",
    latestTrades: "Meine neuesten Trades",
    result: "Ergebnis",
    tradeStatus: "Status",
    noTrades: "Ich habe noch keine Trades.",
    safetyModel: "Mein Sicherheitsmodell",
    portfolioBrakes: "So bleibe ich realistisch",
    ruleSpot: "Nur Spot: kein Leerverkauf, kein Hebel, nie mehr als das vorhandene Guthaben",
    ruleFees: "Gebühren auf jede Order und Preise aus dem echten Orderbuch",
    ruleMinOrder: "Mindestordergrößen und Stückelung der Börse",
    allowAtMost: "Ich halte höchstens",
    simultaneousPositions: "Positionen gleichzeitig",
    noOrderEndpoints: "Ich enthalte keinen Order-, Konto- oder Transfer-Endpunkt",
    system: "System",
    eventLog: "Mein Ereignisprotokoll",
    noEvents: "Ich habe noch keine Ereignisse.",
    resetTitle: "Mein Paper-Konto zurücksetzen",
    resetCopy: "Ich lösche nur lokale Simulationen und starte erneut mit {capital}.",
    deleteData: "Paper-Daten löschen",
    loading: "Wird geladen …",
    offlineDemo: "Offline-Demo",
    fusion: "Bitpanda Fusion",
    everySeconds: "alle {count} Sekunden",
    simulationActive: "Simulation aktiv",
    safetyError: "Sicherheitsfehler",
    sourceDemo: "Ich starte sicher mit reproduzierbaren Demo-Daten. Für Fusion verwende ich ausschließlich einen API-Schlüssel mit Leseberechtigung.",
    sourceFusion: "Ich verwende Fusion-Marktdaten und das Orderbuch nur lesend und gebe den API-Schlüssel niemals an die WebUI weiter.",
    waiting: "wartet",
    noClosedCandle: "Ich habe noch keine abgeschlossene Kerze verarbeitet.",
    buySignal: "Kaufsignal",
    sellSignal: "Verkaufssignal",
    neutral: "Kein Signal",
    breakoutAbove: "Kauf über {price} ({distance})",
    exitUnder: "Verkauf unter {price}",
    cash: "Guthaben",
    invested: "Investiert",
    openPositions: "Positionen",
    feesPaid: "Gezahlte Gebühren",
    drawdownNow: "Drawdown",
    closedTrades: "Abgeschlossene Trades",
    winRate: "Trefferquote",
    lastRun: "Letzter Lauf",
    taxYear: "Steuer {year} (geschätzt)",
    afterTax: "Nach Steuern",
    taxFreeFrom: "Steuerfrei ab",
    taxable: "steuerpflichtig",
    taxFree: "steuerfrei",
    heldDays: "{days} Tage",
    preTax: "Vor Steuern",
    taxesPaid: "Gezahlte Steuern",
    cagrAfterTax: "Pro Jahr nach Steuern",
    ruleTax: "Steuer: Verkauf innerhalb 1 Jahr mit {rate}, Freigrenze {limit} pro Jahr, Verlustvortrag; nach 1 Jahr steuerfrei",
    updated: "Aktualisiert {time}",
    open: "Offen",
    closed: "Geschlossen",
    backtestPeriod: "{from} bis {to} · {bars} Kerzen · {pairs} Paare · Gebühr {fee} je Order",
    totalReturn: "Gesamtrendite",
    cagr: "Pro Jahr",
    maxDrawdown: "Max. Drawdown",
    trades: "Trades",
    timeInvested: "Zeit investiert",
    backtestChartTitle: "Backtest-Kapitalverlauf",
    equalWeightHold: "Kaufen und halten (gleichgewichtet)",
    strategyName: "Trendfolge · Ausbruch {entry}/{exit}",
    unavailable: "Nicht verfügbar",
    scanning: "Ich führe den Scan aus …",
    marketsProcessed: "{count} neue Kerzen verarbeitet.",
    backtesting: "Ich führe den Backtest aus …",
    backtestDone: "Ich habe den Backtest abgeschlossen.",
    resetConfirm: "Möchte ich wirklich alle lokalen Paper-Trades und Kontostände löschen?",
    resetDone: "Ich habe das Paper-Konto zurückgesetzt.",
    info: "Info",
    warning: "Warnung",
    error: "Fehler",
  },
};

let euro;
let preciseEuro;
let microEuro;
let number;
let percent;

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
  percent = new Intl.NumberFormat(locale(), { style: "percent", maximumFractionDigits: 2 });
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

function signedEuro(value) {
  const amount = Number(value) || 0;
  return (amount >= 0 ? "+" : "") + euro.format(amount);
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

function formatDate(value) {
  if (!value) return "–";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? escapeHtml(value) : date.toLocaleDateString(locale());
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

function strategyName() {
  const c = state.config || { entry_window: 55, exit_window: 20 };
  return t("strategyName", { entry: c.entry_window, exit: c.exit_window });
}

function translateRuntimeText(value) {
  const text = String(value ?? "");
  if (state.language !== "de") return text;
  const exact = {
    "I do not have enough candles yet": "Ich habe noch nicht genügend Kerzen.",
    "Breakout above the entry channel": "Ausbruch über den Einstiegskanal",
    "Close below the exit channel": "Schluss unter dem Ausstiegskanal",
    "Inside the channel": "Innerhalb des Kanals",
    "Exit channel broken": "Ausstiegskanal unterschritten",
    "I reset the paper account.": "Ich habe das Paper-Konto zurückgesetzt.",
    "I reset only the local paper account.": "Ich habe nur das lokale Paper-Konto zurückgesetzt.",
    "I am already running a paper cycle.": "Ich führe bereits einen Paper-Zyklus aus.",
    "I have already processed every closed candle.": "Ich habe bereits jede abgeschlossene Kerze verarbeitet.",
    "I received no market data for any configured pair.": "Ich habe für keines der konfigurierten Paare Marktdaten erhalten.",
    "Pair is not active on Bitpanda Fusion": "Das Paar ist auf Bitpanda Fusion nicht aktiv.",
  };
  if (exact[text]) return exact[text];
  let match = text.match(/^I do not have enough candles for (.+)\.$/);
  if (match) return "Ich habe noch nicht genügend Kerzen für " + match[1] + ".";
  match = text.match(/^I could not load market data for (.+): (.+)$/);
  if (match) return "Ich konnte die Marktdaten für " + match[1] + " nicht laden: " + match[2];
  match = text.match(/^(\d+) new market candles processed: (.+)\.$/);
  if (match) return match[1] + " neue Kerzen verarbeitet: " + match[2] + ".";
  match = text.match(/^Paper buy (.+): ([\d.]+) EUR at ([\d.e+-]+) \(fee ([\d.]+) EUR, (order_book|candle)\)\.$/);
  if (match) return "Paper-Kauf " + match[1] + ": " + match[2] + " EUR zu " + match[3] + " (Gebühr " + match[4] + " EUR, " + (match[5] === "order_book" ? "Orderbuch" : "Kerze") + ").";
  match = text.match(/^Paper sell (.+): ([+-][\d.]+) EUR after fees \((order_book|candle)\)\.$/);
  if (match) return "Paper-Verkauf " + match[1] + ": " + match[2] + " EUR nach Gebühren (" + (match[3] === "order_book" ? "Orderbuch" : "Kerze") + ").";
  match = text.match(/^(.+) signal skipped: not enough cash for the minimum order\.$/);
  if (match) return match[1] + ": Signal übersprungen, Guthaben reicht nicht für die Mindestorder.";
  match = text.match(/^Tax (\d{4}): ([\d.-]+) EUR on a taxable result of ([\d.-]+) EUR \(loss carryforward ([\d.-]+) EUR\)\.$/);
  if (match) return "Steuer " + match[1] + ": " + match[2] + " EUR auf ein steuerpflichtiges Ergebnis von " + match[3] + " EUR (Verlustvortrag " + match[4] + " EUR).";
  match = text.match(/^(.+) is skipped because it is not active\.$/);
  if (match) return match[1] + " wird übersprungen, weil das Paar nicht aktiv ist.";
  return text;
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
  document.getElementById("feeRate").textContent = percent.format(c.fee_rate);
  document.getElementById("roundTrip").textContent = "≈ " + percent.format(c.round_trip_cost);
  document.getElementById("positionSize").textContent = "1/" + c.pairs.length + " · " + percent.format(c.position_share);
  document.getElementById("channels").textContent = c.entry_window + " / " + c.exit_window;
  document.getElementById("dataSource").textContent = c.data_source === "demo" ? t("offlineDemo") : t("fusion");
  document.getElementById("nextRun").textContent = t("everySeconds", { count: c.poll_seconds });
  document.getElementById("systemStatus").textContent = c.paper_only ? t("simulationActive") : t("safetyError");
  document.getElementById("maxPositions").textContent = c.max_open_positions;
  document.getElementById("intervalHint").textContent = t("intervalHint", {
    interval: c.candle_interval, entry: c.entry_window, exit: c.exit_window,
  });
  document.getElementById("pairChips").innerHTML = c.pairs.map((pair) => "<span>" + escapeHtml(pair) + "</span>").join("");
  document.getElementById("sourceHint").textContent = c.data_source === "demo" ? t("sourceDemo") : t("sourceFusion");
  document.getElementById("resetCopy").textContent = t("resetCopy", { capital: euro.format(c.starting_capital) });
  document.getElementById("ruleTax").textContent = t("ruleTax", {
    rate: percent.format(c.tax_rate), limit: euro.format(c.tax_free_limit),
  });
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
    const signal = item.signal > 0 ? t("buySignal") : item.signal < 0 ? t("sellSignal") : t("neutral");
    const signalClass = item.signal > 0 ? "positive" : item.signal < 0 ? "negative" : "muted";
    const distance = item.price > 0 && item.entry_level > 0 ? (item.entry_level / item.price - 1) : 0;
    return "<article class=\"market-card\">" +
      "<div><strong>" + escapeHtml(pair) + "</strong><span class=\"" + signalClass + "\">" + escapeHtml(signal) + "</span></div>" +
      "<b>" + escapeHtml(formatMarketPrice(item.price)) + "</b>" +
      "<p>" + escapeHtml(t("breakoutAbove", { price: formatMarketPrice(item.entry_level), distance: (distance >= 0 ? "+" : "") + percent.format(distance) })) + "</p>" +
      "<p>" + escapeHtml(t("exitUnder", { price: formatMarketPrice(item.exit_level) })) + "</p>" +
      "<small>" + escapeHtml(translateRuntimeText(item.reason)) + " · " + escapeHtml(formatDate(item.candle_time)) + "</small>" +
      "</article>";
  }).join("");
}

function renderPortfolios() {
  if (!state.status || !state.config) return;
  const portfolios = state.status.portfolios || [];
  document.getElementById("portfolioGrid").innerHTML = portfolios.map((item) => {
    const resultClass = item.pnl >= 0 ? "positive" : "negative";
    return "<article class=\"portfolio-card\" style=\"--accent:" + escapeHtml(item.color) + "\">" +
      "<div class=\"portfolio-top\"><strong>" + escapeHtml(strategyName()) + "</strong><span class=\"position-tag\">" +
      item.position_count + "/" + state.config.max_open_positions + "</span></div>" +
      "<div class=\"portfolio-value\">" + escapeHtml(euro.format(item.equity)) + "</div>" +
      "<div class=\"portfolio-return " + resultClass + "\">" + escapeHtml(signedEuro(item.pnl)) + " · " + escapeHtml(number.format(item.return_pct)) + " %</div>" +
      "<div class=\"portfolio-details\">" +
        "<div><small>" + escapeHtml(t("cash")) + "</small><strong>" + escapeHtml(euro.format(item.cash)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("invested")) + "</small><strong>" + escapeHtml(euro.format(item.exposure)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("feesPaid")) + "</small><strong>" + escapeHtml(euro.format(item.fees_paid)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("drawdownNow")) + "</small><strong>" + escapeHtml(number.format(item.drawdown_pct)) + " %</strong></div>" +
        "<div><small>" + escapeHtml(t("closedTrades")) + "</small><strong>" + item.closed_trades + "</strong></div>" +
        "<div><small>" + escapeHtml(t("winRate")) + "</small><strong>" + (item.win_rate_pct == null ? "–" : escapeHtml(number.format(item.win_rate_pct)) + " %") + "</strong></div>" +
        "<div><small>" + escapeHtml(t("openPositions")) + "</small><strong>" + item.position_count + "/" + state.config.max_open_positions + "</strong></div>" +
        "<div><small>" + escapeHtml(t("taxYear", { year: item.tax_year })) + "</small><strong>" + escapeHtml(euro.format(item.tax_estimate_year)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("afterTax")) + "</small><strong>" + escapeHtml(euro.format(item.equity_after_tax)) + "</strong></div>" +
        "<div><small>" + escapeHtml(t("lastRun")) + "</small><strong>" + escapeHtml(formatTime(item.last_run_at)) + "</strong></div>" +
      "</div></article>";
  }).join("");
  const dated = portfolios.map((item) => item.last_run_at).filter(Boolean).sort();
  document.getElementById("lastUpdate").textContent = dated.length
    ? t("updated", { time: formatTime(dated.at(-1)) })
    : t("notRun");
}

function renderPositions() {
  if (!state.status) return;
  const positions = state.status.positions || [];
  document.getElementById("positionRows").innerHTML = positions.length ? positions.map((item) => {
    const pnlClass = item.unrealized_pnl >= 0 ? "positive" : "negative";
    return "<tr><td>" + escapeHtml(item.pair) +
      "</td><td>" + escapeHtml(formatMarketPrice(item.entry_price)) +
      "</td><td>" + escapeHtml(formatMarketPrice(item.last_price)) +
      "</td><td>" + escapeHtml(euro.format(item.notional)) +
      "</td><td>" + escapeHtml(formatMarketPrice(item.exit_level)) +
      "</td><td class=\"" + pnlClass + "\">" + escapeHtml(signedEuro(item.unrealized_pnl)) + " · " + escapeHtml(number.format(item.unrealized_pct)) + " %" +
      "</td><td>" + escapeHtml(formatDate(item.opened_at)) +
      "</td><td>" + escapeHtml(formatDate(item.tax_free_from)) + "</td></tr>";
  }).join("") : "<tr><td colspan=\"8\" class=\"muted\">" + escapeHtml(t("noOpenPosition")) + "</td></tr>";
}

function renderTrades() {
  if (!state.status) return;
  const rows = state.status.trades || [];
  document.getElementById("tradeRows").innerHTML = rows.length ? rows.slice(0, 16).map((trade) => {
    const pnl = trade.pnl == null ? "–" : signedEuro(trade.pnl) + " · " + number.format(trade.pnl_pct * 100) + " %";
    const taxNote = trade.pnl == null || trade.holding_days == null ? "" :
      "<br /><small class=\"muted\">" + escapeHtml(t("heldDays", { days: Math.round(trade.holding_days) })) + " · " +
      escapeHtml(trade.taxable ? t("taxable") : t("taxFree")) + "</small>";
    const pnlClass = trade.pnl == null ? "" : trade.pnl >= 0 ? "positive" : "negative";
    return "<tr><td>" + escapeHtml(trade.pair) +
      "</td><td>" + escapeHtml(formatMarketPrice(trade.entry_price)) + "<br /><small class=\"muted\">" + escapeHtml(formatDate(trade.opened_at)) + "</small>" +
      "</td><td>" + (trade.exit_price == null ? "–" : escapeHtml(formatMarketPrice(trade.exit_price)) + "<br /><small class=\"muted\">" + escapeHtml(formatDate(trade.closed_at)) + "</small>") +
      "</td><td class=\"" + pnlClass + "\">" + escapeHtml(pnl) + taxNote +
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

function backtestLabel(item) {
  return item.strategy_id === "benchmark" ? t("equalWeightHold") : strategyName();
}

function renderBacktest() {
  const result = state.backtest;
  if (!result || result.status !== "ok") return;
  document.getElementById("backtestSection").hidden = false;
  document.getElementById("backtestPeriod").textContent = t("backtestPeriod", {
    from: formatDate(result.from),
    to: formatDate(result.to),
    bars: result.bars,
    pairs: result.pairs.length,
    fee: percent.format(result.fee_rate),
  });
  const cards = [...result.strategies, result.benchmark];
  document.getElementById("backtestGrid").innerHTML = cards.map((item) => {
    const returnClass = item.total_return_pct >= 0 ? "positive" : "negative";
    return "<article class=\"backtest-card\" style=\"border-top:2px solid " + escapeHtml(item.color) + "\">" +
      "<span>" + escapeHtml(backtestLabel(item)) + "</span><strong>" + escapeHtml(euro.format(item.final_equity)) + "</strong>" +
      "<div class=\"mini-stats\">" +
        "<div><span>" + escapeHtml(t("totalReturn")) + "</span><b class=\"" + returnClass + "\">" + escapeHtml(number.format(item.total_return_pct)) + " %</b></div>" +
        "<div><span>" + escapeHtml(t("cagrAfterTax")) + "</span><b class=\"" + returnClass + "\">" + escapeHtml(number.format(item.cagr_pct)) + " %</b></div>" +
        "<div><span>" + escapeHtml(t("preTax")) + "</span><b>" + escapeHtml(euro.format(item.pre_tax_final_equity)) + "</b></div>" +
        "<div><span>" + escapeHtml(t("taxesPaid")) + "</span><b>" + escapeHtml(euro.format(item.taxes_paid)) + "</b></div>" +
        "<div><span>" + escapeHtml(t("maxDrawdown")) + "</span><b class=\"negative\">" + escapeHtml(number.format(item.max_drawdown_pct)) + " %</b></div>" +
        "<div><span>" + escapeHtml(t("trades")) + "</span><b>" + (item.trades ?? "–") + "</b></div>" +
        "<div><span>" + escapeHtml(t("winRate")) + "</span><b>" + (item.win_rate_pct == null ? "–" : escapeHtml(number.format(item.win_rate_pct)) + " %") + "</b></div>" +
        "<div><span>" + escapeHtml(t("feesPaid")) + "</span><b>" + escapeHtml(euro.format(item.fees_paid)) + "</b></div>" +
        "<div><span>" + escapeHtml(t("timeInvested")) + "</span><b>" + escapeHtml(number.format(item.time_invested_pct)) + " %</b></div>" +
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
  const padding = Math.max((max - min) * 0.12, 1);
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
  const portfolios = Object.fromEntries((state.status.portfolios || []).map((p) => [p.strategy_id, p]));
  const series = Object.entries(state.status.curves || {}).map(([id, points]) => ({
    label: strategyName(),
    color: portfolios[id]?.color || "#59d3a5",
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
      body: JSON.stringify({ bars: Math.min(1440, state.config.backtest_bars) }),
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
