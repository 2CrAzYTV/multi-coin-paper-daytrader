(() => {
  const baseRenderBacktest = renderBacktest;

  function label(en, de) {
    return state.language === "de" ? de : en;
  }

  function valueOrDash(value, formatter) {
    if (value == null || Number.isNaN(Number(value))) return "–";
    return formatter(Number(value));
  }

  function percent(value) {
    return valueOrDash(value, (v) => number.format(v) + " %");
  }

  function money(value) {
    return valueOrDash(value, (v) => euro.format(v));
  }

  function factor(value) {
    return valueOrDash(value, (v) => number.format(v));
  }

  renderBacktest = function renderBacktestWithDiagnostics() {
    baseRenderBacktest();
    const result = state.backtest;
    if (!result || result.status !== "ok") return;

    const cards = [...result.strategies, result.benchmark];
    const elements = [...document.querySelectorAll("#backtestGrid .backtest-card .mini-stats")];
    cards.forEach((item, index) => {
      const target = elements[index];
      if (!target || item.strategy_id === "benchmark") return;
      target.insertAdjacentHTML("beforeend",
        "<div><span>" + escapeHtml(label("Avg. margin", "Ø Margin-Auslastung")) + "</span><b>" + escapeHtml(percent(item.avg_margin_utilization_pct)) + "</b></div>" +
        "<div><span>" + escapeHtml(label("Profit factor", "Profit Factor")) + "</span><b>" + escapeHtml(factor(item.profit_factor)) + "</b></div>" +
        "<div><span>" + escapeHtml(label("Expectancy / trade", "Erwartungswert / Trade")) + "</span><b>" + escapeHtml(money(item.expectancy_eur)) + "</b></div>" +
        "<div><span>" + escapeHtml(label("Avg. win", "Ø Gewinn")) + "</span><b class=\"positive\">" + escapeHtml(money(item.average_win_eur)) + "</b></div>" +
        "<div><span>" + escapeHtml(label("Avg. loss", "Ø Verlust")) + "</span><b class=\"negative\">" + escapeHtml(money(item.average_loss_eur)) + "</b></div>" +
        "<div><span>" + escapeHtml(label("Largest loss", "Größter Verlust")) + "</span><b class=\"negative\">" + escapeHtml(money(item.largest_loss_eur)) + "</b></div>" +
        "<div><span>" + escapeHtml(label("Long", "Long")) + "</span><b>" + escapeHtml(String(item.long_trades ?? 0)) + " · " + escapeHtml(percent(item.long_win_rate_pct)) + " · " + escapeHtml(money(item.long_pnl_eur)) + "</b></div>" +
        "<div><span>" + escapeHtml(label("Short", "Short")) + "</span><b>" + escapeHtml(String(item.short_trades ?? 0)) + " · " + escapeHtml(percent(item.short_win_rate_pct)) + " · " + escapeHtml(money(item.short_pnl_eur)) + "</b></div>"
      );
    });
  };
})();
