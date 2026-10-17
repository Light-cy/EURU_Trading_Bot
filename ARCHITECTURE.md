# Xephy-AI Trading Platform Architecture

**Status:** Working architecture for project scoping  
**Last updated:** 2026-10-11

This document describes the intended direction for the FYP and separates it
from what the repository currently implements. It is a guide for breaking work
into milestones, not a claim that planned components already exist. Update it
alongside implementation whenever a significant design decision changes.

## 1. Product goal

Build a locally developed, multi-pair trading research platform that can:

- Analyze multiple configured currency pairs using independently evaluated
  strategies or models.
- Produce explainable trade recommendations with entry, stop loss, take profit,
  position size, risk/reward, and an expiry time.
- Let an operator choose recommendation-only or automated operation.
- Inspect a linked MetaTrader 5 (MT5) account without sending orders during
  the initial connector phase.
- Test strategies using persistent paper trading before any demo-account
  automation is enabled.
- Coordinate pair-level ideas under portfolio-wide risk limits.

This is a research and software engineering project, not a promise of
profitability or financial advice.

## 2. Current implementation vs. target

### Current prototype

- React/Vite dashboard and Python/Flask backend.
- Analysis is for one configured pair at a time (EURUSD by default).
- Technical indicators, SMC analysis, and optional ML functionality are in the
  backend.
- Mock market data is available for development; MT5 integration is currently
  read-only when configured.
- Positions are paper simulated; the project does not send broker orders.
- Existing persistence is SQLAlchemy. The schema is versioned with Alembic and
  PostgreSQL is configured as the active database for the current local
  development environment; SQLite remains the code default for fresh local
  setups. A guarded SQLite-to-PostgreSQL history transfer is available. This
  describes the current implementation only; MongoDB is the selected FYP target
  because it is specified in the project proposal, and its implementation and
  safe history transition are still pending.
  Authentication, multi-user isolation, the connector application, and the
  multi-pair coordinator are not implemented.

Synthetic MockMT5 data is opt-in for development/test only. It is not suitable
for model training, backtest evidence, or claims about strategy performance.
Do not treat it as live market data or simulated positions as broker positions.

### Intended target

```text
                          Local development / later AWS hosting
┌──────────────────┐       ┌─────────────────────────────────────────────┐
│ React dashboard  │◄─────►│ API and application services                │
└──────────────────┘       │ - settings and recommendation workflows     │
                           │ - master coordinator and portfolio risk     │
                           │ - paper ledger and audit events              │
                           └───────────────┬─────────────────────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │ MongoDB (FYP target)    │
                              │ users, settings,        │
                              │ recommendations, trades│
                              └─────────────────────────┘
                                           ▲
                           outbound secure connection
                                           │
┌─────────────────────────────────────────┴───────────────────────────────┐
│ User's Windows or Linux machine                                          │
│ Local connector → MT5 terminal / supported integration (read-only first) │
└─────────────────────────────────────────────────────────────────────────┘

                    Backend analysis pipeline
┌─────────────────────────────────────────────────────────────────────────┐
│ Market data → EURUSD agent ─┐                                            │
│ Market data → XAUUSD agent ─┼→ Master coordinator → Risk gate            │
│ Market data → USDJPY agent ─┘          │                 │                │
│                                        └→ Recommendation / Paper / Demo*  │
└─────────────────────────────────────────────────────────────────────────┘
* Demo execution is a later, explicitly gated phase; it is not current behavior.
```

The diagram is logical, not a deployment commitment. During local development,
the API, analysis workers, and database may run on the same computer.

## 3. Main components and responsibilities

### Dashboard

- Configure pairs, analysis settings, risk limits, and operating mode.
- Show data freshness, connector health, recommendations, open paper positions,
  and performance.
- In recommendation mode, allow the operator to review, accept, or reject an
  unexpired recommendation.
- Make the selected mode and the difference between simulated and broker
  activity visible.

### API and application services

- Validate requests and enforce workflow rules; the frontend is not a security
  boundary.
- Expose separate operations for analysis, account/market snapshots,
  recommendations, paper positions, and connector status.
- Persist state and audit important actions and failures.
- Bind to localhost during unauthenticated local development. CORS restrictions
  do not replace authentication.

