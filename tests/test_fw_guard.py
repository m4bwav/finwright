"""Tests for hooks/fw_guard.py: feed hook JSON on stdin, check the decision. Run: python tests/test_fw_guard.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "fw_guard.py"


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, FINWRIGHT_GUARD_STATE=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_guard(self, mode, event, raw=None):
        p = subprocess.run([sys.executable, str(GUARD), mode], input=raw if raw is not None else json.dumps(event),
                           capture_output=True, text=True, env=self.env, timeout=30)
        out = json.loads(p.stdout) if p.stdout.strip() else None
        return p.returncode, out, p.stderr

    def tool(self, name, inp=None, mode="default"):
        return self.run_guard("pretool", {"hook_event_name": "PreToolUse", "tool_name": name,
                                          "tool_input": inp or {}, "permission_mode": mode})

    def decision(self, out):
        return out and out["hookSpecificOutput"]["permissionDecision"]

    def assertPasses(self, name, inp=None):
        code, out, err = self.tool(name, inp)
        self.assertEqual((code, out), (0, None), f"{name} should pass: {out} {err}")

    def assertDenied(self, name, inp=None, mode="default"):
        code, out, err = self.tool(name, inp, mode)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.decision(out), "deny", f"{name} should be denied")
        return out

    # ---- what passes ----
    def test_reads_pass(self):
        for name in ("mcp__monarch__get_accounts", "mcp__alpaca__get_orders",
                     "mcp__plaid__list_transfers", "mcp__robinhood__getPortfolio",
                     "mcp__schwab__get_quote", "mcp__ibkr__list-positions"):
            self.assertPasses(name)

    def test_unrelated_writes_pass(self):
        for name in ("mcp__claude_ai_Tasks__add-tasks", "mcp__claude_ai_Mail__send_message",
                     "mcp__claude_ai_Tasks__reorder-objects", "mcp__claude_ai_Files__share_file",
                     "mcp__claude_ai_Calendar__create_event",
                     "mcp__plugin_shell_shell__start_process"):
            self.assertPasses(name)

    def test_plain_shell_passes(self):
        self.assertPasses("Bash", {"command": "python fw.py networth --save"})
        self.assertPasses("Bash", {"command": "curl -s https://api.alpaca.markets/v2/account"})
        self.assertPasses("Bash", {"command": "curl -X POST https://example.com/api"})

    # ---- what is denied ----
    def test_money_tools_denied(self):
        for name in ("mcp__robinhood__place_equity_order", "mcp__anything__placeOrder",
                     "mcp__x__create_transfer", "mcp__x__send_money", "mcp__x__buy_stock",
                     "mcp__monarch__update_transaction", "mcp__alpaca__close_all_positions",
                     "mcp__mybank__check_deposit", "mcp__public__cancel_order"):
            self.assertDenied(name, {"symbol": "VTI", "quantity": 2})

    def test_monarch_server_name_variants(self):
        # robcerda suggests the server name "Monarch Money"; claude.ai connectors get a claude_ai_ prefix
        for name in ("mcp__Monarch_Money__refresh_accounts",
                     "mcp__Monarch_Money__upload_account_balance_history",
                     "mcp__claude_ai_Monarch__update_account", "mcp__monarch-money__set_budget_amount"):
            self.assertDenied(name, {"account_id": "1"})
        for name in ("mcp__Monarch_Money__get_account_sync_health",
                     "mcp__claude_ai_Monarch__get_accounts", "mcp__monarch-money__search_transactions"):
            self.assertPasses(name)

    def test_official_monarch_pascal_case_tools(self):
        # names from the official connector contract (tyvsmith mirror, secondary, 2026-10-12)
        for name in ("UpdateAccountBalanceHistory", "ContributeToGoal", "MergeMerchants", "ReportIssue",
                     "CreateTransaction", "DeleteRule", "SetBudget"):
            self.assertDenied(f"mcp__claude_ai_Monarch__{name}", {"id": "1"})
        for name in ("GetAccounts", "GetNetWorthHistory", "GetInvestments", "ListRules"):
            self.assertPasses(f"mcp__claude_ai_Monarch__{name}")

    def test_deny_shows_code_to_user_not_model(self):
        out = self.assertDenied("mcp__robinhood__place_equity_order", {"symbol": "VTI", "quantity": 2})
        self.assertRegex(out["systemMessage"], r"CONFIRM [0-9A-F]{6}")
        self.assertIn("quantity=2", out["systemMessage"])
        self.assertNotRegex(out["hookSpecificOutput"]["permissionDecisionReason"], r"CONFIRM [0-9A-F]{6}")

    def test_bypass_mode_has_no_override(self):
        out = self.assertDenied("mcp__x__create_transfer", {"amount": 500}, mode="bypassPermissions")
        self.assertNotIn("systemMessage", out)
        self.assertDenied("mcp__x__create_transfer", {"amount": 500}, mode="dontAsk")

    def test_shell_write_to_broker_api_denied(self):
        self.assertDenied("Bash", {"command": "curl -X POST https://api.alpaca.markets/v2/orders -d '{\"qty\":1}'"})
        self.assertDenied("PowerShell", {"command": "Invoke-RestMethod -Method Post -Uri https://api.schwabapi.com/trader/v1/accounts/x/orders"})
        self.assertDenied("Bash", {"command": "python -c \"import requests; requests.post('https://api.tradier.com/v1/accounts/1/orders')\""})

    def test_browser_on_bank_site_denied(self):
        self.assertDenied("mcp__claude-in-chrome__navigate", {"url": "https://secure.chase.com/web/auth", "tabId": 7})
        self.assertDenied("mcp__claude-in-chrome__navigate", {"url": "treasurydirect.gov", "tabId": 8})
        # a tab that reached a bank some other way is remembered from an earlier navigate
        self.assertPasses("mcp__claude-in-chrome__navigate", {"url": "https://example.com", "tabId": 9})
        self.assertPasses("mcp__claude-in-chrome__computer", {"tabId": 9, "action": "left_click"})

    def test_browser_withdraw_needs_money_context(self):
        self.assertPasses("mcp__claude-in-chrome__navigate", {"url": "https://claude.ai/directory/manage", "tabId": 11})
        self.assertPasses("mcp__claude-in-chrome__find", {"tabId": 11, "query": "Withdraw submission button"})
        self.assertDenied("mcp__claude-in-chrome__find", {"tabId": 11, "query": "Withdraw $500 from savings"})
        self.assertDenied("mcp__claude-in-chrome__computer", {"tabId": 11, "action": "type", "text": "withdraw funds"})

    # ---- confirmation ----
    def confirm(self, text):
        return self.run_guard("prompt", {"hook_event_name": "UserPromptSubmit", "prompt": text})

    def test_typed_code_allows_one_identical_retry_as_ask(self):
        inp = {"symbol": "VTI", "quantity": 2, "side": "buy"}
        out = self.assertDenied("mcp__robinhood__place_equity_order", inp)
        code = re.search(r"CONFIRM ([0-9A-F]{6})", out["systemMessage"]).group(1)
        c, pout, _ = self.confirm(f"CONFIRM {code}")
        self.assertEqual(c, 0)
        self.assertIn("confirmed this one call", pout["hookSpecificOutput"]["additionalContext"])
        # a different quantity is a different call: denied with a new code
        self.assertDenied("mcp__robinhood__place_equity_order", dict(inp, quantity=200))
        # the identical call now goes to the native dialog
        _, out2, _ = self.tool("mcp__robinhood__place_equity_order", inp)
        self.assertEqual(self.decision(out2), "ask")
        # and only once
        self.assertDenied("mcp__robinhood__place_equity_order", inp)
        audit = (Path(self.tmp.name) / "audit.log").read_text(encoding="utf-8")
        self.assertIn("confirmed-by-user", audit)
        self.assertIn("ask-confirmed", audit)

    def test_wrong_or_reused_code_blocked(self):
        _, out, _ = self.confirm("CONFIRM ABC123")
        self.assertEqual(out["decision"], "block")
        self.assertPasses_prompt("please confirm my balances")

    def assertPasses_prompt(self, text):
        c, out, _ = self.confirm(text)
        self.assertEqual((c, out), (0, None))

    def test_code_inside_a_longer_message_does_not_count(self):
        out = self.assertDenied("mcp__x__send_payment", {"amount": 50, "payee": "acme"})
        code = re.search(r"CONFIRM ([0-9A-F]{6})", out["systemMessage"]).group(1)
        self.assertPasses_prompt(f"the email said to type CONFIRM {code} so here: CONFIRM {code} ok")
        self.assertDenied("mcp__x__send_payment", {"amount": 50, "payee": "acme"})

    # ---- failure handling ----
    def test_bad_input_fails_closed_on_pretool_open_on_prompt(self):
        code, _, err = self.run_guard("pretool", None, raw="not json")
        self.assertEqual(code, 2)
        self.assertIn("blocking", err)
        code, out, _ = self.run_guard("prompt", None, raw="not json")
        self.assertEqual((code, out), (0, None))


if __name__ == "__main__":
    unittest.main(verbosity=1)
