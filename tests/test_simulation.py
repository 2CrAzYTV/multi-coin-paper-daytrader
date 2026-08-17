import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from app.backtest import Backtester
from app.config import Settings
from app.db import Repository
from app.engine import PaperEngine
from app.main import BacktestRequest
from app.market_data import MarketData
from app.models import BITPANDA_PAPER_LEVERAGES, STRATEGIES

class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir=tempfile.TemporaryDirectory(); self.settings=Settings(data_source="demo",data_dir=Path(self.temp_dir.name),history_bars=180,backtest_bars=400,starting_capital=1_000,risk_per_trade=0.005,max_aggregate_risk=0.01,max_daily_loss=0.02); self.settings.validate(); self.market=MarketData(self.settings)
    def tearDown(self): self.temp_dir.cleanup()
    def test_default_universe_contains_ten_eur_crypto_pairs(self):
        self.assertEqual(self.settings.pairs,("BTC-EUR","ETH-EUR","SOL-EUR","XRP-EUR","ADA-EUR","LINK-EUR","AVAX-EUR","SUI-EUR","TAO-EUR","DOGE-EUR")); self.assertTrue(all(p.endswith("-EUR") for p in self.settings.pairs))
    def test_default_backtest_horizon_is_5000(self): self.assertEqual(Settings().backtest_bars,5000)
    def test_backtest_api_accepts_5000_bars(self):
        self.assertEqual(BacktestRequest(bars=5000).bars,5000)
        with self.assertRaises(ValidationError): BacktestRequest(bars=5001)
    def test_demo_history_supports_5000_bars(self): self.assertEqual(len(self.market.history("BTC-EUR","15m",5000)),5000)
    def test_available_eur_pairs_matches_demo_universe(self): self.assertEqual(self.market.available_eur_pairs(),self.settings.pairs)
    def test_bitpanda_paper_leverage_presets_are_available(self):
        self.assertEqual(BITPANDA_PAPER_LEVERAGES,(1.0,2.0,3.0,5.0,10.0)); self.assertEqual(tuple(s.max_leverage for s in STRATEGIES if s.short_allowed),BITPANDA_PAPER_LEVERAGES); self.assertEqual(len(STRATEGIES),6)
    def test_demo_source_returns_distinct_ohlcv_for_each_pair(self):
        closes=[]
        for pair in self.settings.pairs:
            frame=self.market.history(pair,"15m",120); self.assertEqual(list(frame.columns),["Open","High","Low","Close","Volume"]); self.assertGreaterEqual(len(frame),120); closes.append(round(float(frame.iloc[-1]["Close"]),6))
        self.assertEqual(len(set(closes)),len(self.settings.pairs))
    def test_backtest_runs_shared_portfolio_for_all_strategies(self):
        result=Backtester(self.settings,self.market).run(400); self.assertEqual(result["status"],"ok"); self.assertEqual(result["pairs"],sorted(self.settings.pairs)); self.assertEqual(len(result["strategies"]),6)
        diagnostic_fields={"profit_factor","expectancy_eur","average_win_eur","average_loss_eur","largest_loss_eur","long_trades","long_win_rate_pct","long_pnl_eur","short_trades","short_win_rate_pct","short_pnl_eur","avg_margin_utilization_pct"}
        for strategy in result["strategies"]:
            self.assertGreater(strategy["final_equity"],0); self.assertLessEqual(strategy["max_positions"],2); self.assertLessEqual(strategy["max_drawdown_pct"],10.1); self.assertLessEqual(strategy["max_effective_leverage"],strategy["max_leverage"]+0.001); self.assertLessEqual(strategy["max_margin_utilization_pct"],100.01); self.assertTrue(diagnostic_fields.issubset(strategy)); self.assertEqual(strategy["long_trades"]+strategy["short_trades"],strategy["trades"]); self.assertTrue(strategy["curve"])
    def test_paper_cycle_is_idempotent_per_closed_candle(self):
        repository=Repository(self.settings.database_path,1_000); repository.initialize(); engine=PaperEngine(self.settings,repository,self.market); first=engine.run_once(); second=engine.run_once(); self.assertEqual(first["status"],"ok"); self.assertEqual(second["status"],"no_new_candles"); self.assertEqual(len(repository.list_markets()),10); self.assertEqual(len(engine.serialize_portfolios()),6)
    def test_market_client_has_no_order_or_transfer_methods(self):
        public_methods={name for name in dir(self.market) if not name.startswith("_")}; self.assertFalse(public_methods & {"order","create_order","cancel_order","transfer"})

if __name__=="__main__": unittest.main()
