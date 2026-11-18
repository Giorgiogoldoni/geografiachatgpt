# Logical Invest World Top 4 — research on the selection engine

**Research date:** 18 November 2026  
**Repository:** geografiachatgpt  
**Status:** documentary reconstruction; not an official or exact replication.

## Executive result

We have now found materially stronger evidence about the historical selection engine than was reflected in the first version of our model.

The public Logical Invest material supports the following:

1. **Monthly rebalance.** The 2019 strategy article explicitly says the strategy rebalances monthly.
2. **Lookback of 68 trading days.** The same article says the country rotation uses a 68-trading-day lookback.
3. **Modified Sharpe ranking.** The article explicitly says it uses a dynamic ranking method based on a modified Sharpe ratio.
4. **Volatility attenuator = 2.** The article says volatility has a slightly higher weight, using an attenuator of 2.
5. **Optimization/solver, not merely a simple sort.** The article says the country ETFs and Treasury instrument are mixed to achieve the maximum modified Sharpe ratio. In a 2015 comment, the author confirms that QuantTrader uses a C# solver, described as similar to Excel Solver, to calculate the optimal combination.
6. **Current geographic structure.** The current WTOP4 page describes four geographic sub-strategies; each sub-strategy picks the best country ETF in its region. The three current sub-strategy lists we could verify are Developed, Asia and South America. A current fourth-region constituents page was not located.

Sources:
- Current World Top 4 description and 49 main-list tickers: https://logical-invest.com/app/strategy/WTOP4 (updated 16 Oct 2026)
- Developed list: https://logical-invest.com/app/strategy/developed/world-countries-developed (updated 30 Sep 2026)
- Asia list: https://logical-invest.com/app/strategy/asia/world-countries-asia (updated 28 Sep 2026)
- South America list: https://logical-invest.com/app/strategy/soamerica/world-countries-south-america (updated 7 Oct 2026)
- Historical method article (20 Jan 2019): https://logical-invest.com/world-country-etf-rotation-strategy/

## What the historical article actually says

The 2019 article describes an earlier World Country Top 4 implementation:
- 68 trading-day lookback;
- monthly rebalance;
- modified Sharpe ratio;
- volatility attenuator of 2;
- a solver that combines the country ETFs and the Treasury hedge to maximize the modified Sharpe ratio;
- an example allocation of 30% EWJ, 20% EWL, 20% EWS and 30% EIS;
- the strategy universe was described as 49 country/region ETFs, with a Treasury ETF used as hedge.

The author states in a 2015 comment that the optimization is calculated in QuantTrader, a proprietary C# program, using a solver similar to Excel Solver.

**Important:** this is strong evidence for the historical engine, but it does not prove that the live 2026 WTOP4 uses every one of those exact parameters unchanged. The current public pages disclose the regional top-country architecture, but do not publish the full current scoring equation, solver constraints or all weights.

## Modified Sharpe: what we can and cannot infer

The existing research code uses:
- 68-day return;
- 68-day annualized volatility;
- modified score = return / volatility².

This is consistent with the historical description of a volatility attenuator of 2 as a plausible implementation of a modified Sharpe score. However, the source does not publish the complete equation, the exact annualization, the risk-free treatment, the exact volatility estimator, or the solver's constraints. Therefore return / volatility² remains a **candidate interpretation**, not a verified proprietary formula.

A plain ranking of each ETF independently is not equivalent to the historical solver: a portfolio optimizer can choose weights jointly, subject to constraints, to maximize a portfolio-level score. We must keep these two methods separate in code and reporting.

## Current public universe by sub-strategy

The new machine-readable register is logical_invest_substrategy_universe.csv.

### Developed — 23 published entries
SPY, DIA, EIRL, EIS, ENZL, EPOL, EWA, EWC, EWD, EWG, EWH, EWI, EWJ, EWK, EWL, EWM, EWN, EWO, EWP, EWQ, EWU, NORW, QQQ.

### Asia — 16 published entries
ASHR, DBKO, EIDO, EPHE, EPI, EWJ, EWM, EWS, EWT, EWY, EWZ, EZA, FXI, IDX, THD, VNM.

### South America — 6 published entries
ARGT, ECH, EPU, EWW, EWZ, GXG.

### Fourth sleeve — not yet verified
The main WTOP4 universe contains plausible Africa / Middle East / frontier / EMEA candidates such as AFK, EGPT, FM, FRN, GAF, GULF, GREK, MES, RSX and TUR. These are marked as candidates only; no ticker is assigned to a fourth official sleeve without a current source.

### Source-list anomalies to preserve
- EWJ and EWM appear in both Developed and Asia.
- EWZ appears in both Asia and South America.
- EZA (South Africa) appears in the Asia list.
- EWW (Mexico) appears in the South America list.
- QQQ is in Developed even though it is not a single-country ETF.
- DBKO, ARGT and GXG appear in regional pages but are absent from the 49-ticker WTOP4 main list.
- SPY and DIA appear in Developed but are absent from the main WTOP4 list.

Do not silently correct these source classifications. Preserve the provider's published memberships and run sensitivity tests for duplicates/anomalies.

## HEDGE — what is public

The current HEDGE description says it combines two components:
- a Treasury sub-strategy;
- a GLD-USD sub-strategy.

The current public GLD-USD description says it rotates between gold and the U.S. dollar based on recent risk-adjusted performance. The exact current Treasury and GLD-USD ranking formulae, weights and monthly holdings are not fully exposed in the public page content available to this audit.

The 60/40 equity/HEDGE allocation and the internal 60/40 Treasury/Gold split are documented in the 2020 strategy update as historical settings. They must not be labelled as confirmed current weights without current allocation evidence.

## Implications for our repository

The existing world_top4.py is not a replication:
- it assigns a fourth region using a provisional residual bucket;
- it selects the top score independently within each region;
- its modified score is a candidate approximation;
- it uses a simplified hedge;
- it includes some region assignments that differ from the currently published sub-strategy lists.

The separate world_top4_6040.py also has provisional regional membership and an approximate hedge implementation.

## Next implementation sequence

1. Keep the existing model and results intact as the baseline approximation.
2. Build a separate research branch/module for the historical modified-Sharpe solver approach; do not overwrite the baseline.
3. Implement multiple explicit variants:
   - simple 68-day momentum rank;
   - 68-day return / volatility² candidate;
   - constrained portfolio-level optimizer with documented assumptions, clearly labelled as an approximation.
4. Reconstruct the fourth sleeve from current or archived provider evidence before running a four-region comparison.
5. Treat provider-published holdings as one-month delayed observations; store publication date and effective month separately to avoid look-ahead.
6. Compare model monthly returns and annual holdings against the provider snapshots on identical dates. A matching ticker on one date is not enough to validate the engine.
7. Only after these checks consider updating the live dashboard.

## Decision

**We have identified the historical core of the motor: monthly, 68 trading days, modified Sharpe with volatility attenuator 2, and a QuantTrader solver for portfolio-level optimization.** We have not verified the complete current 2026 formula, solver constraints, current fourth region or current hedge weights. The right next step is a parallel experimental implementation, not a silent replacement of the current code.
