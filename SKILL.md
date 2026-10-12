---
name: marketing-os
description: use to run marketing for one offer as a connected sequence instead of one-off prompts. collects a business brief, grounds copy in real customer words, builds matching ads and pages, gates every test and every external change, then reconciles platform numbers against the sales record before anything is called a win.
stage: coordinator
reads: business.md, operating-rules.md, sources/, campaigns/, tests/, learnings/
writes: output/, proposals/, campaigns/, tests/
---

# marketing os

this file is enough to start on its own. the repository it came from has one skill per
stage with the detail, but the sequence below is the thing that matters, and it works
read top to bottom.

## what it is for

ai will happily write you an ad, then a page, then an email, and leave you holding the
part that actually decides results: making them agree, remembering the offer, and knowing
which sale came from which ad. this moves that job into a sequence with files between the
steps.

## the brief

everything downstream reads one file. write MISSING rather than a guess, every time.

- offer name
- what the buyer gets, exactly
- price and payment terms
- guarantee or refund wording, word for word, or none
- the one action you want: buy, book, fill in a form
- where they act, on a page you control
- the buyer in one plain sentence, and who this is not for
- usual days from first visit to purchase
- claims you must never make
- existing assets and the tools you build in
- ad platform, ad account name, ad account id, currency, timezone
- the system that records sales, and how a sale links back to one ad
- attribution window you will use in reports
- the approved message, once it is chosen

no passwords, keys or tokens in that file, ever. names and ids only.

## the sequence

each step needs the step before it and sets up the one after. that is the only reason
there are eleven of them rather than eleven interchangeable prompts.

1. `business-brief` - one offer, one buyer, approved by you
2. `buyer-evidence` - real quotes with ids, permissions and conversation counts
3. `message-choice` - two or three options from those quotes, you pick one
4. `campaign-build` - ads and a page that repeat the chosen promise, one variable apart
5. `production-handoff` - build sheet plus the check list that gates spend
6. `content-reuse` - posts and the follow-up email from the same claim table
7. `test-preflight` - one question, your cap, your end rule, a sale traceable to an ad
8. `autoady-read` - read live meta numbers with explicit account and explicit window
9. `autoady-change-proposal` - exact payload, your approval, paused first, then readback
10. `performance-reconciliation` - platform results beside sales records, never blended
11. `next-work-and-learning` - proposals you approve or reject, and the one next job

## rules that hold across all of it

- approved files change only when you say so, in session. everything the agent thinks up
  goes to proposals.
- a missing input stops that step and every step depending on it. no guessing.
- every claim traces to a brief field, a quote id, or an approved learning.
- platform-reported results and money that arrived are two different measurements. they
  are never added together.
- zero linked customers means no observed cost per customer. it never means zero.
- there are no default thresholds here: no acceptable cost per result, no sample size, no
  kill rule. you set those before you see numbers.
- a rule written in a file is not a sandbox. if a run must not write, run it where the
  write tools are not connected.

## miniature worked example

a solo bookkeeper sells one offer: twelve months of books caught up, 240 once, full
refund if the year cannot be caught up. thirty-one quotes come in; twenty-two unique
conversations say the same thing, which becomes the promise "you will know what you owe
before the deadline, not after it". three ads differ only in the opening line, and the
page headline repeats that promise almost word for word.

two weeks later the platform reports 19 results for one ad at 21.47 each and 14 for
another at 29.46 each. the sales record links two new paying customers to the second ad at
206.25 each and one to the first at 408.00. one refund, one repeat purchase and one sale
with no ad id are each reported on their own line.

so the cheaper platform result and the cheaper customer are different ads, and only two
days have passed against a fourteen day wait. the verdict is NOT MATURE, nothing is paused
or scaled, and the next job is to read the same test again after the wait. that is the
output you should expect from this system: a smaller, defensible answer instead of a
confident wrong one.

## the fuller repository

the full kit adds a command line tool that creates and checks a private workspace, a
runnable fictional demo of the reading above, an installer, and one skill file per stage.
see `README.md` and `docs/START-HERE.md`.
