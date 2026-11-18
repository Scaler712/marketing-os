# marketing-os

a portable kit for running marketing for **one offer** as a connected sequence: a brief,
real customer words, ads and a page that match, a test you can actually read, and a
reading that keeps platform-reported results apart from money that arrived.

it is files and skills, not a product. you bring the offer and the judgement.

## what it is

- **11 skill files** under `skills/`, one per stage, each with its inputs, steps, stop
  conditions and a worked mini-example. they work in claude code, hermes, or any agent
  that reads markdown skills.
- **a root `SKILL.md`** that is usable on its own if you want the sequence without the
  rest of the kit.
- **one python command line tool** (`scripts/marketing_os.py`, standard library only) that
  creates a private workspace, checks it for missing inputs, runs a fictional demo of the
  reconciliation maths, validates this distribution, installs the skills, and builds a zip
  with a hash manifest.
- **a fictional worked example** you can run in under a minute to see the output shape.

## what it is not

- not an autonomous system. it drafts and checks; you approve, launch and spend.
- not a saas, not a hosted service, not a dashboard.
- not a source of benchmarks. there is no acceptable cost per result in here, no sample
  size, no kill rule. you set those before you look at numbers.
- it makes no performance claims. no result in this repository came from a real account.

## download

clone:

```bash
git clone https://github.com/Scaler712/marketing-os.git
cd marketing-os
```

or take the archive without git:

```bash
curl -L -o marketing-os.zip https://github.com/Scaler712/marketing-os/archive/refs/heads/main.zip
unzip marketing-os.zip
cd marketing-os-main
```

or pull one skill on its own:

```bash
curl -O https://raw.githubusercontent.com/Scaler712/marketing-os/main/skills/performance-reconciliation/SKILL.md
```

## setup

python 3.9 or newer. no dependencies, no network access, no install step.

```bash
python3 --version
python3 scripts/marketing_os.py check
```

## first command

create your private workspace somewhere **outside** this repository. the tool refuses to
put it inside, so your own business facts never land in a clone you might publish.

```bash
python3 scripts/marketing_os.py init --workspace /absolute/path/to/my-business-os
```

expected output:

```text
workspace created: /absolute/path/to/my-business-os
files written: 12

next:
  1. open business.md and fill it in with your own facts
  2. python3 .../scripts/marketing_os.py doctor --workspace /absolute/path/to/my-business-os
```

then see what is still missing:

```bash
python3 scripts/marketing_os.py doctor --workspace /absolute/path/to/my-business-os
```

on a fresh workspace `doctor` ends with `result: NOT READY` and names every field you
still have to fill. that is the intended first answer, not an error.

see the fictional reading end to end:

```bash
python3 scripts/marketing_os.py demo --workspace /absolute/path/to/my-business-os
```

that writes a labelled fictional folder under `output/` and prints its arithmetic. the
business, the ad ids, the orders and the numbers are invented. walk through what it means
in `docs/WORKED-EXAMPLE.md`.

## a real first request to your agent

the demo only shows you the output shape. the skills are the thing you run, and you run
them by naming the stage and pointing at your workspace:

> my marketing-os workspace is at `/absolute/path/to/my-business-os`. read
> `operating-rules.md` and `business.md` there, then work through the `business-brief`
> skill with me: interview me field by field, write MISSING wherever i have no real
> answer, and show me the exact wording for approval before you change `business.md`.

each later request names the next stage and the file the previous one wrote:

> `business.md` is approved. run `buyer-evidence` over `sources/customer-words.md`: give
> every quote an id, build the evidence index, and stop if a promise has no quote behind
> it.

> the pack in `campaigns/c01-.../` is approved. run `test-preflight`: one question, my
> cap, my end rule, and show me how a sale will trace back to one ad.

the sequence is read top to bottom, but you launch the test yourself after
`test-preflight`, and `autoady-change-proposal` only runs when a reading you already have
suggests a change. `docs/START-HERE.md` has the full table.

## install the skills into an agent

```bash
python3 scripts/marketing_os.py install --target claude \
  --destination /absolute/path/to/staging-skills --dry-run
```

nothing is written without dropping `--dry-run`, nothing is overwritten without
`--overwrite`, and a destination that looks like a live agent skills directory is refused
unless you pass `--allow-live-dir`. install into a staging folder, read what landed, then
move it.

## reading live meta numbers

optional. `skills/autoady-read` and `docs/AUTOADY.md` cover connecting the autoady mcp
server and reading from it; `skills/autoady-change-proposal` covers the approval path for
any change that leaves your machine.

be exact about what read-only means here: **the connection is not read-only.** the autoady
server also exposes tools that create, pause, edit and spend in an ad account, and
connecting it hands every one of those tools to your agent. the read-only part is the
workflow, and a workflow is only read-only if it is enforced outside the markdown: an
allow-list or tool policy that permits the read tools and nothing else in the session
doing the reading. a skill file saying "this stage only reads" is a description, not a
restriction.

the shipped python code in this repository makes no network calls and cannot touch an ad
account.

## safety

`docs/SAFETY.md` is short and worth reading first. the two lines that matter most: a rule
written in a markdown file is not a sandbox, and the only way to keep a scheduled run from
writing is to run it where the write tools are not connected.

## tests

```bash
python3 -m unittest discover -s tests -v
```

## license

MIT. see `LICENSE`.
