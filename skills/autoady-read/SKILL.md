---
name: autoady-read
description: use to read live meta numbers through the autoady mcp server read-only: fresh schema check, explicit account identity, explicit date window, and sums that are reconciled rather than assumed complete.
stage: 8 of 11
reads: business.md, tests/tNN-name/plan.md
writes: tests/tNN-name/data/, output/runs/
---

# autoady read

autoady is an mcp server that exposes meta ad data to an agent. this stage reads. it does
not change anything, and it does not assume which tools are read-only.

connecting the server is not the same as connecting it read-only. the same connection
exposes tools that create, pause and edit objects in an ad account. keeping this stage to
reads is enforced by the session you run it in - an allow-list or tool policy that permits
only the read tools - not by this file.

## connecting

the server endpoint is `https://www.autoady.io/api/mcp`. its published protected-resource
metadata names `https://www.autoady.io` as the authorisation server, with authorisation
at `/oauth/authorize` and tokens at `/api/oauth/token`, so the browser oauth flow is the
documented route.

```bash
hermes mcp add autoady --url https://www.autoady.io/api/mcp --auth oauth
hermes mcp list
```

```bash
claude mcp add --transport http autoady https://www.autoady.io/api/mcp
claude mcp list
```

check your installed client's own `--help` before trusting any command written down
here, including these. if a deployment requires a header api key instead, supply it
through a secure prompt or the client's credential store. never write a key into a file
in the workspace or the repository.

## steps

1. list the server's tools in the current session and read their real schemas. do not act
   on a remembered signature. record the tool names you saw in the run note.
2. resolve identity explicitly with `list_ad_accounts({})` and match the returned id,
   name and currency against `business.md`. never rely on whichever account happens to be
   active.
3. pull with an explicit window and nothing else: `get_account_insights(account_id,
   since, until)`, `get_campaign_insights(account_id, since, until, status='ALL')`,
   `get_campaign_ad_insights(account_id, campaign_id, since, until)`. do not pass a date
   preset alongside an explicit window.
4. where a response exposes paging, follow it, and say in the output whether you reached
   the end or stopped. never describe coverage as complete when you did not page to the
   end.
5. reconcile: ad-level sums against campaign level, campaign level against account level.
   report the difference rather than picking the number you prefer.
6. read `get_adsets` before any opinion about pausing, so status, budget and learning
   state are in front of you.
7. compare like with like: the actual image and copy of each ad, the form or page it
   points at, and whether tracking is the same across versions.
8. write raw pulls into `tests/tNN-name/data/` with dates in the file names, and write
   what you did into the run note, including the exact windows requested.

## stop conditions

- a lead objective and a purchase objective are different measurements. never diagnose a
  sales campaign by its lead count, and never call platform results sales.
- the cheapest cost per lead is not a proven customer winner. that needs a mature cohort
  and the sales record, which is the next stage.
- an ad that took a small share of spend has not been tested. say so, and give no verdict.
- stop and report rather than estimate a missing figure.
- scheduled work that must not touch writes needs a runtime where the write tools are not
  connected at all. a sentence in a markdown file does not revoke access.

## worked mini-example

the pull covers 2027-02-01 to 2027-02-14 on one account id that matches the brief. ad
sums are 842.90 and the campaign total is 842.90, so the reconciliation line says they
agree. a fourth ad appears with a spend of 22.40, about three percent of the window's
spend; the output records that share as a description and gives no verdict on it. the run
note lists the four tools used and the exact window passed to each.

## hands off to

`autoady-change-proposal` if something needs changing, and
`performance-reconciliation` for the reading itself.
