# reading meta numbers through autoady

optional. everything else in this kit works from a csv export dropped into a test's
`data/` folder. this document is for when you want an agent to read the numbers directly.

## what autoady is

an mcp server that exposes meta ad data to an agent. mcp is the protocol agents use to
talk to outside tools.

endpoint: `https://www.autoady.io/api/mcp`

its published protected-resource metadata, at `/.well-known/oauth-protected-resource`,
names the resource as `https://www.autoady.io/api/mcp` and the authorisation server as
`https://www.autoady.io`, with authorisation at `/oauth/authorize` and tokens at
`/api/oauth/token`. so browser-based oauth is the route the server itself documents.

## connecting

hermes:

```bash
hermes mcp add autoady --url https://www.autoady.io/api/mcp --auth oauth
hermes mcp list
```

claude code:

```bash
claude mcp add --transport http autoady https://www.autoady.io/api/mcp
claude mcp list
```

check your installed client's `--help` before trusting any syntax written down anywhere,
including here. clients change their flags.

if a deployment requires a header api key instead of oauth, supply it through a secure
prompt or your client's credential store. never put a key in a file in this repository or
in your workspace.

## before you read anything

1. list the server's tools in the session and read their real schemas. do not act on a
   signature you remember.
2. resolve the account explicitly with `list_ad_accounts({})` and match the returned id,
   name and currency against your `business.md`. never rely on whichever account happens
   to be active.
3. assume the connection can include tools that change things. add it in a setup separate
   from anything that runs on a schedule.

## the read calls

- `get_account_insights(account_id, since, until)`
- `get_campaign_insights(account_id, since, until, status='ALL')`
- `get_campaign_ad_insights(account_id, campaign_id, since, until)`
- `get_adsets(...)` before forming any opinion about pausing, so status, budget and
  learning state are visible

pass an explicit window. do not pass a date preset alongside it. where a response exposes
paging, follow it to the end or say that you stopped early; never describe coverage as
complete when you did not page to the end. reconcile ad sums against campaign sums against
the account total, and report the difference instead of choosing a favourite number.

## reading them honestly

- a lead objective and a purchase objective measure different events. never diagnose a
  sales campaign by its lead count.
- platform-reported results are not sales. they live in their own column, always.
- the lowest cost per lead is not a proven customer winner. that needs a mature cohort and
  your sales record.
- an ad that took a small share of the window's spend has not been tested. report the
  share and give no verdict.
- never add two reported action types that describe the same event, and never let two
  overlapping exports count one order twice.
- a sale that cannot be traced to an ad is unknown origin. it is not zero, and it is not
  evidence for the cheapest ad.

## anything that changes something

follow `skills/autoady-change-proposal`. the short version: verify the tool's real schema
in session, get approval for the exact target and the exact payload, create paused, read
the object back by id, and ask for activation as a separate approval. a tool reporting
success is not evidence; the readback is.

a tool that previews or plans is not assumed to be a pure read. it can persist a preview
object even when it creates nothing in meta, so it goes through the same gate.

if the change needs an identity, a form, or a platform feature the tooling does not
support, stop and hand it to the owner to do by hand. do not route around a missing
capability.

## what this repository does

nothing on the network. the shipped python makes no http calls and has no ad platform
credentials. the mcp path above is something you connect yourself, in your own agent,
with your own account.
