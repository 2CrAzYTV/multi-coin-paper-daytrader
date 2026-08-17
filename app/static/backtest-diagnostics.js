(() => {
  const baseRenderBacktest = renderBacktest;

  function label(en, de) {
    return state.language === "de" ? de : en;
  }

  function installProgressStyles() {
    if (document.getElementById("operationProgressStyles")) return;
    const style = document.createElement("style");
    style.id = "operationProgressStyles";
    style.textContent = `
      .operation-progress { min-width: 230px; margin-top: 9px; display: none; }
      .operation-progress.visible { display: block; }
      .operation-progress-label { color: var(--muted); font-size: .72rem; margin-bottom: 6px; display: flex; justify-content: space-between; gap: 10px; }
      .operation-progress-track { height: 8px; overflow: hidden; border-radius: 999px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.06); }
      .operation-progress-fill { height: 100%; width: 36%; border-radius: inherit; background: var(--blue); transform: translateX(-110%); }
      .operation-progress.running .operation-progress-fill { animation: operation-progress-slide 1.15s ease-in-out infinite; }
      .operation-progress.done .operation-progress-fill { width: 100%; transform: translateX(0); animation: none; background: var(--mint); transition: width .2s ease; }
      .operation-progress.failed .operation-progress-fill { width: 100%; transform: translateX(0); animation: none; background: var(--red); }
      @keyframes operation-progress-slide { 0% { transform: translateX(-110%); } 100% { transform: translateX(290%); } }
      .button-progress-stack { display: grid; align-content: start; min-width: 230px; }
      @media (max-width: 720px) { .button-progress-stack { width: 100%; } .button-progress-stack .button { width: 100%; } }
    `;
    document.head.appendChild(style);
  }

  function progressFor(button, id) {
    installProgressStyles();
    let stack = button.closest(".button-progress-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "button-progress-stack";
      button.parentNode.insertBefore(stack, button);
      stack.appendChild(button);
    }
    let progress = document.getElementById(id);
    if (!progress) {
      progress = document.createElement("div");
      progress.id = id;
      progress.className = "operation-progress";
      progress.setAttribute("role", "progressbar");
      progress.setAttribute("aria-valuemin", "0");
      progress.setAttribute("aria-valuemax", "100");
      progress.innerHTML = "<div class=\"operation-progress-label\"><span></span><strong></strong></div><div class=\"operation-progress-track\"><div class=\"operation-progress-fill\"></div></div>";
      stack.appendChild(progress);
    }
    return progress;
  }

  function setProgress(progress, status, text) {
    progress.className = "operation-progress visible " + status;
    const statusText = status === "running"
      ? label("Running", "Läuft")
      : status === "done"
        ? label("Finished", "Fertig")
        : label("Failed", "Fehlgeschlagen");
    progress.querySelector("span").textContent = text;
    progress.querySelector("strong").textContent = statusText;
    progress.setAttribute("aria-valuenow", status === "done" ? "100" : status === "failed" ? "100" : "0");
    progress.setAttribute("aria-valuetext", statusText);
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

  function qualityPanel(result) {
    const scan = result.coin_scan || {};
    const skipped = result.skipped_pairs || {};
    const failures = result.failures || {};
    if (!scan.automatic && !Object.keys(skipped).length) return "";
    const discovered = scan.discovered_count ?? 0;
    const usable = scan.usable_count ?? result.pairs?.length ?? 0;
    const skippedCount = scan.skipped_count ?? Object.keys(skipped).length;
    const failedCount = scan.failed_count ?? Object.keys(failures).length;
    const minimum = result.minimum_history_bars ?? "–";
    const skippedRows = Object.entries(skipped).slice(0, 40).map(([pair, reason]) =>
      "<tr><td><strong>" + escapeHtml(pair) + "</strong></td><td>" + escapeHtml(reason) + "</td></tr>"
    ).join("");
    return "<section id=\"coinQualityPanel\" class=\"panel\" style=\"margin:18px 0\">" +
      "<p class=\"section-kicker\">" + escapeHtml(label("Automatic coin quality filter", "Automatischer Coin-Qualitätsfilter")) + "</p>" +
      "<h2>" + escapeHtml(label("Research universe", "Research-Universum")) + "</h2>" +
      "<div class=\"mini-stats\" style=\"margin-top:14px;max-width:620px\">" +
      "<div><span>" + escapeHtml(label("Discovered", "Entdeckt")) + "</span><b>" + escapeHtml(String(discovered)) + "</b></div>" +
      "<div><span>" + escapeHtml(label("Usable", "Geeignet")) + "</span><b class=\"positive\">" + escapeHtml(String(usable)) + "</b></div>" +
      "<div><span>" + escapeHtml(label("Skipped", "Übersprungen")) + "</span><b>" + escapeHtml(String(skippedCount)) + "</b></div>" +
      "<div><span>" + escapeHtml(label("Real errors", "Echte Fehler")) + "</span><b class=\"negative\">" + escapeHtml(String(failedCount)) + "</b></div>" +
      "<div><span>" + escapeHtml(label("Minimum history", "Mindesthistorie")) + "</span><b>" + escapeHtml(String(minimum)) + " " + escapeHtml(label("candles", "Kerzen")) + "</b></div>" +
      "</div>" +
      (skippedRows ? "<details style=\"margin-top:14px\"><summary>" + escapeHtml(label("Show skipped coins", "Übersprungene Coins anzeigen")) + "</summary><div class=\"table-wrap\" style=\"margin-top:10px\"><table><thead><tr><th>Coin</th><th>" + escapeHtml(label("Reason", "Grund")) + "</th></tr></thead><tbody>" + skippedRows + "</tbody></table></div></details>" : "") +
      "</section>";
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
    document.getElementById("coinQualityPanel")?.remove();
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

    const grid = document.getElementById("backtestGrid");
    const quality = qualityPanel(result);
    if (quality && grid) grid.insertAdjacentHTML("afterend", quality);
    const panel = selectorPanel(result.coin_selector);
    const anchor = document.getElementById("coinQualityPanel") || grid;
    if (panel && anchor) anchor.insertAdjacentHTML("afterend", panel);
  };

  const runButton = document.getElementById("runButton");
  runButton.addEventListener("click", async (event) => {
    event.stopImmediatePropagation();
    const button = event.currentTarget;
    const progress = progressFor(button, "scanProgress");
    setProgress(progress, "running", label("Scanning Fusion markets and loading signals …", "Fusion-Märkte werden geprüft und Signale geladen …"));
    setBusy(button, true, "scanning");
    try {
      const result = await requestJson("/api/paper/run", { method: "POST" });
      const processed = result.new_pairs?.length ?? result.pairs?.length ?? 0;
      setProgress(progress, "done", label(`Scan finished · ${processed} usable markets`, `Scan fertig · ${processed} nutzbare Märkte`));
      toast(result.status === "ok"
        ? t("marketsProcessed", { count: processed })
        : translateRuntimeText(result.message));
      state.backtest = null;
      document.getElementById("backtestSection").hidden = true;
      await refreshStatus();
    } catch (error) {
      setProgress(progress, "failed", label("Scan failed", "Scan fehlgeschlagen"));
      toast(translateRuntimeText(error.message), true);
    } finally {
      setBusy(button, false);
    }
  }, { capture: true });

  const backtestButton = document.getElementById("backtestButton");
  backtestButton.addEventListener("click", async (event) => {
    event.stopImmediatePropagation();
    const button = event.currentTarget;
    const progress = progressFor(button, "backtestProgress");
    setProgress(progress, "running", label("Loading history and running walk-forward research …", "Historie wird geladen und Walk-Forward-Analyse ausgeführt …"));
    setBusy(button, true, "backtesting");
    try {
      const configuredBars = Math.max(100, Math.min(5000, Number(state.config.backtest_bars) || 5000));
      state.backtest = await requestJson("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bars: configuredBars }),
      });
      renderBacktest();
      const usable = state.backtest.coin_scan?.usable_count ?? state.backtest.pairs?.length ?? 0;
      const skipped = state.backtest.coin_scan?.skipped_count ?? Object.keys(state.backtest.skipped_pairs || {}).length;
      setProgress(progress, "done", label(
        `Backtest finished · ${usable} coins used · ${skipped} skipped`,
        `Backtest fertig · ${usable} Coins verwendet · ${skipped} übersprungen`
      ));
      toast(t("backtestDone"));
    } catch (error) {
      setProgress(progress, "failed", label("Backtest failed", "Backtest fehlgeschlagen"));
      toast(translateRuntimeText(error.message), true);
    } finally {
      setBusy(button, false);
    }
  }, { capture: true });
})();
