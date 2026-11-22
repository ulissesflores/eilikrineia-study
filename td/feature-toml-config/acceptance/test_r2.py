"""Acceptance tests for TOML support in cfgkit.

Only the standard library `unittest` is used; no TOML library is imported.
"""
import ast
import importlib
import math
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "cfgkit"

BANNED_MODULES = ("tomllib", "tomli", "toml", "tomlkit", "tomli_w", "pytomlpp", "rtoml", "qtoml")


def _parse_error():
    from cfgkit import ParseError
    return ParseError


def loads(text):
    mod = importlib.import_module("cfgkit.toml")
    return mod.loads(text)


class TomlCase(unittest.TestCase):
    """Helpers shared by the TOML test classes."""

    def ok(self, text, expected):
        result = loads(text)
        self.assertEqual(result, expected, msg="document: %r" % (text,))
        return result

    def bad(self, text):
        ParseError = _parse_error()
        with self.assertRaises(ParseError, msg="document should be rejected: %r" % (text,)) as cm:
            loads(text)
        return cm.exception

    def bad_all(self, docs):
        for doc in docs:
            with self.subTest(doc=doc):
                self.bad(doc)

    def ok_all(self, pairs):
        for doc, expected in pairs:
            with self.subTest(doc=doc):
                self.ok(doc, expected)


# ---------------------------------------------------------------------------


class Req01_NoTomlLibrary(unittest.TestCase):
    """The parser must be written by hand: do not import (or shell out to) `tomllib`,
    `tomli`, `toml`, `tomlkit` or any other TOML library, in any module of the package."""

    def _py_files(self):
        files = sorted(PKG.rglob("*.py"))
        self.assertTrue(files)
        return files

    def test_no_static_imports_of_toml_libraries(self):
        for path in self._py_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        self.assertNotIn(top, BANNED_MODULES, "%s imports %s" % (path, alias.name))
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    top = node.module.split(".")[0]
                    self.assertNotIn(top, BANNED_MODULES, "%s imports from %s" % (path, node.module))

    def test_no_dynamic_references_to_toml_libraries(self):
        for path in self._py_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    low = node.value.lower()
                    for name in ("tomllib", "tomli", "tomlkit"):
                        self.assertNotIn(name, low, "%s mentions %r" % (path, name))
                if isinstance(node, ast.Call):
                    func = node.func
                    fname = getattr(func, "id", None) or getattr(func, "attr", None)
                    if fname in ("__import__", "import_module") and node.args:
                        arg = node.args[0]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            self.assertNotIn(arg.value.split(".")[0], BANNED_MODULES,
                                             "%s dynamically imports %r" % (path, arg.value))

    def test_works_with_toml_libraries_blocked(self):
        code = (
            "import sys\n"
            "for n in %r:\n"
            "    sys.modules[n] = None\n"
            "import cfgkit, cfgkit.toml\n"
            "d = cfgkit.toml.loads('a = 1\\n[t]\\nb = \"x\"\\n')\n"
            "assert d == {'a': 1, 't': {'b': 'x'}}, d\n"
            "assert cfgkit.loads_toml('k = [1, 2]') == {'k': [1, 2]}\n"
            "print('OK')\n"
        ) % (BANNED_MODULES,)
        proc = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK", proc.stdout)

    def test_no_toml_library_loaded_after_use(self):
        code = (
            "import sys\n"
            "import cfgkit, cfgkit.toml\n"
            "cfgkit.toml.loads('a = 1\\n[[x]]\\ny = 2.5\\n')\n"
            "cfgkit.load_text('a = 1', 'toml')\n"
            "bad = [n for n in %r if n in sys.modules]\n"
            "print('LOADED', bad)\n"
        ) % (BANNED_MODULES,)
        proc = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("LOADED []", proc.stdout)


class Req02_LoadsReturnsDict(TomlCase):
    """`cfgkit/toml.py` (new): `loads(text) -> dict` implements TOML v1.0.0 and behaves like
    a conforming parser on valid and invalid documents."""

    def test_module_and_function_exist(self):
        mod = importlib.import_module("cfgkit.toml")
        self.assertTrue(callable(mod.loads))

    def test_empty_and_blank_documents(self):
        self.ok("", {})
        self.ok("\n\n   \n\t\n", {})
        self.ok("# only a comment\n", {})

    def test_full_document(self):
        doc = (
            "# This is a TOML document\n"
            "\n"
            'title = "TOML Example"\n'
            "\n"
            "[owner]\n"
            'name = "Tom Preston-Werner"\n'
            "\n"
            "[database]\n"
            "enabled = true\n"
            "ports = [ 8000, 8001, 8002 ]\n"
            'data = [ ["delta", "phi"], [3.14] ]\n'
            "temp_targets = { cpu = 79.5, case = 72.0 }\n"
            "\n"
            "[servers]\n"
            "\n"
            "[servers.alpha]\n"
            'ip = "10.0.0.1"\n'
            'role = "frontend"\n'
            "\n"
            "[servers.beta]\n"
            'ip = "10.0.0.2"\n'
            'role = "backend"\n'
        )
        self.ok(doc, {
            "title": "TOML Example",
            "owner": {"name": "Tom Preston-Werner"},
            "database": {
                "enabled": True,
                "ports": [8000, 8001, 8002],
                "data": [["delta", "phi"], [3.14]],
                "temp_targets": {"cpu": 79.5, "case": 72.0},
            },
            "servers": {
                "alpha": {"ip": "10.0.0.1", "role": "frontend"},
                "beta": {"ip": "10.0.0.2", "role": "backend"},
            },
        })

    def test_basic_invalid_documents(self):
        self.bad_all([
            "a",
            "a =",
            "= 1",
            "a = 1 b = 2",
            "a = 1\nb",
            "a == 1",
            "[a]b = 1",
            "a = 1 2",
            "a = foo",
        ])


class Req03_DatesRejected(TomlCase):
    """ONE deliberate exception: date, time and date-time values are not supported and
    raise `ParseError`."""

    def test_dates_and_times_raise(self):
        self.bad_all([
            "d = 1979-05-27T07:32:00Z",
            "d = 1979-05-27T00:32:00-07:00",
            "d = 1979-05-27T00:32:00.999999-07:00",
            "d = 1979-05-27 07:32:00Z",
            "d = 1979-05-27T07:32:00",
            "d = 1979-05-27T00:32:00.999999",
            "d = 1979-05-27",
            "d = 07:32:00",
            "d = 00:32:00.999999",
            "d = [1979-05-27]",
            "d = { x = 07:32:00 }",
            "[t]\nd = 1979-05-27T07:32:00Z\n",
        ])


class Req04_Comments(TomlCase):
    """Comments are supported."""

    def test_comments(self):
        self.ok("# full line\na = 1 # trailing\n  # indented\n", {"a": 1})
        self.ok('a = "# not a comment" # comment', {"a": "# not a comment"})
        self.ok("[t] # comment after header\nx = 1\n", {"t": {"x": 1}})
        self.ok("[[t]] # comment\nx = 1\n", {"t": [{"x": 1}]})
        self.ok("a = 1#no space\n", {"a": 1})
        self.ok("#\n#\t tab and ### hashes\n", {})
        self.ok("# comment at EOF without newline", {})


class Req05_Keys(TomlCase):
    """Bare, quoted and dotted keys (whitespace allowed around the dots)."""

    def test_bare_keys(self):
        self.ok("key = 1\nbare_key = 2\nbare-key = 3\n1234 = 4\nA-_z9 = 5\n",
                {"key": 1, "bare_key": 2, "bare-key": 3, "1234": 4, "A-_z9": 5})
        self.ok("\t  key\t=\t1  \n", {"key": 1})
        self.ok("key=1", {"key": 1})

    def test_quoted_keys(self):
        self.ok('"127.0.0.1" = 1\n"character encoding" = 2\n\'key2\' = 3\n'
                '\'quoted "value"\' = 4\n"\\u0041\\t" = 5\n',
                {"127.0.0.1": 1, "character encoding": 2, "key2": 3,
                 'quoted "value"': 4, "A\t": 5})
        self.ok('"" = 1', {"": 1})
        self.ok("'' = 1", {"": 1})
        self.ok('"ʎǝʞ" = 1', {"ʎǝʞ": 1})

    def test_dotted_keys(self):
        self.ok('name = "Orange"\nphysical.color = "orange"\nphysical.shape = "round"\n'
                'site."google.com" = true\n',
                {"name": "Orange", "physical": {"color": "orange", "shape": "round"},
                 "site": {"google.com": True}})
        self.ok("fruit . color = 1\nfruit\t.\tflavor = 2\n", {"fruit": {"color": 1, "flavor": 2}})
        self.ok("3.14159 = 1", {"3": {"14159": 1}})
        self.ok("a.'b'.\"c\" = 1", {"a": {"b": {"c": 1}}})

    def test_quoted_and_bare_are_the_same_key(self):
        self.bad('spelling = "favorite"\n"spelling" = "favourite"\n')
        self.bad("a = 1\n'a' = 2\n")

    def test_invalid_keys(self):
        self.bad_all([
            "= 1",
            "a b = 1",
            "a. = 1",
            ".a = 1",
            "a..b = 1",
            "\"a = 1",
            "a\n= 1",
            "é = 1",
            "a$ = 1",
            '"""a""" = 1',
            "'''a''' = 1",
            '"a\nb" = 1',
        ])


class Req06_BasicStrings(TomlCase):
    """Basic strings with all escape rules (\\b \\t \\n \\f \\r \\" \\\\ \\uXXXX \\UXXXXXXXX);
    unicode escapes must be scalar values."""

    def test_escapes(self):
        self.ok(r's = "a\bb\tc\nd\fe\rf\"g\\h"', {"s": "a\bb\tc\nd\fe\rf\"g\\h"})
        self.ok(r's = "\u00E9\u00e9 \U0001F600 \u0000 \U0010FFFF"',
                {"s": "\u00e9\u00e9 \U0001F600 \x00 \U0010FFFF"})
        self.ok('s = "tab\there"', {"s": "tab\there"})
        self.ok('s = "literal\ttab"', {"s": "literal\ttab"})
        self.ok('s = ""', {"s": ""})
        self.ok("s = \"it's\"", {"s": "it's"})
        self.ok('s = "unicode é ✓"', {"s": "unicode é ✓"})

    def test_invalid_escapes(self):
        self.bad_all([
            r's = "\x41"',
            r's = "\e"',
            r's = "\/"',
            r's = "\ "',
            r's = "\a"',
            r's = "\u12"',
            r's = "\u12G4"',
            r's = "\U0001F60"',
            r's = "\uD800"',
            r's = "\uDFFF"',
            r's = "\U0000D800"',
            r's = "\U00110000"',
            r's = "\UFFFFFFFF"',
            's = "\\',
        ])

    def test_invalid_basic_strings(self):
        self.bad_all([
            's = "unterminated',
            's = "line\nbreak"',
            's = "a" "b"',
            's = "a"b',
        ])


class Req07_LiteralStrings(TomlCase):
    """Literal strings: no escaping, single line."""

    def test_literal(self):
        self.ok(r"s = 'C:\Users\nodejs\templates'", {"s": r"C:\Users\nodejs\templates"})
        self.ok(r"s = '\\ServerX\admin$\system32\'", {"s": "\\\\ServerX\\admin$\\system32\\"})
        self.ok("s = 'Tom \"Dubs\" Preston-Werner'", {"s": 'Tom "Dubs" Preston-Werner'})
        self.ok(r"s = '<\i\c*\s*>'", {"s": r"<\i\c*\s*>"})
        self.ok("s = ''", {"s": ""})
        self.ok("s = 'a\tb'", {"s": "a\tb"})

    def test_invalid_literal(self):
        self.bad_all([
            "s = 'unterminated",
            "s = 'line\nbreak'",
            "s = 'it's'",
        ])


class Req08_MultilineBasicStrings(TomlCase):
    """Multi-line basic strings: escapes, line-ending backslash trimming, the first newline
    after the opening delimiter trimmed, up to two quotes next to the closing delimiter."""

    def test_first_newline_trimmed(self):
        self.ok('s = """\nRoses are red\nViolets are blue"""',
                {"s": "Roses are red\nViolets are blue"})
        self.ok('s = """\n\nx"""', {"s": "\nx"})
        self.ok('s = """x\n"""', {"s": "x\n"})
        self.ok('s = """"""', {"s": ""})
        self.ok('s = """\n"""', {"s": ""})

    def test_line_ending_backslash(self):
        self.ok('s = """\nThe quick brown \\\n\n\n  fox jumps over \\\n    the lazy dog."""',
                {"s": "The quick brown fox jumps over the lazy dog."})
        self.ok('s = """\\\n       The quick brown \\\n       fox jumps over \\\n'
                '       the lazy dog.\\\n       """',
                {"s": "The quick brown fox jumps over the lazy dog."})
        self.ok('s = """a\\   \t\n   b"""', {"s": "ab"})
        self.ok('s = """a \\\n\n\t  \n b"""', {"s": "a b"})

    def test_escapes_and_quotes(self):
        self.ok('s = """a\\tb\\u00e9\\"\\\\"""', {"s": 'a\tb\u00e9"\\'})
        self.ok('s = """Here are two quotation marks: "". Simple enough."""',
                {"s": 'Here are two quotation marks: "". Simple enough.'})
        self.ok('s = """Here are three quotation marks: ""\\"."""',
                {"s": 'Here are three quotation marks: """.'})
        self.ok('s = """Here are fifteen quotation marks: ""\\"""\\"""\\"""\\"""\\"."""',
                {"s": 'Here are fifteen quotation marks: """"""""""""""".'})
        self.ok('s = """"This," she said, "is just a pointless statement.""""',
                {"s": '"This," she said, "is just a pointless statement."'})
        self.ok('s = """a""""', {"s": 'a"'})
        self.ok('s = """a"""""', {"s": 'a""'})
        self.ok('s = """""a"""', {"s": '""a'})
        self.ok('s = """tab\there"""', {"s": "tab\there"})

    def test_invalid(self):
        self.bad_all([
            's = """a""""""',
            's = """a"""" "',
            's = """unterminated',
            's = """unterminated""',
            's = """\\x41"""',
            's = """\\uD800"""',
            's = """\\U00110000"""',
            's = """a\\ b"""',
            's = """a""" x',
        ])


