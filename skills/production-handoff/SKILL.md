---
name: production-handoff
description: use after a campaign pack is approved, to produce the build sheet and the owner check list that must be fully passed before any money moves.
stage: 5 of 11
reads: campaigns/cNN-name/pack.md, business.md
writes: campaigns/cNN-name/production.md
---

# production handoff

a described image is not an image and page copy is not a live page. this stage writes
instructions and a gate; the owner or their designer builds, in the tools the brief
already names.

## inputs

- `campaigns/cNN-name/pack.md` marked `Approved by owner on` a date
- `existing_assets` and `tools_we_build_in` from `business.md`

## outputs

- `campaigns/cNN-name/production.md`: build sheet plus an owner check list with a blank
  after every line

## steps

1. stop if the pack is not approved.
2. for each ad version write: the export file name, each placement the owner plans to
   use with "owner: confirm the current size in ads manager" beside it, the exact words
   that appear on the image, what the picture or video shows in plain words, and the ad
   text copied exactly from the pack.
3. never state a pixel size, aspect ratio or character limit as fact. those change and
   differ by placement. the sheet asks the owner to read them in the platform.
4. page build sheet: every section in order, exact words, which image sits where, button
   text, and where the button leads.
5. write the owner check list, one blank per line: words on every image and the page
   match the pack; price and terms match the brief; every claim is in the claim table;
   the page headline repeats the ad promise; readable on a real phone at arm's length;
   every button and link works on a phone; the form or checkout completes on a phone; the
   purchase or sign-up appears in the platform's own event testing tool; the ad link
   carries the tracking tag and the tag reaches the sales record; checked by owner on.
6. explain the last two lines in one sentence each, because they are the two that later
   stages depend on and the two most often skipped.

## stop conditions

- do not generate images, video or pages in this stage.
- a blank that has been filled with a failure is not a pass.
- stop the next stage until every blank is filled and dated.
- if the tracking tag line cannot be passed, say plainly that the test can still run but
  cost per customer will be unavailable, and let the owner decide.

## worked mini-example

three exports named `c01-v1-feed.png` through `c01-v3-feed.png`, each with the same
image note: phone against a coffee cup, no legible numbers, same colours. the check list
comes back with every line filled except the event testing line, which says "fires twice
per purchase". that is a failure, not a pass. the run note stops test preflight and names
the duplicate event as the thing to fix first.

## hands off to

`content-reuse`, which can run while the build is in progress, and `test-preflight`,
which cannot start until the check list is clean.
