---
name: content-reuse
description: use after a campaign pack exists, to generate organic posts and the follow-up email from the same approved promise so paid and organic do not drift apart.
stage: 6 of 11
reads: campaigns/cNN-name/pack.md, business.md, learnings/learnings.md
writes: output/YYYY-MM-DD-content.md
---

# content reuse and follow-up

the cheapest content is the pack you already approved, said again in places where nobody
is being sold to. this stage keeps that reuse tied to the same promise and the same claim
table.

## inputs

- `campaigns/cNN-name/pack.md`
- `business.md` and `learnings/learnings.md`

## outputs

- `output/YYYY-MM-DD-content.md` holding the posts and the follow-up email, each with its
  claim sources listed underneath

## steps

1. read the pack's claim table first. this stage may only use claims already in it.
2. write the posts the pack asked for, about the same problem and promise, without hard
   selling. one idea per post, in buyer words, each traceable to a quote id.
3. under each post, list the sources: quote ids, brief fields, learning ids.
4. write the follow-up for people who acted but did not buy: repeat the promise, answer
   the biggest worry using the guarantee wording exactly as the brief has it, one link
   back, no new claim. if the offer has no follow-up step, say so instead of inventing a
   sequence.
5. check the last seven days of `output/` and do not repeat a post already drafted.
6. note which posts are for the owner to publish. nothing in this workspace publishes.

## stop conditions

- stop if the pack is not approved: organic copy built on an unapproved promise will
  contradict the ads that eventually run.
- no claim that is not in the claim table, even a modest one.
- no quote with permission `no` or `unknown` appears in a public post.
- never state or imply a result the offer does not guarantee.

## worked mini-example

three posts come out: the three-days-before-the-deadline moment, why the spreadsheet dies
in march, and what "caught up" actually means step by step. the first two carry quote ids
Q007 and Q011. a fourth draft post said "most of our clients save money" and is cut at
step 2, because no row in the claim table supports it and the brief forbids claims about
savings. the follow-up email reuses the refund wording character for character.

## hands off to

`test-preflight`, and later `next-work-and-learning`, which reads what these posts earned.
