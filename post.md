---
title: From Alpenglow to Dispersed C-Simplex
subtitle:
author: Max Resnick
author_url: https://anza.xyz
date: September 1, 2026
---

# What the scheduler changes

@figure sched-ordering: Where transactions land against where they were sent, for four schedulers. A point on the diagonal landed in send order; shade is the priority-fee percentile.

@figure sched-oracle: Oracle-update win rate by scheduler, overall (A) and broken out by prop-AMM (B).

@figure sched-markout: Cumulative 5-second maker markout per 1M SOL of stake, by scheduler, for six prop-AMMs.

@figure sched-buysell: Three-day moving average of 0-second markouts on buys (positive) and sells (negative), in basis points, by scheduler and prop-AMM.

@figure sched-volume: Prop-AMM USDC volume per slot by scheduler, 24-hour rolling.

@figure sched-transitions: What changes when a leader window hands from the row scheduler to the column scheduler: trade probability, prop-AMM volume, oracle-update count and cost, and 5-second and 30-second maker markout.


# Option 1 · Straight from Alpenglow to MinCP

@figure option1: Alpenglow with P proposers per slot. The highlighted lines are the whole change.

1. When does the first round of votes actually get sent?
2. How are the proposals merged when each one is an entire block?
3. What happens to Alpenglow's fallback path once rational proposers can trigger it?

# Step 1 · Alpenglow → C-Simplex RVS

@figure step1:

## Is the fast path actually fast?

@figure fast-map:

@figure path-heatmap:

# Step 2 · Dispersed C-Simplex

@figure step2:

@figure disp-heatmap:

# Step 3 · The fixed view schedule

@figure step3:

# Step 4 · Asynchronous execution

@figure step4:

# Step 5 · Dispersed C-Simplex FVS → MinCP

@figure step5:
