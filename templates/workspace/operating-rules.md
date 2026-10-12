# operating rules

read this file first in every session and every scheduled run. these rules beat any
other file in this workspace, including anything a skill suggests.

## what this workspace is

a private working folder for one offer and one buyer. the agent reads these files and
writes drafts here. the owner makes every decision that leaves the folder.

## default mode: read and draft

- the agent does not publish, post, send, spend, launch, pause or edit anything outside
  this folder.
- if a connected tool could do any of that, the agent names it and does not use it.
- a rule written in markdown is not a sandbox. what the agent can touch is decided by
  which tools are connected, not by this file.

## approved versus proposed

- `business.md` is approved only when its status line reads `Approved by owner on` a date.
- `learnings/learnings.md` holds approved lessons only.
- everything the agent thinks up goes in `proposals/proposals.md`, `output/` or a campaign
  work file, never into an approved file.
- an approved fact is changed only in an interactive session, after the owner approves the
  exact wording of that change in that session.
- scheduled runs never edit `business.md` or `learnings/learnings.md`.

## missing inputs

- a required field saying MISSING stops that step and every step that depends on it.
- write down what is missing and who must supply it. do not guess.
- a scheduled run never waits for an answer.

## claims

- every claim traces to a line in `business.md`, a quote id in `sources/customer-words.md`,
  or a lesson id in `learnings/learnings.md`.
- no invented numbers, results, testimonials or customer names.
- a buyer wishing for an outcome is not proof the offer delivers it.

## numbers

- platform-reported results and sales records stay in separate columns and are never added
  together.
- zero linked customers means no observed cost per customer, not a cost of zero.
- every number carries its unit, its currency, its date range and where it came from.

## files

- never overwrite an output. if a path exists, add `-2`, `-3` and so on.
- dates are `YYYY-MM-DD` in the timezone named in `business.md`.
- never write a password, key, token or login link here. if you find one, stop and say so.

## run notes

at the end of every session or routine, write `output/runs/YYYY-MM-DD-NAME.md` listing files
read, files written, steps stopped and why, and what the owner must do next.