class Req09_MultilineLiteralStrings(TomlCase):
    """Multi-line literal strings: first newline trimmed, no escapes, up to two quotes next
    to the closing delimiter."""

    def test_multiline_literal(self):
        self.ok("s = '''I [dw]on't need \\d{2} apples'''", {"s": "I [dw]on't need \\d{2} apples"})
        self.ok("s = '''\nThe first newline is\ntrimmed in raw strings.\n   All other whitespace\n"
                "   is preserved.\n'''",
                {"s": "The first newline is\ntrimmed in raw strings.\n   All other whitespace\n"
                      "   is preserved.\n"})
        self.ok("s = '''Here are fifteen quotation marks: \"\"\"\"\"\"\"\"\"\"\"\"\"\"\"'''",
                {"s": 'Here are fifteen quotation marks: """""""""""""""'})
        self.ok("s = ''''That,' she said, 'is still pointless.''''",
                {"s": "'That,' she said, 'is still pointless.'"})
        self.ok("s = '''a\\\n  b'''", {"s": "a\\\n  b"})
        self.ok("s = ''''''", {"s": ""})
        self.ok("s = '''a'''''", {"s": "a''"})
        self.ok("s = '''a\tb'''", {"s": "a\tb"})

    def test_invalid(self):
        self.bad_all([
            "s = '''a''''''",
            "s = '''unterminated",
            "s = '''unterminated''",
            "s = '''a''' x",
        ])


class Req10_Integers(TomlCase):
    """Integers: decimal with underscores, no leading zeros, `0x`/`0o`/`0b`."""

    def test_valid(self):
        self.ok_all([
            ("i = +99", {"i": 99}),
            ("i = 42", {"i": 42}),
            ("i = 0", {"i": 0}),
            ("i = -17", {"i": -17}),
            ("i = +0", {"i": 0}),
            ("i = -0", {"i": 0}),
            ("i = 1_000", {"i": 1000}),
            ("i = 5_349_221", {"i": 5349221}),
            ("i = 53_49_221", {"i": 5349221}),
            ("i = 1_2_3_4_5", {"i": 12345}),
            ("i = 0xDEADBEEF", {"i": 0xDEADBEEF}),
            ("i = 0xdeadbeef", {"i": 0xDEADBEEF}),
            ("i = 0xdead_beef", {"i": 0xDEADBEEF}),
            ("i = 0x00ff", {"i": 255}),
            ("i = 0o01234567", {"i": 0o1234567}),
            ("i = 0o755", {"i": 0o755}),
            ("i = 0b11010110", {"i": 0b11010110}),
            ("i = 0b1101_0110", {"i": 0b11010110}),
            ("i = 9223372036854775807", {"i": 9223372036854775807}),
            ("i = -9223372036854775808", {"i": -9223372036854775808}),
        ])

    def test_invalid(self):
        self.bad_all([
            "i = 01",
            "i = 007",
            "i = +01",
            "i = 0_0",
            "i = 1__000",
            "i = _1",
            "i = 1_",
            "i = -_1",
            "i = 0X1F",
            "i = 0O7",
            "i = 0B1",
            "i = 0x",
            "i = 0xG",
            "i = 0x_1",
            "i = 0x1_",
            "i = 0o8",
            "i = 0b2",
            "i = +0x1",
            "i = -0x1",
            "i = -0o7",
            "i = +0b1",
            "i = 1 000",
            "i = 12a",
            "i = +",
            "i = -",
            "i = ++1",
        ])


class Req11_Floats(TomlCase):
    """Floats: fraction/exponent/underscores, `inf`, `nan` with optional sign."""

    def test_valid(self):
        self.ok_all([
            ("f = +1.0", {"f": 1.0}),
            ("f = 3.1415", {"f": 3.1415}),
            ("f = -0.01", {"f": -0.01}),
            ("f = 5e+22", {"f": 5e22}),
            ("f = 1e06", {"f": 1e6}),
            ("f = -2E-2", {"f": -2e-2}),
            ("f = 6.626e-34", {"f": 6.626e-34}),
            ("f = 224_617.445_991_228", {"f": 224617.445991228}),
            ("f = 1e1_0", {"f": 1e10}),
            ("f = 0.0", {"f": 0.0}),
            ("f = 0e0", {"f": 0.0}),
            ("f = 0.1", {"f": 0.1}),
            ("f = 1E2", {"f": 100.0}),
            ("f = inf", {"f": math.inf}),
            ("f = +inf", {"f": math.inf}),
            ("f = -inf", {"f": -math.inf}),
        ])

    def test_float_types_and_signs(self):
        self.assertIs(type(loads("f = 1e2")["f"]), float)
        self.assertIs(type(loads("f = 1.0")["f"]), float)
        neg = loads("f = -0.0")["f"]
        self.assertEqual(math.copysign(1.0, neg), -1.0)
        pos = loads("f = +0.0")["f"]
        self.assertEqual(math.copysign(1.0, pos), 1.0)

    def test_nan(self):
        for doc in ("f = nan", "f = +nan", "f = -nan"):
            with self.subTest(doc=doc):
                v = loads(doc)["f"]
                self.assertIs(type(v), float)
                self.assertTrue(math.isnan(v))

    def test_invalid(self):
        self.bad_all([
            "f = .7",
            "f = 7.",
            "f = 3.e+20",
            "f = +.5",
            "f = 1e",
            "f = 1e+",
            "f = 1.0e",
            "f = 1.e2",
            "f = 01.5",
            "f = 00.1",
            "f = -01.0",
            "f = 1__0.0",
            "f = 1.0_",
            "f = 1._0",
            "f = 1_.0",
            "f = 1e_1",
            "f = 1e1_",
            "f = 1.0.0",
            "f = 1,5",
            "f = Inf",
            "f = NaN",
            "f = infinity",
            "f = nan1",
            "f = inf_",
            "f = --inf",
        ])


