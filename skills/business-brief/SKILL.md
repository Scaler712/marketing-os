---
name: business-brief
description: use when starting a marketing-os cycle or when any later stage stops on a missing fact. interviews the owner and fills the one brief every later stage reads.
stage: 1 of 11
reads: operating-rules.md
writes: business.md
---

# business brief

the first stage. nothing downstream is allowed to run on guesses, so this stage either
produces an owner-approved brief or a written list of what is still missing.

## inputs

- `operating-rules.md` in the workspace
- the owner, in an interactive session (this stage never runs on a schedule)

## outputs

- `business.md` with every machine field filled or explicitly marked MISSING
- a run note in `output/runs/YYYY-MM-DD-business-brief.md`

## steps

1. read `operating-rules.md` and then `business.md`. if the status line already says
   `Approved by owner on`, do not edit anything: report what would change and stop.
2. check the one-offer rule before asking anything else. one offer, one buyer. if the
   owner names a catalogue, ask which single offer already has paying buyers and park
   the rest in `proposals/proposals.md`.
3. interview one question at a time, in the field order of `business.md`. save answers
   in the owner's words, not tidied.
4. when the owner does not know, write MISSING. never offer a plausible value as a fact.
5. never ask for a password, key, token or login link. if one is pasted, say so, do not
   save it, and tell the owner to rotate it.
6. three fields decide whether later stages can run at all, so confirm them out loud:
   `primary_action`, `ad_to_sale_link` and `usual_days_to_purchase`.
7. show the whole file back. tell the owner to read every line and set the status line
   themselves. the status line is their signature, not yours.

## stop conditions

- stop and hand back if the owner cannot say what the buyer gets and what it costs in
  one plain sentence. there is no message to find yet.
- stop if the offer has no buyers at all. a brand new offer gives the next stage nothing
  real to learn from, and the only honest output would be your own guesses.
- stop if there is no page or form the owner controls where a buyer can act.
- never set the status line yourself.

## checks before handing off

- `marketing_os.py doctor --workspace <path>` returns READY
- `ad_to_sale_link` is not `not set up`, or the owner has accepted that cost per customer
  will be unavailable later

## worked mini-example

a solo bookkeeper says the offer is "catch-up bookkeeping, 240 once, refund if we cannot
catch up your year" and the buyer is "freelancers who have not touched their books since
last spring". asked how a sale would be traced back to an ad, they say they do not know.
the brief is written with `ad_to_sale_link: MISSING`, the interview continues, and the run
note says: cost per customer cannot be computed until the store saves the ad id with the
order, owner to set up. buyer evidence can still start. test preflight cannot.

## hands off to

`buyer-evidence`, which only runs once this brief is approved.
