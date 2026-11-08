"""German tax model for private crypto sales (§ 23 EStG), simplified.

- A sale within ``holding_days`` (365) of the purchase is a private sale
  ("privates Veräußerungsgeschäft"); the gain or loss counts for the tax year.
- Coins held longer are sold tax-free; their losses do not count either.
- Freigrenze (not Freibetrag): if the net taxable result of a year is BELOW
  ``allowance`` (EUR 1,000 since 2024) it stays completely tax-free; at or
  above it the whole amount is taxed.
- A net loss is carried forward and only offsets later private-sale gains.
  It is not consumed in years that stay below the Freigrenze.
- The flat ``rate`` approximates the personal marginal rate incl. solidarity
  surcharge. Church tax, other private sales of the same person (which share
  the Freigrenze!) and the actual payment date are not modelled.

This is a simulation aid, not tax advice.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxResult:
    net_taxable: float
    tax: float
    loss_carryforward: float


def is_taxable(holding_days: float, holding_limit_days: int = 365) -> bool:
    return holding_days <= holding_limit_days


def settle_year(
    taxable_pnls: list[float],
    *,
    loss_carryforward: float,
    rate: float,
    allowance: float,
) -> TaxResult:
    """Tax for one calendar year from the net results of its taxable sales."""
    net = sum(taxable_pnls)
    if net <= 0:
        return TaxResult(net, 0.0, loss_carryforward - net)
    if net < allowance:
        return TaxResult(net, 0.0, loss_carryforward)
    offset = min(loss_carryforward, net)
    taxable = net - offset
    return TaxResult(net, round(taxable * rate, 2), loss_carryforward - offset)