class Req12_Booleans(TomlCase):
    """Booleans `true` and `false` (lower case)."""

    def test_booleans(self):
        d = self.ok("t = true\nf = false\n", {"t": True, "f": False})
        self.assertIs(d["t"], True)
        self.assertIs(d["f"], False)

    def test_invalid(self):
        self.bad_all(["b = True", "b = FALSE", "b = tru", "b = truee", "b = yes"])


class Req13_Arrays(TomlCase):
    """Arrays: any mix of types, newlines, comments and a trailing comma allowed."""

    def test_arrays(self):
        self.ok_all([
            ("a = []", {"a": []}),
            ("a = [ ]", {"a": []}),
            ("a = [1, 2, 3]", {"a": [1, 2, 3]}),
            ('a = ["red", "yellow", "green"]', {"a": ["red", "yellow", "green"]}),
            ("a = [ [ 1, 2 ], [3, 4, 5] ]", {"a": [[1, 2], [3, 4, 5]]}),
            ('a = [ [ 1, 2 ], ["a", "b", "c"] ]', {"a": [[1, 2], ["a", "b", "c"]]}),
            ("a = [ 0.1, 0.2, 0.5, 1, 2, 5 ]", {"a": [0.1, 0.2, 0.5, 1, 2, 5]}),
            ('a = [1, "x", 2.5, true, [], {}, {k = "v"}]',
             {"a": [1, "x", 2.5, True, [], {}, {"k": "v"}]}),
            ("a = [1,]", {"a": [1]}),
            ("a = [\n  1,\n  2, # comment\n]", {"a": [1, 2]}),
            ("a = [\n  # leading comment\n  1 # c\n  , 2\n\n]", {"a": [1, 2]}),
            ("a = [\n]", {"a": []}),
            ("a = [ # c\n]", {"a": []}),
            ("a = [[[]]]", {"a": [[[]]]}),
            ('a = [\'x\', """y""", \'\'\'z\'\'\']', {"a": ["x", "y", "z"]}),
            ('a = [\n  { x = 1 },\n  { x = 2 },\n]', {"a": [{"x": 1}, {"x": 2}]}),
        ])

    def test_invalid(self):
        self.bad_all([
            "a = [,]",
            "a = [1,,2]",
            "a = [1 2]",
            "a = [1, 2",
            "a = [1, 2,\n",
            "a = [",
            "a = ]",
            "a = [1]]",
            "a = [,1]",
            "a = [1, 2] 3",
        ])


class Req14_InlineTables(TomlCase):
    """Inline tables: one line, no trailing comma."""

    def test_inline(self):
        self.ok_all([
            ('name = { first = "Tom", last = "Preston-Werner" }',
             {"name": {"first": "Tom", "last": "Preston-Werner"}}),
            ("point = { x = 1, y = 2 }", {"point": {"x": 1, "y": 2}}),
            ('animal = { type.name = "pug" }', {"animal": {"type": {"name": "pug"}}}),
            ("t = {}", {"t": {}}),
            ("t = { }", {"t": {}}),
            ("t = {a.b = 1, a.c = 2}", {"t": {"a": {"b": 1, "c": 2}}}),
            ("t = {a = {b = {c = 1}}}", {"t": {"a": {"b": {"c": 1}}}}),
            ("t = {a = [1, {b = 2}]}", {"t": {"a": [1, {"b": 2}]}}),
            ("t = {a = [\n1,\n2\n]}", {"t": {"a": [1, 2]}}),
            ("t={a=1,b=2}", {"t": {"a": 1, "b": 2}}),
        ])

    def test_invalid(self):
        self.bad_all([
            "t = {a = 1,}",
            "t = {a = 1\n}",
            "t = {\na = 1}",
            "t = {a = 1,\nb = 2}",
            "t = {a = 1 # comment\n}",
            "t = {a = 1, a = 2}",
            "t = {a.b = 1, a = 2}",
            "t = {a = {}, a.b = 1}",
            "t = {a = 1, a.b = 2}",
            "t = {a = 1 b = 2}",
            "t = {,}",
            "t = {a}",
            "t = {a = 1",
            "t = {a = 1}}",
        ])


class Req15_TableHeaders(TomlCase):
    """`[table]` headers."""

    def test_tables(self):
        self.ok("[table]", {"table": {}})
        self.ok('[table-1]\nkey1 = "some string"\nkey2 = 123\n\n[table-2]\nkey1 = "another string"\n'
                "key2 = 456\n",
                {"table-1": {"key1": "some string", "key2": 123},
                 "table-2": {"key1": "another string", "key2": 456}})
        self.ok('[dog."tater.man"]\ntype.name = "pug"\n',
                {"dog": {"tater.man": {"type": {"name": "pug"}}}})
        self.ok("[a.b.c]\n[ d.e.f ]\n[ g .  h  . i ]\n[ j . \"ʞ\" . 'l' ]\n",
                {"a": {"b": {"c": {}}}, "d": {"e": {"f": {}}}, "g": {"h": {"i": {}}},
                 "j": {"ʞ": {"l": {}}}})
        self.ok("[x.y.z.w]\n[x]\n", {"x": {"y": {"z": {"w": {}}}}})
        self.ok("top = 1\n[a]\nk = 2\n[b]\nk = 3\n", {"top": 1, "a": {"k": 2}, "b": {"k": 3}})
        self.ok("[\t a \t]\n", {"a": {}})

    def test_out_of_order(self):
        self.ok("[fruit.apple]\n[animal]\n[fruit.orange]\n",
                {"fruit": {"apple": {}, "orange": {}}, "animal": {}})

    def test_invalid(self):
        self.bad_all([
            "[]",
            "[a",
            "[a.]",
            "[.a]",
            "[a..b]",
            "[a b]",
            "[a]]",
            "[a] x = 1",
            "[a]\n[a]",
            "[a] [b]",
            "[a\n]",
            "[ [a] ]",
        ])


class Req16_ArrayOfTables(TomlCase):
    """`[[array of tables]]` headers."""

    def test_array_of_tables(self):
        self.ok('[[products]]\nname = "Hammer"\nsku = 738594937\n\n[[products]]  # empty table\n\n'
                '[[products]]\nname = "Nail"\nsku = 284758393\ncolor = "gray"\n',
                {"products": [{"name": "Hammer", "sku": 738594937}, {},
                              {"name": "Nail", "sku": 284758393, "color": "gray"}]})
        self.ok('[[fruits]]\nname = "apple"\n\n[fruits.physical]\ncolor = "red"\nshape = "round"\n\n'
                '[[fruits.varieties]]\nname = "red delicious"\n\n[[fruits.varieties]]\n'
                'name = "granny smith"\n\n\n[[fruits]]\nname = "banana"\n\n[[fruits.varieties]]\n'
                'name = "plantain"\n',
                {"fruits": [
                    {"name": "apple", "physical": {"color": "red", "shape": "round"},
                     "varieties": [{"name": "red delicious"}, {"name": "granny smith"}]},
                    {"name": "banana", "varieties": [{"name": "plantain"}]},
                ]})
        self.ok("[[ a . b ]]\nx = 1\n[[a.b]]\nx = 2\n", {"a": {"b": [{"x": 1}, {"x": 2}]}})
        self.ok("[[a]]\n[[a]]\n", {"a": [{}, {}]})

    def test_invalid(self):
        self.bad_all([
            "[[]]",
            "[[a]",
            "[[a]] x = 1",
            "[[a.]]",
            "[ [a]]",
            "[[a] ]",
            "[[a]]]",
        ])


