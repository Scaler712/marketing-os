# start here

read this once, then work from the skills.

## what you need

- python 3.9 or newer. nothing else to install.
- one offer you can describe exactly: what the buyer gets, the price, the terms.
- some real words from the people you sell to: reviews, email replies, support questions,
  call notes, or interview and discovery-call notes if you have no customers yet.
- a page or form you control where someone can act.

paying buyers make this kit stronger, because only a paid order lets you read ad spend
against money that arrived. you can still run it before the first sale, with one rule
that does not bend: anything built from interviews, discovery calls or desk research is a
hypothesis, and the files say so. research-grounded is not proven. until a real buyer and
a real order exist behind a line, write no result claim, no performance number and no
testimonial-shaped sentence. a reconciliation with zero linked customers reads unknown,
never zero.

## thirty minutes, in order

1. confirm the kit is intact:

   ```bash
   python3 scripts/marketing_os.py check
   ```

2. create your private workspace. the tool refuses to create it inside this repository,
   because this repository is the thing you might publish:

   ```bash
   python3 scripts/marketing_os.py init --workspace /absolute/path/to/my-business-os
   ```

3. open `business.md` in that workspace and fill it in. write MISSING rather than a guess.
   the three fields that unlock the most are the one action you want, how a sale links back
   to an ad, and the usual number of days from first visit to purchase.
4. see what is still missing. it will say NOT READY and name every field. that is the
   point of it, not an error:

   ```bash
   python3 scripts/marketing_os.py doctor --workspace /absolute/path/to/my-business-os
   ```

5. write a labelled fictional example so you can see what a reading looks like before you
   have one of your own:

   ```bash
   python3 scripts/marketing_os.py demo --workspace /absolute/path/to/my-business-os
   ```
6. then run the sequence, one skill at a time, starting with `skills/business-brief`.

## how the sequence fits together

| stage | needs | produces |
|---|---|---|
| business-brief | you, in a session | approved `business.md` |
| buyer-evidence | approved brief | quotes with ids, an evidence index |
| message-choice | quotes | options, then one approved promise |
| campaign-build | approved promise | a pack: ads, page copy, claim table |
| production-handoff | approved pack | build sheet and the check list that gates spend |
| content-reuse | the pack's claim table | posts and the follow-up email |
| test-preflight | a passed check list | a test plan with your cap and end rule |
| autoady-read | a launched test | raw numbers with explicit identity and window |
| autoady-change-proposal | a reading | an approved, paused, read-back change |
| performance-reconciliation | exports in `data/` | a reading with a verdict |
| next-work-and-learning | a reading | proposals, and the one next job |

skipping a row does not save time; it removes the thing the next row reads. two rows in
that table need saying out loud, because the order alone misleads:

- **launching happens between rows 7 and 8, and you do it.** `test-preflight` hands you a
  plan and a check list; the first launch is your action once that list passes. nothing in
  this kit launches, spends or pauses anything.
- **`autoady-change-proposal` is an optional branch, not a step you owe.** it runs only
  when a reading you already have in hand suggests a change outside the workspace. that
  reading is the raw read from row 8, or a full `performance-reconciliation` reading from
  an earlier pass. so on a first pass the order is read, reconcile, then stop; on later
  passes it is read, reconcile, then propose. if nothing in the reading calls for a
  change, the row is skipped and that is the normal outcome.

## installing the skills into your agent

```bash
python3 scripts/marketing_os.py install --target claude \
  --destination /absolute/path/to/staging-skills --dry-run
```

drop `--dry-run` when the plan looks right. each skill folder is self-contained, so you
can copy one out on its own.

## when something stops

a stop is a result. a skill that stops names the missing input and who has to supply it.
fix the input rather than raising a limit or loosening a rule.
