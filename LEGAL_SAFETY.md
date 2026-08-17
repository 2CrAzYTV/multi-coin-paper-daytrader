# Legal and regulatory safety boundaries

This document is a project-maintenance guardrail, not legal advice. It records the boundaries that keep the current public beta focused on technical learning, backtesting, and paper trading.

## Current public-beta scope

The application must remain **paper only**. It may simulate balances, long/short positions, leverage, stops, targets, fees, slippage, profit/loss, scanner outputs, and backtests, but it must not place or route real-money orders.

Bitpanda Fusion integration is limited to **read-only market data**. Users supply their own API key and should enable **Read** permission only. Trade and Transfer permissions are not required and should remain disabled.

Strategy outputs are **simulated paper signals**, not personalized investment recommendations. The project must not promise or guarantee profit, income, return, win rate, or future performance.

The project is not affiliated with, endorsed by, sponsored by, or supported by Bitpanda.

## Features that require a new legal/regulatory review before release

Do not add or publish any of the following without a fresh legal and regulatory assessment for the intended jurisdictions and business model:

- real-money order creation, modification, cancellation, routing, or execution;
- custody of customer crypto assets, fiat funds, credentials, or private keys;
- trading or portfolio management on behalf of another person;
- personalized buy/sell/hold/short recommendations based on a user's personal circumstances;
- centralized copying, redistribution, resale, or sublicensing of third-party market data;
- coordinated trading, pump/dump functionality, or market-manipulation features;
- monetization models such as paid subscriptions, premium trading features, advertising, affiliate promotions, or managed hosting where additional financial, consumer, tax, privacy, imprint, or Cyber Resilience Act obligations may apply.

## Security and privacy boundary

The dashboard has no authentication and must be treated as a trusted-LAN application. API keys must never be returned by public endpoints, written to logs, committed to Git, or included in support material.

## Release rule

A release is not considered ready if automated tests detect a Fusion write method or an order/transfer/withdrawal/deposit API path. Any intentional change to these safeguards requires an explicit maintainer review and a new legal/regulatory assessment before merge.