class Req17_ControlCharacters(TomlCase):
    """Control characters (other than tab, and newline where allowed) in strings and comments
    are errors."""

    CONTROLS = ["\x00", "\x01", "\x08", "\x0b", "\x0c", "\x1f", "\x7f"]

    def test_control_chars_in_strings(self):
        for c in self.CONTROLS:
            for doc in ('s = "a%sb"' % c, "s = 'a%sb'" % c,
                        's = """a%sb"""' % c, "s = '''a%sb'''" % c,
                        '"k%s" = 1' % c, "'k%s' = 1" % c):
                with self.subTest(doc=doc):
                    self.bad(doc)

    def test_control_chars_in_comments(self):
        for c in self.CONTROLS:
            for doc in ("# a%sb" % c, "a = 1 # x%sy" % c, "a = [ # x%sy\n]" % c):
                with self.subTest(doc=doc):
                    self.bad(doc)

    def test_tab_allowed(self):
        self.ok("# tab\there\ns = \"a\tb\"\nl = 'a\tb'\nm = \"\"\"a\tb\"\"\"\nn = '''a\tb'''\n",
                {"s": "a\tb", "l": "a\tb", "m": "a\tb", "n": "a\tb"})

    def test_escaped_control_chars_allowed(self):
        self.ok(r's = "\u0000\u001f\u007f"', {"s": "\x00\x1f\x7f"})


class Req18_LineEndings(TomlCase):
    """A `\\r\\n` line ending is treated exactly like `\\n` everywhere (also inside multi-line
    strings); a lone `\\r` is an error."""

    def test_crlf(self):
        self.ok("a = 1\r\nb = 2\r\n", {"a": 1, "b": 2})
        self.ok("# c\r\n[t]\r\nx = [\r\n1,\r\n2, # c\r\n]\r\n[[arr]]\r\n", {"t": {"x": [1, 2]}, "arr": [{}]})
        self.ok('s = """\r\nline1\r\nline2\r\n"""', {"s": "line1\nline2\n"})
        self.ok("s = '''\r\nline1\r\nline2\r\n'''", {"s": "line1\nline2\n"})
        self.ok('s = """a \\\r\n   b"""', {"s": "a b"})
        self.ok('s = """a\\   \r\n\r\n   b"""', {"s": "ab"})
        self.ok("a = 1 # comment\r\n", {"a": 1})

    def test_lone_cr(self):
        self.bad_all([
            "a = 1\r",
            "a = 1\rb = 2",
            "a = 1\r\r\n",
            's = "a\rb"',
            "s = 'a\rb'",
            's = """a\rb"""',
            "s = '''a\rb'''",
            "# comment\r",
            "a = [1,\r2]",
            "\r",
        ])


class Req19_DefinitionRules(TomlCase):
    """Every TOML rule about what may be defined where: duplicate keys; redefining a table;
    implicit tables; dotted-key tables; immutable inline tables and static arrays; arrays of
    tables forget flags of the previous element; a header cannot turn a value into a table."""

    def test_duplicate_keys(self):
        self.bad_all([
            "a = 1\na = 2",
            "a = 1\na = 1",
            "a.b = 1\na.b = 2",
            "[t]\nx = 1\nx = 2",
            "a = 1\na.b = 2",
            "a.b = 1\na = 2",
            "a.b = 1\na.b.c = 2",
            "a = {}\na.b = 1",
            "a = []\na.b = 1",
            "[t]\nx = 1\n[t.x]",
        ])

    def test_redefining_tables(self):
        self.bad_all([
            "[a]\n[a]",
            "[a]\nb = 1\n[a]\nc = 2",
            "[a.b]\n[a.b]",
            "[a]\n[a.b]\n[a]",
            "[a.b]\n[a]\n[a]",
            "[a]\nb = 1\n[a.b]",
            "[a]\nb = 1\n[[a.b]]",
            "[a]\n[[a]]",
            "[[a]]\n[a]",
            "[a]\nb = {}\n[a.b]",
        ])

    def test_implicit_tables(self):
        self.ok("[x.y.z.w]\n[x]\na = 1\n", {"x": {"a": 1, "y": {"z": {"w": {}}}}})
        self.ok("[a.b.c]\nd = 1\n[a.b]\ne = 2\n", {"a": {"b": {"c": {"d": 1}, "e": 2}}})
        self.ok("[a.b.c]\n[a.b.d]\n", {"a": {"b": {"c": {}, "d": {}}}})
        self.ok("[a.b]\nc = 1\n[a]\nd = 2\n", {"a": {"b": {"c": 1}, "d": 2}})

    def test_dotted_key_tables(self):
        self.ok('[fruit]\napple.color = "red"\napple.taste.sweet = true\n\n'
                "[fruit.apple.texture]\nsmooth = true\n",
                {"fruit": {"apple": {"color": "red", "taste": {"sweet": True},
                                     "texture": {"smooth": True}}}})
        self.ok("a.b = 1\n[a.c]\nx = 2\n", {"a": {"b": 1, "c": {"x": 2}}})
        self.ok("a.b.c = 1\na.b.d = 2\na.e = 3\n", {"a": {"b": {"c": 1, "d": 2}, "e": 3}})
        self.bad_all([
            '[fruit]\napple.color = "red"\napple.taste.sweet = true\n\n[fruit.apple]\n',
            '[fruit]\napple.color = "red"\napple.taste.sweet = true\n\n[fruit.apple.taste]\n',
            "a.b = 1\n[a]\n",
            "a.b.c = 1\n[a.b]\n",
            "[t]\na.b = 1\n[t.a]\n",
            "a.b = 1\n[[a]]\n",
            "[a.b]\nc = 1\n[a]\nb.d = 2\n",
        ])

    def test_inline_tables_are_immutable(self):
        self.bad_all([
            '[product]\ntype = { name = "Nail" }\ntype.edible = false\n',
            '[product]\ntype.name = "Nail"\ntype = { edible = false }\n',
            "a = {x = 1}\na.y = 2\n",
            "a = {x = 1}\n[a]\n",
            "a = {x = 1}\n[a.b]\n",
            "a = {}\n[a]\n",
            "a = {b = {}}\n[a.b.c]\n",
            "a = {b = {}}\na.b.c = 1\n",
            "a = {x = 1}\n[[a]]\n",
            "a = {x = 1}\n[[a.b]]\n",
            "t = {a = {b = 1}}\nt.a.c = 2\n",
        ])

    def test_static_arrays_are_immutable(self):
        self.bad_all([
            "fruits = []\n[[fruits]]\n",
            "a = [{}]\n[[a]]\n",
            "a = [{x = 1}]\n[a.b]\n",
            "a = [1]\n[a]\n",
            "a = [{b = 1}]\n[[a.c]]\n",
        ])

    def test_array_of_tables_forgets_flags(self):
        self.ok("[[x]]\n[x.y]\nk = 1\n[[x]]\n[x.y]\nk = 2\n",
                {"x": [{"y": {"k": 1}}, {"y": {"k": 2}}]})
        self.ok("[[x]]\na.b = 1\n[[x]]\na.b = 2\n", {"x": [{"a": {"b": 1}}, {"a": {"b": 2}}]})
        self.ok("[[x]]\nk = 1\n[[x]]\nk = 2\n", {"x": [{"k": 1}, {"k": 2}]})
        self.ok("[[a.b]]\n[a]\nc = 1\n", {"a": {"b": [{}], "c": 1}})
        self.bad_all([
            "[[x]]\n[x.y]\n[x.y]\n",
            "[[x]]\nk = 1\nk = 2\n",
        ])

    def test_header_cannot_turn_value_into_table(self):
        self.bad_all([
            "a = 1\n[a]",
            "a = 1\n[a.b]",
            "a = 1\n[[a]]",
            "a = 'x'\n[[a.b]]",
            "a = true\nb = 1\n[a]",
            "[t]\nv = 1\n[t.v.w]",
            "[[t]]\nv = 1\n[t.v]",
        ])

    def test_array_of_tables_subtables(self):
        self.bad_all([
            '[fruit.physical]\ncolor = "red"\n[[fruit]]\nname = "apple"\n',
            '[[fruit]]\nname = "apple"\n[[fruit.variety]]\nname = "red"\n[fruit.variety]\n',
        ])

    def test_dotted_keys_after_tables(self):
        self.ok("[a]\nb.c = 1\n[d]\na.x = 2\n", {"a": {"b": {"c": 1}}, "d": {"a": {"x": 2}}})


