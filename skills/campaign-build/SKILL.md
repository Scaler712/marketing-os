---
name: campaign-build
description: use after a message is approved, to write one campaign pack whose ads, landing page, and claim table all agree and differ in exactly one variable.
stage: 4 of 11
reads: business.md, sources/customer-words.md, learnings/learnings.md
writes: campaigns/cNN-name/pack.md
---

# campaign build

one pack, built from one promise: the ads, the page copy, and a claim table that ties
every factual sentence to a source.

## inputs

- `business.md` approved, with `approved_message` filled
- `sources/customer-words.md`
- `learnings/learnings.md`

## outputs

- `campaigns/cNN-short-name/pack.md`, where NN is the next unused number

## steps

1. stop if `approved_message` is MISSING, or if any field this pack needs says MISSING.
2. pick the next unused campaign folder. never write into an existing one.
3. header: date, files read, the core promise copied word for word, and a blank
   `Approved by owner on` line.
4. claim table first, before any copy. every factual claim, with its source: a
   `business.md` field, a quote id, or a learning id. a claim with no source is cut, not
   softened.
5. the one difference: name the single variable that changes between ad versions, and
   list what stays identical - offer, price, page, audience, image style. one variable
   only, or the test two stages later cannot be read.
6. write two or three ad versions: primary text, headline, description, and a plain
   description of the image or video built from assets the brief says already exist.
7. write the landing page section by section: headline repeating the ad promise in nearly
   the same words, the problem in buyer words, what they get exactly as written in the
   brief, proof, the biggest worry and its answer, price and terms word for word, one
   button with one action.
8. check message match by reading the ad headline and the page headline side by side. if
   a clicker could wonder whether they are in the right place, rewrite the page headline.
9. list open questions for the owner at the end.

## stop conditions

- stop if the same pack would need two offers or two buyers. split it.
- cut any number, result or testimonial that is not in the claim table.
- do not use a quote publicly unless its entry records permission.
- do not change more than one variable between versions, even when a second change looks
  obviously better. put that second idea in `proposals/proposals.md` as the next test.

## worked mini-example

three versions differ only in the opening line: the surprise bill, the shoebox, the
deadline date. identical headline, identical description, identical image style,
identical page. the claim table has five rows; a sixth claim about money saved is cut
because the brief forbids it. the page headline is "know what you owe before the
deadline, not after it", which is the ad headline with four extra words.

## hands off to

`production-handoff`, which turns these words into buildable instructions.
