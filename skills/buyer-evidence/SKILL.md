---
name: buyer-evidence
description: use after the business brief is approved, to collect and index real customer words so later copy quotes evidence instead of invention.
stage: 2 of 11
reads: business.md, sources/customer-words.md
writes: sources/customer-words.md, output/evidence-index-YYYY-MM-DD.md
---

# buyer evidence

the brief says who the buyer is in the owner's words. this stage collects the buyer's own
words, because those are the ones the next buyer will recognise.

## inputs

- approved `business.md`
- whatever raw sources the owner can reach: reviews, email replies, support questions,
  call notes, survey answers, comments, direct messages, refund reasons

## outputs

- new entries at the bottom of `sources/customer-words.md`, one id each
- `output/evidence-index-YYYY-MM-DD.md`: counts by theme, with quote ids only

## steps

1. read `business.md`. if its status line is not approved, stop.
2. collect verbatim. paste exact words, including typos, swearing and tangents. do not
   summarise: a summary replaces the customer's words with yours.
3. strip names, emails, phone numbers and anything else identifying before pasting.
4. include people who did not buy and people who refunded. their reasons are the worries
   your ads will have to answer, and nothing else in the workspace carries them.
5. give every entry a `conversation_id` so one long thread is never counted as five
   customers.
6. record `public_use_permission` per entry. `no` and `unknown` are research only and may
   never appear in public copy.
7. tag each entry: pain, tried-and-failed, wanted-outcome, objection, wrong-belief,
   phrasing.
8. write the index: for each theme, the unique conversation count and the quote ids.
   count conversations, not mentions. say plainly that the counts describe this collected
   sample and nothing wider.
9. list every quote that contradicts a fact in `business.md` as a possible fact problem,
   naming the field.

## stop conditions

- stop if `business.md` is not approved.
- stop before writing copy if the only available words are the owner's. go collect first.
- never edit or delete an existing entry. append only.
- never put a quote with `public_use_permission: no` into anything public-facing.

## worked mini-example

thirty-one entries come in from reviews and email replies. twenty-two unique
conversations mention not knowing what is owed; nine mention an abandoned spreadsheet;
four mention a fine. two quotes say the price is 180, which the brief says is 240. the
index reports 22 of 31 conversations on the first theme and flags the price contradiction
against `price_and_terms` as a fact problem to resolve before any spend.

## hands off to

`message-choice`, which may only use quote ids that exist here.