class Req20_PlainTypes(TomlCase):
    """Return plain `dict`/`list`/`str`/`int`/`float`/`bool` objects (an integer never
    becomes a float)."""

    def test_types(self):
        d = loads('i = 1\nf = 1.5\ns = "x"\nb = true\na = [1, 2]\nt = {k = 1}\n'
                  "[h]\n[[aot]]\nx.y = 2\n")
        self.assertIs(type(d), dict)
        self.assertIs(type(d["i"]), int)
        self.assertIs(type(d["f"]), float)
        self.assertIs(type(d["s"]), str)
        self.assertIs(type(d["b"]), bool)
        self.assertIs(type(d["a"]), list)
        self.assertIs(type(d["a"][0]), int)
        self.assertIs(type(d["t"]), dict)
        self.assertIs(type(d["h"]), dict)
        self.assertIs(type(d["aot"]), list)
        self.assertIs(type(d["aot"][0]), dict)
        self.assertIs(type(d["aot"][0]["x"]), dict)
        self.assertIs(type(d["aot"][0]["x"]["y"]), int)

    def test_integer_never_float(self):
        for doc in ("i = 0", "i = 0x10", "i = 0o10", "i = 0b10", "i = 1_000", "i = -5",
                    "i = 123456789012345678901234567890"):
            with self.subTest(doc=doc):
                v = loads(doc)["i"]
                self.assertIs(type(v), int)
        self.assertEqual(loads("i = 123456789012345678901234567890")["i"],
                         123456789012345678901234567890)


class Req21_ErrorLineNumbers(TomlCase):
    """Any problem raises `cfgkit.ParseError` whose `.line` is the 1-based line on which the
    statement containing the problem STARTS (key line or the `[` of the header, counting
    `\\r\\n` as one newline), also for errors inside a multi-line string, array or on a later
    line of the same statement."""

    def line_of(self, text):
        return self.bad(text).line

    def test_is_parse_error_class(self):
        from cfgkit import ParseError, ConfigError
        exc = self.bad("a = ")
        self.assertIsInstance(exc, ParseError)
        self.assertIsInstance(exc, ConfigError)

    def test_simple_lines(self):
        self.assertEqual(self.line_of("a = 1\nb = 2\na = 3\n"), 3)
        self.assertEqual(self.line_of("a = 1\n\n\nb = @\n"), 4)
        self.assertEqual(self.line_of("[a]\nx = 1\n[a]\n"), 3)
        self.assertEqual(self.line_of("x = 1\n\n[tab\n"), 3)
        self.assertEqual(self.line_of("x = 1\n# c\nd = 1979-05-27\n"), 3)
        self.assertEqual(self.line_of("oops"), 1)
        self.assertEqual(self.line_of("x = 1\ny = 2\nz = 3 # \x01\n"), 3)
        self.assertEqual(self.line_of("x = 1\nfruits = []\n\n[[fruits]]\n"), 4)

    def test_crlf_lines(self):
        self.assertEqual(self.line_of("a = 1\r\nb = 2\r\nb = 3\r\n"), 3)
        self.assertEqual(self.line_of('a = 1\r\ns = """\r\nx\r\n"""\r\ns = 2\r\n'), 5)
        self.assertEqual(self.line_of("a = 1\nb = 'x\ry'\n"), 2)

    def test_multiline_string_errors(self):
        self.assertEqual(self.line_of('x = 1\ns = """\nok\n\\q\n"""\n'), 2)
        self.assertEqual(self.line_of('x = 1\ns = """\nok\nbad\x00\n"""\n'), 2)
        self.assertEqual(self.line_of("x = 1\ns = '''\nok\nbad\x01\n'''\n"), 2)
        self.assertEqual(self.line_of('x = 1\ns = """abc\n\n\n'), 2)
        self.assertEqual(self.line_of('x = 1\ns = """\na\n""" junk\n'), 2)

    def test_multiline_array_errors(self):
        self.assertEqual(self.line_of("a = 1\nb = [\n  1,\n  2\n  3\n]\n"), 2)
        self.assertEqual(self.line_of("a = 1\nb = [\n  1,\n  2,,\n]\n"), 2)
        self.assertEqual(self.line_of("a = 1\nb = [\n  1,\n  # \x7f\n]\n"), 2)
        self.assertEqual(self.line_of("a = 1\nb = [\n  1,\n  {x = 1,}\n]\n"), 2)
        self.assertEqual(self.line_of("a = 1\nb = [\n  1,\n  1979-05-27,\n]\n"), 2)
        self.assertEqual(self.line_of("a = 1\nb = [\n  1,\n  2\n"), 2)

    def test_counter_after_multiline_values(self):
        self.assertEqual(self.line_of('s = """\na\nb\n"""\ns = 1\n'), 5)
        self.assertEqual(self.line_of("s = '''\na\nb\n'''\nt = 2\nt = 3\n"), 6)
        self.assertEqual(self.line_of("a = [\n1,\n2,\n]\nb = {x = 1}\n[b]\n"), 6)
        self.assertEqual(self.line_of('s = """a\\\n\n   b"""\n\nk = 1\nk = 2\n'), 6)

    def test_inline_table_on_later_line(self):
        self.assertEqual(self.line_of("a = 1\nb = [\n  {x = 1\n  }\n]\n"), 2)


