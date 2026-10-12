---
name: message-choice
description: use after buyer evidence exists, to turn quotes into two or three message options the owner can choose between, then record the chosen promise.
stage: 3 of 11
reads: business.md, sources/customer-words.md, learnings/learnings.md
writes: output/message-options-YYYY-MM-DD.md, business.md approved_message
---

# message choice

the stage that converts evidence into one sentence everything else repeats. the agent
proposes options; the owner chooses. that split is the whole point.

## inputs

- approved `business.md`
- `sources/customer-words.md` with entries
- `learnings/learnings.md`

## outputs

- `output/message-options-YYYY-MM-DD.md`
- after the owner chooses: `approved_message` filled in `business.md`, with the options
  file named as its source

## steps

1. stop unless `what_the_buyer_gets`, `price_and_terms` and `primary_action` are all
   filled, and at least one quote entry exists.
2. read every entry, including the ones that disagree with the offer.
3. group quote ids under problems, wanted outcomes, worries, repeated phrasings. count
   unique conversations. note whether each group comes from buyers or non-buyers, because
   a non-buyer's wish is not evidence the offer delivers.
4. write two or three options. each option carries: the promise in one sentence in buyer
   words, the supporting quote ids, the single fact from `business.md` that makes it true,
   what it cannot prove yet, and the worry it has to answer.
5. say which option has the most direct support and why, in one paragraph. do not choose.
6. list contradictions between quotes and the brief as fact problems.
7. when the owner picks one, write it into `approved_message` word for word, in the same
   interactive session, and record the options file path and the date.

## stop conditions

- stop if there are no quote entries. this stage cannot run on the owner's own words.
- do not write `approved_message` without the owner naming an option number in session.
- an option with no quote ids behind it does not go in the file, however good it sounds.
- never quietly rewrite an approved message. propose the change instead.

## worked mini-example

three options come out. option 1, "you will know what you owe before the deadline, not
after it", carries four quote ids and rests on `what_the_buyer_gets`. option 2 is about
peace of mind and carries one quote. option 3 promises a smaller bill and is removed
during step 6, because `claims_we_must_never_make` forbids any claim about tax savings.
the file says option 1 has the most direct support. the owner picks it, and that exact
sentence becomes the headline the page has to repeat two stages later.

## hands off to

`campaign-build`, which copies the approved message verbatim.
