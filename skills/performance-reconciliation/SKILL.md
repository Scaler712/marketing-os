---
name: performance-reconciliation
description: use when a test has ended and exports exist, to reconcile platform-reported results against the sales record with exact arithmetic, honest unknowns, and a verdict that may be inconclusive.
stage: 10 of 11
reads: tests/tNN-name/plan.md, tests/tNN-name/data/
writes: tests/tNN-name/readings/YYYY-MM-DD.md
---

# performance and crm reconciliation

two sets of numbers arrive and they will not agree. both can be honest. this stage keeps
them apart and says what is actually known.

## inputs

- `tests/tNN-name/plan.md` with the launch record filled
- at least one ad export and one sales export in `tests/tNN-name/data/`

## outputs

- `tests/tNN-name/readings/YYYY-MM-DD.md`, never overwritten, `-2` on collision

## steps

1. confirm identity before arithmetic: the export's account id, currency, timezone and
   attribution window against the plan, and the sales system id against the brief. a
   sales system id does not have to equal the ad account id, but an unexplained
   difference stops the reading.
2. run the arithmetic with the bundled tool rather than by hand. it uses exact decimal
   division and refuses to divide by zero:

```bash
python3 scripts/marketing_os.py demo --workspace /absolute/path/to/your/workspace
```

   the demo runs the same code paths over bundled fictional data, so you can see the shape
   of a reading before trusting one of your own.
3. write a platform-reported section per ad id: spend, impressions, clicks, and the
   platform's own result count with its action type. never call these sales.
4. write a sales-records section: only sales whose record carries an ad id or code from
   this test. deduplicate overlapping exports by order id. separate new customers from
   repeat ones, and report refunds and unlinked sales on their own lines.
5. maturity check: if fewer days have passed since the end than the plan's wait period,
   the reading is NOT MATURE and no comparison between versions is allowed to conclude.
6. cost per new paying customer per version: test spend divided by unique linked new
   paying customers. with zero linked customers write "no observed cost per customer yet"
   and report the spend. missing linkage is unknown, never zero.
7. compare versions only over matching date ranges and the same attribution window.
8. if results dropped, list what to check before naming a cause: is tracking still
   firing, did traffic or audience change, did the page break or change, did the offer or
   price change.
9. verdict: CLEAR, LEANING, INCONCLUSIVE or NOT MATURE, judged only against what the plan
   said would count, with one sentence of why.

## stop conditions

- never add platform results to sales records.
- never count one order twice because two exports overlap, and never count two reported
  action types that describe the same event.
- a sale on the same day as a click is not linked unless the record carries the id.
- a malformed row is reported and excluded, never repaired by guesswork.
- stop if the exports mix currencies or accounts.

## worked mini-example

three ads, 842.90 spent, one currency. the platform reports 19 results for the shoebox ad
at 21.47 each and 14 for the surprise-bill ad at 29.46 each, so the shoebox ad leads there.
the sales record links two new paying customers to the surprise-bill ad at 206.25 each and
one to the shoebox ad at 408.00. one refund and one repeat purchase are reported
separately, one sale carries no ad id and is recorded as unknown origin, a duplicated
order row is dropped once, and one malformed amount is excluded and named. the two leaders
disagree, only two days have passed against a 14 day wait, and the verdict is NOT MATURE.
no ad is paused or scaled on this reading.

## hands off to

`next-work-and-learning`.