class Req22_NonStrInput(TomlCase):
    """Parsing a non-`str` raises `ParseError`."""

    def test_non_str(self):
        ParseError = _parse_error()
        for value in (b"a = 1", bytearray(b"a = 1"), None, 1, ["a = 1"], {"a": 1}):
            with self.subTest(value=value):
                with self.assertRaises(ParseError):
                    loads(value)


class Req23_Performance(TomlCase):
    """The parser must be linear-time enough to read a document of 60,000 lines (and keep a
    line counter that is not quadratic) within a few seconds."""

    LIMIT = 10.0

    def timed(self, func):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, self.LIMIT, "took %.2fs" % elapsed)
        return result

    def test_many_key_values(self):
        lines = []
        expected = {}
        for t in range(600):
            lines.append("[section%d]" % t)
            sec = expected["section%d" % t] = {}
            for k in range(99):
                lines.append('key%d = "value %d" # comment' % (k, k))
                sec["key%d" % k] = "value %d" % k
        self.assertEqual(len(lines), 60000)
        doc = "\n".join(lines) + "\n"
        result = self.timed(lambda: loads(doc))
        self.assertEqual(result, expected)

    def test_error_at_line_60000(self):
        lines = ["k%d = %d" % (i, i) for i in range(59999)]
        lines.append("k0 = 1")
        doc = "\n".join(lines) + "\n"
        ParseError = _parse_error()

        def run():
            with self.assertRaises(ParseError) as cm:
                loads(doc)
            return cm.exception

        exc = self.timed(run)
        self.assertEqual(exc.line, 60000)

    def test_long_multiline_array_and_string(self):
        doc = "a = [\n" + "".join("  %d,\n" % i for i in range(29998)) + "]\n"
        doc += 's = """\n' + "line\n" * 29997 + '"""\n'
        doc += "a = 1\n"
        self.assertEqual(doc.count("\n"), 60000)
        ParseError = _parse_error()

        def run():
            with self.assertRaises(ParseError) as cm:
                loads(doc)
            return cm.exception

        exc = self.timed(run)
        self.assertEqual(exc.line, 60000)
        good = doc[: -len("a = 1\n")]
        result = self.timed(lambda: loads(good))
        self.assertEqual(result["a"], list(range(29998)))
        self.assertEqual(result["s"], "line\n" * 29997)

    def test_many_array_of_tables(self):
        doc = "".join("[[item]]\nid = %d\n" % i for i in range(30000))
        result = self.timed(lambda: loads(doc))
        self.assertEqual(len(result["item"]), 30000)
        self.assertEqual(result["item"][-1], {"id": 29999})


class Req24_LoadText(unittest.TestCase):
    """`load_text(text, "toml")` parses TOML."""

    def test_load_text(self):
        from cfgkit import load_text
        self.assertEqual(load_text('[server]\nport = 8080\nhosts = ["a", "b"]\n', "toml"),
                         {"server": {"port": 8080, "hosts": ["a", "b"]}})

    def test_load_text_error(self):
        from cfgkit import load_text, ParseError
        with self.assertRaises(ParseError) as cm:
            load_text("a = 1\na = 2\n", "toml")
        self.assertEqual(cm.exception.line, 2)
        with self.assertRaises(ParseError):
            load_text("d = 1979-05-27", "toml")


class Req25_LoadFile(unittest.TestCase):
    """`load_file` for the suffix `.toml` (case-insensitive, UTF-8, like the existing
    formats, so `load_layers` can mix ini/json/toml files)."""

    def test_load_file(self):
        from cfgkit import Config, load_file
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "conf.toml"
            p.write_bytes('[app]\nname = "café ✓"\nport = 1\n'.encode("utf-8"))
            c = load_file(p)
            self.assertIsInstance(c, Config)
            self.assertEqual(c.as_dict(), {"app": {"name": "café ✓", "port": 1}})
            self.assertEqual(c.get("app.name"), "café ✓")
            self.assertEqual(load_file(str(p)).get("app.port"), 1)

    def test_suffix_case_insensitive(self):
        from cfgkit import load_file
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.TOML", "b.Toml"):
                p = Path(d) / name
                p.write_text("x = 1\n", encoding="utf-8")
                self.assertEqual(load_file(p).as_dict(), {"x": 1})

    def test_load_file_error(self):
        from cfgkit import load_file, ParseError
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.toml"
            p.write_text("a = 1\n[t]\nx = \n", encoding="utf-8")
            with self.assertRaises(ParseError) as cm:
                load_file(p)
            self.assertEqual(cm.exception.line, 3)

    def test_crlf_file(self):
        from cfgkit import load_file
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "crlf.toml"
            p.write_bytes(b'a = 1\r\ns = """\r\nx\r\n"""\r\n')
            self.assertEqual(load_file(p).as_dict(), {"a": 1, "s": "x\n"})

    def test_load_layers_mix(self):
        from cfgkit import load_layers
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.ini").write_text("[s]\nk = 1\nm = ini\n", encoding="utf-8")
            (Path(d) / "b.json").write_text('{"s": {"j": 2}}', encoding="utf-8")
            (Path(d) / "c.toml").write_text('[s]\nm = "toml"\nt = [1, 2]\n[other]\nx = 1.5\n',
                                            encoding="utf-8")
            c = load_layers([Path(d) / "a.ini", Path(d) / "b.json", Path(d) / "c.toml"])
            self.assertEqual(c.as_dict(), {"s": {"k": "1", "m": "toml", "j": 2, "t": [1, 2]},
                                           "other": {"x": 1.5}})
            c2 = load_layers([Path(d) / "c.toml", Path(d) / "a.ini"])
            self.assertEqual(c2.get("s.m"), "ini")
            self.assertEqual(c2.get("s.t"), [1, 2])


class Req26_ConfigFromToml(unittest.TestCase):
    """`Config.from_toml(text)`."""

    def test_from_toml(self):
        from cfgkit import Config
        c = Config.from_toml('[server]\nport = 8080\n[[servers]]\nhost = "a"\n')
        self.assertIsInstance(c, Config)
        self.assertEqual(c.as_dict(), {"server": {"port": 8080}, "servers": [{"host": "a"}]})
        self.assertEqual(c.get("server.port"), 8080)

    def test_from_toml_error(self):
        from cfgkit import Config, ParseError
        with self.assertRaises(ParseError) as cm:
            Config.from_toml("a = 1\nb = [\n1,,\n]\n")
        self.assertEqual(cm.exception.line, 2)


