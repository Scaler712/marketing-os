---
name: autoady-change-proposal
description: use when a read suggests an external change: writes a proposal with exact target and payload, gates it on verified schema and explicit owner approval, creates paused first, then reads the change back before calling it done.
stage: 9 of 11
reads: tests/tNN-name/readings/, business.md
writes: proposals/proposals.md, output/change-YYYY-MM-DD.md
---

# autoady change proposal

every mutation outside this workspace goes through this stage. the default answer is a
written proposal, not a call.

## when this stage runs

this is an optional branch, not a step owed on every pass. it runs only when a reading
already in hand suggests a change outside the workspace: either the raw read from the
previous stage, or a full reconciliation reading from an earlier pass of the sequence.
the reconciliation stage sits after this one in the numbering because the first pass
reads, reconciles and stops; a later pass reads, reconciles, and only then proposes. if
the reading calls for no change, skipping this stage is the correct outcome.

## steps

1. write the proposal before anything else: the exact object being changed, its id, the
   current value read back from the platform in this session, the proposed value, the
   reason with the reading it came from, and what would make you undo it.
2. capability gate: confirm in the current session that a tool exists for exactly this
   change and read its real schema. never hardcode a payload shape you have not seen in
   this session's schema.
3. approval gate: the owner approves the exact target and the exact payload, both quoted
   in full. an approval of an intent is not an approval of a payload.
4. create paused. anything new comes into existence paused, with no spend possible.
5. read back. fetch the created object by id and quote its real state. a tool returning
   success is not evidence; the readback is.
6. ask for activation separately. approval to create is not approval to spend. the
   activation request quotes the readback and waits for its own yes.
7. record it: what was proposed, approved, created, read back and activated, with
   timestamps and ids, in `output/change-YYYY-MM-DD.md`.

## stop conditions

- no identity to attach to, no form support, or no support for an enhancement the object
  needs: stop and hand to the owner to do manually. never route around a missing
  capability.
- if a readback disagrees with what was requested, stop and report. do not retry.
- treat a tool whose effects you cannot confirm as a write. a preview or plan tool can
  persist a preview object even when it creates nothing in the ad platform, so it is not
  assumed to be a pure read.
- a markdown rule is not a sandbox. if a session must not write, run it where the write
  tools are not connected.
- never batch unrelated changes behind one approval.
- never pause or edit an object that is currently meeting the owner's stated bar just
  because a number looks better elsewhere; a sequence you cannot see may depend on it.

## worked mini-example

a reading suggests a fourth ad version. the proposal names the target ad set id, quotes
its current status and budget as read back in session, and includes the full creation
payload copied from the live schema. the owner approves that exact payload. the ad is
created paused. the readback shows the paused status and the ad id, which is recorded. a
second, separate request asks for activation, and the owner defers it until the current
test's wait period has passed. nothing was activated, and the record says so.

## hands off to

`performance-reconciliation`, which will later judge whatever was activated.
