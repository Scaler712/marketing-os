"""tests for the marketing-os command line tool. standard library only."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO / "scripts" / "marketing_os.py"

_spec = importlib.util.spec_from_file_location("marketing_os", MODULE_PATH)
mos = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mos)


def rows(text, columns, label):
    return mos.read_rows(text, columns, label)


def demo_rows():
    source = REPO / "examples" / "demo"
    ads = rows((source / "ads-2027-02-16-fictional.csv").read_text(encoding="utf-8"),
               mos.ADS_COLUMNS, "ads")
    sales = rows((source / "sales-2027-02-16-fictional.csv").read_text(encoding="utf-8"),
                 mos.SALES_COLUMNS, "sales")
    return ads, sales


class TempMixin(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mos-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        mos._WRITE_HOOK = None

    def workspace(self, name="ws"):
        target = self.tmp / name
        code = mos.main(["init", "--workspace", str(target)])
        self.assertEqual(code, 0)
        return target


class InitPathSafetyTests(TempMixin):
    def test_relative_path_refused(self):
        with self.assertRaises(mos.UserError):
            mos.validate_workspace_target("relative/path")

    def test_parent_traversal_refused(self):
        with self.assertRaises(mos.UserError):
            mos.validate_workspace_target(str(self.tmp / ".." / "escape"))

    def test_inside_distribution_source_refused(self):
        with self.assertRaises(mos.UserError) as ctx:
            mos.validate_workspace_target(str(REPO / "workspaces" / "mine"))
        self.assertIn("distribution", str(ctx.exception))

    def test_distribution_source_itself_refused(self):
        with self.assertRaises(mos.UserError):
            mos.validate_workspace_target(str(REPO))

    def test_symlinked_target_refused(self):
        real = self.tmp / "real"
        real.mkdir()
        link = self.tmp / "link"
        os.symlink(real, link)
        with self.assertRaises(mos.UserError) as ctx:
            mos.validate_workspace_target(str(link))
        self.assertIn("symlink", str(ctx.exception))

    def test_symlinked_parent_refused(self):
        real = self.tmp / "real2"
        real.mkdir()
        link = self.tmp / "link2"
        os.symlink(real, link)
        with self.assertRaises(mos.UserError) as ctx:
            mos.validate_workspace_target(str(link / "ws"))
        self.assertIn("symlink", str(ctx.exception))

    def test_symlink_escape_into_repo_refused(self):
        link = self.tmp / "sneaky"
        os.symlink(REPO, link)
        with self.assertRaises(mos.UserError):
            mos.validate_workspace_target(str(link / "ws"))

    def test_missing_parent_refused(self):
        with self.assertRaises(mos.UserError) as ctx:
            mos.validate_workspace_target(str(self.tmp / "nope" / "ws"))
        self.assertIn("parent", str(ctx.exception))

    def test_non_empty_directory_refused(self):
        target = self.tmp / "busy"
        target.mkdir()
        (target / "notes.md").write_text("mine", encoding="utf-8")
        with self.assertRaises(mos.UserError) as ctx:
            mos.validate_workspace_target(str(target))
        self.assertIn("not empty", str(ctx.exception))
        self.assertEqual((target / "notes.md").read_text(encoding="utf-8"), "mine")

    def test_existing_file_refused(self):
        target = self.tmp / "afile"
        target.write_text("x", encoding="utf-8")
        with self.assertRaises(mos.UserError):
            mos.validate_workspace_target(str(target))


class InitBehaviourTests(TempMixin):
    def test_init_creates_expected_structure(self):
        target = self.workspace()
        for rel in mos.WORKSPACE_REQUIRED_PATHS + [mos.META_NAME]:
            self.assertTrue((target / rel).exists(), rel + " missing")
        meta = json.loads((target / mos.META_NAME).read_text(encoding="utf-8"))
        self.assertEqual(meta["schema"], mos.WORKSPACE_SCHEMA)

    def test_init_twice_refuses_and_changes_nothing(self):
        target = self.workspace()
        before = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
        code = mos.main(["init", "--workspace", str(target)])
        self.assertEqual(code, 2)
        after = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_collision_fails_before_any_write(self):
        target = self.tmp / "clash"
        target.mkdir()
        (target / "business.md").write_text("my own notes", encoding="utf-8")
        original = mos.validate_workspace_target
        mos.validate_workspace_target = lambda raw, repo_root=None, must_exist=False: Path(raw)
        try:
            with self.assertRaises(mos.UserError) as ctx:
                mos.cmd_init(type("A", (), {"workspace": str(target)})())
        finally:
            mos.validate_workspace_target = original
        self.assertIn("fail-before-write", str(ctx.exception))
        self.assertEqual([p.name for p in target.iterdir()], ["business.md"])
        self.assertEqual((target / "business.md").read_text(encoding="utf-8"), "my own notes")

    def test_partial_init_rolls_back(self):
        target = self.tmp / "rollback"
        state = {"writes": 0}

        def hook(path):
            state["writes"] += 1
            if state["writes"] == 3:
                raise OSError("simulated disk failure")

        mos._WRITE_HOOK = hook
        try:
            with self.assertRaises(OSError):
                mos.cmd_init(type("A", (), {"workspace": str(target)})())
        finally:
            mos._WRITE_HOOK = None
        self.assertFalse(target.exists(), "rollback left the workspace directory behind")

    def test_rollback_keeps_pre_existing_parent(self):
        parent = self.tmp / "keepme"
        parent.mkdir()
        (parent / "untouched.txt").write_text("hi", encoding="utf-8")
        target = parent / "ws"

        def hook(path):
            raise OSError("fail on first write")

        mos._WRITE_HOOK = hook
        try:
            with self.assertRaises(OSError):
                mos.cmd_init(type("A", (), {"workspace": str(target)})())
        finally:
            mos._WRITE_HOOK = None
        self.assertTrue((parent / "untouched.txt").is_file())
        self.assertFalse(target.exists())


class DoctorTests(TempMixin):
    def test_fresh_workspace_is_not_ready(self):
        target = self.workspace()
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_doctor(type("A", (), {"workspace": str(target)})())
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 1)
        report = buf.getvalue()
        self.assertIn("NOT READY", report)
        self.assertIn("business.md field still MISSING: offer_name", report)
        self.assertIn("business.md field still MISSING: ad_account_id", report)

    def test_filled_workspace_is_ready(self):
        target = self.workspace()
        brief = REPO / "examples" / "demo" / "business-fictional.md"
        shutil.copy2(brief, target / "business.md")
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_doctor(type("A", (), {"workspace": str(target)})())
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0, buf.getvalue())
        self.assertIn("READY", buf.getvalue())

    def test_doctor_rejects_non_workspace(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        with self.assertRaises(mos.UserError) as ctx:
            mos.cmd_doctor(type("A", (), {"workspace": str(plain)})())
        self.assertIn("not a marketing-os workspace", str(ctx.exception))

    def test_doctor_flags_a_credential_in_the_workspace(self):
        target = self.workspace()
        (target / "sources" / "notes.md").write_text(
            "ad login " + "api" "_key=hunter2abc", encoding="utf-8")
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_doctor(type("A", (), {"workspace": str(target)})())
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 1)
        self.assertIn("possible credential", buf.getvalue())


class ArithmeticTests(unittest.TestCase):
    def test_zero_denominator_returns_none_not_zero(self):
        self.assertIsNone(mos.ratio(Decimal("22.40"), 0))
        self.assertEqual(mos.ratio(Decimal("22.40"), 0), None)

    def test_division_is_exact(self):
        self.assertEqual(mos.money(mos.ratio(Decimal("412.50"), 2)), Decimal("206.25"))
        self.assertEqual(mos.money(mos.ratio(Decimal("408.00"), 1)), Decimal("408.00"))
        self.assertEqual(mos.money(mos.ratio(Decimal("412.50"), 14)), Decimal("29.46"))
        self.assertEqual(mos.money(mos.ratio(Decimal("408.00"), 19)), Decimal("21.47"))

    def test_sum_of_decimals_is_exact(self):
        total = sum([Decimal("412.50"), Decimal("408.00"), Decimal("22.40")], Decimal("0"))
        self.assertEqual(total, Decimal("842.90"))

    def test_malformed_number_is_reported_not_guessed(self):
        with self.assertRaises(mos.MalformedRow):
            mos.to_decimal("n/a", "spend")
        with self.assertRaises(mos.MalformedRow):
            mos.to_decimal("", "spend")
        with self.assertRaises(mos.MalformedRow):
            mos.to_decimal("NaN", "spend")


class ParsingTests(unittest.TestCase):
    def test_missing_columns_stop_the_read(self):
        with self.assertRaises(mos.UserError) as ctx:
            mos.read_rows("a,b\n1,2\n", mos.ADS_COLUMNS, "ads")
        self.assertIn("missing columns", str(ctx.exception))

    def test_identical_duplicate_ad_row_is_dropped_once(self):
        ads_rows, _ = demo_rows()
        ads, duplicates, malformed = mos.parse_ads(ads_rows)
        self.assertEqual(len(ads), 3)
        self.assertEqual(len(duplicates), 1)
        self.assertIn("a_demo_1002", duplicates[0])
        self.assertEqual(len(malformed), 1)
        self.assertIn("spend is not a number", malformed[0])

    def test_conflicting_duplicate_ad_row_stops_the_read(self):
        text = (REPO / "examples" / "demo" / "ads-2027-02-16-fictional.csv").read_text(
            encoding="utf-8").splitlines()
        conflicting = text[2].replace("408.00", "999.00")
        broken = "\n".join(text[:4] + [conflicting]) + "\n"
        with self.assertRaises(mos.UserError) as ctx:
            mos.parse_ads(mos.read_rows(broken, mos.ADS_COLUMNS, "ads"))
        self.assertIn("two different rows", str(ctx.exception))

    def test_duplicate_order_counted_once(self):
        _, sales_rows = demo_rows()
        sales, duplicates, malformed = mos.parse_sales(sales_rows)
        order_ids = [s["order_id"] for s in sales]
        self.assertEqual(len(order_ids), len(set(order_ids)))
        self.assertEqual(len(duplicates), 1)
        self.assertIn("o_demo_5001", duplicates[0])
        self.assertEqual(len(malformed), 1)
        self.assertIn("amount is not a number", malformed[0])


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.ads_rows, self.sales_rows = demo_rows()
        self.config = json.loads(
            (REPO / "examples" / "demo" / "demo.json").read_text(encoding="utf-8"))

    def run_default(self, **overrides):
        kwargs = dict(
            expected_account_id=self.config["ad_account_id"],
            expected_sales_system_id=self.config["sales_system_id"],
            as_of=self.config["as_of"],
            wait_days=int(self.config["wait_days"]),
        )
        kwargs.update(overrides)
        return mos.reconcile(self.ads_rows, self.sales_rows, **kwargs)

    def test_known_numbers(self):
        result = self.run_default()
        self.assertEqual(result["total_spend"], Decimal("842.90"))
        self.assertEqual(result["platform_results_total"], 33)
        self.assertEqual(result["linked_new_paying_total"], 3)
        per_ad = result["per_ad"]
        self.assertEqual(mos.money(per_ad["a_demo_1001"]["cost_per_new_paying_customer"]),
                         Decimal("206.25"))
        self.assertEqual(mos.money(per_ad["a_demo_1002"]["cost_per_new_paying_customer"]),
                         Decimal("408.00"))
        self.assertIsNone(per_ad["a_demo_1003"]["cost_per_new_paying_customer"])
        self.assertEqual(per_ad["a_demo_1001"]["linked_refunded"], 1)
        self.assertEqual(per_ad["a_demo_1001"]["linked_repeat"], 1)
        self.assertEqual(len(result["unmatched_sales"]), 1)

    def test_platform_leader_and_customer_leader_can_disagree(self):
        result = self.run_default()
        self.assertEqual(result["platform_leader"], "a_demo_1002")
        self.assertEqual(result["customer_leader"], "a_demo_1001")

    def test_immature_data_is_not_a_verdict(self):
        result = self.run_default()
        self.assertEqual(result["maturity"], "not mature")
        self.assertEqual(result["verdict"], "NOT MATURE")

    def test_mature_but_disagreeing_leaders_is_inconclusive(self):
        result = self.run_default(as_of="2027-03-10")
        self.assertEqual(result["maturity"], "mature")
        self.assertEqual(result["verdict"], "INCONCLUSIVE")

    def test_mismatched_ad_account_identity_stops(self):
        with self.assertRaises(mos.UserError) as ctx:
            self.run_default(expected_account_id="act_demo_999999999999999")
        self.assertIn("identity mismatch", str(ctx.exception))

    def test_mismatched_sales_system_identity_stops(self):
        with self.assertRaises(mos.UserError) as ctx:
            self.run_default(expected_sales_system_id="some-other-store")
        self.assertIn("identity mismatch", str(ctx.exception))

    def test_mixed_ad_accounts_stop(self):
        extra = dict(self.ads_rows[0])
        extra["account_id"] = "act_demo_000000000000002"
        extra["ad_id"] = "a_demo_2001"
        with self.assertRaises(mos.UserError) as ctx:
            mos.reconcile(self.ads_rows + [extra], self.sales_rows,
                          expected_account_id=None, expected_sales_system_id=None,
                          as_of=None, wait_days=0)
        self.assertIn("mixes ad accounts", str(ctx.exception))

    def test_mixed_currencies_stop(self):
        extra = dict(self.ads_rows[0])
        extra["ad_id"] = "a_demo_2002"
        extra["currency"] = "USD"
        with self.assertRaises(mos.UserError) as ctx:
            mos.reconcile(self.ads_rows + [extra], self.sales_rows,
                          expected_account_id=None, expected_sales_system_id=None,
                          as_of=None, wait_days=0)
        self.assertIn("mixed currencies", str(ctx.exception))

    def test_no_linked_sales_is_inconclusive_not_a_win(self):
        sales = [r for r in self.sales_rows]
        for row in sales:
            row["ad_id"] = ""
        result = self.run_default(as_of="2027-03-10")
        self.assertEqual(result["linked_new_paying_total"], 0)
        self.assertEqual(result["verdict"], "INCONCLUSIVE")

    def test_empty_ads_export_stops(self):
        with self.assertRaises(mos.UserError):
            mos.reconcile([], self.sales_rows, expected_account_id=None,
                          expected_sales_system_id=None, as_of=None, wait_days=0)


class DemoTests(TempMixin):
    def test_demo_end_to_end(self):
        target = self.workspace("demo-ws")
        code = mos.main(["demo", "--workspace", str(target)])
        self.assertEqual(code, 0)
        folders = sorted((target / "output").glob("demo-*"))
        self.assertEqual(len(folders), 1)
        out = folders[0]
        for name in ("00-README.md", "01-business-fictional.md",
                     "02-campaign-pack-fictional.md", "03-test-plan-fictional.md",
                     "04-reconciliation-fictional.md", "05-summary-fictional.json"):
            self.assertTrue((out / name).is_file(), name + " missing")
        reading = (out / "04-reconciliation-fictional.md").read_text(encoding="utf-8")
        self.assertIn("FICTIONAL SYNTHETIC DATA", reading)
        self.assertIn("206.25 EUR", reading)
        self.assertIn("no observed cost per customer yet", reading)
        self.assertIn("NOT MATURE", reading)
        summary = json.loads((out / "05-summary-fictional.json").read_text(encoding="utf-8"))
        self.assertTrue(summary["fictional"])
        self.assertEqual(summary["total_spend"], "842.90")
        self.assertIsNone(summary["per_ad"]["a_demo_1003"]["cost_per_new_paying_customer"])

    def test_demo_never_overwrites(self):
        target = self.workspace("demo-twice")
        self.assertEqual(mos.main(["demo", "--workspace", str(target)]), 0)
        self.assertEqual(mos.main(["demo", "--workspace", str(target)]), 0)
        folders = sorted(p.name for p in (target / "output").glob("demo-*"))
        self.assertEqual(len(folders), 2)
        self.assertTrue(folders[1].endswith("-2"))

    def test_demo_requires_a_workspace(self):
        plain = self.tmp / "nothing"
        plain.mkdir()
        self.assertEqual(mos.main(["demo", "--workspace", str(plain)]), 2)


class CheckAndPackageTests(TempMixin):
    def test_check_passes_on_this_repo(self):
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_check(type("A", (), {})())
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0, buf.getvalue())

    def test_packageable_files_exclude_private_and_runtime(self):
        files = [p.relative_to(REPO).as_posix() for p in mos.packageable_files(REPO)]
        self.assertIn("scripts/marketing_os.py", files)
        self.assertIn("skills/business-brief/SKILL.md", files)
        for bad in files:
            self.assertFalse(bad.startswith("dist/"), bad)
            self.assertNotIn("__pycache__", bad)
            self.assertFalse(bad.endswith(".pyc"), bad)
            self.assertNotEqual(Path(bad).name, mos.META_NAME)
            self.assertFalse(Path(bad).name.startswith(".env"), bad)

    def test_package_dry_run_writes_nothing(self):
        dist = REPO / "dist"
        before = sorted(p.name for p in dist.glob("*")) if dist.exists() else []
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_package(type("A", (), {"dry_run": True, "overwrite": False})())
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0)
        self.assertIn("dry run", buf.getvalue())
        after = sorted(p.name for p in dist.glob("*")) if dist.exists() else []
        self.assertEqual(before, after)

    def test_shipped_code_has_no_network_imports(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        for banned in ("import socket", "import urllib", "import requests",
                       "import http.client", "from urllib"):
            self.assertNotIn(banned, source, banned + " must not be used")


class InstallTests(TempMixin):
    def args(self, **kwargs):
        base = {"target": "claude", "destination": str(self.tmp / "staging"),
                "dry_run": False, "overwrite": False, "allow_live_dir": False}
        base.update(kwargs)
        return type("A", (), base)()

    def test_dry_run_writes_nothing(self):
        destination = self.tmp / "staging"
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_install(self.args(dry_run=True))
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0)
        self.assertIn("nothing was written", buf.getvalue())
        self.assertFalse(destination.exists())

    def test_install_then_refuse_overwrite(self):
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            self.assertEqual(mos.cmd_install(self.args()), 0)
        finally:
            sys.stdout = stdout
        destination = self.tmp / "staging"
        self.assertTrue((destination / "business-brief" / "SKILL.md").is_file())
        self.assertTrue((destination / "marketing-os" / "SKILL.md").is_file())
        self.assertTrue((destination / "marketing-os-install.json").is_file())
        with self.assertRaises(mos.UserError) as ctx:
            mos.cmd_install(self.args())
        self.assertIn("refusing to overwrite", str(ctx.exception))

    def test_live_agent_directory_refused(self):
        with self.assertRaises(mos.UserError) as ctx:
            mos.cmd_install(self.args(destination=str(self.tmp / "home" / ".claude" / "skills")))
        self.assertIn("live agent skills directory", str(ctx.exception))

    def test_destination_equal_to_the_checkout_refused(self):
        with self.assertRaises(mos.UserError) as ctx:
            mos.cmd_install(self.args(destination=str(REPO)))
        self.assertIn("over this checkout", str(ctx.exception))

    def test_relative_destination_refused(self):
        with self.assertRaises(mos.UserError):
            mos.cmd_install(self.args(destination="staging"))

    def test_installed_skills_are_self_contained(self):
        stdout, sys.stdout = sys.stdout, io.StringIO()
        try:
            mos.cmd_install(self.args())
        finally:
            sys.stdout = stdout
        destination = self.tmp / "staging"
        installed = sorted(destination.glob("*/SKILL.md"))
        self.assertGreaterEqual(len(installed), 11)
        for path in installed:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---"), path.name + " lost its frontmatter")
            self.assertNotIn("](../", text)
            self.assertNotIn("](./references", text)


def ads_row(**overrides):
    row = {
        "account_id": "act_demo_000000000000001",
        "campaign_id": "c_demo_900001",
        "ad_id": "a_demo_1001",
        "ad_name": "hook-one",
        "date_start": "2027-02-01",
        "date_end": "2027-02-14",
        "currency": "EUR",
        "timezone": "Europe/Riga",
        "attribution_window": "7d_click",
        "spend": "100.00",
        "impressions": "1000",
        "clicks": "100",
        "platform_results": "10",
        "results_action_type": "offsite_purchase",
    }
    row.update(overrides)
    return row


def sales_row(**overrides):
    row = {
        "sales_system_id": "fablewright-demo-store",
        "order_id": "o_demo_7001",
        "order_date": "2027-02-05",
        "amount": "240.00",
        "currency": "EUR",
        "refunded": "no",
        "customer_type": "new",
        "ad_id": "a_demo_1001",
    }
    row.update(overrides)
    return row


class SalesFieldValidationTests(unittest.TestCase):
    """a field we cannot read is a reported row, never a counted new paying customer."""

    def parse_one(self, **overrides):
        return mos.parse_sales([sales_row(**overrides)])

    def test_blank_customer_type_is_malformed_not_new_paid(self):
        sales, _, malformed = self.parse_one(customer_type="")
        self.assertEqual(sales, [])
        self.assertIn("customer_type must be new or repeat", malformed[0])

    def test_unknown_customer_type_is_malformed_not_new_paid(self):
        sales, _, malformed = self.parse_one(customer_type="vip")
        self.assertEqual(sales, [])
        self.assertIn("customer_type must be new or repeat", malformed[0])

    def test_repeat_and_new_are_both_accepted(self):
        for value in ("new", "repeat", "REPEAT"):
            sales, _, malformed = self.parse_one(customer_type=value)
            self.assertEqual(malformed, [], value)
            self.assertEqual(len(sales), 1)

    def test_non_positive_amount_is_malformed(self):
        for value in ("0", "0.00", "-240.00"):
            sales, _, malformed = self.parse_one(amount=value)
            self.assertEqual(sales, [], value)
            self.assertIn("positive paid amount", malformed[0])

    def test_invalid_order_date_is_malformed(self):
        for value in ("", "16/02/2027", "2027-02-30"):
            sales, _, malformed = self.parse_one(order_date=value)
            self.assertEqual(sales, [], value)
            self.assertIn("order_date", malformed[0])

    def test_refunded_field_is_strict(self):
        sales, _, malformed = self.parse_one(refunded="maybe")
        self.assertEqual(sales, [])
        self.assertIn("refunded must be one of", malformed[0])
        sales, _, malformed = self.parse_one(refunded="")
        self.assertEqual(sales, [])
        self.assertIn("refunded must be one of", malformed[0])
        for value, expected in (("yes", True), ("TRUE", True), ("1", True),
                                ("no", False), ("false", False), ("0", False)):
            sales, _, malformed = self.parse_one(refunded=value)
            self.assertEqual(malformed, [], value)
            self.assertIs(sales[0]["refunded"], expected)

    def test_invalid_row_never_reaches_the_new_paying_count(self):
        result = mos.reconcile(
            [ads_row()],
            [sales_row(order_id="o_bad", customer_type=""),
             sales_row(order_id="o_good")],
            expected_account_id=None, expected_sales_system_id=None,
            as_of="2027-03-01", wait_days=14)
        self.assertEqual(result["linked_new_paying_total"], 1)
        self.assertEqual(len(result["sales_malformed"]), 1)


class SalesSystemIdentityTests(unittest.TestCase):
    def test_extra_sales_system_is_rejected_even_when_expected_is_present(self):
        with self.assertRaises(mos.UserError) as ctx:
            mos.reconcile(
                [ads_row()],
                [sales_row(), sales_row(order_id="o_x", sales_system_id="other-store")],
                expected_account_id=None,
                expected_sales_system_id="fablewright-demo-store",
                as_of=None, wait_days=0)
        self.assertIn("identity mismatch", str(ctx.exception))
        self.assertIn("other-store", str(ctx.exception))

    def test_single_expected_system_is_accepted(self):
        result = mos.reconcile(
            [ads_row()], [sales_row()],
            expected_account_id=None,
            expected_sales_system_id="fablewright-demo-store",
            as_of=None, wait_days=0)
        self.assertEqual(result["sales_systems"], ["fablewright-demo-store"])

    def test_mixed_systems_with_no_expected_id_stop(self):
        with self.assertRaises(mos.UserError) as ctx:
            mos.reconcile(
                [ads_row()],
                [sales_row(), sales_row(order_id="o_x", sales_system_id="other-store")],
                expected_account_id=None, expected_sales_system_id=None,
                as_of=None, wait_days=0)
        self.assertIn("mixes sales systems", str(ctx.exception))


class VerdictGuardTests(unittest.TestCase):
    def test_unknown_maturity_is_never_leaning(self):
        result = mos.reconcile(
            [ads_row()], [sales_row()],
            expected_account_id=None, expected_sales_system_id=None,
            as_of="not-a-date", wait_days=14)
        self.assertEqual(result["maturity"], "unknown")
        self.assertNotEqual(result["verdict"], "LEANING")
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        self.assertIn("maturity could not be established", result["verdict_why"])

    def test_missing_as_of_is_never_leaning(self):
        result = mos.reconcile(
            [ads_row()], [sales_row()],
            expected_account_id=None, expected_sales_system_id=None,
            as_of=None, wait_days=14)
        self.assertEqual(result["maturity"], "unknown")
        self.assertEqual(result["verdict"], "INCONCLUSIVE")

    def test_agreeing_leaders_on_mature_data_can_still_lean(self):
        result = mos.reconcile(
            [ads_row()], [sales_row()],
            expected_account_id=None, expected_sales_system_id=None,
            as_of="2027-03-01", wait_days=14)
        self.assertEqual(result["maturity"], "mature")
        self.assertEqual(result["verdict"], "LEANING")

    def mixed(self, **second):
        return mos.reconcile(
            [ads_row(), ads_row(ad_id="a_demo_1002", **second)],
            [sales_row()],
            expected_account_id=None, expected_sales_system_id=None,
            as_of="2027-03-01", wait_days=14)

    def test_mixed_attribution_windows_are_not_ranked(self):
        result = self.mixed(attribution_window="1d_view")
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        self.assertIsNone(result["platform_leader"])
        self.assertIsNone(result["customer_leader"])
        self.assertIn("attribution windows", result["verdict_why"])

    def test_mixed_window_dates_are_not_ranked(self):
        result = self.mixed(date_end="2027-02-20")
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        self.assertIn("window end dates", result["verdict_why"])
        result = self.mixed(date_start="2027-01-01")
        self.assertIn("window start dates", result["verdict_why"])

    def test_mixed_result_action_types_are_not_ranked(self):
        result = self.mixed(results_action_type="lead")
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        self.assertIn("result action types", result["verdict_why"])

    def test_mixed_export_says_so_in_the_rendered_reading(self):
        report = mos.render_reconciliation(self.mixed(attribution_window="1d_view"),
                                           "mixed")
        self.assertIn("NOT COMPARABLE", report)
        self.assertIn("None", str(mos.reconcile(
            [ads_row(), ads_row(ad_id="a_demo_1002", attribution_window="1d_view")],
            [sales_row()], expected_account_id=None, expected_sales_system_id=None,
            as_of="2027-03-01", wait_days=14)["platform_leader"]))


class RenderThresholdTests(unittest.TestCase):
    def report(self):
        result = mos.reconcile(
            [ads_row(), ads_row(ad_id="a_demo_1003", spend="2.00",
                                platform_results="0", clicks="2")],
            [sales_row()],
            expected_account_id=None, expected_sales_system_id=None,
            as_of="2027-03-01", wait_days=14)
        return mos.render_reconciliation(result, "threshold check")

    def test_no_invented_spend_threshold_in_the_reading(self):
        report = self.report()
        for banned in ("enough spend", "0.05", "under-funded by", "too little spend"):
            self.assertNotIn(banned, report, banned)

    def test_share_of_spend_is_shown_as_a_description(self):
        report = self.report()
        self.assertIn("share of spend in this window", report)
        self.assertIn("that bar is the owner's to set", report)


class SymlinkWriteSafetyTests(TempMixin):
    def test_demo_refuses_a_symlinked_output_directory(self):
        target = self.workspace("demo-symlink")
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        shutil.rmtree(target / "output")
        os.symlink(elsewhere, target / "output")
        with self.assertRaises(mos.UserError) as ctx:
            mos.cmd_demo(type("A", (), {"workspace": str(target)})())
        self.assertIn("symlink", str(ctx.exception))
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_symlink_guard_rejects_a_planted_file_link(self):
        base = self.tmp / "base"
        (base / "sub").mkdir(parents=True)
        outside = self.tmp / "outside.md"
        outside.write_text("owner data", encoding="utf-8")
        os.symlink(outside, base / "sub" / "report.md")
        with self.assertRaises(mos.UserError) as ctx:
            mos.assert_no_symlink_within(base, base / "sub" / "report.md", "demo output path")
        self.assertIn("symlink", str(ctx.exception))

    def test_symlink_guard_accepts_a_plain_path(self):
        base = self.tmp / "plainbase"
        base.mkdir()
        self.assertEqual(mos.assert_no_symlink_within(base, base / "a" / "b.md", "x"),
                         base / "a" / "b.md")

    def test_symlink_guard_refuses_a_path_outside_base(self):
        base = self.tmp / "outsidebase"
        base.mkdir()
        with self.assertRaises(mos.UserError) as ctx:
            mos.assert_no_symlink_within(base, self.tmp / "other.md", "x")
        self.assertIn("not inside", str(ctx.exception))

    def install_args(self, **kwargs):
        base = {"target": "claude", "destination": str(self.tmp / "staging"),
                "dry_run": False, "overwrite": True, "allow_live_dir": False}
        base.update(kwargs)
        return type("A", (), base)()

    def test_install_refuses_a_symlinked_skill_subfolder(self):
        destination = self.tmp / "staging"
        destination.mkdir()
        elsewhere = self.tmp / "escape"
        elsewhere.mkdir()
        os.symlink(elsewhere, destination / "business-brief")
        with self.assertRaises(mos.UserError) as ctx:
            mos.cmd_install(self.install_args())
        self.assertIn("symlink", str(ctx.exception))
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_install_refuses_a_symlinked_destination_file(self):
        destination = self.tmp / "staging2"
        (destination / "business-brief").mkdir(parents=True)
        victim = self.tmp / "victim.md"
        victim.write_text("owner data", encoding="utf-8")
        os.symlink(victim, destination / "business-brief" / "SKILL.md")
        with self.assertRaises(mos.UserError) as ctx:
            mos.cmd_install(self.install_args(destination=str(destination)))
        self.assertIn("symlink", str(ctx.exception))
        self.assertEqual(victim.read_text(encoding="utf-8"), "owner data")


class PackageSymlinkAndGateTests(TempMixin):
    def plant_symlink(self):
        outside = self.tmp / "private.md"
        outside.write_text("owner only", encoding="utf-8")
        link = REPO / "docs" / "zz-test-link.md"
        self.addCleanup(lambda: link.unlink() if link.is_symlink() else None)
        os.symlink(outside, link)
        return link

    def test_packageable_files_never_follow_a_symlink(self):
        link = self.plant_symlink()
        files = [p.relative_to(REPO).as_posix() for p in mos.packageable_files(REPO)]
        self.assertNotIn("docs/zz-test-link.md", files)
        self.assertIn(link, mos.symlinked_paths(REPO))

    def test_check_reports_a_symlink_in_the_source(self):
        self.plant_symlink()
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_check(type("A", (), {})())
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 1)
        self.assertIn("symlink in the distribution source", buf.getvalue())

    def test_package_runs_the_check_gate_before_writing(self):
        self.plant_symlink()
        archive = REPO / "dist" / ("marketing-os-" + mos.KIT_VERSION + ".zip")
        existed = archive.exists()
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            with self.assertRaises(mos.UserError) as ctx:
                mos.cmd_package(type("A", (), {"dry_run": False, "overwrite": True})())
        finally:
            sys.stdout = stdout
        self.assertIn("nothing was packaged", str(ctx.exception))
        self.assertEqual(archive.exists(), existed)

    def test_package_dry_run_does_not_create_dist(self):
        dist = REPO / "dist"
        removed = False
        if dist.is_dir() and not any(dist.iterdir()):
            dist.rmdir()
            removed = True
        if removed:
            self.addCleanup(lambda: dist.mkdir(exist_ok=True))
        buf = io.StringIO()
        stdout, sys.stdout = sys.stdout, buf
        try:
            code = mos.cmd_package(type("A", (), {"dry_run": True, "overwrite": False})())
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0)
        if removed:
            self.assertFalse(dist.exists(), "dry run created dist/")
            self.assertIn("dist/ was not created", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
