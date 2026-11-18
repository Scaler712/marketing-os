#!/usr/bin/env python3
"""marketing-os command line tool.

python standard library only. this tool never opens a network connection and
never writes to an ad platform. it creates and checks local files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dtmod
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

KIT_VERSION = "0.1.0"
WORKSPACE_SCHEMA = 1
MONEY_Q = Decimal("0.01")
RATE_Q = Decimal("0.000001")
META_NAME = ".marketing-os.json"

REPO_ROOT = Path(__file__).resolve().parent.parent

# tests may replace this with a callable(path) that raises, to exercise rollback
_WRITE_HOOK = None


class UserError(Exception):
    """a problem the operator can fix. printed without a traceback."""


class MalformedRow(Exception):
    """one row of supplied data could not be read. the row is reported, not guessed."""


# ---------------------------------------------------------------- numbers

def to_decimal(raw, field):
    text = (raw or "").strip().replace(",", "")
    if text == "":
        raise MalformedRow(field + " is empty")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise MalformedRow(field + " is not a number: " + repr(raw))
    if value.is_nan() or value.is_infinite():
        raise MalformedRow(field + " is not a finite number: " + repr(raw))
    return value


VALID_CUSTOMER_TYPES = ("new", "repeat")
TRUE_WORDS = ("yes", "true", "1")
FALSE_WORDS = ("no", "false", "0")


def parse_iso_date(raw, field):
    """returns a date, or reports the row. a date we cannot read is never assumed."""
    text = (raw or "").strip()
    if text == "":
        raise MalformedRow(field + " is empty")
    try:
        return dtmod.date.fromisoformat(text)
    except ValueError:
        raise MalformedRow(field + " is not an iso date (YYYY-MM-DD): " + repr(raw))


def parse_bool_field(raw, field):
    text = (raw or "").strip().lower()
    if text in TRUE_WORDS:
        return True
    if text in FALSE_WORDS:
        return False
    raise MalformedRow(
        field + " must be one of yes/no/true/false/1/0, got " + repr(raw))


def parse_customer_type(raw, field):
    text = (raw or "").strip().lower()
    if text not in VALID_CUSTOMER_TYPES:
        raise MalformedRow(
            field + " must be new or repeat, got " + repr(raw))
    return text


def assert_no_symlink_within(base, path, label):
    """refuse a write path that passes through a symlink at or below base.

    the walk stops at base so a symlink higher up the real filesystem (a temp
    directory, for instance) is not mistaken for an escape planted in the tree.
    """
    base = Path(os.path.abspath(base))
    path = Path(os.path.abspath(path))
    chain = []
    cur = path
    while cur != base:
        chain.append(cur)
        parent = cur.parent
        if parent == cur:
            raise UserError("refusing: " + label + " is not inside " + str(base)
                            + ": " + str(path))
        cur = parent
    for candidate in reversed(chain):
        if candidate.is_symlink():
            raise UserError("refusing: " + label + " passes through a symlink: "
                            + str(candidate))
    return path


def money(value):
    return value.quantize(MONEY_Q, rounding=ROUND_HALF_UP)


def ratio(numerator, denominator):
    """exact division, or None when the denominator is zero.

    a zero denominator means not observed. it never means zero cost.
    """
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def fmt_money(value, currency):
    if value is None:
        return "not observed"
    return str(money(value)) + " " + currency


def fmt_rate(value):
    if value is None:
        return "not observed"
    return str(value.quantize(RATE_Q, rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------- paths

def validate_workspace_target(raw, repo_root=None, must_exist=False):
    repo_root = Path(repo_root) if repo_root else REPO_ROOT
    path = Path(raw)
    if not path.is_absolute():
        raise UserError("--workspace must be an absolute path, got: " + str(raw))
    if ".." in path.parts:
        raise UserError("--workspace must not contain '..': " + str(raw))

    if path.is_symlink():
        raise UserError("refusing: the workspace path is a symlink: " + str(path))
    if path.parent.is_symlink() and not must_exist:
        raise UserError("refusing: the parent directory is a symlink: " + str(path.parent))

    real = Path(os.path.realpath(path))
    real_repo = Path(os.path.realpath(repo_root))
    if real == real_repo or real_repo in real.parents:
        raise UserError(
            "refusing: a business workspace may not live inside the distribution "
            "source (" + str(real_repo) + ")")
    if real in real_repo.parents:
        raise UserError("refusing: that workspace path would contain the distribution source")

    if must_exist:
        if not path.is_dir():
            raise UserError("workspace directory not found: " + str(path))
        if not (path / META_NAME).is_file():
            raise UserError(
                "not a marketing-os workspace (missing " + META_NAME + "): " + str(path))
        return path

    if not path.parent.is_dir():
        raise UserError("parent directory does not exist: " + str(path.parent))
    if path.exists():
        if not path.is_dir():
            raise UserError("exists and is not a directory: " + str(path))
        if any(path.iterdir()):
            raise UserError("refusing: " + str(path) + " is not empty (init never overwrites)")
    return path


def _write(path, data):
    if _WRITE_HOOK is not None:
        _WRITE_HOOK(path)
    if isinstance(data, str):
        data = data.encode("utf-8")
    path.write_bytes(data)


def _mkdirs(path, created_dirs):
    missing = []
    cur = path
    while not cur.exists():
        missing.append(cur)
        cur = cur.parent
    for directory in reversed(missing):
        directory.mkdir()
        created_dirs.append(directory)


def template_files(repo_root=None):
    root = (Path(repo_root) if repo_root else REPO_ROOT) / "templates" / "workspace"
    if not root.is_dir():
        return []
    out = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != ".DS_Store":
            out.append((path.relative_to(root).as_posix(), path.read_bytes()))
    return out


def today_iso():
    return dtmod.date.today().isoformat()


def unused_dir(parent, stem):
    candidate = parent / stem
    counter = 2
    while candidate.exists():
        candidate = parent / (stem + "-" + str(counter))
        counter += 1
    return candidate


# ---------------------------------------------------------------- init

def cmd_init(args):
    target = validate_workspace_target(args.workspace)
    files = template_files()
    if not files:
        raise UserError("templates/workspace is missing from this checkout; run: check")

    clashes = [target / rel for rel, _ in files if (target / rel).exists()]
    if clashes:
        raise UserError(
            "fail-before-write: these paths already exist, nothing was written:\n  "
            + "\n  ".join(str(c) for c in clashes))

    created_files = []
    created_dirs = []
    try:
        for rel, data in files:
            dest = target / rel
            _mkdirs(dest.parent, created_dirs)
            _write(dest, data)
            created_files.append(dest)
        meta = {
            "schema": WORKSPACE_SCHEMA,
            "kit_version": KIT_VERSION,
            "created_utc": dtmod.datetime.now(dtmod.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "note": "private business workspace. not part of the distribution source.",
        }
        meta_path = target / META_NAME
        _mkdirs(target, created_dirs)
        _write(meta_path, json.dumps(meta, indent=2) + "\n")
        created_files.append(meta_path)
    except Exception:
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise

    print("workspace created: " + str(target))
    print("files written: " + str(len(created_files)))
    print("")
    print("next:")
    print("  1. open business.md and fill it in with your own facts")
    print("  2. python3 " + str(REPO_ROOT / "scripts" / "marketing_os.py")
          + " doctor --workspace " + str(target))
    return 0


# ---------------------------------------------------------------- fields

REQUIRED_FIELDS = [
    "offer_name",
    "price_and_terms",
    "primary_action",
    "buyer_in_one_sentence",
    "ad_platform",
    "ad_account_id",
    "currency",
    "timezone",
    "sales_system_id",
    "ad_to_sale_link",
]


def parse_fields(text):
    fields = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:]
        if ":" not in body:
            continue
        key, _, value = body.partition(":")
        key = key.strip().strip("`")
        if key and " " not in key:
            fields[key] = value.strip()
    return fields


WORKSPACE_REQUIRED_PATHS = [
    "business.md",
    "operating-rules.md",
    "sources/customer-words.md",
    "campaigns/README.md",
    "tests/README.md",
    "proposals/proposals.md",
    "learnings/learnings.md",
    "output/README.md",
]


def cmd_doctor(args):
    target = validate_workspace_target(args.workspace, must_exist=True)
    errors = []
    warnings = []
    notes = []

    for rel in WORKSPACE_REQUIRED_PATHS:
        if not (target / rel).exists():
            errors.append("missing required path: " + rel)

    business = target / "business.md"
    fields = {}
    if business.is_file():
        text = business.read_text(encoding="utf-8")
        fields = parse_fields(text)
        for key in REQUIRED_FIELDS:
            if key not in fields:
                errors.append("business.md has no field named: " + key)
            elif fields[key] == "" or fields[key].upper().startswith("MISSING"):
                errors.append("business.md field still MISSING: " + key)
        status = fields.get("status", "")
        if not status.startswith("Approved by owner on"):
            warnings.append(
                "business.md status is " + repr(status)
                + " - downstream skills stop until the owner approves it")
        if fields.get("ad_to_sale_link", "").lower().startswith("not set up"):
            warnings.append(
                "ad_to_sale_link says not set up - cost per customer cannot be computed")

    quotes = target / "sources" / "customer-words.md"
    if quotes.is_file():
        count = len(re.findall(r"^## Q\d+\s*$", quotes.read_text(encoding="utf-8"),
                               flags=re.MULTILINE))
        notes.append("customer quote entries found: " + str(count))
        if count == 0:
            warnings.append("sources/customer-words.md has no entries - buyer evidence is empty")

    secrets = scan_for_secrets([p for p in target.rglob("*") if p.is_file()])
    for hit in secrets:
        errors.append("possible credential in workspace file: " + hit)

    campaigns = sorted(p.name for p in (target / "campaigns").glob("c*") if p.is_dir())
    tests = sorted(p.name for p in (target / "tests").glob("t*") if p.is_dir())
    notes.append("campaign folders: " + (", ".join(campaigns) if campaigns else "none"))
    notes.append("test folders: " + (", ".join(tests) if tests else "none"))

    print("doctor report for " + str(target))
    print("kit version " + KIT_VERSION)
    print("")
    for note in notes:
        print("note    : " + note)
    for warning in warnings:
        print("warning : " + warning)
    for error in errors:
        print("error   : " + error)
    print("")
    if errors:
        print("result: NOT READY (" + str(len(errors)) + " errors, "
              + str(len(warnings)) + " warnings)")
        return 1
    print("result: READY to draft (" + str(len(warnings)) + " warnings)")
    return 0


# ---------------------------------------------------------------- reading data

ADS_COLUMNS = [
    "account_id", "campaign_id", "ad_id", "ad_name", "date_start", "date_end",
    "currency", "timezone", "attribution_window", "spend", "impressions",
    "clicks", "platform_results", "results_action_type",
]
SALES_COLUMNS = [
    "sales_system_id", "order_id", "order_date", "amount", "currency",
    "refunded", "customer_type", "ad_id",
]


def read_rows(text, required_columns, label):
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise UserError(label + " export is empty")
    missing = [c for c in required_columns if c not in reader.fieldnames]
    if missing:
        raise UserError(label + " export is missing columns: " + ", ".join(missing))
    return list(reader)


def parse_ads(rows):
    """returns (ads, duplicates, malformed). duplicates are identical repeat rows."""
    ads = {}
    seen = {}
    duplicates = []
    malformed = []
    for index, row in enumerate(rows, start=2):
        key = (row.get("account_id", ""), row.get("ad_id", ""),
               row.get("date_start", ""), row.get("date_end", ""))
        try:
            parsed = {
                "account_id": row["account_id"].strip(),
                "campaign_id": row["campaign_id"].strip(),
                "ad_id": row["ad_id"].strip(),
                "ad_name": row["ad_name"].strip(),
                "date_start": row["date_start"].strip(),
                "date_end": row["date_end"].strip(),
                "currency": row["currency"].strip(),
                "timezone": row["timezone"].strip(),
                "attribution_window": row["attribution_window"].strip(),
                "results_action_type": row["results_action_type"].strip(),
                "spend": to_decimal(row["spend"], "spend"),
                "impressions": int(to_decimal(row["impressions"], "impressions")),
                "clicks": int(to_decimal(row["clicks"], "clicks")),
                "platform_results": int(to_decimal(row["platform_results"], "platform_results")),
            }
        except MalformedRow as exc:
            malformed.append("ads row " + str(index) + ": " + str(exc))
            continue
        except (KeyError, ValueError) as exc:
            malformed.append("ads row " + str(index) + ": " + str(exc))
            continue
        if not parsed["ad_id"]:
            malformed.append("ads row " + str(index) + ": ad_id is empty")
            continue
        if key in seen:
            if seen[key] == parsed:
                duplicates.append("ads row " + str(index) + ": identical repeat of ad "
                                  + parsed["ad_id"] + " for the same window (ignored once)")
            else:
                raise UserError(
                    "ads export has two different rows for the same ad and window ("
                    + parsed["ad_id"] + " " + parsed["date_start"] + ".." + parsed["date_end"]
                    + "). resolve the export before reading results.")
            continue
        seen[key] = parsed
        ads[parsed["ad_id"]] = parsed
    return ads, duplicates, malformed


def parse_sales(rows):
    sales = []
    seen = set()
    duplicates = []
    malformed = []
    for index, row in enumerate(rows, start=2):
        order_id = row.get("order_id", "").strip()
        system = row.get("sales_system_id", "").strip()
        if not order_id or not system:
            malformed.append("sales row " + str(index) + ": sales_system_id and order_id are required")
            continue
        try:
            amount = to_decimal(row["amount"], "amount")
            if amount <= 0:
                raise MalformedRow(
                    "amount must be a positive paid amount, got " + repr(row.get("amount")))
            parse_iso_date(row.get("order_date", ""), "order_date")
            refunded = parse_bool_field(row.get("refunded", ""), "refunded")
            customer_type = parse_customer_type(row.get("customer_type", ""), "customer_type")
        except (MalformedRow, KeyError) as exc:
            malformed.append("sales row " + str(index) + ": " + str(exc))
            continue
        key = (system, order_id)
        if key in seen:
            duplicates.append("sales row " + str(index) + ": order " + order_id
                              + " already counted (overlapping export, ignored once)")
            continue
        seen.add(key)
        sales.append({
            "sales_system_id": system,
            "order_id": order_id,
            "order_date": row.get("order_date", "").strip(),
            "amount": amount,
            "currency": row.get("currency", "").strip(),
            "refunded": refunded,
            "customer_type": customer_type,
            "ad_id": row.get("ad_id", "").strip(),
        })
    return sales, duplicates, malformed


def reconcile(ads_rows, sales_rows, expected_account_id, expected_sales_system_id,
              as_of, wait_days):
    """pure function. decimal arithmetic. no files, no network."""
    ads, ad_dupes, ad_bad = parse_ads(ads_rows)
    sales, sale_dupes, sale_bad = parse_sales(sales_rows)
    if not ads:
        raise UserError("no readable ad rows in the export")

    account_ids = sorted({a["account_id"] for a in ads.values()})
    if len(account_ids) > 1:
        raise UserError("ads export mixes ad accounts: " + ", ".join(account_ids))
    if expected_account_id and account_ids[0] != expected_account_id:
        raise UserError(
            "identity mismatch: ads export is for account " + account_ids[0]
            + " but the brief says " + expected_account_id
            + ". stop and resolve before reading results.")

    systems = sorted({s["sales_system_id"] for s in sales})
    if expected_sales_system_id:
        unexpected = [s for s in systems if s != expected_sales_system_id]
        if unexpected:
            raise UserError(
                "identity mismatch: sales export also carries records from "
                + ", ".join(unexpected) + " but the brief names only "
                + expected_sales_system_id
                + ". stop and resolve before reading results.")
    elif len(systems) > 1:
        raise UserError("sales export mixes sales systems: " + ", ".join(systems))

    currencies = sorted({a["currency"] for a in ads.values()}
                        | {s["currency"] for s in sales if s["currency"]})
    if len(currencies) > 1:
        raise UserError("mixed currencies in supplied data: " + ", ".join(currencies))
    currency = currencies[0] if currencies else "unknown"

    windows = sorted({a["attribution_window"] for a in ads.values()})
    date_starts = sorted({a["date_start"] for a in ads.values()})
    date_ends = sorted({a["date_end"] for a in ads.values()})
    result_types = sorted({a["results_action_type"] for a in ads.values()})

    mixed_dimensions = []
    if len(windows) > 1:
        mixed_dimensions.append("attribution windows: " + ", ".join(windows))
    if len(date_starts) > 1:
        mixed_dimensions.append("window start dates: " + ", ".join(date_starts))
    if len(date_ends) > 1:
        mixed_dimensions.append("window end dates: " + ", ".join(date_ends))
    if len(result_types) > 1:
        mixed_dimensions.append("result action types: " + ", ".join(result_types))

    per_ad = {}
    for ad_id, ad in ads.items():
        per_ad[ad_id] = dict(ad)
        per_ad[ad_id].update({
            "linked_new_paying": 0,
            "linked_refunded": 0,
            "linked_repeat": 0,
            "linked_revenue": Decimal("0"),
        })

    unmatched = []
    unknown_ad = []
    for sale in sales:
        ad_id = sale["ad_id"]
        if not ad_id:
            unmatched.append(sale)
            continue
        if ad_id not in per_ad:
            unknown_ad.append(sale)
            continue
        bucket = per_ad[ad_id]
        if sale["refunded"]:
            bucket["linked_refunded"] += 1
        elif sale["customer_type"] == "repeat":
            bucket["linked_repeat"] += 1
        else:
            bucket["linked_new_paying"] += 1
            bucket["linked_revenue"] += sale["amount"]

    total_spend = sum((a["spend"] for a in ads.values()), Decimal("0"))
    for ad_id, bucket in per_ad.items():
        bucket["ctr"] = ratio(bucket["clicks"], bucket["impressions"])
        bucket["cost_per_click"] = ratio(bucket["spend"], bucket["clicks"])
        bucket["cost_per_platform_result"] = ratio(bucket["spend"], bucket["platform_results"])
        bucket["cost_per_new_paying_customer"] = ratio(
            bucket["spend"], bucket["linked_new_paying"])
        bucket["share_of_spend"] = ratio(bucket["spend"], total_spend)

    platform_total = sum(a["platform_results"] for a in ads.values())
    linked_total = sum(b["linked_new_paying"] for b in per_ad.values())

    funded = [b for b in per_ad.values() if b["cost_per_new_paying_customer"] is not None]
    platform_leader = None
    ranked_platform = [b for b in per_ad.values() if b["cost_per_platform_result"] is not None]
    if ranked_platform:
        platform_leader = min(ranked_platform, key=lambda b: b["cost_per_platform_result"])
    customer_leader = None
    if funded:
        customer_leader = min(funded, key=lambda b: b["cost_per_new_paying_customer"])
    if mixed_dimensions:
        # rows measured over different windows, or counting different actions, are not
        # comparable. no leader is published rather than a silently wrong one.
        platform_leader = None
        customer_leader = None

    maturity = "unknown"
    days_since_end = None
    if as_of and date_ends:
        try:
            end = dtmod.date.fromisoformat(date_ends[-1])
            asof = dtmod.date.fromisoformat(as_of)
            days_since_end = (asof - end).days
            maturity = "mature" if days_since_end >= wait_days else "not mature"
        except ValueError:
            maturity = "unknown"

    if mixed_dimensions:
        verdict = "INCONCLUSIVE"
        verdict_why = ("the supplied ad rows are not comparable to each other ("
                       + "; ".join(mixed_dimensions)
                       + "), so nothing in this export can be ranked. split the export "
                         "by window and result type and read each one on its own")
    elif maturity == "not mature":
        verdict = "NOT MATURE"
        verdict_why = ("only " + str(days_since_end) + " days have passed since the window ended; "
                       "the brief says wait " + str(wait_days))
    elif maturity == "unknown":
        verdict = "INCONCLUSIVE"
        verdict_why = ("maturity could not be established from the supplied window end "
                       "and reading date, so there is nothing to judge against the "
                       "brief's waiting period")
    elif linked_total == 0:
        verdict = "INCONCLUSIVE"
        verdict_why = "no sale in the supplied records carries an ad identifier from this test"
    elif customer_leader and platform_leader and (
            customer_leader["ad_id"] != platform_leader["ad_id"]):
        verdict = "INCONCLUSIVE"
        verdict_why = ("the platform-result leader and the linked-customer leader are "
                       "different ads, and the owner has not set what counts as clear")
    else:
        verdict = "LEANING"
        verdict_why = "one ad leads on both platform results and linked new paying customers"

    return {
        "currency": currency,
        "account_id": account_ids[0],
        "sales_systems": systems,
        "attribution_windows": windows,
        "result_action_types": result_types,
        "mixed_dimensions": mixed_dimensions,
        "window_end": date_ends[-1] if date_ends else None,
        "as_of": as_of,
        "wait_days": wait_days,
        "days_since_end": days_since_end,
        "maturity": maturity,
        "total_spend": total_spend,
        "platform_results_total": platform_total,
        "linked_new_paying_total": linked_total,
        "per_ad": per_ad,
        "unmatched_sales": unmatched,
        "sales_with_unknown_ad": unknown_ad,
        "ads_duplicates": ad_dupes,
        "ads_malformed": ad_bad,
        "sales_duplicates": sale_dupes,
        "sales_malformed": sale_bad,
        "platform_leader": platform_leader["ad_id"] if platform_leader else None,
        "customer_leader": customer_leader["ad_id"] if customer_leader else None,
        "verdict": verdict,
        "verdict_why": verdict_why,
    }


# ---------------------------------------------------------------- demo

def render_reconciliation(result, title):
    currency = result["currency"]
    lines = []
    out = lines.append
    out("# " + title)
    out("")
    out("FICTIONAL SYNTHETIC DATA. the numbers below come from bundled example files")
    out("invented for this kit. they are not a real campaign and not an api response.")
    out("")
    out("## provenance")
    out("")
    out("- ad account in the supplied export: " + result["account_id"])
    out("- sales system in the supplied export: " + (", ".join(result["sales_systems"]) or "none"))
    out("- attribution window stated in the export: " + ", ".join(result["attribution_windows"]))
    out("- window end: " + str(result["window_end"]))
    out("- read as of: " + str(result["as_of"]) + " (fictional reading date)")
    out("- days since window end: " + str(result["days_since_end"])
        + ", brief asks to wait " + str(result["wait_days"]))
    out("- maturity: " + result["maturity"])
    out("- result action type stated in the export: "
        + ", ".join(result["result_action_types"]))
    if result["mixed_dimensions"]:
        out("- NOT COMPARABLE: this export mixes " + "; ".join(result["mixed_dimensions"])
            + ". no ranking and no leader is published from it.")
    out("- currency: " + currency + " (single currency confirmed before any division)")
    out("")
    out("## data problems found in the supplied files")
    out("")
    problems = (result["ads_malformed"] + result["sales_malformed"]
                + result["ads_duplicates"] + result["sales_duplicates"])
    if problems:
        for problem in problems:
            out("- " + problem)
    else:
        out("- none")
    out("")
    out("## platform reported (never called sales)")
    out("")
    out("| ad | spend | impressions | clicks | ctr | platform results | cost per platform result | share of spend |")
    out("|---|---|---|---|---|---|---|---|")
    for ad_id in sorted(result["per_ad"]):
        row = result["per_ad"][ad_id]
        out("| " + ad_id + " (" + row["ad_name"] + ") | "
            + fmt_money(row["spend"], currency) + " | "
            + str(row["impressions"]) + " | " + str(row["clicks"]) + " | "
            + fmt_rate(row["ctr"]) + " | " + str(row["platform_results"]) + " | "
            + fmt_money(row["cost_per_platform_result"], currency) + " | "
            + fmt_rate(row["share_of_spend"]) + " |")
    out("")
    out("results_action_type in this export: "
        + ", ".join(sorted({r["results_action_type"] for r in result["per_ad"].values()})))
    out("")
    out("## sales records (only sales carrying an ad identifier)")
    out("")
    out("| ad | linked new paying | refunded | repeat | linked revenue | cost per new paying customer |")
    out("|---|---|---|---|---|---|")
    for ad_id in sorted(result["per_ad"]):
        row = result["per_ad"][ad_id]
        out("| " + ad_id + " | " + str(row["linked_new_paying"]) + " | "
            + str(row["linked_refunded"]) + " | " + str(row["linked_repeat"]) + " | "
            + fmt_money(row["linked_revenue"], currency) + " | "
            + (fmt_money(row["cost_per_new_paying_customer"], currency)
               if row["cost_per_new_paying_customer"] is not None
               else "no observed cost per customer yet") + " |")
    out("")
    out("- sales with no ad identifier (unknown origin, not zero): "
        + str(len(result["unmatched_sales"])))
    out("- sales naming an ad that is not in this export: "
        + str(len(result["sales_with_unknown_ad"])))
    out("")
    out("## the arithmetic, shown")
    out("")
    for ad_id in sorted(result["per_ad"]):
        row = result["per_ad"][ad_id]
        if row["cost_per_new_paying_customer"] is None:
            out("- " + ad_id + ": " + fmt_money(row["spend"], currency)
                + " spent, 0 linked new paying customers -> no observed cost per customer yet. "
                "the spend is still spent.")
        else:
            out("- " + ad_id + ": " + fmt_money(row["spend"], currency) + " / "
                + str(row["linked_new_paying"]) + " linked new paying customers = "
                + fmt_money(row["cost_per_new_paying_customer"], currency) + " each")
    out("")
    out("## diagnosis")
    out("")
    out("- platform counted " + str(result["platform_results_total"])
        + " results; the sales records link " + str(result["linked_new_paying_total"])
        + " new paying customers. these are two different measurements and are not blended.")
    out("- leader by cost per platform result: " + str(result["platform_leader"]))
    out("- leader by cost per linked new paying customer: " + str(result["customer_leader"]))
    if result["platform_leader"] != result["customer_leader"]:
        out("- these disagree. the cheaper platform result is not evidence of the cheaper "
            "customer. no kill or scale decision follows from this reading.")
    shares = []
    for ad_id in sorted(result["per_ad"]):
        row = result["per_ad"][ad_id]
        shares.append(ad_id + " " + fmt_rate(row["share_of_spend"]))
    out("- share of spend in this window: " + "; ".join(shares)
        + ". this is a description of how the budget was split, nothing more. there is no "
          "minimum share and no minimum spend in this kit, so no ad here is called "
          "under-funded or unreadable; that bar is the owner's to set.")
    out("")
    out("## verdict")
    out("")
    out("- " + result["verdict"] + ": " + result["verdict_why"])
    out("- owner actions: confirm the tracking still fires, confirm nothing changed on the "
        "page or in the offer, and wait out the stated maturity period before judging.")
    out("")
    return "\n".join(lines) + "\n"


def demo_paths(repo_root=None):
    root = (Path(repo_root) if repo_root else REPO_ROOT) / "examples" / "demo"
    return root


def cmd_demo(args):
    target = validate_workspace_target(args.workspace, must_exist=True)
    source = demo_paths()
    needed = ["business-fictional.md", "campaign-pack-fictional.md", "test-plan-fictional.md",
              "ads-2027-02-16-fictional.csv", "sales-2027-02-16-fictional.csv", "demo.json"]
    for name in needed:
        if not (source / name).is_file():
            raise UserError("bundled demo file missing: " + str(source / name))

    config = json.loads((source / "demo.json").read_text(encoding="utf-8"))
    ads_text = (source / "ads-2027-02-16-fictional.csv").read_text(encoding="utf-8")
    sales_text = (source / "sales-2027-02-16-fictional.csv").read_text(encoding="utf-8")

    ads_rows = read_rows(ads_text, ADS_COLUMNS, "ads")
    sales_rows = read_rows(sales_text, SALES_COLUMNS, "sales")
    result = reconcile(
        ads_rows, sales_rows,
        expected_account_id=config["ad_account_id"],
        expected_sales_system_id=config["sales_system_id"],
        as_of=config["as_of"],
        wait_days=int(config["wait_days"]),
    )

    out_dir = unused_dir(target / "output", "demo-" + today_iso())
    data_dir = out_dir / "data"
    planned_outputs = [
        out_dir, data_dir,
        out_dir / "00-README.md",
        out_dir / "01-business-fictional.md",
        out_dir / "02-campaign-pack-fictional.md",
        out_dir / "03-test-plan-fictional.md",
        out_dir / "04-reconciliation-fictional.md",
        out_dir / "05-summary-fictional.json",
        data_dir / "ads-2027-02-16-fictional.csv",
        data_dir / "sales-2027-02-16-fictional.csv",
    ]
    for planned in planned_outputs:
        assert_no_symlink_within(target, planned, "demo output path")
    data_dir.mkdir(parents=True)
    shutil.copy2(source / "business-fictional.md", out_dir / "01-business-fictional.md")
    shutil.copy2(source / "campaign-pack-fictional.md", out_dir / "02-campaign-pack-fictional.md")
    shutil.copy2(source / "test-plan-fictional.md", out_dir / "03-test-plan-fictional.md")
    shutil.copy2(source / "ads-2027-02-16-fictional.csv", data_dir / "ads-2027-02-16-fictional.csv")
    shutil.copy2(source / "sales-2027-02-16-fictional.csv", data_dir / "sales-2027-02-16-fictional.csv")

    report = render_reconciliation(result, "reconciliation reading (fictional demo)")
    (out_dir / "04-reconciliation-fictional.md").write_text(report, encoding="utf-8")

    readme = []
    readme.append("# demo output (fictional)")
    readme.append("")
    readme.append("every file in this folder is synthetic. the business, the ad ids, the order")
    readme.append("ids and the numbers were invented for this kit. nothing here came from a real")
    readme.append("ad account, a real crm or an mcp response.")
    readme.append("")
    readme.append("read in this order:")
    readme.append("")
    readme.append("1. 01-business-fictional.md - the brief every later file is built from")
    readme.append("2. 02-campaign-pack-fictional.md - ads and the page that must match them")
    readme.append("3. 03-test-plan-fictional.md - the one difference, the cap, the end rule")
    readme.append("4. 04-reconciliation-fictional.md - the computed reading of data/")
    readme.append("5. 05-summary-fictional.json - the same numbers for a machine")
    readme.append("")
    (out_dir / "00-README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    summary = {
        "fictional": True,
        "source": "examples/demo bundled synthetic data",
        "currency": result["currency"],
        "account_id": result["account_id"],
        "total_spend": str(money(result["total_spend"])),
        "platform_results_total": result["platform_results_total"],
        "linked_new_paying_total": result["linked_new_paying_total"],
        "maturity": result["maturity"],
        "verdict": result["verdict"],
        "verdict_why": result["verdict_why"],
        "per_ad": {
            ad_id: {
                "spend": str(money(row["spend"])),
                "platform_results": row["platform_results"],
                "cost_per_platform_result": (
                    str(money(row["cost_per_platform_result"]))
                    if row["cost_per_platform_result"] is not None else None),
                "linked_new_paying": row["linked_new_paying"],
                "cost_per_new_paying_customer": (
                    str(money(row["cost_per_new_paying_customer"]))
                    if row["cost_per_new_paying_customer"] is not None else None),
            }
            for ad_id, row in result["per_ad"].items()
        },
        "data_problems": (result["ads_malformed"] + result["sales_malformed"]
                          + result["ads_duplicates"] + result["sales_duplicates"]),
    }
    (out_dir / "05-summary-fictional.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("demo written (all files labelled fictional): " + str(out_dir))
    print("")
    print("total spend       : " + fmt_money(result["total_spend"], result["currency"]))
    print("platform results  : " + str(result["platform_results_total"]))
    print("linked customers  : " + str(result["linked_new_paying_total"]))
    for ad_id in sorted(result["per_ad"]):
        row = result["per_ad"][ad_id]
        print("  " + ad_id + ": cost per platform result "
              + fmt_money(row["cost_per_platform_result"], result["currency"])
              + " | cost per new paying customer "
              + (fmt_money(row["cost_per_new_paying_customer"], result["currency"])
                 if row["cost_per_new_paying_customer"] is not None
                 else "no observed cost per customer yet"))
    print("verdict           : " + result["verdict"] + " - " + result["verdict_why"])
    return 0


# ---------------------------------------------------------------- check

def _marker(*parts):
    """assembled at runtime so this file does not match its own scanner."""
    return "".join(parts)


SECRET_MARKERS = [
    _marker("sk-", "ant-"), _marker("sk-", "proj-"), _marker("ghp", "_"),
    _marker("xoxb", "-"), _marker("AKI", "A"),
    _marker("BEGIN ", "RSA PRIVATE KEY"), _marker("BEGIN ", "OPENSSH PRIVATE KEY"),
    _marker("EA", "AB"),
]
SECRET_FIELD_HINTS = [
    _marker("api", "_key="), _marker("api-", "key:"), _marker("access", "_token="),
    _marker("pass", "word="), _marker("client", "_secret="),
]


def scan_for_secrets(paths):
    hits = []
    for path in paths:
        if path.suffix in (".png", ".jpg", ".jpeg", ".zip", ".pdf"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for marker in SECRET_MARKERS + SECRET_FIELD_HINTS:
            if marker in text:
                hits.append(str(path) + " contains " + repr(marker))
    return hits


PRIVATE_LEAK_MARKERS = [
    _marker("/Us", "ers/"), _marker("/ho", "me/"), _marker("Mastery", " Box"),
    _marker("act_", "1"), _marker("act_", "2"), _marker("act_", "3"),
]
REQUIRED_REPO_PATHS = [
    "README.md", "AGENTS.md", "SKILL.md", "LICENSE", ".gitignore",
    "docs/START-HERE.md", "docs/AUTOADY.md", "docs/SAFETY.md",
    "docs/WORKED-EXAMPLE.md", "docs/PROVENANCE.md",
    "scripts/marketing_os.py", "tests/test_marketing_os.py",
    "templates/workspace/business.md", "examples/demo/demo.json",
]


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    block = text[4:end]
    data = {}
    for line in block.splitlines():
        if line.startswith(("  ", "\t")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip()
    return data


def cmd_check(args):
    root = REPO_ROOT
    errors = []
    warnings = []

    for rel in REQUIRED_REPO_PATHS:
        if not (root / rel).exists():
            errors.append("missing required repo path: " + rel)

    skills_dir = root / "skills"
    skill_names = []
    if not skills_dir.is_dir():
        errors.append("skills/ directory is missing")
    else:
        for skill_path in sorted(skills_dir.glob("*/SKILL.md")):
            text = skill_path.read_text(encoding="utf-8")
            front = parse_frontmatter(text)
            rel = skill_path.relative_to(root).as_posix()
            if front is None:
                errors.append(rel + ": no yaml frontmatter block")
                continue
            for key in ("name", "description", "stage", "reads", "writes"):
                if key not in front:
                    errors.append(rel + ": frontmatter missing key " + key)
            name = front.get("name", "")
            if name and name != skill_path.parent.name:
                errors.append(rel + ": frontmatter name " + name
                              + " does not match folder " + skill_path.parent.name)
            if name:
                skill_names.append(name)
            for heading in ("## stop conditions", "## worked mini-example", "## steps"):
                if heading not in text:
                    errors.append(rel + ": missing section " + heading)
            if len(text.split()) < 220:
                warnings.append(rel + ": short skill body (" + str(len(text.split())) + " words)")
        if len(skill_names) < 10:
            errors.append("expected at least 10 skills, found " + str(len(skill_names)))

    root_skill = root / "SKILL.md"
    if root_skill.is_file():
        text = root_skill.read_text(encoding="utf-8")
        for name in skill_names:
            if name not in text:
                errors.append("root SKILL.md does not reference skill: " + name)

    for link in symlinked_paths(root):
        errors.append("symlink in the distribution source (never packaged): "
                      + link.relative_to(root).as_posix())

    tracked = [p for p in packageable_files(root)]
    for hit in scan_for_secrets(tracked):
        errors.append("possible credential: " + hit)
    for path in tracked:
        if path.suffix not in (".md", ".py", ".yml", ".yaml", ".txt", ".json", ".csv"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for marker in PRIVATE_LEAK_MARKERS:
            if marker in text:
                errors.append(str(path.relative_to(root)) + " leaks a private marker: "
                              + repr(marker))

    print("check report for " + str(root))
    print("skills found: " + str(len(skill_names)))
    print("packageable files: " + str(len(tracked)))
    print("")
    for warning in warnings:
        print("warning : " + warning)
    for error in errors:
        print("error   : " + error)
    print("")
    if errors:
        print("result: FAIL (" + str(len(errors)) + " errors)")
        return 1
    print("result: PASS (" + str(len(warnings)) + " warnings)")
    return 0


# ---------------------------------------------------------------- package

EXCLUDE_DIRS = {".git", ".github_cache", "__pycache__", "dist", ".venv", "node_modules",
                "receipts", ".idea", ".pytest_cache"}
EXCLUDE_NAMES = {".DS_Store", META_NAME, ".env", "global.env"}
EXCLUDE_SUFFIXES = {".pyc", ".log", ".zip"}


def _excluded_dir(rel):
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def symlinked_paths(root=None):
    """every symlink inside the distribution source. a symlink is never packaged.

    a symlinked file can point anywhere on the machine, so following one would put
    private content into a public archive or a published hash manifest.
    """
    root = Path(root) if root else REPO_ROOT
    found = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if _excluded_dir(rel):
            continue
        if path.is_symlink():
            found.append(path)
    return found


def packageable_files(root=None):
    root = Path(root) if root else REPO_ROOT
    links = {p for p in symlinked_paths(root)}
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if _excluded_dir(rel):
            continue
        if path.is_symlink() or any(parent in links for parent in path.parents):
            continue
        if not path.is_file():
            continue
        if path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES:
            continue
        if path.name.startswith(".env"):
            continue
        files.append(path)
    return files


def cmd_package(args):
    root = REPO_ROOT
    files = packageable_files(root)
    if not files:
        raise UserError("nothing to package")
    dist = root / "dist"
    name = "marketing-os-" + KIT_VERSION + ".zip"
    archive = dist / name
    if archive.exists() and not args.overwrite:
        raise UserError("archive exists (use --overwrite): " + str(archive))

    manifest_lines = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_lines.append(digest + "  " + path.relative_to(root).as_posix())
    manifest = "\n".join(manifest_lines) + "\n"

    if args.dry_run:
        print("dry run: would write " + str(archive))
        print("entries: " + str(len(files) + 1))
        for line in manifest_lines[:10]:
            print("  " + line)
        if len(manifest_lines) > 10:
            print("  ... " + str(len(manifest_lines) - 10) + " more")
        print("dry run: nothing was written and dist/ was not created")
        return 0

    if cmd_check(argparse.Namespace(command="check")) != 0:
        raise UserError("check failed, so nothing was packaged. fix the errors above "
                        "and run package again.")

    dist.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, "marketing-os/" + path.relative_to(root).as_posix())
        zf.writestr("marketing-os/MANIFEST.sha256", manifest)
    print("wrote " + str(archive))
    print("entries: " + str(len(files) + 1) + " (including MANIFEST.sha256)")
    print("manifest sha256: " + hashlib.sha256(manifest.encode("utf-8")).hexdigest())
    return 0


# ---------------------------------------------------------------- install

LIVE_DIR_MARKERS = (".claude/skills", ".hermes/skills", ".hermes/profiles")


def cmd_install(args):
    destination = Path(args.destination)
    if not destination.is_absolute():
        raise UserError("--destination must be an absolute path")
    posix = destination.as_posix()
    if any(marker in posix for marker in LIVE_DIR_MARKERS) and not args.allow_live_dir:
        raise UserError(
            "refusing: " + posix + " looks like a live agent skills directory. "
            "install into a staging directory first, review it, then pass "
            "--allow-live-dir if you really mean it.")
    if destination.is_symlink() or destination.parent.is_symlink():
        raise UserError("refusing: the destination or its parent is a symlink: " + str(destination))
    real_destination = Path(os.path.realpath(destination))
    if real_destination == Path(os.path.realpath(REPO_ROOT)):
        raise UserError("refusing: that would install the skills over this checkout")

    skills = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        raise UserError("no skills found in this checkout")

    layout = "skills/<name>/SKILL.md"
    planned = []
    for skill in skills:
        planned.append((skill, destination / skill.parent.name / "SKILL.md"))
    planned.append((REPO_ROOT / "SKILL.md", destination / "marketing-os" / "SKILL.md"))

    for _, dest in planned:
        assert_no_symlink_within(destination, dest, "install destination path")

    existing = [dest for _, dest in planned if dest.exists()]
    if existing and not args.overwrite:
        raise UserError(
            "refusing to overwrite " + str(len(existing)) + " existing file(s); "
            "re-run with --overwrite if that is what you want:\n  "
            + "\n  ".join(str(e) for e in existing[:10]))

    print("target agent : " + args.target)
    print("destination  : " + str(destination))
    print("layout       : " + layout)
    print("skills       : " + str(len(planned)))
    if args.dry_run:
        for source, dest in planned:
            print("  would copy " + source.relative_to(REPO_ROOT).as_posix() + " -> " + str(dest))
        print("dry run: nothing was written")
        return 0

    written = 0
    for source, dest in planned:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        written += 1
    receipt = {
        "kit_version": KIT_VERSION,
        "target": args.target,
        "destination": str(destination),
        "files": written,
        "installed_utc": dtmod.datetime.now(dtmod.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (destination / "marketing-os-install.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("installed " + str(written) + " skill files")
    print("receipt: " + str(destination / "marketing-os-install.json"))
    return 0


# ---------------------------------------------------------------- cli

def build_parser():
    parser = argparse.ArgumentParser(
        prog="marketing_os.py",
        description="create and check a private marketing workspace. local files only.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create a new private business workspace")
    p_init.add_argument("--workspace", required=True,
                        help="absolute path to a new or empty directory outside this repo")
    p_init.set_defaults(func=cmd_init)

    p_doctor = sub.add_parser("doctor", help="check a workspace for missing inputs")
    p_doctor.add_argument("--workspace", required=True)
    p_doctor.set_defaults(func=cmd_doctor)

    p_demo = sub.add_parser("demo", help="run the bundled fictional example end to end")
    p_demo.add_argument("--workspace", required=True)
    p_demo.set_defaults(func=cmd_demo)

    p_check = sub.add_parser("check", help="validate this distribution before publishing")
    p_check.set_defaults(func=cmd_check)

    p_package = sub.add_parser("package", help="build a zip with a sha256 manifest")
    p_package.add_argument("--dry-run", action="store_true")
    p_package.add_argument("--overwrite", action="store_true")
    p_package.set_defaults(func=cmd_package)

    p_install = sub.add_parser("install", help="copy the skills into an explicit directory")
    p_install.add_argument("--target", required=True, choices=["claude", "hermes"])
    p_install.add_argument("--destination", required=True,
                           help="absolute path to the directory that will hold the skills")
    p_install.add_argument("--dry-run", action="store_true")
    p_install.add_argument("--overwrite", action="store_true")
    p_install.add_argument("--allow-live-dir", action="store_true",
                           help="permit a path that looks like a live agent skills directory")
    p_install.set_defaults(func=cmd_install)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UserError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    except MalformedRow as exc:
        print("error: unreadable row: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
