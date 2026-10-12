# agents

instructions for an agent working inside this repository, and for an agent running the
kit in someone's workspace.

## in this repository

- this repo is the distribution source. it holds no business facts, no account ids, no
  customer data and no credentials. keep it that way.
- never add a real ad account id, a real client name, a real campaign result, or an
  export from a real account. every example here is fictional and labelled fictional.
- python is standard library only. do not add a dependency, and do not add a network call
  to shipped code.
- before proposing a commit: `python3 scripts/marketing_os.py check` and
  `python3 -m unittest discover -s tests`. `check` is also the public-safety gate; it
  fails on credential markers and on absolute home paths.
- skills are self-contained. a skill file must make sense when it is copied out of this
  repo on its own, so do not add links between skill files that break outside the tree.

## running the kit for someone

- read the workspace's `operating-rules.md` first. it beats anything written here.
- default mode is read and draft. you do not publish, post, send, spend, launch, pause or
  edit anything outside the workspace.
- a field saying MISSING stops that step and every step that depends on it. say what is
  missing and who must supply it.
- approved files (`business.md`, `learnings/learnings.md`) change only in an interactive
  session after the owner approves the exact wording. scheduled runs never touch them.
- every claim traces to a brief field, a quote id, or an approved learning.
- platform-reported results and sales records stay separate. zero linked customers is
  unknown cost, never zero cost.
- do not invent a threshold. if the owner has not set a bar, there is no verdict.
- never write a password, key or token into a file. if you find one, stop and say so.
- every external change follows `skills/autoady-change-proposal`: exact payload, explicit
  approval, created paused, read back, activation approved separately.
