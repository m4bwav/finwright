"""Tests for fw.py. Invented numbers only; no network. Run: python tests/test_fw.py"""
import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "finwright" / "scripts"))
import fw  # noqa: E402


def run(*argv) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = fw.main(list(argv))
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class FwTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = str(Path(self.tmp.name) / "data")
        os.environ["FINWRIGHT_TODAY"] = "2026-10-12"
        self.assertEqual(run("--data", self.d, "init")[0], 0)

    def tearDown(self):
        self.tmp.cleanup()

    def fw(self, *argv):
        code, out, err = run("--data", self.d, *argv)
        self.assertEqual(code, 0, err)
        return out

    def household(self):
        self.fw("account", "add", "checking", "--type", "cash", "--last4", "1111")
        self.fw("account", "add", "brokerage", "--type", "taxable")
        self.fw("account", "add", "401k", "--type", "tax_deferred")
        self.fw("account", "add", "house", "--type", "real_estate")
        self.fw("account", "add", "mortgage", "--type", "mortgage")
        self.fw("account", "add", "visa", "--type", "credit_card")
        self.fw("account", "add", "match", "--type", "unvested")
        self.fw("balance", "set", "checking", "$5,000.00", "--as-of", "2026-10-01", "--source", "statement")
        self.fw("balance", "set", "brokerage", "20000", "--as-of", "2026-10-01")
        self.fw("balance", "set", "401k", "100000", "--as-of", "2026-09-30")
        self.fw("balance", "set", "house", "300000", "--as-of", "2026-06-01", "--source", "zillow")
        self.fw("balance", "set", "mortgage", "-200000", "--as-of", "2026-10-01")
        self.fw("balance", "set", "visa", "1500", "--as-of", "2026-10-05")
        self.fw("balance", "set", "match", "4000", "--as-of", "2026-09-30")

    # ---- parsing ----
    def test_money_formats(self):
        self.assertEqual(fw.money("$1,234.50"), Decimal("1234.50"))
        self.assertEqual(fw.money("(12.00)"), Decimal("-12.00"))
        self.assertEqual(fw.money("12.00-"), Decimal("-12.00"))
        with self.assertRaises(fw.FwError):
            fw.money("--")

    def test_init_refuses_inside_git(self):
        repo = Path(self.tmp.name) / "repo"
        (repo / ".git").mkdir(parents=True)
        code, _, err = run("--data", str(repo / "money"), "init")
        self.assertEqual(code, 2)
        self.assertIn("inside the git repository", err)

    def test_last4_only(self):
        code, _, err = run("--data", self.d, "account", "add", "x", "--type", "cash", "--last4", "123456789")
        self.assertEqual(code, 2)
        self.assertIn("four letters or digits", err)

    # ---- net worth ----
    def test_networth_lines(self):
        self.household()
        nw = json.loads(self.fw("networth", "--json"))
        # assets 5000+20000+100000+300000 = 425000; liabilities 200000+1500
        self.assertEqual(Decimal(nw["assets"]), Decimal("425000"))
        self.assertEqual(Decimal(nw["liabilities"]), Decimal("201500"))
        self.assertEqual(Decimal(nw["total"]), Decimal("223500"))
        self.assertEqual(Decimal(nw["liquid"]), Decimal("23500"))  # 5000+20000-1500
        self.assertEqual(Decimal(nw["investable"]), Decimal("125000"))
        # after tax: 223500 - 100000*0.22 - 300000*0.06 = 183500
        self.assertEqual(Decimal(nw["after_tax_estimate"]), Decimal("183500"))
        self.assertEqual(Decimal(nw["unvested_not_counted"]), Decimal("4000"))

    def test_latest_balance_wins_and_as_of(self):
        self.household()
        self.fw("balance", "set", "checking", "6000", "--as-of", "2026-10-10")
        nw = json.loads(self.fw("networth", "--json"))
        self.assertEqual(Decimal(nw["by_type"]["cash"]), Decimal("6000"))
        old = json.loads(self.fw("networth", "--json", "--as-of", "2026-10-02"))
        self.assertEqual(Decimal(old["by_type"]["cash"]), Decimal("5000"))

    def test_stale_warning(self):
        self.household()
        os.environ["FINWRIGHT_TODAY"] = "2026-12-31"
        out = self.fw("networth")
        self.assertIn("checking: balance is 91 days old", out)
        self.assertIn("not financial", out)

    def test_snapshot_and_history(self):
        self.household()
        self.fw("networth", "--save", "--as-of", "2026-09-30")
        self.fw("balance", "set", "checking", "7000", "--as-of", "2026-10-11")
        self.fw("config", "set", "after_tax_rate", "0.24")
        self.fw("networth", "--save")
        out = self.fw("history")
        self.assertIn("2026-10-12", out)
        self.assertIn("(method changed)", out)

    # ---- bonds ----
    def write_sb_cache(self):
        rows = [{"issue_year": "2022", "issue_jan_amt": "30.66", "issue_feb_amt": "30.58",
                 "issue_mar_amt": "30.50", "issue_apr_amt": "30.42", "issue_may_amt": "29.76",
                 "issue_jun_amt": "29.68", "issue_jul_amt": "29.60", "issue_aug_amt": "29.53",
                 "issue_sep_amt": "29.45", "issue_oct_amt": "29.38", "issue_nov_amt": "28.81",
                 "issue_dec_amt": "28.72"},
                {"issue_year": "2026", **{f"issue_{m}_amt": "0.00" for m in fw.MONTHS[:10]},
                 "issue_nov_amt": "null", "issue_dec_amt": "null"}]
        (Path(self.d) / "cache" / "sb_value-I-2026-10.json").write_text(json.dumps(rows))

    def test_bond_value_from_treasury_file(self):
        self.write_sb_cache()
        self.fw("bond", "add", "--series", "I", "--issue", "2022-01", "--denomination", "1000")
        self.fw("bond", "add", "--series", "I", "--issue", "2026-03", "--denomination", "500")
        out = self.fw("bond", "value", "--month", "2026-10")
        self.assertIn("$1,226.40", out)  # 30.66 * 40
        self.assertIn("12-month minimum hold", out)
        nw = json.loads(self.fw("networth", "--json"))
        self.assertEqual(Decimal(nw["by_type"]["savings_bond"]), Decimal("1226.40"))

    def test_bond_account_total_until_bonds_listed(self):
        self.fw("account", "add", "td", "--type", "savings_bond")
        self.fw("balance", "set", "td", "2000")
        nw = json.loads(self.fw("networth", "--json"))
        self.assertEqual(Decimal(nw["by_type"]["savings_bond"]), Decimal("2000"))
        self.assertEqual(Decimal(nw["liquid"]), Decimal("2000"))
        self.write_sb_cache()
        self.fw("bond", "add", "--series", "I", "--issue", "2022-01", "--denomination", "1000")
        nw = json.loads(self.fw("networth", "--json"))
        self.assertEqual(Decimal(nw["by_type"]["savings_bond"]), Decimal("1226.40"))
        self.assertTrue(any("td: balance ignored" in w for w in nw["warnings"]))

    def test_bond_without_cache_warns(self):
        self.fw("bond", "add", "--series", "EE", "--issue", "2020-05", "--denomination", "100")
        nw = json.loads(self.fw("networth", "--json"))
        self.assertTrue(any("bond refresh" in w for w in nw["warnings"]))

    # ---- allocation, fees, returns ----
    def test_allocation_bands(self):
        self.household()
        self.fw("holding", "set", "401k", "FXAIX", "70000", "--asset-class", "us_stock", "--expense-ratio", "0.00015")
        self.fw("holding", "set", "401k", "BOND", "30000", "--asset-class", "bond", "--expense-ratio", "0.005")
        self.fw("config", "set", "target", "us_stock=0.6")
        self.fw("config", "set", "target", "bond=0.4")
        out = self.fw("allocation")
        self.assertIn("REBALANCE BAND CROSSED", out)  # 70% vs 60% is 10 points
        fees = self.fw("fees")
        # 70000*0.00015 + 30000*0.005 = 10.5 + 150 = 160.50 on 100000 -> 0.16%
        self.assertIn("$160.50", fees)
        self.assertIn("0.16%", fees)

    def test_import_holdings_with_preamble(self):
        self.household()
        f = Path(self.tmp.name) / "positions.csv"
        f.write_text("Account summary,,\n\nSymbol,Description,Quantity,Current Value\n"
                     "VTI,Total market,10,\"$2,500.00\"\nSPAXX**,Money market,,$500.00\n"
                     "Pending activity,,,\n", encoding="utf-8")
        out = self.fw("import", "holdings", str(f), "--account", "brokerage", "--as-of", "2026-10-11",
                      "--classes", "VTI=us_stock,SPAXX=cash", "--units-col", "Quantity", "--set-balance")
        self.assertIn("imported 2 holding(s)", out)
        self.assertIn("$3,000.00", out)
        nw = json.loads(self.fw("networth", "--json"))
        self.assertEqual(Decimal(nw["by_type"]["taxable"]), Decimal("3000.00"))

    def test_xirr_known_answer(self):
        # 1000 in, worth 1100 a year later = 10%
        r = fw.xirr([(dt.date(2025, 1, 1), Decimal(-1000)), (dt.date(2026, 1, 1), Decimal(1100))])
        self.assertAlmostEqual(float(r), 0.10, places=5)

    def test_returns_with_contribution(self):
        self.fw("account", "add", "ira", "--type", "roth")
        self.fw("balance", "set", "ira", "10000", "--as-of", "2025-01-01")
        self.fw("flow", "add", "ira", "7000", "--date", "2025-07-02")
        self.fw("balance", "set", "ira", "18000", "--as-of", "2026-01-01")
        out = self.fw("returns", "ira")
        # 10000*(1+r) + 7000*(1+r)**0.5 = 18000 gives r = 7.44% (Modified Dietz agrees: 1000/13500)
        self.assertIn("XIRR) 7.44%", out)

    # ---- reference data ----
    def test_limits_known_and_unknown_year(self):
        self.assertIn("$24,500.00", self.fw("limits", "--year", "2026"))
        code, _, err = run("--data", self.d, "limits", "--year", "2031")
        self.assertEqual(code, 2)
        self.assertIn("do not guess", err)

    def test_benchmark(self):
        self.assertIn("$253,700.00", self.fw("benchmark", "--age", "52"))

    def test_check_flags_rates_after_change_date(self):
        self.assertEqual(run("--data", self.d, "check")[0], 0)
        os.environ["FINWRIGHT_TODAY"] = "2026-11-02"
        code, out, _ = run("--data", self.d, "check")
        self.assertEqual(code, 1)
        self.assertIn("i_bond_rate", out)

    # ---- redaction ----
    def test_redact(self):
        text = "Acct 1234567890123 SSN 123-45-6789 card 4111 1111 1111 1234 total $1,234.56"
        out = fw.redact_text(text)
        self.assertNotIn("1234567890123", out)
        self.assertIn("****0123", out)
        self.assertIn("***-**-****", out)
        self.assertIn("****1234", out)
        self.assertIn("$1,234.56", out)

    def test_rates_file_shape(self):
        rates = json.loads(fw.RATES_FILE.read_text(encoding="utf-8"))
        for key in ("limits", "savings_bond_rates", "scf", "next_change"):
            self.assertIn(key, rates)
        for p in rates["savings_bond_rates"]:
            self.assertTrue(p["source"].startswith("https://"))

    def test_hunt_tracks_old_plans(self):
        out = self.fw("hunt", "add", "acme", "--employer", "Acme Widgets", "--years", "2011-2014",
                      "--ein", "123456789")
        self.assertIn("Form 5500", out)
        code, _, err = run("--data", self.d, "hunt", "add", "acme", "--employer", "Acme")
        self.assertEqual(code, 2)
        code, _, err = run("--data", self.d, "hunt", "update", "acme", "--ein", "12-34")
        self.assertEqual(code, 2)
        code, _, err = run("--data", self.d, "hunt", "update", "acme", "--account", "nope")
        self.assertEqual(code, 2)
        self.fw("hunt", "update", "acme", "--status", "found", "--recordkeeper", "Example RK",
                "--note", "called, balance on next statement")
        self.fw("account", "add", "acme401k", "--type", "tax_deferred")
        self.fw("hunt", "update", "acme", "--status", "rolled_over", "--account", "acme401k")
        self.fw("hunt", "add", "beta", "--employer", "Beta Co", "--next", "order SSA-7050")
        out = self.fw("hunt", "list")
        self.assertIn("EIN 12-3456789", out)
        self.assertIn("-> acme401k", out)
        self.assertIn("1 of 2 searches open", out)
        self.assertIn("2026-10-12: called", out)
        self.assertIn("next: order SSA-7050", out)

    def test_import_monarch_balances(self):
        self.fw("account", "add", "chk", "--type", "cash")
        self.fw("account", "add", "visa", "--type", "credit_card")
        f = Path(self.tmp.name) / "monarch.csv"
        f.write_text(chr(0xFEFF) + """Date,Balance,Account
2026-10-01,1000.50,Everyday Checking (...1234)
2026-10-11,1200.00,Everyday Checking (...1234)
2026-10-11,-250.25,Visa Signature
2026-10-11,99.00,Old Brokerage
""", encoding="utf-8")
        code, _, err = run("--data", self.d, "import", "monarch", str(f))
        self.assertEqual(code, 2)
        self.assertIn("'Everyday Checking (...1234)'", err)
        self.fw("monarch", "map", "Everyday Checking (...1234)", "chk")
        self.fw("monarch", "map", "Visa Signature", "visa")
        out = self.fw("import", "monarch", str(f), "--skip-unmapped", "--dry-run")
        self.assertIn("would import 2", out)
        out = self.fw("import", "monarch", str(f), "--skip-unmapped")
        self.assertIn("imported 2", out)
        self.assertIn("'Old Brokerage'", out)
        rows = {r["account"]: r["value"] for r in fw.read_rows(Path(self.d), "balances.csv")}
        self.assertEqual(rows, {"chk": "1200.00", "visa": "250.25"})
        out = self.fw("import", "monarch", str(f), "--skip-unmapped")
        self.assertIn("imported 0 balance row(s)", out)
        self.assertIn("2 duplicate(s)", out)
        f.write_text("""Date,Balance,Account
2026-10-12,40.00,Visa Signature
""", encoding="utf-8")
        self.assertIn("positive Monarch balance", self.fw("import", "monarch", str(f)))

    def test_import_bofa_activity(self):
        self.fw("account", "add", "chk", "--type", "cash")
        self.fw("account", "add", "card", "--type", "credit_card", "--last4", "1111")
        f = Path(self.tmp.name) / "stmt.csv"
        f.write_text(chr(0xFEFF) + """Description,,Summary Amt.
Beginning balance as of 08/30/2026,,"1,000.00"
Total credits,,"2,500.00"
Total debits,,"-1,300.00"
Ending balance as of 10/12/2026,,"2,200.00"

Date,Description,Amount,Running Bal.
08/30/2026,Beginning balance as of 08/30/2026,,"1,000.00"
09/05/2026,"Widget Co DES:PAYROLL ID:123456 INDN:A Person CO ID:999 PPD","2,500.00","3,500.00"
09/20/2026,"Online Banking payment to CRD 1111 Confirmation# abc123","-300.00","3,200.00"
10/02/2026,"Online Banking transfer to BRK 9z99 Confirmation# 777","-1,000.00","2,200.00"
""", encoding="utf-8")
        out = self.fw("import", "bofa", str(f), "chk", "--monthly")
        self.assertIn("arithmetic OK", out)
        self.assertIn("imported 3 balance row(s)", out)  # Aug, Sep, Oct month ends (Oct = ending)
        self.assertIn("Widget Co", out)
        self.assertNotIn("123456", out)
        self.assertIn("CRD ...1111: 1 transfer(s), -$300.00  [tracked as card]", out)
        self.assertIn("BRK ...9Z99: 1 transfer(s), -$1,000.00  [NOT TRACKED]", out)
        rows = [(r["date"], r["value"]) for r in fw.read_rows(Path(self.d), "balances.csv")]
        self.assertEqual(rows, [("2026-08-30", "1000.00"), ("2026-09-20", "3200.00"),
                                ("2026-10-12", "2200.00")])
        self.assertIn("3 duplicate(s)", self.fw("import", "bofa", str(f), "chk", "--monthly"))
        f.write_text(f.read_text(encoding="utf-8").replace('"3,200.00"', '"3,250.00"'), encoding="utf-8")
        self.assertIn("warning: 2026-09-20 running balance", self.fw("import", "bofa", str(f), "chk", "--dry-run"))
        code, _, err = run("--data", self.d, "import", "bofa", str(f), "card")
        self.assertEqual(code, 2)

    def test_hunt_file_created_for_old_data_folders(self):
        (Path(self.d) / "hunt.csv").unlink()
        self.assertIn("no searches yet", self.fw("hunt", "list"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