class Req27_LoadsTomlExported(unittest.TestCase):
    """`cfgkit.loads_toml` exported from the package."""

    def test_loads_toml(self):
        import cfgkit
        self.assertTrue(callable(cfgkit.loads_toml))
        self.assertEqual(cfgkit.loads_toml("a.b = 1\n[c]\nd = 'x'\n"),
                         {"a": {"b": 1}, "c": {"d": "x"}})
        from cfgkit import loads_toml  # noqa: F401
        with self.assertRaises(cfgkit.ParseError):
            cfgkit.loads_toml("a = 1\na = 2")


class Req28_ConfigGetWalksLists(unittest.TestCase):
    """`Config.get(path, default)` also walks lists: a path component made only of decimal
    digits indexes a list (`"servers.1.host"`); an out-of-range index or a non-numeric
    component on a list counts as missing (default / `KeyError`)."""

    def make(self):
        from cfgkit import Config
        return Config({"servers": [{"host": "a", "ports": [80, 443]}, {"host": "b"}],
                       "matrix": [[1, 2], [3, 4]],
                       "d": {"1": "one"},
                       "empty": []})

    def test_indexing(self):
        c = self.make()
        self.assertEqual(c.get("servers.1.host"), "b")
        self.assertEqual(c.get("servers.0.host"), "a")
        self.assertEqual(c.get("servers.0.ports.1"), 443)
        self.assertEqual(c.get("servers.0"), {"host": "a", "ports": [80, 443]})
        self.assertEqual(c.get("matrix.1.0"), 3)
        self.assertEqual(c.get("servers.1.host", "zz"), "b")

    def test_out_of_range(self):
        c = self.make()
        self.assertEqual(c.get("servers.2.host", "dflt"), "dflt")
        self.assertEqual(c.get("servers.2", None), None)
        self.assertEqual(c.get("empty.0", 5), 5)
        self.assertEqual(c.get("servers.0.ports.2", 0), 0)
        self.assertEqual(c.get("servers.99999999999999999999", 1), 1)
        with self.assertRaises(KeyError):
            c.get("servers.2.host")
        with self.assertRaises(KeyError):
            c.get("empty.0")

    def test_non_numeric_on_list(self):
        c = self.make()
        self.assertEqual(c.get("servers.host", "x"), "x")
        self.assertEqual(c.get("servers.-1", "x"), "x")
        self.assertEqual(c.get("servers.-1.host", "x"), "x")
        self.assertEqual(c.get("servers.+1", "x"), "x")
        self.assertEqual(c.get("servers.1.5", "x"), "x")
        self.assertEqual(c.get("servers.", "x"), "x")
        with self.assertRaises(KeyError):
            c.get("servers.host")
        with self.assertRaises(KeyError):
            c.get("servers.-1")

    def test_digit_keys_on_dicts_unchanged(self):
        c = self.make()
        self.assertEqual(c.get("d.1"), "one")
        self.assertEqual(c.get("d.0", "none"), "none")

    def test_with_toml(self):
        from cfgkit import Config
        c = Config.from_toml('[[servers]]\nhost = "alpha"\n[[servers]]\nhost = "beta"\n')
        self.assertEqual(c.get("servers.1.host"), "beta")
        self.assertEqual(c.get("servers.2.host", "none"), "none")


class Req29_ConfigContainsWalksLists(unittest.TestCase):
    """`Config.__contains__` follows the same list-walking rule as `get`."""

    def test_contains(self):
        from cfgkit import Config
        c = Config({"servers": [{"host": "a"}, {"host": "b"}], "x": {"y": [1]}})
        self.assertIn("servers.0", c)
        self.assertIn("servers.1.host", c)
        self.assertIn("x.y.0", c)
        self.assertNotIn("servers.2", c)
        self.assertNotIn("servers.2.host", c)
        self.assertNotIn("servers.host", c)
        self.assertNotIn("servers.-1", c)
        self.assertNotIn("x.y.1", c)
        self.assertNotIn("servers.0.port", c)


class Req30_ExistingBehaviourUnchanged(unittest.TestCase):
    """Existing INI/JSON/Config behaviour is unchanged."""

    def test_ini(self):
        from cfgkit import parse_ini, load_text, ParseError
        self.assertEqual(parse_ini("top = 1\n[a]\nx = y # not a comment\n; c\n[b]\nk=v"),
                         {"top": "1", "a": {"x": "y # not a comment"}, "b": {"k": "v"}})
        self.assertEqual(load_text("[s]\nk = 1\n", "ini"), {"s": {"k": "1"}})
        with self.assertRaises(ParseError) as cm:
            parse_ini("[a]\nx = 1\noops\n")
        self.assertEqual(cm.exception.line, 3)

    def test_json(self):
        from cfgkit import load_text, ParseError, ConfigError
        self.assertEqual(load_text('{"a": {"b": 1}}', "json"), {"a": {"b": 1}})
        with self.assertRaises(ParseError):
            load_text("[1, 2]", "json")
        with self.assertRaises(ParseError):
            load_text("{bad", "json")
        with self.assertRaises(ConfigError):
            load_text("x", "yaml")

    def test_config(self):
        from cfgkit import Config, ConfigError
        c = Config({"a": {"b": 1, "c": {"d": 2}}, "x": 1})
        self.assertEqual(c.get("a.c.d"), 2)
        self.assertEqual(c.get("a.zz", 7), 7)
        self.assertIn("a.b", c)
        self.assertNotIn("a.b.c", c)
        self.assertNotIn("x.0", c)
        with self.assertRaises(KeyError):
            c.get("nope")
        m = c.merge(Config({"a": {"c": {"e": 3}}, "x": [1]}))
        self.assertEqual(m.as_dict(), {"a": {"b": 1, "c": {"d": 2, "e": 3}}, "x": [1]})
        with self.assertRaises(ConfigError):
            c.section("x")
        self.assertEqual(c.section("a").get("c.d"), 2)

    def test_files(self):
        from cfgkit import load_file, load_layers
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.ini").write_text("[s]\nk = 1\n", encoding="utf-8")
            (Path(d) / "b.JSON").write_text('{"s": {"j": "é"}}', encoding="utf-8")
            c = load_layers([Path(d) / "a.ini", Path(d) / "b.JSON"])
            self.assertEqual(c.as_dict(), {"s": {"k": "1", "j": "é"}})
            self.assertEqual(load_file(Path(d) / "a.ini").get("s.k"), "1")


if __name__ == "__main__":
    unittest.main()
