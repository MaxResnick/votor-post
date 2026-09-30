---
title: From Alpenglow to Dispersed C-Simplex
subtitle:
author: Max Resnick
author_url: https://anza.xyz
date: September 1, 2026
---

# Option 1 · Straight from Alpenglow to MinCP

The shortest route to multiple concurrent proposers is to leave Alpenglow alone and let P validators propose in every slot. Each block still replays against the parent, validators still cast one first-round vote, and since no single block can trigger it any more, the vote waits for the 2Δ deadline and goes out on a vector B of whatever arrived by then. The edit is a handful of lines.

@figure option1: The naive edit. The highlighted lines are the whole change.

It is a straw man. Three things go wrong, and each one points at a change the rest of this post makes on purpose.

1. **When does the first round of votes go out?** Alpenglow's vote fires on an event, `Block(s, b)`, so a slot is as fast as its block. With P proposers the honest analogue is line 16: vote as soon as a valid block from every proposer has replayed, and otherwise fall back to the deadline on line 21. Two things are lost. The early vote needs all P blocks, so the slot is as slow as its slowest proposer, and one proposer who is offline, or who simply sits the slot out, drops every validator to the full 2Δ, a price Alpenglow only paid when its single leader was late. And `T_s` is a local timer that each validator started at its own `ParentReady`, so that deadline is a different wall-clock instant everywhere: a block that beats my timer and misses yours puts different vectors in our two votes, in an ordinary slot with honest proposers. MinCP votes at a global time instead, 3sΔ+Δ, which every validator reads the same way. That clock only exists once the view schedule is fixed (Step 3), and the vote can only be cheap at that time if it is on the first shred of the block's final FEC set, whose delivery is what 3sΔ+Δ bounds (Step 2).
2. **Merging proposals that are entire blocks.** An Alpenglow vote asserts that the block executed correctly on top of its parent. Each of the P blocks does, on its own. The ledger has to contain their union in some order, and nobody has executed that merged sequence before voting: transactions collide on accounts, fee payers that covered one block cannot cover both, duplicate signatures and nonces appear across blocks. Replaying the merge before voting needs all P blocks in hand, which is problem 1 again. Voting without it means the vote no longer says what it used to. MinCP takes the second horn deliberately, finalizing the vector and executing the priority-order merge afterwards, which is only safe once execution is asynchronous (Step 4) and finality is gated on "reconstructed and valid" rather than "executed".
3. **The fallback path and rational proposers.** Alpenglow's fallback votes on lines 30 to 41 exist for the rare case that Notarize votes split. With P proposers a split is the normal case: every block that lands between two validators' deadlines produces two vectors, so the 40% and 20%+60% triggers fire in ordinary slots and finalization drops to the slow path. Worse, a proposer whose block is about to be left out of the vector can cause the split on purpose by releasing right at the deadline, and every slot now has P parties with that option. MinCP has no such lever: the vote fires at 3sΔ+Δ regardless, a late block is simply absent from everyone's vector, and the only fallback left is a single `SkipFallback` at a fixed time.

The rest of this post is Option 2: the same destination, one change at a time, with each intermediate protocol safe on its own.

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

# What the scheduler changes

@figure sched-ordering: Where transactions land against where they were sent, for four schedulers. A point on the diagonal landed in send order; shade is the priority-fee percentile.

@figure sched-oracle: Oracle-update win rate by scheduler, overall (A) and broken out by prop-AMM (B).

@figure sched-markout: Cumulative 5-second maker markout per 1M SOL of stake, by scheduler, for six prop-AMMs.

@figure sched-buysell: Three-day moving average of 0-second markouts on buys (positive) and sells (negative), in basis points, by scheduler and prop-AMM.

@figure sched-volume: Prop-AMM USDC volume per slot by scheduler, 24-hour rolling.

@figure sched-transitions: What changes when a leader window hands from the row scheduler to the column scheduler: trade probability, prop-AMM volume, oracle-update count and cost, and 5-second and 30-second maker markout.
