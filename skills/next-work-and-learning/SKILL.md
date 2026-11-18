---
name: next-work-and-learning
description: use at the end of a cycle, to turn readings into proposals the owner can approve or reject and to queue the next single piece of work.
stage: 11 of 11
reads: tests/tNN-name/readings/, proposals/proposals.md, learnings/learnings.md
writes: proposals/proposals.md, output/YYYY-MM-DD-next-work.md
---

# next work and approved learning

a reading describes one window. a learning claims something about the business. this
stage keeps the gap between those two honest, and decides what gets built next.

## inputs

- the readings written in this cycle, or new entries in `sources/customer-words.md`
- `proposals/proposals.md` and `learnings/learnings.md`

## outputs

- new entries appended to `proposals/proposals.md`
- `output/YYYY-MM-DD-next-work.md` naming the one next piece of work

## steps

1. read the newest readings and the existing learnings. never edit `learnings.md` or
   `business.md` in this stage.
2. for each candidate lesson, append a proposal: the lesson in one plain sentence, the
   evidence with paths and numbers, how strong it is, what it applies to, what would
   change your mind, and whether it conflicts with an approved fact.
3. from a NOT MATURE or INCONCLUSIVE reading, propose only "we do not know yet" notes,
   with what would need to happen to know.
4. mark a single result as tentative and say what would have to repeat before it is used
   more widely.
5. do not repeat anything already in proposals or learnings.
6. choose the next piece of work and write why: usually either the next one-variable test
   from the parked ideas in `campaign-build`, a fix to a fact problem raised by
   `buyer-evidence`, or more evidence collection when the last cycle ran thin.
7. write the owner's queue plainly: what they approve, what they fix, what they launch.
8. the owner moves an APPROVED proposal into `learnings.md` themselves, or approves the
   exact entry in an interactive session.

## stop conditions

- the agent never writes into `learnings.md`.
- never promote a lesson from a reading whose verdict was NOT MATURE or INCONCLUSIVE.
- never widen a lesson past the offer and buyer it was observed on, unless the evidence
  itself covers more.
- if a proposal contradicts an approved fact, say which file and which line, and leave
  the resolution to the owner. do not fix the brief silently.

## worked mini-example

the cycle's only reading is NOT MATURE. two proposals are appended. the first is a
not-yet note: the platform-result leader and the linked-customer leader disagree, so a
further week of mature data is needed before either is believed. the second is a fact
problem: two quotes describe a price the brief does not charge, naming
`price_and_terms`. the next-work file picks one job, re-reading the same test after the
wait period, and lists two owner actions: resolve the price confusion, and confirm
tracking is still firing. no learning is written, because nothing earned one yet.

## closes the loop to

`business-brief`, when an approved learning or a fact problem changes the brief.
