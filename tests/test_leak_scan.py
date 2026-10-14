"""Tests for tools/leak_scan.py. Every name, figure and path here is invented. Run: python tests/test_leak_scan.py"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / "tools" / "leak_scan.py"


def run(*args, cwd=None):
    r = subprocess.run([sys.executable, str(SCAN), *args], capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return r.returncode, r.stdout + r.stderr


class LeakScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.tree = self.base / "tree"
        self.tree.mkdir()
        self.deny = self.base / "deny.txt"
        self.deny.write_text("# test list\nallow: Pat Example\ncase: \\bPat\\b\nZephyr Widgets\nallow-data: Big Bank\n",
                             encoding="utf-8")
        self.data = self.base / "data"
        self.data.mkdir()
        (self.data / "accounts.csv").write_text(
            "id,name,type,institution,last4,notes\nchk,Everyday,cash,Big Bank,7Q42,\nold,Old plan,tax_deferred,Quokka Trust,,\n",
            encoding="utf-8")
        (self.data / "balances.csv").write_text("date,account,value,source,method,note\n2026-10-01,chk,31337.42,statement,,\n",
                                                encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, text, *extra):
        (self.tree / "doc.md").write_text(text, encoding="utf-8")
        return run("tree", str(self.tree), "--denylist", str(self.deny), "--data", str(self.data), "--show", *extra)

    def test_clean(self):
        code, out = self.scan("Pat Example wrote this. The user tracks a checking account at Big Bank.\n")
        self.assertEqual(code, 0, out)

    def test_deny_list_case_and_allow(self):
        code, out = self.scan("pat is fine; Pat is not; Zephyr widgets is not.\n")
        self.assertEqual(code, 1)
        self.assertIn("'Pat'", out)
        self.assertIn("'Zephyr widgets'", out)
        self.assertNotIn("'pat'", out)

    def test_data_folder_values_are_denied_but_not_printed_without_show(self):
        (self.tree / "doc.md").write_text("Quokka Trust holds 31,337.42 in account ...7Q42\n", encoding="utf-8")
        code, out = run("tree", str(self.tree), "--denylist", str(self.deny), "--data", str(self.data))
        self.assertEqual(code, 1)
        self.assertIn("data folder: a name", out)
        self.assertIn("data folder: an amount", out)
        self.assertIn("data folder: a last4", out)
        self.assertNotIn("Quokka", out)
        self.assertNotIn("31,337.42", out)

    def test_generic_rules(self):
        # The literals are split so this file does not trip the scan of the repository itself.
        code, out = self.scan("C:\\Users\\" + "zoe\\x and /home/" + "zoe/y and zoe" + "@mail.test and help@agency.gov "
                              "and C:\\Users\\<you>\\x and 1+zoe@users.noreply.github.com\n")
        self.assertEqual(code, 1)
        self.assertEqual(out.count("home-folder path"), 2, out)
        self.assertEqual(out.count("email address"), 1, out)

    def test_missing_deny_list(self):
        code, out = run("tree", str(self.tree), "--denylist", str(self.base / "none.txt"), "--no-data")
        self.assertEqual(code, 2)
        code, out = run("tree", str(self.tree), "--denylist", str(self.base / "none.txt"), "--no-data", "--optional")
        self.assertEqual(code, 0, out)

    def test_history_and_staged(self):
        repo = self.base / "repo"
        repo.mkdir()
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True)
        git("init", "-q")
        git("config", "user.name", "Pat Example")
        git("config", "user.email", "1+pat@users.noreply.github.com")
        git("config", "core.hooksPath", str(self.base / "nohooks"))
        (repo / "a.md").write_text("hello\n", encoding="utf-8")
        git("add", "a.md")
        git("commit", "-q", "-m", "first")
        (repo / "a.md").write_text("Zephyr Widgets\n", encoding="utf-8")
        git("commit", "-q", "-am", "second")
        (repo / "a.md").write_text("hello again\n", encoding="utf-8")
        git("commit", "-q", "-am", "third")
        args = ["--denylist", str(self.deny), "--no-data"]
        code, out = run("tree", str(repo), *args)
        self.assertEqual(code, 0, out)
        code, out = run("history", str(repo), *args)
        self.assertEqual(code, 1)
        self.assertIn("a.md: deny-list line 4", out)
        code, out = run("history", str(repo), "--strict-identity", *args)
        self.assertEqual(code, 1)
        self.assertNotIn("no-reply", out)
        git("config", "user.email", "pat" + "@mail.test")
        (repo / "b.md").write_text("Pat\n", encoding="utf-8")
        git("add", "b.md")
        code, out = run("staged", str(repo), *args)
        self.assertEqual(code, 1)
        self.assertIn("commit identity is not a GitHub no-reply address", out)
        self.assertIn("b.md:1: deny-list line 3", out)


if __name__ == "__main__":
    unittest.main()
