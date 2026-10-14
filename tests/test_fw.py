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
        self.assertIn("over 1 period(s)) 7.40% a year", out)  # 1000 / (10000 + 7000 * 183/365)

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

    # ---- 0.6.0 ----
    def test_holdings_reimport_replaces_and_keeps_expense_ratio(self):
        self.household()
        f = Path(self.tmp.name) / "positions.csv"
        f.write_text("Symbol,Current Value\nVTI,\"$2,500.00\"\nSPAXX**,$500.00\n", encoding="utf-8")
        args = ("import", "holdings", str(f), "--account", "brokerage", "--as-of", "2026-10-11",
                "--classes", "VTI=us_stock,SPAXX=cash")
        self.fw(*args)
        self.fw("holding", "set", "brokerage", "VTI", "2500", "--asset-class", "us_stock",
                "--expense-ratio", "0.0003", "--as-of", "2026-10-11")
        self.assertIn("replaced 2 earlier row(s)", self.fw(*args))
        self.assertIn("total $3,000.00", self.fw("allocation"))
        fees = self.fw("fees")
        self.assertIn("$0.75", fees)  # 2500 * 0.0003, carried over from the hand-entered row
        self.assertIn("no expense ratio for: SPAXX", fees)

    def test_fee_projection(self):
        self.fw("account", "add", "401k", "--type", "tax_deferred")
        self.fw("holding", "set", "401k", "FUND", "100000", "--asset-class", "us_stock", "--expense-ratio", "0.01")
        out = self.fw("fees", "--project", "--admin-fee", "100")
        # 100000 * (1.06^10 - 1.05^10) and 100 * (1.06^10 - 1) / 0.06
        self.assertIn("$16,195.31", out)
        self.assertIn("$1,318.08", out)
        self.assertIn("$17,513.39", out)
        self.assertIn("$150,060.70", out)  # 30 years, both together
        code, _, err = run("--data", self.d, "fees", "--project", "--growth", "6")
        self.assertEqual(code, 2)

    def test_time_weighted_return(self):
        self.fw("account", "add", "ira", "--type", "roth")
        self.fw("balance", "set", "ira", "10000", "--as-of", "2025-01-01")
        self.fw("flow", "add", "ira", "5000", "--date", "2025-07-01")
        self.fw("balance", "set", "ira", "10000", "--as-of", "2025-07-01")  # halved, then 5000 added
        self.fw("balance", "set", "ira", "20000", "--as-of", "2026-01-01")  # then doubled
        out = self.fw("returns", "ira")
        self.assertIn("over 2 period(s)) 0.00% a year", out)  # -50% then +100%
        self.assertNotIn("XIRR) 0.00%", out)  # the deposit before the doubling helps the user's own result
        r, n, days = fw.twr([(dt.date(2026, 1, 1), Decimal(1000)), (dt.date(2026, 7, 1), Decimal(1100))], [])
        self.assertEqual((r, n, days), (Decimal("0.1"), 1, 181))

    def test_returns_under_a_year_not_annualised(self):
        self.fw("account", "add", "brk", "--type", "taxable")
        self.fw("balance", "set", "brk", "1000", "--as-of", "2026-01-01")
        self.fw("balance", "set", "brk", "1100", "--as-of", "2026-07-01")
        self.assertIn("10.00% over 181 days (not annualised", self.fw("returns", "brk"))

    def test_networth_percent_only(self):
        self.household()
        out = self.fw("networth", "--percent-only")
        self.assertIn("52.59% of assets", out)  # 223500 / 425000
        self.assertNotIn("$", out)
        self.assertNotIn("checking", out)
        shares = json.loads(self.fw("networth", "--percent-only", "--json"))
        self.assertEqual(shares["assets_by_type"]["real_estate"], "0.7059")
        self.assertNotIn("unvested", shares["assets_by_type"])

    SGML = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII

<OFX>
<SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO</STATUS><DTSERVER>20261012120000</SONRS></SIGNONMSGSRSV1>
<BANKMSGSRSV1><STMTTRNRS><TRNUID>1<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<STMTRS><CURDEF>USD<BANKACCTFROM><BANKID>000000000<ACCTID>000012341111<ACCTTYPE>CHECKING</BANKACCTFROM>
<BANKTRANLIST><DTSTART>20260901<DTEND>20261010
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20260905<TRNAMT>2500.00<FITID>1<NAME>Widget Co &amp; Sons</STMTTRN>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20260920<TRNAMT>-300.00<FITID>2<NAME>Card payment</STMTTRN>
</BANKTRANLIST>
<LEDGERBAL><BALAMT>3200.00<DTASOF>20261010120000.000[-5:EST]</LEDGERBAL>
<AVAILBAL><BALAMT>3100.00<DTASOF>20261010</AVAILBAL>
</STMTRS></STMTTRNRS>
<STMTTRNRS><TRNUID>2<STMTRS><CURDEF>USD<BANKACCTFROM><BANKID>0<ACCTID>55559999<ACCTTYPE>SAVINGS</BANKACCTFROM>
<LEDGERBAL><BALAMT>10.00<DTASOF>20261010</LEDGERBAL></STMTRS></STMTTRNRS></BANKMSGSRSV1>
<CREDITCARDMSGSRSV1><CCSTMTTRNRS><TRNUID>3<CCSTMTRS><CURDEF>USD<CCACCTFROM><ACCTID>4111000000002222</CCACCTFROM>
<LEDGERBAL><BALAMT>-450.25<DTASOF>20261009</LEDGERBAL>
</CCSTMTRS></CCSTMTTRNRS></CREDITCARDMSGSRSV1>
</OFX>
"""

    XML = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>
<OFX><INVSTMTMSGSRSV1><INVSTMTTRNRS><TRNUID>1</TRNUID><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
<INVSTMTRS><DTASOF>20261011</DTASOF><CURDEF>USD</CURDEF>
<INVACCTFROM><BROKERID>example.com</BROKERID><ACCTID>X99887766</ACCTID></INVACCTFROM>
<INVTRANLIST><DTSTART>20260901</DTSTART><DTEND>20261011</DTEND></INVTRANLIST>
<INVPOSLIST>
<POSMF><INVPOS><SECID><UNIQUEID>000000101</UNIQUEID><UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE></SECID><HELDINACCT>CASH</HELDINACCT>
<POSTYPE>LONG</POSTYPE><UNITS>10</UNITS><UNITPRICE>250</UNITPRICE><MKTVAL>2500.00</MKTVAL><DTPRICEASOF>20261011</DTPRICEASOF><MEMO></MEMO></INVPOS></POSMF>
<POSDEBT><INVPOS><SECID><UNIQUEID>000000202</UNIQUEID><UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE></SECID><HELDINACCT>CASH</HELDINACCT>
<POSTYPE>LONG</POSTYPE><UNITS>1000</UNITS><UNITPRICE>99</UNITPRICE><MKTVAL>990.00</MKTVAL><DTPRICEASOF>20261011</DTPRICEASOF></INVPOS></POSDEBT>
<POSSTOCK><INVPOS><SECID><UNIQUEID>000000303</UNIQUEID><UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE></SECID><HELDINACCT>CASH</HELDINACCT>
<POSTYPE>LONG</POSTYPE><UNITS>1</UNITS><UNITPRICE>100</UNITPRICE><MKTVAL>100.00</MKTVAL><DTPRICEASOF>20261011</DTPRICEASOF></INVPOS></POSSTOCK>
</INVPOSLIST>
<INVBAL><AVAILCASH>500.00</AVAILCASH><MARGINBALANCE>0</MARGINBALANCE><SHORTBALANCE>0</SHORTBALANCE></INVBAL>
</INVSTMTRS></INVSTMTTRNRS></INVSTMTMSGSRSV1>
<SECLISTMSGSRSV1><SECLIST>
<MFINFO><SECINFO><SECID><UNIQUEID>000000101</UNIQUEID><UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE></SECID><SECNAME>Total Market &amp; Co</SECNAME><TICKER>TOTMX</TICKER></SECINFO></MFINFO>
<DEBTINFO><SECINFO><SECID><UNIQUEID>000000202</UNIQUEID><UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE></SECID><SECNAME>Example Note</SECNAME></SECINFO><PARVALUE>1000</PARVALUE></DEBTINFO>
</SECLIST></SECLISTMSGSRSV1></OFX>
"""

    def test_import_ofx_bank_and_card(self):
        self.fw("account", "add", "chk", "--type", "cash", "--last4", "1111")
        self.fw("account", "add", "visa", "--type", "credit_card", "--last4", "2222")
        f = Path(self.tmp.name) / "download.qfx"
        f.write_text(self.SGML, encoding="utf-8")
        out = self.fw("import", "ofx", str(f))
        self.assertIn("chk: bank ...1111 $3,200.00 as of 2026-10-10; 2 transaction(s)", out)
        self.assertIn("visa: card ...2222 $450.25 as of 2026-10-09", out)
        self.assertIn("imported 2 balance row(s)", out)
        self.assertIn("not tracked (add each", out)
        self.assertIn("bank ...9999", out)
        self.assertNotIn("000012341111", out)
        nw = json.loads(self.fw("networth", "--json"))
        self.assertEqual(Decimal(nw["total"]), Decimal("2749.75"))
        self.assertIn("2 already recorded", self.fw("import", "ofx", str(f)))
        code, _, err = run("--data", self.d, "import", "ofx", str(f), "--account", "chk")
        self.assertEqual(code, 2)
        self.assertIn("3 statements", err)
        f.write_text("Date,Amount\n", encoding="utf-8")
        self.assertEqual(run("--data", self.d, "import", "ofx", str(f))[0], 2)

    def test_import_ofx_brokerage_positions(self):
        self.fw("account", "add", "brk", "--type", "taxable", "--last4", "7766")
        f = Path(self.tmp.name) / "brokerage.ofx"
        f.write_text(self.XML, encoding="utf-8")
        out = self.fw("import", "ofx", str(f), "--classes", "TOTMX=us_stock")
        self.assertIn("brk: invest ...7766 $4,090.00 as of 2026-10-11; 3 position(s) + cash $500.00", out)
        self.assertIn("class 'other' for 000000303", out)
        rows = {r["symbol"]: r["asset_class"] for r in fw.read_rows(Path(self.d), "holdings.csv")}
        self.assertEqual(rows, {"TOTMX": "us_stock", "000000202": "bond", "000000303": "other", "CASH": "cash"})
        self.fw("import", "ofx", str(f), "--classes", "TOTMX=us_stock")
        self.assertEqual(len(fw.read_rows(Path(self.d), "holdings.csv")), 4)  # replaced, not doubled
        self.assertIn("total $4,090.00", self.fw("allocation"))

    def ofx_file(self, body: str, name: str = "x.qfx", encoding: str = "utf-8") -> str:
        f = Path(self.tmp.name) / name
        f.write_bytes(body.encode(encoding))
        return str(f)

    def test_ofx_review_cases(self):
        # two accounts with the same last 4: refuse rather than guess
        self.fw("account", "add", "chk", "--type", "cash", "--last4", "4444")
        self.fw("account", "add", "sav", "--type", "cash", "--last4", "4444")
        two = ("<OFX><STMTRS><BANKACCTFROM><ACCTID>00011114444</BANKACCTFROM><LEDGERBAL><BALAMT>100"
               "<DTASOF>20261010</LEDGERBAL></STMTRS></OFX>")
        code, _, err = run("--data", self.d, "import", "ofx", self.ofx_file(two))
        self.assertEqual(code, 2)
        self.assertIn("all end in 4444", err)
        # comma decimal mark, and a file named after the full account number
        f = self.ofx_file(two.replace("<BALAMT>100", "<BALAMT>1234,56"), "00011114444.qfx")
        out = self.fw("import", "ofx", f, "--account", "chk")
        self.assertIn("$1,234.56", out)
        self.assertIn("****4444.qfx", out)
        self.assertNotIn("00011114444", out + (Path(self.d) / "balances.csv").read_text(encoding="utf-8")
                         + (Path(self.d) / "methods.log").read_text(encoding="utf-8"))
        # a re-downloaded file with a new value for the same day replaces the balance
        self.fw("import", "ofx", self.ofx_file(two.replace("<BALAMT>100", "<BALAMT>150")), "--account", "chk")
        rows = [r for r in fw.read_rows(Path(self.d), "balances.csv") if r["account"] == "chk"]
        self.assertEqual([r["value"] for r in rows], ["150"])

    def test_ofx_empty_sgml_leaves_and_cp1252(self):
        self.fw("account", "add", "brk", "--type", "taxable", "--last4", "7766")
        body = ("OFXHEADER:100\r\nCHARSET:1252\r\n\r\n<OFX><INVSTMTRS><DTASOF>20261011<INVACCTFROM><BROKERID>b"
                "<ACCTID>X99887766</INVACCTFROM><INVPOSLIST><POSMF><INVPOS><SECID><UNIQUEID>000000101"
                "<UNIQUEIDTYPE>CUSIP</SECID><UNITS>10<UNITPRICE><MKTVAL>1000<DTPRICEASOF>20261011</INVPOS>"
                "</POSMF></INVPOSLIST></INVSTMTRS><SECLIST><MFINFO><SECINFO><SECID><UNIQUEID>000000101"
                "<UNIQUEIDTYPE>CUSIP</SECID><SECNAME>Café Fund<TICKER><FIID>9</SECINFO></MFINFO></SECLIST></OFX>")
        out = self.fw("import", "ofx", self.ofx_file(body, encoding="cp1252"))
        self.assertIn("brk: invest ...7766 $1,000.00", out)  # the empty <UNITPRICE> no longer swallows MKTVAL
        tree = fw.ofx_tree(body)
        self.assertEqual(fw.ofx_one(tree, "SECNAME"), "Café Fund")
        self.assertEqual(fw.ofx_one(tree, "TICKER"), "")
        code, _, err = run("--data", self.d, "import", "ofx",
                           self.ofx_file(body.replace("<MKTVAL>1000", ""), "nomkt.qfx"))
        self.assertEqual(code, 2)
        self.assertIn("no amount", err)
        xml = ('<?xml version="1.0"?><OFX xmlns="http://example.com/ofx"><STMTRS><BANKACCTFROM>'
               "<ACCTID>1</ACCTID><BRANCHID></BRANCHID></BANKACCTFROM><MEMO/><LEDGERBAL><BALAMT>5</BALAMT>"
               "<DTASOF>20261010</DTASOF></LEDGERBAL></STMTRS></OFX>")
        self.assertEqual(fw.ofx_statements(fw.ofx_tree(xml))[0]["value"], Decimal("5"))

    def test_review_holdings_and_twr_edges(self):
        self.household()
        f = Path(self.tmp.name) / "positions.csv"
        f.write_text("Symbol,Current Value\nVTI,1000\n", encoding="utf-8")
        args = ("import", "holdings", str(f), "--account", "brokerage", "--as-of", "2026-10-11", "--set-balance")
        self.fw(*args)
        f.write_text("Symbol,Current Value\nVTI,1500\n", encoding="utf-8")
        self.assertIn("recorded balance $1,500.00", self.fw(*args))
        nw = json.loads(self.fw("networth", "--json"))
        self.assertEqual(Decimal(nw["by_type"]["taxable"]), Decimal("1500"))
        f.write_text("Ticker,Current Value\nVTI,1500\n", encoding="utf-8")  # wrong column: refuse, keep data
        self.assertEqual(run("--data", self.d, *args)[0], 2)
        self.assertEqual(len(fw.read_rows(Path(self.d), "holdings.csv")), 1)
        # an account that starts empty still gets a time-weighted return
        self.fw("account", "add", "new", "--type", "roth")
        self.fw("balance", "set", "new", "0", "--as-of", "2025-01-01")
        self.fw("flow", "add", "new", "1000", "--date", "2025-02-01")
        self.fw("balance", "set", "new", "1000", "--as-of", "2025-02-01")
        self.fw("balance", "set", "new", "1100", "--as-of", "2026-02-01")
        self.assertIn("over 1 period(s)) 10.00% a year", self.fw("returns", "new"))

    def test_import_logs_do_not_mark_a_method_change(self):
        self.fw("account", "add", "chk", "--type", "cash", "--last4", "1111")
        self.fw("balance", "set", "chk", "100", "--as-of", "2026-09-30")
        self.fw("networth", "--save", "--as-of", "2026-09-30")
        f = Path(self.tmp.name) / "download.qfx"
        f.write_text(self.SGML, encoding="utf-8")
        self.fw("import", "ofx", str(f))
        self.fw("networth", "--save")
        self.assertNotIn("(method changed)", self.fw("history"))

    def test_hunt_file_created_for_old_data_folders(self):
        (Path(self.d) / "hunt.csv").unlink()
        self.assertIn("no searches yet", self.fw("hunt", "list"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
