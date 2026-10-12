---
name: test-preflight
description: use before any spend, to write a test plan that can actually be read later: one question, one variable, owner-set cap and end rule, and a working path from a sale back to an ad.
stage: 7 of 11
reads: campaigns/cNN-name/production.md, business.md
writes: tests/tNN-name/plan.md
---

# test preflight

a test is only worth running if its result can be read. this stage is the gate between a
built campaign and spent money.

## inputs

- `campaigns/cNN-name/production.md` with every check filled, passed and dated
- `business.md` with platform, account name, account id, currency, timezone and
  `ad_to_sale_link` filled

## outputs

- `tests/tNN-short-name/plan.md`, plus empty `data/` and `readings/` folders

## steps

1. stop if any check list blank is empty or records a failure, if any required brief
   field says MISSING, or if `ad_to_sale_link` says `not set up`.
2. create the next unused test folder. never reuse one.
3. write the question in one sentence, naming the one variable under test.
4. copy the identity block from the brief verbatim: platform, account name, account id,
   currency, timezone, attribution window. a later reading will compare these against the
   export and refuse to continue if they disagree.
5. record how a sale reaches an ad: tag carrying the ad id, a code per version, or a form
   field. if only the platform's own count will exist, write that down as a limit of the
   test before it runs.
6. leave the cap, the end rule, and the definition of a clear answer as MISSING for the
   owner. never suggest a budget, a daily split, or how many results are needed.
7. set the wait period from `usual_days_to_purchase`, and say that no verdict may be
   called before it passes.
8. leave a launch record for the owner: launch date, the ad id of every version, and any
   change made after launch.

## stop conditions

- the agent never sets the cap, the end rule, or the success bar. those three are the
  owner's, decided before numbers exist.
- no universal thresholds. there is no default acceptable cost per result, no default
  sample size, and no default kill rule in this kit.
- stop if two variables differ between versions. send it back to `campaign-build`.
- the owner launches. nothing in this workspace launches, pauses or edits an ad.

## worked mini-example

the plan asks which opening line brings in more paying customers for the same spend.
three ad ids are recorded at launch. the owner sets a 900 cap, an end date two weeks out,
and a clear-answer rule that needs two full weeks of mature data with unchanged tracking.
the wait period is 14 days, rounded up by the owner from a 9 day usual purchase time. the
plan's identity block names one account id, which the reading stage will later check
against the export header.

## hands off to

`autoady-read` for pulling numbers, or a plain export into `tests/tNN-name/data/`.
