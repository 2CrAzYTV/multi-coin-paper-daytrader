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

  function attributionTable(item) {
    const rows = Array.isArray(item.pair_attribution) ? item.pair_attribution : [];
    if (!rows.length) return "";
    const body = rows.map((row) => {
      const pnlClass = Number(row.pnl_eur) >= 0 ? "positive" : "negative";
      return "<tr>" +
        "<td><strong>" + escapeHtml(row.pair) + "</strong></td>" +
        "<td>" + escapeHtml(String(row.trades ?? 0)) + "</td>" +
        "<td>" + escapeHtml(percent(row.win_rate_pct)) + "</td>" +
        "<td class=\"" + pnlClass + "\">" + escapeHtml(money(row.pnl_eur)) + "</td>" +
        "<td>" + escapeHtml(String(row.long_trades ?? 0)) + " / " + escapeHtml(String(row.short_trades ?? 0)) + "</td>" +
        "</tr>";
    }).join("");
    return "<div class=\"table-wrap\" style=\"margin-top:14px\">" +
      "<table><thead><tr>" +
      "<th>" + escapeHtml(label("Coin", "Coin")) + "</th>" +
      "<th>" + escapeHtml(label("Trades", "Trades")) + "</th>" +
      "<th>" + escapeHtml(label("Win rate", "Trefferquote")) + "</th>" +
      "<th>" + escapeHtml(label("P/L", "G/V")) + "</th>" +
      "<th>" + escapeHtml(label("L / S", "L / S")) + "</th>" +
      "</tr></thead><tbody>" + body + "</tbody></table></div>";
  }

  renderBacktest = function renderBacktestWithDiagnostics() {
    baseRenderBacktest();
    const result = state.backtest;
    if (!result || result.status !== "ok") return;

    const cards = [...result.strategies, result.benchmark];
    const cardElements = [...document.querySelectorAll("#backtestGrid .backtest-card")];
    const elements = [...document.querySelectorAll("#backtestGrid .backtest-card .mini-stats")];
    cards.forEach((item, index) => {
      const target = elements[index];
      const card = cardElements[index];
      if (!target || !card || item.strategy_id === "benchmark") return;
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
      const table = attributionTable(item);
      if (table) {
        card.insertAdjacentHTML("beforeend", "<p class=\"section-kicker\" style=\"margin-top:16px\">" + escapeHtml(label("Coin attribution", "Coin-Auswertung")) + "</p>" + table);
      }
    });
  };

  const backtestButton = document.getElementById("backtestButton");
  backtestButton.addEventListener("click", async (event) => {
    event.stopImmediatePropagation();
    const button = event.currentTarget;
    setBusy(button, true, "backtesting");
    try {
      const configuredBars = Math.max(100, Math.min(5000, Number(state.config.backtest_bars) || 5000));
      state.backtest = await requestJson("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bars: configuredBars }),
      });
      renderBacktest();
      toast(t("backtestDone"));
    } catch (error) {
      toast(translateRuntimeText(error.message), true);
    } finally {
      setBusy(button, false);
    }
  }, { capture: true });
})();