### Pair agents

Each configured pair has an isolated analysis configuration and produces a
structured candidate rather than placing an order. A candidate should identify
the pair, direction, analysis timestamp, source data freshness, entry
assumptions, proposed SL/TP, risk inputs, rationale, and expiry.

EURUSD, USDJPY, and XAUUSD are the initial research targets, not a limit on the
eventual number of pairs. The strategy/model assigned to each pair must be
selected by documented validation and walk-forward evaluation; no model is
assumed to be best in advance. Start with transparent, testable coordination
logic. Add an LLM or other agentic planner only where evaluation demonstrates
value and deterministic safety checks remain authoritative.

### Master coordinator and portfolio risk gate

- Collect candidate recommendations from pair agents.
- Reject stale, invalid, conflicting, or over-limit candidates.
- Rank eligible candidates using documented criteria and account/portfolio
  constraints.
- Prevent simultaneous pair signals from exceeding configured aggregate risk.
- Record the decision and its rationale for later review.

The coordinator does not bypass the risk gate and does not directly connect to
MT5. A model's confidence score alone is never authorization to trade.

### Risk and recommendation service

- Support explicit sizing preferences, such as fixed lot size or risk-based
  sizing, after their definitions and limits are finalized.
- Validate lot size against symbol volume constraints and configured risk
  limits.
- Calculate SL/TP, expected risk/reward, and an exact expiry timestamp.
- Reject invalid prices, stop distances, or expired recommendations.

The supported SL/TP methods and account-currency conversion rules still need
to be specified and tested per broker symbol. UI values must not silently
override server-side limits.

### Paper ledger

- Store paper orders, positions, fills, and closures persistently.
- Model spread and, as sufficient data becomes available, commission, swap,
  and slippage using stated assumptions.
- Keep paper activity strictly separate from MT5 broker positions and broker
  performance.
- Report metrics with definitions and sample period; do not imply simulated
  performance predicts future returns.

### User-run MT5 connector

- Runs on the operator's own Windows or Linux machine, where the MT5 terminal
  and account remain under the operator's control.
- Detects the operating system and reports integration prerequisites and
  connector health.
- Sends account snapshots, quotes, symbol metadata, and later approved commands
  to the platform over an outbound connection. The platform must not require
  the broker password.
- Begin read-only. Keep platform account data and the connector's local MT5
  access distinct; never expose terminal credentials to the web dashboard.

The Windows integration and Linux/Wine integration must be validated
separately. Linux may require an MT5 Expert Advisor (EA) bridge; support,
packaging, and broker compatibility are not yet established. Do not describe
Linux MT5 support as ready until it has been tested.

### Persistence and audit

- MongoDB is the selected target datastore to match the FYP proposal. The
  current PostgreSQL/SQLite implementation remains in place until the MongoDB
  persistence path and history transition are designed, tested, and documented.
- Preserve the existing PostgreSQL and SQLite databases during the transition;
  take verified backups and document restore procedures before any data copy.
- Design records for ownership from the start, including account links,
  preferences, recommendations, commands, paper trades, and audit events.
- Enforce ownership in backend service queries and commands, not only through
  frontend filtering.
- Defer sign-in implementation, but do not expose a multi-user service without
  authentication and authorization.

## 4. Operating modes and safety boundaries

| Mode | Behavior | Initial availability |
|------|----------|----------------------|
| Analysis | Analyze configured pairs and show results; no position is opened. | Current prototype, one pair |
| Recommendation | Produce expiring trade proposals for operator review; no broker order is sent. | Planned |
| Paper automation | Automatically open and manage positions in the internal paper ledger. | Planned |
| Demo automation | A local connector may execute explicitly authorized commands on a verified demo account. | Later phase; not current behavior |
| Live automation | Send orders to a real-money account. | Out of scope for the FYP plan unless separately reviewed and approved |

Demo mode must fail closed when account type cannot be established. Demo/live
classification varies by broker and must be validated against supported
terminals. A connector-side check is defense in depth, not a guarantee. Before
enabling demo execution, require command expiry, idempotency, strict parameter
validation, order reconciliation, audit records, pause/revoke controls, and
failure testing. The default and fallback behavior must never silently switch
from paper to broker execution.

## 5. Core data flow

