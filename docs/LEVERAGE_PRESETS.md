# Simulated leverage presets

The development branch compares one Long-only 1× baseline with Long/Short paper strategies at these presets:

- 1×
- 2×
- 3×
- 5×
- 10×

These presets are simulation limits only. The application does not open a margin account, borrow funds, create a derivative, or place a real order.

Leverage does not multiply the configured risk budget. `RISK_PER_TRADE`, `MAX_AGGREGATE_RISK`, `MAX_DAILY_LOSS`, and `HARD_DRAWDOWN` continue to cap the paper simulator independently. Higher leverage only raises the maximum notional exposure the position-sizing logic may use when the stop-distance risk model permits it.

The application currently uses fixed presets because Bitpanda Fusion does not expose a documented read-only endpoint that returns the currently permitted leverage levels per trading pair. If such metadata becomes officially available, the intended future implementation is to discover those levels from the read-only API instead of maintaining the preset list manually.
