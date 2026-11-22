"""Acceptance tests for TOML support in cfgkit.

Each TestCase class corresponds to one requirement of the task, in the order the task states
them.  Data-driven classes keep their documents in class attributes:
``VALID`` (document, expected result), ``INVALID`` (documents that must raise ParseError),
``DATES`` (otherwise-valid documents using date/time values, which must raise ParseError) and
``LINES`` (document, expected ``ParseError.line``).
"""
import ast
import json
import math
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "cfgkit"


def _loads(text):
    from cfgkit.toml import loads

    return loads(text)


def _parse_error():
    from cfgkit import ParseError

    return ParseError


def _strict_equal(a, b):
    """Equality that also compares types (1 != 1.0 != True) and treats nan == nan."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_strict_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_strict_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and math.isnan(a):
        return math.isnan(b)
    return a == b


class TomlCase:
    """Mixin with the data-driven checks (combined with unittest.TestCase below)."""

    VALID = []
    INVALID = []
    DATES = []
    LINES = []

    def assertParses(self, doc, expected):
        result = _loads(doc)
        self.assertTrue(_strict_equal(result, expected),
                        "loads(%r) returned %r, expected %r" % (doc, result, expected))

    def assertInvalid(self, doc):
        ParseError = _parse_error()
        try:
            result = _loads(doc)
        except ParseError:
            return
        self.fail("loads(%r) should raise ParseError, returned %r" % (doc, result))

    def assertErrorLine(self, doc, line):
        ParseError = _parse_error()
        with self.assertRaises(ParseError, msg=repr(doc)) as cm:
            _loads(doc)
        self.assertEqual(cm.exception.line, line, "wrong .line for %r" % (doc,))

    def test_valid_documents(self):
        if not self.VALID:
            self.skipTest("no VALID data for this requirement")
        for doc, expected in self.VALID:
            with self.subTest(doc=doc):
                self.assertParses(doc, expected)

    def test_invalid_documents(self):
        if not self.INVALID:
            self.skipTest("no INVALID data for this requirement")
        for doc in self.INVALID:
            with self.subTest(doc=doc):
                self.assertInvalid(doc)

    def test_date_documents(self):
        if not self.DATES:
            self.skipTest("no DATES data for this requirement")
        for doc in self.DATES:
            with self.subTest(doc=doc):
                self.assertInvalid(doc)

    def test_error_lines(self):
        if not self.LINES:
            self.skipTest("no LINES data for this requirement")
        for doc, line in self.LINES:
            with self.subTest(doc=doc):
                self.assertErrorLine(doc, line)


# ---------------------------------------------------------------------------------------------

FORBIDDEN_MODULES = {"tomllib", "tomli", "toml", "tomlkit", "tomli_w", "pytoml", "rtoml", "qtoml"}


class Req01_NoTomlLibrary(unittest.TestCase):
    """The parser must be written by hand: do not import (or shell out to) `tomllib`, `tomli`,
    `toml`, `tomlkit` or any other TOML library, in any module of the package."""

    def _modules(self):
        files = sorted(PACKAGE.rglob("*.py"))
        self.assertTrue(any(f.name == "toml.py" for f in files), "cfgkit/toml.py is missing")
        return files

    def test_no_absolute_import_of_toml_libraries(self):
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module]
                for name in names:
                    self.assertNotIn(name.split(".")[0], FORBIDDEN_MODULES,
                                     "%s imports %s" % (path.name, name))
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value, FORBIDDEN_MODULES - {"toml"},
                                     "%s mentions %r" % (path.name, node.value))

    def test_no_shelling_out(self):
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        self.assertNotEqual(a.name.split(".")[0], "subprocess", path.name)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    self.assertNotEqual(node.module.split(".")[0], "subprocess", path.name)
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                        and node.value.id == "os":
                    self.assertFalse(node.attr in ("system", "popen")
                                     or node.attr.startswith(("exec", "spawn")),
                                     "%s uses os.%s" % (path.name, node.attr))

    def test_works_with_toml_libraries_blocked(self):
        code = (
            "import sys\n"
            "for m in %r: sys.modules[m] = None\n"
            "import cfgkit, cfgkit.toml\n"
            "d = cfgkit.toml.loads('a = 1\\n[t]\\nb = \"x\"\\n')\n"
            "assert d == {'a': 1, 't': {'b': 'x'}}, d\n"
            "assert cfgkit.load_text('c = 2', 'toml') == {'c': 2}\n"
            "print('OK')\n" % (sorted(FORBIDDEN_MODULES),)
        )
        proc = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK", proc.stdout)


class Req02_LoadsReturnsDict(TomlCase, unittest.TestCase):
    """`cfgkit/toml.py` (new) provides `loads(text) -> dict` implementing TOML v1.0.0."""

    VALID = [
        ("", {}),
        ("\n\n   \n\t\n", {}),
        ("a = 1", {"a": 1}),
        ("a = 1\n", {"a": 1}),
        ("title = \"TOML Example\"\n\n[owner]\nname = \"Tom\"\n\n[database]\nenabled = true\n"
         "ports = [ 8000, 8001, 8002 ]\ntemp_targets = { cpu = 79.5, case = 72.0 }\n\n"
         "[servers]\n\n[servers.alpha]\nip = \"10.0.0.1\"\nrole = \"frontend\"\n",
         {"title": "TOML Example", "owner": {"name": "Tom"},
          "database": {"enabled": True, "ports": [8000, 8001, 8002],
                       "temp_targets": {"cpu": 79.5, "case": 72.0}},
          "servers": {"alpha": {"ip": "10.0.0.1", "role": "frontend"}}}),
    ]

    def test_module_function(self):
        import cfgkit.toml

        self.assertTrue(callable(cfgkit.toml.loads))
        self.assertIs(type(cfgkit.toml.loads("a = 1")), dict)
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution
    test_invalid_documents = None  # failed on the reference solution


class Req03_Comments(TomlCase, unittest.TestCase):
    """Comments: `#` starts a comment that runs to the end of the line (not inside strings)."""

    VALID = [
        ("# full line comment\na = 1 # trailing comment\n", {"a": 1}),
        ("#\n#no space\n", {}),
        ("a = \"# not a comment\" # comment\n", {"a": "# not a comment"}),
        ("a = '# nor this'#c\n", {"a": "# nor this"}),
        ("[t] # comment after header\nx = 1\n[[arr]] # c\n",
         {"t": {"x": 1}, "arr": [{}]}),
        ("a = [ # comment\n  1, # one\n  # alone\n  2 # two\n] # end\n", {"a": [1, 2]}),
        ("# comment with \t tab and unicode \u00e9\u2603\n", {}),
        ("a = 1 # comment # more", {"a": 1}),
    ]
    INVALID = [
        "a = 1 // not a comment\n",
        "; not a comment\n",
        "a = # missing value\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req04_Keys(TomlCase, unittest.TestCase):
    """Bare, quoted and dotted keys (whitespace allowed around the dots)."""

    VALID = [
        ("key = 1\nbare_key = 2\nbare-key = 3\n1234 = 4\nAZaz09_- = 5\n",
         {"key": 1, "bare_key": 2, "bare-key": 3, "1234": 4, "AZaz09_-": 5}),
        ("\"127.0.0.1\" = 1\n\"character encoding\" = 2\n\"\u0281\u0254\u0282\" = 3\n"
         "'key2' = 4\n'quoted \"value\"' = 5\n",
         {"127.0.0.1": 1, "character encoding": 2, "\u0281\u0254\u0282": 3, "key2": 4,
          "quoted \"value\"": 5}),
        ("\"\" = 1\n", {"": 1}),
        ("'' = 1\n", {"": 1}),
        ("\"\\u00e9\\n\" = 1\n", {"\u00e9\n": 1}),
        ("name = \"Orange\"\nphysical.color = \"orange\"\nphysical.shape = \"round\"\n"
         "site.\"google.com\" = true\n",
         {"name": "Orange", "physical": {"color": "orange", "shape": "round"},
          "site": {"google.com": True}}),
        ("fruit.name = \"banana\"\nfruit. color = \"yellow\"\nfruit . flavor = \"banana\"\n",
         {"fruit": {"name": "banana", "color": "yellow", "flavor": "banana"}}),
        ("a\t.\tb = 1\n", {"a": {"b": 1}}),
        ("3.14159 = \"pi\"\n", {"3": {"14159": "pi"}}),
        ("  indented = 1\n\tkey=2\n", {"indented": 1, "key": 2}),
        ("a.'b.c'.\"d\" = 1\n", {"a": {"b.c": {"d": 1}}}),
        ("true = 1\nfalse = 2\ninf = 3\nnan = 4\n", {"true": 1, "false": 2, "inf": 3, "nan": 4}),
    ]
    INVALID = [
        "= \"no key\"\n",
        "key = \n",
        "key\n",
        "a b = 1\n",
        "a. = 1\n",
        ".a = 1\n",
        "a..b = 1\n",
        "k\u00e9y = 1\n",
        "a.b c = 1\n",
        "\"\"\"multi\"\"\" = 1\n",
        "'''multi''' = 1\n",
        "\"unterminated = 1\n",
        "a =\n1\n",
        "a\n= 1\n",
        "a = 1 b = 2\n",
        "a = 1, b = 2\n",
        "a = 1\na = 2\n",
        "a = 1\n\"a\" = 2\n",
        "spelling = 1\n'spelling' = 2\n",
        "a.b = 1\na.\"b\" = 2\n",
        "a = 1\na.b = 2\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req05_Strings(TomlCase, unittest.TestCase):
    """Basic, literal, multi-line basic and multi-line literal strings with all escape rules
    (`\\b \\t \\n \\f \\r \\" \\\\ \\uXXXX \\UXXXXXXXX`, line-ending backslash trimming, the
    first newline after the opening delimiter trimmed, up to two quotes next to the closing
    delimiter, unicode escapes must be scalar values)."""

    VALID = [
        # basic strings
        ("s = \"hello\"\n", {"s": "hello"}),
        ("s = \"\"\n", {"s": ""}),
        ("s = \"\\b\\t\\n\\f\\r\\\"\\\\\"\n", {"s": "\b\t\n\f\r\"\\"}),
        ("s = \"I'm a string. \\\"You can quote me\\\". Name\\tJos\\u00E9\\nLocation\\tSF.\"\n",
         {"s": "I'm a string. \"You can quote me\". Name\tJos\u00e9\nLocation\tSF."}),
        ("s = \"\\u00e9\\u00E9\\U0001F600\\U0001f600\"\n", {"s": "\u00e9\u00e9\U0001F600\U0001F600"}),
        ("s = \"\\u0000\\u007F\\uFFFF\\U0010FFFF\\uE000\\uD7FF\"\n",
         {"s": "\x00\x7f\uffff\U0010ffff\ue000\ud7ff"}),
        ("s = \"tab\there\"\n", {"s": "tab\there"}),
        ("s = \"\u00e9\u2603\U0001F600\"\n", {"s": "\u00e9\u2603\U0001F600"}),
        ("s = \"'single' inside\"\n", {"s": "'single' inside"}),
        # literal strings
        ("winpath = 'C:\\Users\\nodejs\\templates'\nregex = '<\\i\\c*\\s*>'\n",
         {"winpath": "C:\\Users\\nodejs\\templates", "regex": "<\\i\\c*\\s*>"}),
        ("s = 'Tom \"Dubs\" Preston-Werner'\n", {"s": "Tom \"Dubs\" Preston-Werner"}),
        ("s = ''\n", {"s": ""}),
        ("s = 'tab\there'\n", {"s": "tab\there"}),
        ("s = '\\u00e9'\n", {"s": "\\u00e9"}),
        # multi-line basic strings
        ("s = \"\"\"\nRoses are red\nViolets are blue\"\"\"\n",
         {"s": "Roses are red\nViolets are blue"}),
        ("s = \"\"\"Roses\nViolets\n\"\"\"\n", {"s": "Roses\nViolets\n"}),
        ("s = \"\"\"\n\nfirst\"\"\"\n", {"s": "\nfirst"}),
        ("s = \"\"\"\"\"\"\n", {"s": ""}),
        ("s = \"\"\"\n\"\"\"\n", {"s": ""}),
        ("s = \"\"\"\nThe quick brown \\\n\n\n  fox jumps over \\\n    the lazy dog.\"\"\"\n",
         {"s": "The quick brown fox jumps over the lazy dog."}),
        ("s = \"\"\"\\\n       The quick brown \\\n       fox jumps over \\\n"
         "       the lazy dog.\\\n       \"\"\"\n",
         {"s": "The quick brown fox jumps over the lazy dog."}),
        ("s = \"\"\"a \\   \t \n   b\"\"\"\n", {"s": "a b"}),
        ("s = \"\"\"a\\\n\"\"\"\n", {"s": "a"}),
        ("s = \"\"\"Here are two quotation marks: \"\". Simple enough.\"\"\"\n",
         {"s": "Here are two quotation marks: \"\". Simple enough."}),
        ("s = \"\"\"Here are three quotation marks: \"\"\\\".\"\"\"\n",
         {"s": "Here are three quotation marks: \"\"\"."}),
        ("s = \"\"\"Here are fifteen quotation marks: \"\"\\\"\"\"\\\"\"\"\\\"\"\"\\\"\"\"\\\".\"\"\"\n",
         {"s": "Here are fifteen quotation marks: " + "\"" * 15 + "."}),
        ("s = \"\"\"\"This,\" she said, \"is just a pointless statement.\"\"\"\"\n",
         {"s": "\"This,\" she said, \"is just a pointless statement.\""}),
        ("s = \"\"\"a\"\"\"\"\n", {"s": "a\""}),
        ("s = \"\"\"a\"\"\"\"\"\n", {"s": "a\"\""}),
        ("s = \"\"\"\"\"a\"\"\"\"\"\n", {"s": "\"\"a\"\""}),
        ("s = \"\"\"\\b\\t\\n\\f\\r\\\"\\\\\\u00e9\\U0001F600\"\"\"\n",
         {"s": "\b\t\n\f\r\"\\\u00e9\U0001F600"}),
        ("s = \"\"\"tab\there\n'single'\"\"\"\n", {"s": "tab\there\n'single'"}),
        ("s = \"\"\"# not a comment\"\"\"\n", {"s": "# not a comment"}),
        # multi-line literal strings
        ("s = '''I [dw]on't need \\d{2} apples'''\n", {"s": "I [dw]on't need \\d{2} apples"}),
        ("s = '''\nThe first newline is\ntrimmed in raw strings.\n   All other whitespace\n"
         "   is preserved.\n'''\n",
         {"s": "The first newline is\ntrimmed in raw strings.\n   All other whitespace\n"
               "   is preserved.\n"}),
        ("s = '''Here are fifteen quotation marks: \"\"\"\"\"\"\"\"\"\"\"\"\"\"\"'''\n",
         {"s": "Here are fifteen quotation marks: " + "\"" * 15}),
        ("s = ''''That,' she said, 'is still pointless.''''\n",
         {"s": "'That,' she said, 'is still pointless.'"}),
        ("s = '''a''''\n", {"s": "a'"}),
        ("s = '''a'''''\n", {"s": "a''"}),
        ("s = ''''''\n", {"s": ""}),
        ("s = '''\n'''\n", {"s": ""}),
        ("s = '''a \\\n  b'''\n", {"s": "a \\\n  b"}),
        ("s = '''\\n\\u00e9\t'''\n", {"s": "\\n\\u00e9\t"}),
    ]
    INVALID = [
        "s = \"unterminated\n",
        "s = \"line\nbreak\"\n",
        "s = 'unterminated\n",
        "s = 'line\nbreak'\n",
        "s = 'it's'\n",
        "s = \"\"\"unterminated\n",
        "s = '''unterminated\n",
        "s = \"\\q\"\n",
        "s = \"\\x41\"\n",
        "s = \"\\e\"\n",
        "s = \"\\a\"\n",
        "s = \"\\0\"\n",
        "s = \"\\ \"\n",
        "s = \"\\\"\n",
        "s = \"a \\\nb\"\n",
        "s = \"\\u12\"\n",
        "s = \"\\u12G4\"\n",
        "s = \"\\U0001F60\"\n",
        "s = \"\\uD800\"\n",
        "s = \"\\uDFFF\"\n",
        "s = \"\\U0000D800\"\n",
        "s = \"\\U00110000\"\n",
        "s = \"\\UFFFFFFFF\"\n",
        "s = \"\"\"\\q\"\"\"\n",
        "s = \"\"\"\\uD800\"\"\"\n",
        "s = \"\"\"\\x41\"\"\"\n",
        "s = \"\"\"a\"\"\"\"\"\"\n",
        "s = \"\"\"Here are three quotation marks: \"\"\".\"\"\"\n",
        "s = '''Here are fifteen apostrophes: ''''''''''''''''''\n",
        "s = '''a''''''\n",
        "s = \"a\" \"b\"\n",
        "s = \"a\"b\n",
        "s = 'a'b\n",
        "s = \"\"\"a\"\"\"b\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req06_Integers(TomlCase, unittest.TestCase):
    """Integers: decimal with underscores, no leading zeros, `0x`/`0o`/`0b`."""

    VALID = [
        ("a = +99\nb = 42\nc = 0\nd = -17\n", {"a": 99, "b": 42, "c": 0, "d": -17}),
        ("a = +0\nb = -0\n", {"a": 0, "b": 0}),
        ("a = 1_000\nb = 5_349_221\nc = 53_49_221\nd = 1_2_3_4_5\n",
         {"a": 1000, "b": 5349221, "c": 5349221, "d": 12345}),
        ("a = 0xDEADBEEF\nb = 0xdeadbeef\nc = 0xdead_beef\nd = 0x00ff\n",
         {"a": 0xDEADBEEF, "b": 0xDEADBEEF, "c": 0xDEADBEEF, "d": 255}),
        ("a = 0o01234567\nb = 0o755\nc = 0o7_5_5\n", {"a": 0o1234567, "b": 0o755, "c": 0o755}),
        ("a = 0b11010110\nb = 0b1_0\nc = 0b0\n", {"a": 0b11010110, "b": 2, "c": 0}),
        ("a = 9223372036854775807\nb = -9223372036854775808\n",
         {"a": 9223372036854775807, "b": -9223372036854775808}),
        ("a = 0x7FFFFFFFFFFFFFFF\n", {"a": 9223372036854775807}),
    ]
    INVALID = [
        "a = 01\n", "a = 00\n", "a = +01\n", "a = -012\n", "a = 0_1\n",
        "a = 1__000\n", "a = _1000\n", "a = 1000_\n", "a = +_1\n",
        "a = 0x\n", "a = 0o\n", "a = 0b\n",
        "a = 0xG\n", "a = 0o8\n", "a = 0b2\n",
        "a = +0x1\n", "a = -0x1\n", "a = +0o7\n", "a = -0b1\n",
        "a = 0X1F\n", "a = 0O7\n", "a = 0B1\n",
        "a = 0x_1\n", "a = 0x1_\n", "a = 0x1__2\n", "a = 0b_1\n", "a = 0o_7\n",
        "a = 1 2\n", "a = ++1\n", "a = --1\n", "a = +\n", "a = -\n",
        "a = 1a\n", "a = 12_a\n", "a = 0xG1\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req07_Floats(TomlCase, unittest.TestCase):
    """Floats: fraction/exponent/underscores, `inf`, `nan` with optional sign."""

    VALID = [
        ("a = +1.0\nb = 3.1415\nc = -0.01\n", {"a": 1.0, "b": 3.1415, "c": -0.01}),
        ("a = 5e+22\nb = 1e06\nc = -2E-2\nd = 1e0\ne = 1E+0\n",
         {"a": 5e22, "b": 1e6, "c": -2e-2, "d": 1.0, "e": 1.0}),
        ("a = 6.626e-34\nb = 0.0\nc = -0.0\nd = +0.0\n",
         {"a": 6.626e-34, "b": 0.0, "c": -0.0, "d": 0.0}),
        ("a = 224_617.445_991_228\nb = 1_0.0_1e1_0\n", {"a": 224617.445991228, "b": 10.01e10}),
        ("a = 0e0\nb = 0.5e-3\nc = 1e-05\n", {"a": 0.0, "b": 0.5e-3, "c": 1e-5}),
        ("a = inf\nb = +inf\nc = -inf\n",
         {"a": float("inf"), "b": float("inf"), "c": float("-inf")}),
        ("a = nan\nb = +nan\nc = -nan\n",
         {"a": float("nan"), "b": float("nan"), "c": float("nan")}),
        ("a = [inf, -nan, 1.5]\n", {"a": [float("inf"), float("nan"), 1.5]}),
    ]
    INVALID = [
        "a = .7\n", "a = 7.\n", "a = 3.e+20\n", "a = +.5\n", "a = -.5\n",
        "a = 1e\n", "a = 1e+\n", "a = 1e_1\n", "a = 1_e1\n", "a = 1.0e\n",
        "a = 1.e1\n", "a = 01.5\n", "a = 00.5\n", "a = -01.5\n", "a = 01e1\n",
        "a = 1.5_\n", "a = 1._5\n", "a = 1_.5\n", "a = 1.5__0\n", "a = 1e1_\n",
        "a = 1.2.3\n", "a = 1e1e1\n", "a = 1e1.5\n",
        "a = Inf\n", "a = INF\n", "a = NaN\n", "a = infinity\n", "a = nan1\n",
        "a = ++inf\n", "a = inf_\n", "a = 0x1.5\n", "a = 0x1p3\n",
    ]

    def test_signed_zero_and_nan_are_floats(self):
        d = _loads("a = -0.0\nb = -nan\nc = 1e2\n")
        self.assertIs(type(d["a"]), float)
        self.assertEqual(math.copysign(1.0, d["a"]), -1.0)
        self.assertIs(type(d["b"]), float)
        self.assertTrue(math.isnan(d["b"]))
        self.assertIs(type(d["c"]), float)
        self.assertEqual(d["c"], 100.0)
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req08_Booleans(TomlCase, unittest.TestCase):
    """Booleans `true` / `false`."""

    VALID = [
        ("a = true\nb = false\n", {"a": True, "b": False}),
        ("a = [true, false]\nt = {x = true}\n", {"a": [True, False], "t": {"x": True}}),
    ]
    INVALID = [
        "a = True\n", "a = FALSE\n", "a = yes\n", "a = tru\n", "a = truee\n",
        "a = true false\n", "a = t\n", "a = 'true'x\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req09_Arrays(TomlCase, unittest.TestCase):
    """Arrays: any mix of types, newlines, comments and a trailing comma allowed."""

    VALID = [
        ("a = []\nb = [ ]\n", {"a": [], "b": []}),
        ("integers = [ 1, 2, 3 ]\ncolors = [ \"red\", \"yellow\", \"green\" ]\n"
         "nested_arrays_of_ints = [ [ 1, 2 ], [3, 4, 5] ]\n"
         "nested_mixed_array = [ [ 1, 2 ], [\"a\", \"b\", \"c\"] ]\n"
         "string_array = [ \"all\", 'strings', \"\"\"are the same\"\"\", '''type''' ]\n",
         {"integers": [1, 2, 3], "colors": ["red", "yellow", "green"],
          "nested_arrays_of_ints": [[1, 2], [3, 4, 5]],
          "nested_mixed_array": [[1, 2], ["a", "b", "c"]],
          "string_array": ["all", "strings", "are the same", "type"]}),
        ("numbers = [ 0.1, 0.2, 0.5, 1, 2, 5 ]\n", {"numbers": [0.1, 0.2, 0.5, 1, 2, 5]}),
        ("contributors = [\n  \"Foo Bar <foo@example.com>\",\n"
         "  { name = \"Baz Qux\", email = \"bazqux@example.com\", url = \"https://example.com/bazqux\" }\n]\n",
         {"contributors": ["Foo Bar <foo@example.com>",
                           {"name": "Baz Qux", "email": "bazqux@example.com",
                            "url": "https://example.com/bazqux"}]}),
        ("a = [\n  1,\n  2, # this is ok\n]\n", {"a": [1, 2]}),
        ("a = [1,]\nb = [1,2,]\nc = [\n1\n,\n]\n", {"a": [1], "b": [1, 2], "c": [1]}),
        ("a = [\n\n# only a comment\n\n]\n", {"a": []}),
        ("a = [true, 1, 1.5, \"s\", [], {}, [[]], {x = [1]}]\n",
         {"a": [True, 1, 1.5, "s", [], {}, [[]], {"x": [1]}]}),
        ("a = [\"\"\"multi\nline\"\"\", '''x\ny''']\n", {"a": ["multi\nline", "x\ny"]}),
        ("a = [ \"] , [ #\" ]\n", {"a": ["] , [ #"]}),
        ("a = [\t1\t,\t2\t]\n", {"a": [1, 2]}),
        ("a = [[[[[[1]]]]]]\n", {"a": [[[[[[1]]]]]]}),
    ]
    INVALID = [
        "a = [\n", "a = [1\n", "a = [1,\n", "a = [1 2]\n", "a = [1,,2]\n", "a = [,]\n",
        "a = [,1]\n", "a = [1,]]\n", "a = ]\n", "a = [1] 2\n", "a = [1]]\n",
        "a = [\"a\" \"b\"]\n", "a = [ key = 1 ]\n", "a = [1, 2\nb = 3\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req10_InlineTables(TomlCase, unittest.TestCase):
    """Inline tables: one line, no trailing comma."""

    VALID = [
        ("name = { first = \"Tom\", last = \"Preston-Werner\" }\npoint = { x = 1, y = 2 }\n"
         "animal = { type.name = \"pug\" }\n",
         {"name": {"first": "Tom", "last": "Preston-Werner"}, "point": {"x": 1, "y": 2},
          "animal": {"type": {"name": "pug"}}}),
        ("a = {}\nb = { }\n", {"a": {}, "b": {}}),
        ("a = {b = {c = {d = 1}}}\n", {"a": {"b": {"c": {"d": 1}}}}),
        ("a = {x=1,y=[1,2],z={}}\n", {"a": {"x": 1, "y": [1, 2], "z": {}}}),
        ("a = {b.c = 1, b.d = 2, e = 3}\n", {"a": {"b": {"c": 1, "d": 2}, "e": 3}}),
        ("a = { \"q.k\" = 1, 'l' = 2 }\n", {"a": {"q.k": 1, "l": 2}}),
        ("a = [{x = 1}, {x = 2}]\n", {"a": [{"x": 1}, {"x": 2}]}),
        ("a = {x = [\n1,\n2]}\n", {"a": {"x": [1, 2]}}),
    ]
    INVALID = [
        "a = {x = 1,}\n",
        "a = {,}\n",
        "a = {x = 1\n}\n",
        "a = {\nx = 1}\n",
        "a = {x = 1,\ny = 2}\n",
        "a = {x = 1 y = 2}\n",
        "a = {x = 1,, y = 2}\n",
        "a = {x}\n",
        "a = {x = }\n",
        "a = {x = 1\n",
        "a = {x = 1}}\n",
        "a = {x = 1} b = 2\n",
        "a = {x = 1, x = 2}\n",
        "a = {x = 1, \"x\" = 2}\n",
        "a = {b = 1, b.c = 2}\n",
        "a = {b = {}, b.c = 1}\n",
        "a = {b.c = 1, b = {}}\n",
        "a = {x = 1 # comment\n}\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req11_TableHeaders(TomlCase, unittest.TestCase):
    """`[table]` and `[[array of tables]]` headers."""

    VALID = [
        ("[table-1]\nkey1 = \"some string\"\nkey2 = 123\n\n[table-2]\nkey1 = \"another string\"\n"
         "key2 = 456\n",
         {"table-1": {"key1": "some string", "key2": 123},
          "table-2": {"key1": "another string", "key2": 456}}),
        ("[dog.\"tater.man\"]\ntype.name = \"pug\"\n",
         {"dog": {"tater.man": {"type": {"name": "pug"}}}}),
        ("[a.b.c]\n[ d.e.f ]\n[ g .  h  . i ]\n[ j . \"\u029e\" . 'l' ]\n",
         {"a": {"b": {"c": {}}}, "d": {"e": {"f": {}}}, "g": {"h": {"i": {}}},
          "j": {"\u029e": {"l": {}}}}),
        ("[x.y.z.w]\n[x]\n", {"x": {"y": {"z": {"w": {}}}}}),
        ("top = 1\n[t]\nk = 2\n", {"top": 1, "t": {"k": 2}}),
        ("[\"\"]\nk = 1\n", {"": {"k": 1}}),
        ("[[products]]\nname = \"Hammer\"\nsku = 738594937\n\n[[products]]  # empty table\n\n"
         "[[products]]\nname = \"Nail\"\nsku = 284758393\n\ncolor = \"gray\"\n",
         {"products": [{"name": "Hammer", "sku": 738594937}, {},
                       {"name": "Nail", "sku": 284758393, "color": "gray"}]}),
        ("[[fruits]]\nname = \"apple\"\n\n[fruits.physical]  # subtable\ncolor = \"red\"\n"
         "shape = \"round\"\n\n[[fruits.varieties]]  # nested array of tables\n"
         "name = \"red delicious\"\n\n[[fruits.varieties]]\nname = \"granny smith\"\n\n\n"
         "[[fruits]]\nname = \"banana\"\n\n[[fruits.varieties]]\nname = \"plantain\"\n",
         {"fruits": [{"name": "apple", "physical": {"color": "red", "shape": "round"},
                      "varieties": [{"name": "red delicious"}, {"name": "granny smith"}]},
                     {"name": "banana", "varieties": [{"name": "plantain"}]}]}),
        ("[[ a ]]\n[[ a . b ]]\n[[\ta\t]]\n", {"a": [{"b": [{}]}, {}]}),
        ("[[a.b]]\nx = 1\n", {"a": {"b": [{"x": 1}]}}),
        ("[t]\n[t.u]\n[t.v]\n[w]\n[t.x]\n", {"t": {"u": {}, "v": {}, "x": {}}, "w": {}}),
    ]
    INVALID = [
        "[]\n", "[[]]\n", "[a\n", "[a]]\n", "[[a]\n", "[[a]]]\n", "a]\n",
        "[a b]\n", "[a.]\n", "[.a]\n", "[a..b]\n", "[a] x = 1\n", "[a]x = 1\n",
        "[a]\n[a]\n", "[[a]] [[b]]\n", "[ [a] ]\n", "[ [a]]\n", "[[a] ]\n",
        "[a] [b]\n", "[\"a\"\n", "[a = 1]\n", "[a]\nb = 1\n[a]\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req12_DatesNotSupported(TomlCase, unittest.TestCase):
    """The ONE deliberate exception: date, time and date-time values are not supported and
    raise `ParseError`."""

    DATES = [
        "odt1 = 1979-05-27T07:32:00Z\n",
        "odt2 = 1979-05-27T00:32:00-07:00\n",
        "odt3 = 1979-05-27T00:32:00.999999-07:00\n",
        "odt4 = 1979-05-27 07:32:00Z\n",
        "odt5 = 1979-05-27t07:32:00z\n",
        "ldt1 = 1979-05-27T07:32:00\n",
        "ldt2 = 1979-05-27T00:32:00.999999\n",
        "ld1 = 1979-05-27\n",
        "lt1 = 07:32:00\n",
        "lt2 = 00:32:00.999999\n",
        "a = [1979-05-27]\n",
        "a = [1, 2]\nb = [\n  1,\n  07:32:00,\n]\n",
        "t = { d = 1979-05-27 }\n",
        "[t]\nd = 2000-01-01T00:00:00+00:00\n",
    ]

    def test_error_is_parse_error_subclass_of_config_error(self):
        from cfgkit import ConfigError, ParseError

        with self.assertRaises(ParseError) as cm:
            _loads("ok = 1\nd = 1979-05-27\n")
        self.assertIsInstance(cm.exception, ConfigError)
        self.assertEqual(cm.exception.line, 2)
    test_error_lines = None  # failed on the reference solution
    test_invalid_documents = None  # failed on the reference solution
    test_valid_documents = None  # failed on the reference solution


class Req13_ControlCharsAndLineEndings(TomlCase, unittest.TestCase):
    """Control characters (other than tab, and newline where allowed) in strings and comments
    are errors; a `\\r\\n` line ending is treated exactly like `\\n` everywhere (also inside
    multi-line strings); a lone `\\r` is an error."""

    VALID = [
        ("a = 1\r\nb = 2\r\n", {"a": 1, "b": 2}),
        ("# comment\r\n[t]\r\nx = 'v' # c\r\n\r\n[[arr]]\r\n", {"t": {"x": "v"}, "arr": [{}]}),
        ("s = \"\"\"\r\nline1\r\nline2\"\"\"\r\n", {"s": "line1\nline2"}),
        ("s = \"\"\"a\r\n\r\nb\r\n\"\"\"\r\n", {"s": "a\n\nb\n"}),
        ("s = '''\r\nline1\r\nline2\r\n'''\r\n", {"s": "line1\nline2\n"}),
        ("s = \"\"\"a \\\r\n   b \\  \r\n\r\n  c\"\"\"\r\n", {"s": "a b c"}),
        ("a = [\r\n  1,\r\n  2, # c\r\n]\r\n", {"a": [1, 2]}),
        ("s = \"\\r\\n\"\n", {"s": "\r\n"}),
        ("s = \"a\tb\"\nt = 'a\tb'\nu = \"\"\"a\tb\"\"\"\nv = '''a\tb'''\n# tab\there\n",
         {"s": "a\tb", "t": "a\tb", "u": "a\tb", "v": "a\tb"}),
    ]
    INVALID = [
        # lone carriage return
        "a = 1\rb = 2\n",
        "a = 1\r",
        "s = \"a\rb\"\n",
        "s = 'a\rb'\n",
        "s = \"\"\"a\rb\"\"\"\n",
        "s = '''a\rb'''\n",
        "s = \"\"\"a \\\rb\"\"\"\n",
        "# comment\rwith lone cr\n",
        "a = [1,\r2]\n",
        "\r\n\r",
    ] + [
        # control characters in all kinds of strings and in comments
        template % ch
        for ch in ("\x00", "\x01", "\x08", "\x0b", "\x0c", "\x1f", "\x7f")
        for template in ("s = \"a%sb\"\n", "s = 'a%sb'\n", "s = \"\"\"a%sb\"\"\"\n",
                         "s = '''a%sb'''\n", "a = 1 # c%s\n", "# c%s\n", "\"k%s\" = 1\n",
                         "'k%s' = 1\n")
    ] + [
        "a = 1\x0b\n",
        "\x00a = 1\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req14_DefinitionRules(TomlCase, unittest.TestCase):
    """Every TOML rule about what may be defined where: duplicate keys; redefining a table;
    tables created implicitly by `[a.b.c]` or by dotted keys; dotted-key tables cannot be
    reopened with a `[header]` but sub-tables of them can be added; inline tables and static
    arrays are immutable (no extending them by dotted keys, `[a.b]` headers or `[[a]]`); an
    `[[array of tables]]` header starts a new element and forgets the table flags of the
    previous element; a header cannot turn a value into a table, and so on."""

    VALID = [
        # implicit super-tables may be defined later, once
        ("[x.y.z.w]\n[x]\nk = 1\n", {"x": {"k": 1, "y": {"z": {"w": {}}}}}),
        ("[a.b.c]\n[a.b]\nk = 1\n", {"a": {"b": {"k": 1, "c": {}}}}),
        ("[fruit.apple]\n[animal]\n[fruit.orange]\n",
         {"fruit": {"apple": {}, "orange": {}}, "animal": {}}),
        # dotted keys in any order within one table
        ("apple.type = \"fruit\"\norange.type = \"fruit\"\napple.skin = \"thin\"\n",
         {"apple": {"type": "fruit", "skin": "thin"}, "orange": {"type": "fruit"}}),
        ("a.b.c = 1\na.b.d = 2\na.e = 3\n", {"a": {"b": {"c": 1, "d": 2}, "e": 3}}),
        # sub-tables of dotted-key tables can be added with a header
        ("[fruit]\napple.color = \"red\"\napple.taste.sweet = true\n\n[fruit.apple.texture]\n"
         "smooth = true\n",
         {"fruit": {"apple": {"color": "red", "taste": {"sweet": True},
                              "texture": {"smooth": True}}}}),
        ("a.b.c = 1\n[a.b.d]\n", {"a": {"b": {"c": 1, "d": {}}}}),
        # dotted keys may create sub-tables of a table defined by a header
        ("[a]\nb.c = 1\n[x]\n", {"a": {"b": {"c": 1}}, "x": {}}),
        ("[a.b]\nc.d = 1\n", {"a": {"b": {"c": {"d": 1}}}}),
        # [[array]] starts a new element and forgets the previous element's flags
        ("[[a]]\n[a.b]\nx = 1\n[[a]]\n[a.b]\nx = 2\n",
         {"a": [{"b": {"x": 1}}, {"b": {"x": 2}}]}),
        ("[[a]]\nb.c = 1\n[[a]]\nb.c = 2\n", {"a": [{"b": {"c": 1}}, {"b": {"c": 2}}]}),
        ("[[a]]\nx = 1\n[[a]]\nx = 2\n", {"a": [{"x": 1}, {"x": 2}]}),
        ("[[a]]\n[[a.b]]\nx = 1\n[[a.b]]\nx = 2\n[[a]]\n[[a.b]]\nx = 3\n",
         {"a": [{"b": [{"x": 1}, {"x": 2}]}, {"b": [{"x": 3}]}]}),
        ("[[a]]\n[a.b.c]\n[[a]]\n[a.b.c]\n", {"a": [{"b": {"c": {}}}, {"b": {"c": {}}}]}),
        ("[[a.b]]\n[a]\nx = 1\n", {"a": {"b": [{}], "x": 1}}),
        ("[a]\n[[a.b]]\n[[a.b]]\n", {"a": {"b": [{}, {}]}}),
        ("[[a]]\nk = 1\n[a.t]\n[[a.u]]\n",
         {"a": [{"k": 1, "t": {}, "u": [{}]}]}),
    ]
    INVALID = [
        # duplicate keys
        "name = \"Tom\"\nname = \"Pradyun\"\n",
        "a = 1\n\"a\" = 2\n",
        "[t]\na = 1\na = 2\n",
        "[[t]]\na = 1\na = 2\n",
        "a.b = 1\na.b = 2\n",
        # redefining a table
        "[fruit]\napple = \"red\"\n\n[fruit]\norange = \"orange\"\n",
        "[a.b]\n[a.b]\n",
        "[a.b]\n[a]\n[a]\n",
        "[a]\n[\"a\"]\n",
        "[a]\nb = 1\n[x]\n[a]\n",
        # a header cannot turn a value into a table / table into value
        "[fruit]\napple = \"red\"\n\n[fruit.apple]\ntexture = \"smooth\"\n",
        "a = 1\n[a]\n",
        "a = 1\n[a.b]\n",
        "a = 1\n[[a]]\n",
        "a = 1\n[[a.b]]\n",
        "[a]\nb = 1\n[a.b.c]\n",
        "[a.b]\n[a]\nb = 1\n",
        "[a.b]\nc = 1\n[a]\nb.c = 2\n",
        "[a.b]\n[a]\nb.c = 1\n",
        "a.b = 1\na.b.c = 2\n",
        "a.b.c = 1\na.b = 2\n",
        "[a]\nb.c = 1\nb = 2\n",
        # dotted-key tables cannot be reopened with a header
        "[fruit]\napple.color = \"red\"\napple.taste.sweet = true\n\n[fruit.apple]\n",
        "[fruit]\napple.color = \"red\"\napple.taste.sweet = true\n\n[fruit.apple.taste]\n",
        "a.b = 1\n[a]\n",
        "a.b.c = 1\n[a.b]\n",
        "a.b.c = 1\n[a]\n",
        "[a]\nb.c.d = 1\n[a.b.c]\n",
        "a.b = 1\n[[a]]\n",
        # dotted keys cannot extend a table defined by a header elsewhere
        "[t.x]\n[t]\nx.y = 1\n",
        # inline tables are immutable
        "a = {}\na.b = 1\n",
        "a = {b = 1}\na.c = 2\n",
        "a = {b = {c = 1}}\na.b.d = 2\n",
        "a = {b = 1}\n[a]\n",
        "a = {b = 1}\n[a.c]\n",
        "a = {b = {}}\n[a.b]\n",
        "a = {b = {}}\n[a.b.c]\n",
        "a = {}\n[[a]]\n",
        "a = {b = []}\n[[a.b]]\n",
        "[product]\ntype = { name = \"Nail\" }\ntype.edible = false\n",
        "[product]\ntype.name = \"Nail\"\ntype = { edible = false }\n",
        "a.b = {c = 1}\na.b.d = 2\n",
        "[[a]]\nb = {c = 1}\n[a.b.d]\n",
        "[[a]]\nb = {c = 1}\nb.d = 2\n",
        # static arrays are immutable
        "fruits = []\n\n[[fruits]]\n",
        "a = [{b = 1}]\n[[a]]\n",
        "a = [{b = 1}]\n[a.c]\n",
        "a = [{b = 1}]\n[a]\n",
        "a = [{b = 1}]\na.c = 2\n",
        "a = []\na.b = 1\n",
        "a = [{}]\n[[a.b]]\n",
        "[t]\na = []\n[[t.a]]\n",
        # mixing tables and arrays of tables
        "[[a]]\n[a]\n",
        "[a]\n[[a]]\n",
        "[[fruits]]\nname = \"apple\"\n\n[[fruits.varieties]]\nname = \"red delicious\"\n\n"
        "[fruits.varieties]\nname = \"granny smith\"\n",
        "[[fruits]]\nname = \"apple\"\n\n[fruits.physical]\ncolor = \"red\"\n\n"
        "[[fruits.physical]]\ncolor = \"green\"\n",
        "[[a]]\n[a.b]\n[a.b]\n",
        "[[a]]\nb.c = 1\n[a.b]\n",
        "[a.b]\n[[a]]\n",
        "[[a.b]]\n[[a]]\n",
        "[a.b]\nx = 1\n[[a.b]]\n",
    ]
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution


class Req15_PlainPythonTypes(TomlCase, unittest.TestCase):
    """Return plain `dict`/`list`/`str`/`int`/`float`/`bool` objects (an integer never becomes
    a float)."""

    VALID = [
        ("i = 1\nz = 0\nn = -5\nh = 0xff\nb = true\nf = 1.0\ns = 's'\n",
         {"i": 1, "z": 0, "n": -5, "h": 255, "b": True, "f": 1.0, "s": "s"}),
        ("a = [1, 2.0, 3]\n", {"a": [1, 2.0, 3]}),
    ]

    def _check_plain(self, value):
        self.assertIn(type(value), (dict, list, str, int, float, bool), repr(value))
        if isinstance(value, dict):
            for k, v in value.items():
                self.assertIs(type(k), str)
                self._check_plain(v)
        elif isinstance(value, list):
            for v in value:
                self._check_plain(v)

    def test_exact_types(self):
        d = _loads("i = 1\nbig = 1_000_000\nf = 1.5\ne = 1e3\nb = false\ns = \"x\"\n"
                   "l = '''y'''\na = [1, [2]]\nt = {x = 1}\n[h]\n[[aot]]\n")
        self.assertIs(type(d), dict)
        self.assertIs(type(d["i"]), int)
        self.assertIs(type(d["big"]), int)
        self.assertIs(type(d["f"]), float)
        self.assertIs(type(d["e"]), float)
        self.assertIs(type(d["b"]), bool)
        self.assertIs(type(d["s"]), str)
        self.assertIs(type(d["l"]), str)
        self.assertIs(type(d["a"]), list)
        self.assertIs(type(d["a"][1]), list)
        self.assertIs(type(d["t"]), dict)
        self.assertIs(type(d["h"]), dict)
        self.assertIs(type(d["aot"]), list)
        self.assertIs(type(d["aot"][0]), dict)
        self._check_plain(d)

    def test_integers_never_float(self):
        d = _loads("a = 1\nb = [1, 2.5]\nc = {x = 3}\n")
        self.assertIs(type(d["a"]), int)
        self.assertIs(type(d["b"][0]), int)
        self.assertIs(type(d["b"][1]), float)
        self.assertIs(type(d["c"]["x"]), int)

    def test_result_is_json_serialisable(self):
        d = _loads("a = 1\n[t]\nb = [1, 'x', {c = true}]\n[[u]]\n")
        self.assertEqual(json.loads(json.dumps(d)), d)
    test_error_lines = None  # failed on the reference solution
    test_date_documents = None  # failed on the reference solution
    test_invalid_documents = None  # failed on the reference solution


class Req16_ErrorLines(TomlCase, unittest.TestCase):
    """Any problem raises `cfgkit.ParseError` whose `.line` is the 1-based line on which the
    statement containing the problem STARTS (the line of the key or the `[` of the header,
    counted after treating `\\r\\n` as a newline), also for errors inside a multi-line string,
    array or on a later line of the same statement."""

    LINES = [
        ("?\n", 1),
        ("a = 1\n?\n", 2),
        ("a = 1\nb = 2\na = 3\n", 3),
        ("a = 1\nb = 2 c = 3\n", 2),
        ("a = 1\nb = \"abc\n", 2),
        ("x = 1\n\ns = \"\"\"\nline\n\x01\n\"\"\"\n", 3),
        ("a = 1\ns = \"\"\"abc\nde\\q\"\"\"\n", 2),
        ("a = 1\ns = \"\"\"abc\nde\\uD800\"\"\"\n", 2),
        ("a = 1\ns = \"\"\"\nfoo\nbar\n", 2),
        ("a = 1\ns = '''\nfoo\nbar\n", 2),
        ("x = 1\narr = [\n  1,\n  2,\n  oops,\n]\n", 2),
        ("x = 1\narr = [\n  1, # bad \x01 comment\n]\n", 2),
        ("a = 1\nb = [1,\n2,\n3 4]\n", 2),
        ("a = 1\nb = [\n1,\n2\n", 2),
        ("a = 1\nb = [\n[\n1,\n],\n]\nc = {d = 1}\nc.e = 2\n", 8),
        ("a = 1\nt = {x = 1, x = 2}\n", 2),
        ("a = 1\nt = {x = 1,\ny = 2}\n", 2),
        ("[a]\nx = 1\n[b]\n[a]\n", 4),
        ("[a]\nb.c = 1\n[a.b]\n", 3),
        ("a = 1\n[[t]]\n[t]\n", 3),
        ("a = 1\n\n\n[t]\nk = 0x\n", 5),
        ("a = 1\n\n\n[t\n", 4),
        ("ok = 1\n# fine\n# bad \x7f\n", 3),
        ("a = 1\nd = 1979-05-27\n", 2),
        ("a = 1\nb = [\n1,\n1979-05-27,\n]\n", 2),
        ("x = 1\nb = \"a\rb\"\n", 2),
        ("x = 1\nb = \"\"\"\nline\n  a\rb\n\"\"\"\n", 2),
        # \r\n counts as one newline
        ("a = 1\r\nb = 2\r\nb = 3\r\n", 3),
        ("a = 1\r\ns = '''\r\nx\r\ny\r\n'''\r\nt = '''\r\n\x00'''\r\n", 6),
        ("a = \"\"\"\r\n\r\n\r\n\"\"\"\r\nb = [\r\n1,\r\n\r\n2 3]\r\n", 5),
        ("a = 1\r\n\r\n[x]\r\n[x]\r\n", 4),
        # indentation and comments before the statement do not change its line
        ("# c\n# c\n   key = [\n 1,\n ?]\n", 3),
        ("\n\n\t[ a\n", 3),
        ("a = 1\n\n[[x]]\ny = {z = 1}\ny.w = 2\n", 5),
    ]

    def test_parse_error_is_the_existing_class(self):
        import cfgkit
        import cfgkit.errors

        self.assertIs(cfgkit.ParseError, cfgkit.errors.ParseError)
        with self.assertRaises(cfgkit.errors.ParseError) as cm:
            _loads("a = 1\na = 2\n")
        self.assertIsInstance(cm.exception, cfgkit.ConfigError)
        self.assertIs(type(cm.exception.line), int)
        self.assertEqual(cm.exception.line, 2)

    def test_every_invalid_document_raises_parse_error_with_a_line(self):
        ParseError = _parse_error()
        docs = []
        for cls in (Req03_Comments, Req04_Keys, Req05_Strings, Req06_Integers, Req07_Floats,
                    Req08_Booleans, Req09_Arrays, Req10_InlineTables, Req11_TableHeaders,
                    Req13_ControlCharsAndLineEndings, Req14_DefinitionRules):
            docs.extend(cls.INVALID)
        for doc in docs:
            with self.subTest(doc=doc):
                try:
                    _loads(doc)
                except ParseError as exc:
                    self.assertIs(type(exc.line), int)
                    self.assertGreaterEqual(exc.line, 1)
                else:
                    self.fail("no ParseError for %r" % (doc,))
    test_date_documents = None  # failed on the reference solution
    test_invalid_documents = None  # failed on the reference solution
    test_valid_documents = None  # failed on the reference solution


class Req17_NonStrInput(unittest.TestCase):
    """Parsing a non-`str` raises `ParseError`."""

    def test_non_str(self):
        ParseError = _parse_error()
        for value in (b"a = 1", bytearray(b"a = 1"), None, 1, 1.5, ["a = 1"], {"a": 1}, object()):
            with self.subTest(value=value):
                with self.assertRaises(ParseError):
                    _loads(value)


class Req18_Performance(unittest.TestCase):
    """The parser must be linear-time enough to read a document of 60,000 lines (and keep a
    line counter that is not quadratic) within a few seconds."""

    LIMIT = 10.0
    N = 60000

    def _timed(self, func):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, self.LIMIT, "took %.1fs" % elapsed)
        return result

    def test_many_key_value_lines(self):
        doc = "".join("key%d = %d # comment\n" % (i, i) for i in range(self.N))
        d = self._timed(lambda: _loads(doc))
        self.assertEqual(len(d), self.N)
        self.assertEqual(d["key59999"], 59999)

    def test_many_tables(self):
        doc = "".join("[t%d]\nv = \"s%d\"\n" % (i, i) for i in range(self.N // 2))
        d = self._timed(lambda: _loads(doc))
        self.assertEqual(len(d), self.N // 2)
        self.assertEqual(d["t29999"], {"v": "s29999"})

    def test_many_array_of_tables_elements(self):
        doc = "".join("[[s]]\nk = %d\n" % i for i in range(self.N // 2))
        d = self._timed(lambda: _loads(doc))
        self.assertEqual(len(d["s"]), self.N // 2)
        self.assertEqual(d["s"][-1], {"k": self.N // 2 - 1})

    def test_long_multiline_array_and_string(self):
        doc = "a = [\n" + "  1,\n" * self.N + "]\ns = \"\"\"\n" + "line\n" * self.N + "\"\"\"\n"
        d = self._timed(lambda: _loads(doc))
        self.assertEqual(len(d["a"]), self.N)
        self.assertEqual(d["s"], "line\n" * self.N)

    def test_error_line_at_end_of_long_document(self):
        ParseError = _parse_error()
        doc = "".join("k%d = %d\r\n" % (i, i) for i in range(self.N)) + "k0 = 1\r\n"

        def run():
            with self.assertRaises(ParseError) as cm:
                _loads(doc)
            return cm.exception

        exc = self._timed(run)
        self.assertEqual(exc.line, self.N + 1)

    def test_error_late_in_long_statement(self):
        ParseError = _parse_error()
        doc = "x = 1\nbig = [\n" + "  1,\n" * self.N + "  ?\n]\n"

        def run():
            with self.assertRaises(ParseError) as cm:
                _loads(doc)
            return cm.exception

        exc = self._timed(run)
        self.assertEqual(exc.line, 2)


class Req19_LoadTextToml(unittest.TestCase):
    """Integration: `load_text(text, "toml")`."""

    def test_load_text(self):
        from cfgkit import load_text

        self.assertEqual(load_text("a = 1\n[s]\nk = 'v'\n", "toml"), {"a": 1, "s": {"k": "v"}})
        self.assertEqual(load_text("", "toml"), {})

    def test_load_text_errors(self):
        from cfgkit import ParseError, load_text

        with self.assertRaises(ParseError) as cm:
            load_text("a = 1\na = 2\n", "toml")
        self.assertEqual(cm.exception.line, 2)
        with self.assertRaises(ParseError):
            load_text("d = 1979-05-27\n", "toml")


class Req20_LoadFileToml(unittest.TestCase):
    """`load_file` for the suffix `.toml` (case-insensitive, UTF-8, like the existing formats,
    so `load_layers` can mix ini/json/toml files)."""

    def test_load_file_suffixes(self):
        from cfgkit import Config, load_file

        with tempfile.TemporaryDirectory() as d:
            for name in ("a.toml", "b.TOML", "c.Toml"):
                p = Path(d) / name
                p.write_bytes("[s]\nname = \"Jos\u00e9 \u2603\"\nport = 80\n".encode("utf-8"))
                with self.subTest(name=name):
                    c = load_file(p)
                    self.assertIsInstance(c, Config)
                    self.assertEqual(c.as_dict(), {"s": {"name": "Jos\u00e9 \u2603", "port": 80}})
                    self.assertEqual(c.get("s.port"), 80)
            self.assertEqual(load_file(str(Path(d) / "a.toml")).get("s.port"), 80)

    def test_load_file_parse_error(self):
        from cfgkit import ParseError, load_file

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.toml"
            p.write_text("a = 1\n[a]\n", encoding="utf-8")
            with self.assertRaises(ParseError) as cm:
                load_file(p)
            self.assertEqual(cm.exception.line, 2)

    def test_load_layers_mixes_formats(self):
        from cfgkit import load_layers

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.ini").write_text("[s]\nk = 1\ni = ini\n", encoding="utf-8")
            (Path(d) / "b.json").write_text('{"s": {"j": 2, "i": "json"}}', encoding="utf-8")
            (Path(d) / "c.toml").write_text("[s]\nt = 3\ni = \"toml\"\n[[servers]]\nhost = \"h\"\n",
                                            encoding="utf-8")
            c = load_layers([Path(d) / "a.ini", Path(d) / "b.json", Path(d) / "c.toml"])
            self.assertEqual(c.as_dict(), {"s": {"k": "1", "j": 2, "t": 3, "i": "toml"},
                                           "servers": [{"host": "h"}]})
            c2 = load_layers([Path(d) / "c.toml", Path(d) / "a.ini"])
            self.assertEqual(c2.get("s.i"), "ini")
            self.assertEqual(c2.get("s.t"), 3)


class Req21_ConfigFromToml(unittest.TestCase):
    """`Config.from_toml(text)`."""

    def test_from_toml(self):
        from cfgkit import Config

        c = Config.from_toml("[server]\nport = 8080\nhosts = ['a', 'b']\n")
        self.assertIsInstance(c, Config)
        self.assertEqual(c.as_dict(), {"server": {"port": 8080, "hosts": ["a", "b"]}})
        self.assertEqual(c.get("server.port"), 8080)
        self.assertEqual(c.section("server").get("port"), 8080)

    def test_from_toml_error(self):
        from cfgkit import Config, ParseError

        with self.assertRaises(ParseError) as cm:
            Config.from_toml("a = 1\n\nb = [1,\n2 3]\n")
        self.assertEqual(cm.exception.line, 3)


class Req22_LoadsTomlExported(unittest.TestCase):
    """`cfgkit.loads_toml` exported from the package."""

    def test_exported(self):
        import cfgkit

        self.assertTrue(callable(cfgkit.loads_toml))
        self.assertEqual(cfgkit.loads_toml("a.b = 1\n"), {"a": {"b": 1}})
        from cfgkit import loads_toml  # noqa: F401

    def test_raises_parse_error(self):
        import cfgkit

        with self.assertRaises(cfgkit.ParseError):
            cfgkit.loads_toml("a = \n")


class Req23_ConfigGetWalksLists(unittest.TestCase):
    """`Config.get(path, default)` now also walks lists: a path component made only of decimal
    digits indexes a list (`"servers.1.host"`), an out-of-range index or a non-numeric
    component on a list counts as missing (default / `KeyError`)."""

    def _config(self):
        from cfgkit import Config

        return Config({"servers": [{"host": "a", "ports": [80, 443]}, {"host": "b"}],
                       "matrix": [[1, 2], [3]], "d": {"0": "zero", "1": ["x", "y"]}})

    def test_indexing(self):
        c = self._config()
        self.assertEqual(c.get("servers.1.host"), "b")
        self.assertEqual(c.get("servers.0.host"), "a")
        self.assertEqual(c.get("servers.0.ports.1"), 443)
        self.assertEqual(c.get("servers.1"), {"host": "b"})
        self.assertEqual(c.get("matrix.0.1"), 2)
        self.assertEqual(c.get("matrix.1.0"), 3)
        self.assertEqual(c.get("d.0"), "zero")
        self.assertEqual(c.get("d.1.1"), "y")
        self.assertEqual(c.get("servers.1.host", "dflt"), "b")
        self.assertEqual(c.get("servers")[1]["host"], "b")

    def test_missing_with_default(self):
        c = self._config()
        self.assertEqual(c.get("servers.2.host", "dflt"), "dflt")
        self.assertEqual(c.get("servers.2", None), None)
        self.assertEqual(c.get("servers.99", 7), 7)
        self.assertEqual(c.get("servers.x", 7), 7)
        self.assertEqual(c.get("servers.host", 7), 7)
        self.assertEqual(c.get("servers.-1", 7), 7)
        self.assertEqual(c.get("servers.+1", 7), 7)
        self.assertEqual(c.get("servers.1x", 7), 7)
        self.assertEqual(c.get("servers. 1", 7), 7)
        self.assertEqual(c.get("servers.", 7), 7)
        self.assertEqual(c.get("servers.1.5", 7), 7)
        self.assertEqual(c.get("matrix.1.1", 7), 7)
        self.assertEqual(c.get("servers.0.ports.2", 7), 7)

    def test_missing_raises_keyerror(self):
        c = self._config()
        for path in ("servers.2", "servers.2.host", "servers.x", "servers.-1", "matrix.5.0",
                     "servers.0.ports.9", "servers.1.nope"):
            with self.subTest(path=path):
                with self.assertRaises(KeyError):
                    c.get(path)

    def test_from_toml_array_of_tables(self):
        from cfgkit import Config

        c = Config.from_toml("[[servers]]\nhost = \"a\"\n[[servers]]\nhost = \"b\"\n")
        self.assertEqual(c.get("servers.1.host"), "b")
        self.assertEqual(c.get("servers.2.host", None), None)


class Req24_ConfigContainsWalksLists(unittest.TestCase):
    """`Config.__contains__` follows the same rule as `Config.get` for lists."""

    def test_contains(self):
        from cfgkit import Config

        c = Config({"servers": [{"host": "a"}, {"host": "b"}], "m": [[1]]})
        self.assertIn("servers", c)
        self.assertIn("servers.0", c)
        self.assertIn("servers.1.host", c)
        self.assertIn("m.0.0", c)
        self.assertNotIn("servers.2", c)
        self.assertNotIn("servers.2.host", c)
        self.assertNotIn("servers.x", c)
        self.assertNotIn("servers.-1", c)
        self.assertNotIn("servers.1.port", c)
        self.assertNotIn("m.0.1", c)
        self.assertNotIn("m.0.0.0", c)


class Req25_ExistingBehaviourUnchanged(unittest.TestCase):
    """Existing INI/JSON/Config behaviour is unchanged."""

    def test_ini(self):
        from cfgkit import ParseError, load_text, parse_ini

        self.assertEqual(parse_ini("top = 1\n[a]\nx = y # not a comment\n; c\n[b]\nk=v"),
                         {"top": "1", "a": {"x": "y # not a comment"}, "b": {"k": "v"}})
        self.assertEqual(load_text("[a]\nx = 1\n", "ini"), {"a": {"x": "1"}})
        with self.assertRaises(ParseError) as cm:
            parse_ini("[a]\nx = 1\noops\n")
        self.assertEqual(cm.exception.line, 3)

    def test_json(self):
        from cfgkit import ParseError, load_text

        self.assertEqual(load_text('{"a": {"b": 1}}', "json"), {"a": {"b": 1}})
        with self.assertRaises(ParseError):
            load_text("[1, 2]", "json")
        with self.assertRaises(ParseError):
            load_text("{bad", "json")

    def test_unknown_format(self):
        from cfgkit import ConfigError, load_text

        with self.assertRaises(ConfigError):
            load_text("x", "yaml")

    def test_config(self):
        from cfgkit import Config, ConfigError

        c = Config({"a": {"b": 1, "c": {"d": 2}}, "x": 1})
        self.assertEqual(c.get("a.c.d"), 2)
        self.assertEqual(c.get("a.zz", 7), 7)
        self.assertEqual(c.get("x.y", 7), 7)
        self.assertIn("a.b", c)
        self.assertNotIn("a.b.c", c)
        with self.assertRaises(KeyError):
            c.get("nope")
        m = c.merge(Config({"a": {"c": {"e": 3}}, "x": [1]}))
        self.assertEqual(m.as_dict(), {"a": {"b": 1, "c": {"d": 2, "e": 3}}, "x": [1]})
        with self.assertRaises(ConfigError):
            c.section("x")
        self.assertEqual(Config().as_dict(), {})

    def test_files(self):
        from cfgkit import load_file, load_layers

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.ini").write_text("[s]\nk = 1\n", encoding="utf-8")
            (Path(d) / "b.json").write_text('{"s": {"j": 2}}', encoding="utf-8")
            c = load_layers([Path(d) / "a.ini", Path(d) / "b.json"])
            self.assertEqual(c.as_dict(), {"s": {"k": "1", "j": 2}})
            (Path(d) / "c.INI").write_text("[s]\nk = 3\n", encoding="utf-8")
            self.assertEqual(load_file(Path(d) / "c.INI").get("s.k"), "3")
            (Path(d) / "d.JSON").write_text('{"u": "\u00e9"}', encoding="utf-8")
            self.assertEqual(load_file(Path(d) / "d.JSON").get("u"), "\u00e9")


if __name__ == "__main__":
    unittest.main()
