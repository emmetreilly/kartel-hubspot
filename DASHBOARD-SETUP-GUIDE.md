# Kartel Sales Dashboards

Focus: **Close the first enterprise deal.**

Create at: https://app-na2.hubspot.com/reports-dashboard/242991070

---

## 1. CRO Dashboard (Ben)

**Purpose:** Execute the 30-day sales cycle. Close deals.

### Create Dashboard
- Name: `Sales Command`
- Access: Private

### Reports:

#### 1.1 Pipeline by Stage
Where's the money in the 30-day cycle?
- Type: **Horizontal bar chart**
- Filter: Pipeline = Enterprise (1880222397), NOT closed
- X-axis: SUM of Amount
- Y-axis: Deal Stage (Discovery → Product Scope → Budget Scope → Proposal → Negotiation → Procurement)

#### 1.2 Active Deals Table
Your working list
- Type: **Table**
- Filter: Pipeline = Enterprise, NOT closed
- Columns: Deal Name, Amount, Stage, Next Step, Next Activity Date, Owner
- Sort: Amount (descending)

#### 1.3 Spec Status
Proving capability to win champions
- Type: **Table**
- Filter: Pipeline = Enterprise, Stage IN (Product Scope, Budget Scope), spec_required IS KNOWN
- Columns: Deal Name, Amount, Stage, spec_required, Owner
- Sort: Amount (descending)

#### 1.4 Stalled (7+ Days No Activity)
What's going cold?
- Type: **Table**
- Filter: Pipeline = Enterprise, NOT closed, Last Activity > 7 days ago
- Columns: Deal Name, Amount, Stage, Last Activity Date, Owner
- Sort: Last Activity (oldest first)

#### 1.5 Closing This Month
Target list
- Type: **Table**
- Filter: Close Date = This month, Pipeline = Enterprise, NOT closed
- Columns: Deal Name, Amount, Stage, Close Date, Owner
- Total: SUM of Amount

#### 1.6 Procurement Queue
Deals waiting on signature
- Type: **Table**
- Filter: Pipeline = Enterprise, Stage = Procurement
- Columns: Deal Name, Amount, days_in_procurement, Owner, Next Step

---

## 2. CEO Dashboard (Kevin)

**Purpose:** Pipeline health. Are we going to close?

### Create Dashboard
- Name: `Pipeline Health`
- Access: Private

### Reports:

#### 2.1 Total Active Pipeline
Single number - what's in play
- Type: **Single value**
- Filter: Pipeline IN (Enterprise, SMB), NOT closed
- Measure: SUM of Amount

#### 2.2 Enterprise Funnel
Deal flow through stages
- Type: **Funnel**
- Filter: Pipeline = Enterprise, NOT closed
- Breakdown: Stage
- Measure: SUM of Amount

#### 2.3 Top 5 Deals
Biggest opportunities
- Type: **Table**
- Filter: Pipeline = Enterprise, NOT closed
- Columns: Deal Name, Amount, Stage, Owner, Next Step
- Sort: Amount (descending)
- Limit: 5

#### 2.4 Pipeline by Owner
Who's carrying what
- Type: **Horizontal bar chart**
- Filter: Pipeline IN (Enterprise, SMB), NOT closed
- X-axis: SUM of Amount
- Y-axis: Owner

#### 2.5 Deals at Risk
Big deals going cold
- Type: **Table**
- Filter: Pipeline = Enterprise, NOT closed, Amount > 100000, Last Activity > 14 days
- Columns: Deal Name, Amount, Stage, Last Activity Date, Owner

#### 2.6 Win Rate (Last 90 Days)
- Type: **Single value**
- Filter: Close Date = Last 90 days
- Calculation: Closed Won / (Closed Won + Closed Lost)

---

## Your 30-Day Sales Cycle

| Day | Call | Goal | Exit With |
|-----|------|------|-----------|
| 0 | Intro/Qualification | Qualify, ID decision maker | MSA sent |
| 3-7 | Product Scope | "What will it take to win" | RFP/discovery answers |
| 14-21 | Budget Scope | Current spend, budget alignment | Info to craft proposal |
| 21-30 | Proposal | Present, confirm nothing out of range | **Signed SOW** |

---

## Pipeline IDs
- Enterprise: `1880222397`
- SMB: `1880222398`

## Key Properties
- `spec_required`: yes / no / in_progress / delivered
- `days_in_procurement`: Days waiting on signature
- `hs_next_step`: What's the next action

---

## Setup Checklist

### CRO (Ben)
- [ ] Pipeline by Stage (bar)
- [ ] Active Deals Table
- [ ] Spec Status (table)
- [ ] Stalled Deals (table)
- [ ] Closing This Month (table)
- [ ] Procurement Queue (table)

### CEO (Kevin)
- [ ] Total Pipeline (single value)
- [ ] Enterprise Funnel
- [ ] Top 5 Deals (table)
- [ ] Pipeline by Owner (bar)
- [ ] Deals at Risk (table)
- [ ] Win Rate (single value)
