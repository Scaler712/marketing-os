# safety

short on purpose.

## the two that matter most

**a rule in a markdown file is not a sandbox.** an agent follows these rules because you
asked it to, not because anything stops it. what it can actually touch is decided by which
tools are connected to it.

**a scheduled run cannot be restricted by a prompt.** if a job must not write to an ad
account, run it in an environment where the write tools are not connected, or have it only
read files you exported yourself. a sentence telling the model not to use a tool does not
revoke its access.

## separation

- keep your private workspace outside this repository. `init` enforces that, refuses
  symlinked paths, and refuses a non-empty directory.
- start in an agent setup with nothing connected that can post, send or spend. check with
  your client's mcp listing before the first run.
- connect read-only data sources in a different setup from the one your scheduled jobs use.
- if you cannot tell what a connected tool is allowed to do, remove it until you can.

## credentials

- no password, key, token or login link goes into any file in this kit or in your
  workspace. account names and ids are fine.
- `doctor` scans your workspace and `check` scans this repository for credential markers,
  and both fail if they find one. they are a backstop, not permission to be careless.
- if a key reaches a file, rotate it. deleting the line is not enough once it has been
  committed or read.

## external changes

every mutation outside the workspace follows one path: exact target and payload approved
in session, created paused, read back by id, activation approved separately. approval to
create is not approval to spend.

## numbers

- platform-reported results and money that arrived are never added together.
- zero linked customers means no observed cost per customer. it never means zero.
- a malformed row is reported and excluded, never repaired by guesswork.
- no threshold in this kit is a default. you set your bar before you see the numbers, or
  there is no verdict.

## what the shipped code does

creates, reads and checks local files. no network, no ad platform access, no telemetry.
it refuses to overwrite an output, and a failed `init` rolls back the files it created
rather than leaving half a workspace behind.
