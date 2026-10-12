# provenance

where the content in this repository came from, and what has not been verified.

## the method

the sequence, the stop conditions and the number-handling rules come from running paid
social and landing page work for small businesses, and from the failure modes that showed
up repeatedly: copy that contradicted the page, tests with more than one variable, sales
that could not be traced to an ad, and confident verdicts drawn from immature data.

every stage was rewritten here from the method itself. no client work, no account
identifier, no client result and no private file is reproduced in this repository, and
none is referenced.

## claims

- no performance number anywhere in this repository came from a real account.
- the only numbers present are in `examples/demo/`, and they are invented. every file
  generated from them is labelled fictional.
- there are no benchmarks here. no acceptable cost per result, no sample size, no kill
  rule, no fatigue threshold. those are set by the owner, per business, before the numbers
  arrive.

## autoady

the endpoint, the oauth metadata and the tool names in `docs/AUTOADY.md` were checked
against what the server publishes at the time of writing:

- resource `https://www.autoady.io/api/mcp`
- authorisation server `https://www.autoady.io`, authorisation `/oauth/authorize`,
  token `/api/oauth/token`
- read tools used by the skills: `list_ad_accounts`, `get_account_insights`,
  `get_campaign_insights`, `get_campaign_ad_insights`, `get_adsets`

not verified, and therefore treated as unknown in the skills: the full tool list of any
given deployment, the schema of any write tool, and whether a preview or plan tool has
side effects. the skills require reading the real schema in session for exactly this
reason.

client command syntax changes. the hermes and claude code commands shown were checked
against the installed clients at the time of writing, and the documents tell you to run
`--help` rather than trust them.

## the code

`scripts/marketing_os.py` is original, python standard library only, no network calls.
the arithmetic uses `decimal` so that money is divided exactly rather than through binary
floating point, and division by zero returns "not observed" rather than a number.

the tests in `tests/` were written against the behaviours that matter for safety:
collisions, rollback, path and symlink escape, missing inputs, malformed and duplicate
rows, zero denominators and mismatched identities. they are run by ci on every push.

## influences

the packaging idea for distributing agent skills as a small repository with an installer
is common practice in the agent-skills ecosystem; two public skill collections prompted
the decision to ship this as a kit rather than one long document. no text, naming,
structure or content was taken from either. what is different here is that the stages are
sequential rather than interchangeable, the kit ships a runnable first command, every
claim in a draft has to trace to a source file, and the ad-platform work is gated behind
explicit identity checks, paused-first creation and readback.
