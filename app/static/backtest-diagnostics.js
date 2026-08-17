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

  function selectorPanel(selector) {
    if (!selector || selector.status !== "ok") return "";
    const rows = (selector.comparisons || []).map((row) => {
      const returnClass = Number(row.total_return_pct) >= 0 ? "positive" : "negative";
      const recommendation = row.recommended
        ? " <span class=\"positive\">★ " + escapeHtml(label("recommended", "empfohlen")) + "</span>"
        : "";
      return "<tr>" +
        "<td><strong>Top " + escapeHtml(String(row.size)) + "</strong>" + recommendation + "</td>" +
        "<td>" + escapeHtml((row.pairs || []).join(", ")) + "</td>" +
        "<td class=\"" + returnClass + "\">" + escapeHtml(percent(row.total_return_pct)) + "</td>" +
        "<td>" + escapeHtml(percent(row.max_drawdown_pct)) + "</td>" +
        "<td>" + escapeHtml(String(row.trades ?? 0)) + "</td>" +
        "<td>" + escapeHtml(factor(row.profit_factor)) + "</td>" +
        "</tr>";
    }).join("");
    const ranking = (selector.ranking || []).map((row, index) =>
      "<span class=\"position-tag\">" + escapeHtml(String(index + 1)) + ". " + escapeHtml(row.pair) +
      " · " + escapeHtml(money(row.training_pnl_eur)) + "</span>"
    ).join(" ");
    return "<section id=\"coinSelectorPanel\" class=\"panel\" style=\"margin-top:18px\">" +
      "<p class=\"section-kicker\">" + escapeHtml(label("Walk-forward coin selector", "Walk-Forward Coin-Selektor")) + "</p>" +
      "<h2>" + escapeHtml(label("Out-of-sample comparison: all / 7 / 5 / 3 coins", "Out-of-Sample-Vergleich: alle / 7 / 5 / 3 Coins")) + "</h2>" +
      "<p class=\"muted\">" + escapeHtml(label(
        "The first 60% of the period ranks the coins. Only the later 40% is used to compare the selected baskets. Reference strategy: ",
        "Die ersten 60 % des Zeitraums bestimmen das Ranking. Nur die späteren 40 % werden zum Vergleich der ausgewählten Körbe verwendet. Referenzstrategie: "
      )) + escapeHtml(selector.reference_strategy_label || selector.reference_strategy_id || "–") + "</p>" +
      "<div class=\"pair-chips\" style=\"margin-top:12px\">" + ranking + "</div>" +
      "<div class=\"table-wrap\" style=\"margin-top:12px\"><table><thead><tr>" +
      "<th>" + escapeHtml(label("Basket", "Korb")) + "</th>" +
      "<th>" + escapeHtml(label("Coins", "Coins")) + "</th>" +
      "<th>" + escapeHtml(label("Validation return", "Validierungsrendite")) + "</th>" +
      "<th>" + escapeHtml(label("Drawdown", "Drawdown")) + "</th>" +
      "<th>" + escapeHtml(label("Trades", "Trades")) + "</th>" +
      "<th>" + escapeHtml(label("Profit factor", "Profit Factor")) + "</th>" +
      "</tr></thead><tbody>" + rows + "</tbody></table></div>" +
      "<p class=\"disclaimer\">" + escapeHtml(label(
        "The recommendation is a paper-research result from one chronological holdout, not a prediction or investment recommendation.",
        "Die Empfehlung ist ein Paper-Research-Ergebnis aus einem chronologischen Holdout und keine Prognose oder Anlageempfehlung."
      )) + "</p></section>";
  }

  renderBacktest = function renderBacktestWithDiagnostics() {
    baseRenderBacktest();
    const result = state.backtest;
    if (!result || result.status !== "ok") return;

    document.getElementById("coinSelectorPanel")?.remove();
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

    const panel = selectorPanel(result.coin_selector);
    const grid = document.getElementById("backtestGrid");
    if (panel && grid) grid.insertAdjacentHTML("afterend", panel);
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