1. The connector or an explicitly selected development data adapter supplies
   timestamped market data. The API identifies its source and freshness.
2. Each enabled pair agent evaluates its own pair and emits a structured
   candidate or a no-trade result.
3. The master coordinator filters candidates and applies portfolio-level risk
   rules.
4. The recommendation service validates sizing and levels, assigns an expiry,
   and persists the result and decision rationale.
5. The chosen operating mode determines the next step:
   - Analysis: display results only.
   - Recommendation: wait for operator review; reject acceptance after expiry.
   - Paper automation: execute against the paper ledger.
   - Demo automation: after all safety gates are satisfied, issue an
     idempotent, expiring command to the paired connector and reconcile the
     broker result.
6. Persist outcomes and audit events, then calculate performance separately
   for broker activity and simulated activity.

## 6. Technology and deployment direction

| Area | Direction |
|------|-----------|
| Frontend | Keep the existing React/Vite dashboard. |
| API and analysis | Keep Python; retain Flask initially unless measured needs justify a change. |
| Database | MongoDB for the FYP target, matching the proposal. Current local code still uses SQLAlchemy with PostgreSQL/SQLite; migration work is pending. |
| Local development | Continue running locally; provide reproducible setup instructions. |
| MT5 access | User-run connector; read-only first. Evaluate Windows integration and Linux/EA bridge independently. |
| Cloud | AWS is a later deployment target, after local workflows, security boundaries, and operational requirements are proven. |
| Authentication | Deferred for early local development; mandatory before exposing user data or remote connector pairing to a network. |

No additional database, cloud services, queues, or cache should be introduced
until a concrete requirement warrants them. MongoDB is the selected replacement
for the current relational persistence, not an additional parallel datastore.

## 7. Delivery milestones

The following order captures current planning. Week estimates are indicative;
integration findings may change scope or duration. Documentation is part of
every milestone, not a final-only task.

1. **Foundation and cleanup** — define production vs. development adapters,
   align persistence with the proposal by designing and implementing MongoDB,
   safely retain/transition existing relational history, design
   ownership-ready records, add audit foundations, and document setup,
   architecture, data model, backups, and decisions.
2. **Recommendation workflow** — implement configurable sizing, risk checks,
   SL/TP, rationale, expiry, and review actions; document formulas, contracts,
   configuration, and operator workflow.
3. **Read-only connector** — prototype Windows and Linux integration, pairing
   design, account/quote/symbol snapshots, and health reporting; document
   prerequisites, data flow, supported environments, and troubleshooting.
4. **Persistent paper trading** — implement the ledger and cost assumptions;
   document calculations, metric definitions, and limitations.
5. **Demo automation safety** — only after connector and paper workflows are
   tested, implement demo-only commands, validation, idempotency, expiry,
   reconciliation, emergency controls, and audit; document procedures and
   test evidence.
6. **Multi-pair agents and master coordination** — evaluate pair strategies,
   coordinator behavior, and portfolio risk in paper mode; document selection
   methodology and results.
7. **Evaluation and FYP delivery** — failure/security testing, performance
   analysis, limitations, final setup/API/user/operator documentation, and
   presentation materials.

Authentication, AWS deployment, and live-money execution are not prerequisites
for the initial local research milestones. Authentication and authorization
are prerequisites for any later multi-user network deployment.

## 8. Decisions to resolve before implementation reaches them

- What risk controls are user-adjustable, and what hard platform limits apply?
- Which SL/TP methods and sizing modes are in the first recommendation release?
- Which timeframes, data source, and data-quality/freshness thresholds are
  supported per pair?
- How will pair models and strategies be compared (baseline, costs, validation
  windows, and acceptance criteria)?
- Which Windows MT5 versions/brokers and Linux/Wine/EA combinations will be
  supported and tested?
- How will demo-account status be established for each supported broker, and
  what happens when it is unknown?
- Which pairing protocol, command transport, and local secret-storage
  mechanisms are appropriate before remote connector implementation?
- When authentication is introduced, what identity provider and authorization
  model will be used?
- What operational, privacy, retention, and recovery requirements apply before
  AWS deployment?

Record resolved decisions with rationale and update this document and
milestone-specific setup/API/user documentation as the design evolves.
