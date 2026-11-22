"""Acceptance tests for TOML support in cfgkit.

Expected values follow TOML v1.0.0 (as implemented by Python 3.11's ``tomllib``),
except that date/time values must raise ``ParseError``.
"""
import importlib
import math
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

import cfgkit
from cfgkit import Config, ConfigError, ParseError, load_file, load_layers, load_text, parse_ini

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "cfgkit"


def _loads(text):
    return importlib.import_module("cfgkit.toml").loads(text)


class TomlCase(unittest.TestCase):
    def ok(self, text, expected):
        self.assertEqual(_loads(text), expected, msg=repr(text))

    def bad(self, text):
        with self.assertRaises(ParseError, msg=repr(text)):
            _loads(text)

    def bad_line(self, text, line):
        with self.assertRaises(ParseError, msg=repr(text)) as cm:
            _loads(text)
        self.assertEqual(cm.exception.line, line, msg=repr(text))


class Req01_NoTomlLibrary(unittest.TestCase):
    """The parser is written by hand: do not import (or shell out to) `tomllib`, `tomli`,
    `toml`, `tomlkit` or any other TOML library, in any module of the package."""

    FORBIDDEN = ("tomllib", "tomli", "tomli_w", "toml", "tomlkit", "pytoml", "rtoml", "qtoml")

    def test_module_exists(self):
        self.assertTrue((PACKAGE_DIR / "toml.py").is_file())

    def test_no_imports_of_toml_libraries_in_source(self):
        names = "|".join(self.FORBIDDEN)
        pat = re.compile(r"^\s*(?:import\s+(?:%s)\b|from\s+(?:%s)\b\s+import)" % (names, names), re.M)
        for path in PACKAGE_DIR.rglob("*.py"):
            src = path.read_text(encoding="utf-8")
            self.assertIsNone(pat.search(src), "%s imports a TOML library" % path)
            self.assertNotIn("subprocess", src, "%s uses subprocess" % path)
            self.assertNotRegex(src, r"__import__|import_module", "%s imports dynamically" % path)

    def test_works_with_toml_libraries_blocked(self):
        code = textwrap.dedent("""
            import sys
            for name in %r:
                sys.modules[name] = None
            import cfgkit, cfgkit.toml
            assert cfgkit.toml.loads('a = 1\\n[t]\\nb = "x"\\n') == {"a": 1, "t": {"b": "x"}}
            assert cfgkit.loads_toml('a = 2') == {"a": 2}
            for name in %r:
                assert sys.modules.get(name) is None, name
            print("OK")
        """ % (self.FORBIDDEN, self.FORBIDDEN))
        res = subprocess.run([sys.executable, "-c", code], cwd=str(REPO_ROOT),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("OK", res.stdout)


class Req02_CommentsAndKeys(TomlCase):
    """`loads(text) -> dict`: comments, bare/quoted/dotted keys (whitespace allowed around the dots)."""

    def test_empty_and_comment_only(self):
        self.ok("", {})
        self.ok("# just a comment\n\n   # another\n", {})
        self.ok("\n\n\n", {})

    def test_comments(self):
        self.ok("# c\na = 1 # trailing comment\nb = 2#x\n", {"a": 1, "b": 2})
        self.ok('s = "# not a comment" # comment\n', {"s": "# not a comment"})
        self.ok("# comment with unicode é ✓ and \"quotes\" and 'x'\na = true", {"a": True})

    def test_bare_keys(self):
        self.ok("key = 1\nbare_key = 2\nbare-key = 3\n1234 = 4\nABC_x-9 = 5",
                {"key": 1, "bare_key": 2, "bare-key": 3, "1234": 4, "ABC_x-9": 5})

    def test_quoted_keys(self):
        self.ok('"127.0.0.1" = "v"\n"character encoding" = 1\n\'key2\' = 2\n'
                '\'quoted "value"\' = 3\n"ʎǝʞ" = 4\n"a\\tb" = 5',
                {"127.0.0.1": "v", "character encoding": 1, "key2": 2,
                 'quoted "value"': 3, "ʎǝʞ": 4, "a\tb": 5})

    def test_empty_quoted_key(self):
        self.ok('"" = "blank"', {"": "blank"})
        self.ok("'' = 'blank'", {"": "blank"})

    def test_dotted_keys(self):
        self.ok('name = "Orange"\nphysical.color = "orange"\nphysical.shape = "round"\n'
                'site."google.com" = true',
                {"name": "Orange", "physical": {"color": "orange", "shape": "round"},
                 "site": {"google.com": True}})

    def test_whitespace_around_dots(self):
        self.ok('fruit.name = "banana"\nfruit. color = "yellow"\nfruit . flavor = "banana"\n'
                'a \t.\t b . "c" = 1',
                {"fruit": {"name": "banana", "color": "yellow", "flavor": "banana"},
                 "a": {"b": {"c": 1}}})

    def test_numeric_looking_dotted_key(self):
        self.ok("3.14159 = 'pi'", {"3": {"14159": "pi"}})

    def test_whitespace_around_equals(self):
        self.ok("a=1\n  b   =\t2  \n\tc = 3", {"a": 1, "b": 2, "c": 3})

    def test_bad_keys(self):
        for text in ("= 1", "a", "a =", "a = # x", "a b = 1", "a. = 1", ".a = 1", "a..b = 1",
                     "a = 1 b = 2", "a = 1 2", "k@y = 1", '"a\nb" = 1', "a = 1\n = 2",
                     '"""a""" = 1', "a\n= 1", "a =\n1"):
            self.bad(text)


class Req03_Strings(TomlCase):
    """Basic, literal, multi-line basic and multi-line literal strings with all escape rules
    (`\\b \\t \\n \\f \\r \\" \\\\ \\uXXXX \\UXXXXXXXX`, line-ending backslash trimming, the first
    newline after the opening delimiter trimmed, up to two quotes next to the closing delimiter,
    unicode escapes must be scalar values)."""

    def test_basic(self):
        self.ok('s = "I\'m a string. \\"You can quote me\\". Name\\tJos\\u00E9\\nLocation\\tSF."',
                {"s": "I'm a string. \"You can quote me\". Name\tJos\u00e9\nLocation\tSF."})
        self.ok('s = ""', {"s": ""})
        self.ok('s = "tab\there"', {"s": "tab\there"})
        self.ok('s = "é ✓ 😀"', {"s": "é ✓ 😀"})

    def test_all_escapes(self):
        self.ok(r's = "\b\t\n\f\r\"\\"', {"s": "\b\t\n\f\r\"\\"})
        self.ok(r's = "\u00e9\u00E9\U0001F600\U0000004A\u0000"', {"s": "éé😀J\x00"})
        self.ok(r's = "\uD7FF\uE000\U0010FFFF"', {"s": "\ud7ff\ue000\U0010ffff"})

    def test_invalid_escapes(self):
        for esc in (r"\a", r"\e", r"\x41", r"\ ", r"\0", r"\'", r"\/", r"\N", r"\u12", r"\u12G4",
                    r"\U0001F60", r"\UFFFFFFFF", "\\"):
            self.bad('s = "%s"' % esc)

    def test_unicode_escape_must_be_scalar(self):
        for esc in (r"\uD800", r"\uDFFF", r"\uDBFF", r"\U0000D800", r"\U00110000"):
            self.bad('s = "%s"' % esc)
            self.bad('s = """%s"""' % esc)

    def test_basic_string_errors(self):
        for text in ('s = "abc', 's = "abc\n"', 's = "a"b"', "s = 'abc", "s = 'ab'c'",
                     "s = 'a\nb'", 's = abc', 's = "a" "b"'):
            self.bad(text)

    def test_literal(self):
        self.ok(r"winpath = 'C:\Users\nodejs\templates'", {"winpath": r"C:\Users\nodejs\templates"})
        self.ok(r"""quoted = 'Tom "Dubs" Preston-Werner'""", {"quoted": 'Tom "Dubs" Preston-Werner'})
        self.ok(r"regex = '<\i\c*\s*>'", {"regex": r"<\i\c*\s*>"})
        self.ok("s = ''", {"s": ""})
        self.ok("s = '\tx\t'", {"s": "\tx\t"})

    def test_multiline_basic(self):
        self.ok('s = """\nRoses are red\nViolets are blue"""', {"s": "Roses are red\nViolets are blue"})
        self.ok('s = """Roses"""', {"s": "Roses"})
        self.ok('s = """\n\nx"""', {"s": "\nx"})
        self.ok('s = """"""', {"s": ""})
        self.ok('s = """a\\tb\\u00e9"""', {"s": "a\tbé"})
        self.ok('s = """ a "quoted" b ""quoted"" """', {"s": ' a "quoted" b ""quoted"" '})
        self.ok('s = """\\""""""', {"s": '"""'})

    def test_line_ending_backslash(self):
        self.ok('s = """\nThe quick brown \\\n\n\n  fox jumps over \\\n    the lazy dog."""',
                {"s": "The quick brown fox jumps over the lazy dog."})
        self.ok('s = """\\\n       The quick brown \\\n       fox jumps over \\\n       the lazy dog.\\\n       """',
                {"s": "The quick brown fox jumps over the lazy dog."})
        self.ok('s = """one \\  \t \n   two"""', {"s": "one two"})
        self.ok('s = """a\\\\\nb"""', {"s": "a\\\nb"})
        self.bad('s = """a\\ b"""')

    def test_quotes_next_to_closing_delimiter(self):
        self.ok('s = """x""""', {"s": 'x"'})
        self.ok('s = """x"""""', {"s": 'x""'})
        self.ok('s = """""x"""', {"s": '""x'})
        self.ok('s = """"This," she said, "is just a pointless statement.""""',
                {"s": '"This," she said, "is just a pointless statement."'})
        self.bad('s = """x""""""')
        self.bad('s = """a"""b"""')
        self.ok("s = '''x''''", {"s": "x'"})
        self.ok("s = '''x'''''", {"s": "x''"})
        self.ok("s = ''''That,' she said, 'is still pointless.''''",
                {"s": "'That,' she said, 'is still pointless.'"})
        self.bad("s = '''x''''''")

    def test_multiline_literal(self):
        self.ok("regex2 = '''I [dw]on't need \\d{2} apples'''", {"regex2": "I [dw]on't need \\d{2} apples"})
        self.ok("lines = '''\nThe first newline is\ntrimmed in raw strings.\n   All other whitespace\n   is preserved.\n'''",
                {"lines": "The first newline is\ntrimmed in raw strings.\n   All other whitespace\n   is preserved.\n"})
        self.ok("s = '''a\\\nb\\n'''", {"s": "a\\\nb\\n"})
        self.ok("s = ''''''", {"s": ""})
        self.ok("s = '''x '' y'''", {"s": "x '' y"})

    def test_unterminated_multiline(self):
        for text in ('s = """abc', 's = """abc\n\n', "s = '''abc\n", 's = """abc""', "s = '''x''"):
            self.bad(text)


class Req04_Integers(TomlCase):
    """Integers: decimal with underscores, no leading zeros, `0x`/`0o`/`0b`."""

    def test_decimal(self):
        self.ok("a = +99\nb = 42\nc = 0\nd = -17\ne = -0\nf = +0",
                {"a": 99, "b": 42, "c": 0, "d": -17, "e": 0, "f": 0})
        self.ok("a = 1_000\nb = 5_349_221\nc = 53_49_221\nd = 1_2_3_4_5",
                {"a": 1000, "b": 5349221, "c": 5349221, "d": 12345})
        self.ok("a = 9223372036854775807\nb = -9223372036854775808",
                {"a": 9223372036854775807, "b": -9223372036854775808})

    def test_prefixed(self):
        self.ok("a = 0xDEADBEEF\nb = 0xdeadbeef\nc = 0xdead_beef\nd = 0x00\ne = 0x0001",
                {"a": 0xDEADBEEF, "b": 0xDEADBEEF, "c": 0xDEADBEEF, "d": 0, "e": 1})
        self.ok("a = 0o01234567\nb = 0o755\nc = 0o7_7", {"a": 0o1234567, "b": 0o755, "c": 0o77})
        self.ok("a = 0b11010110\nb = 0b1_0\nc = 0b0", {"a": 0b11010110, "b": 2, "c": 0})

    def test_invalid(self):
        for v in ("01", "00", "-01", "+01", "007", "1__000", "_1", "1_", "-_1", "+_1", "1_000_",
                  "0x", "0o", "0b", "0X1F", "0O7", "0B1", "+0x1", "-0x1", "+0o7", "-0b1",
                  "0xG", "0o8", "0b2", "0x_1", "0x1_", "0x1__2", "1 000", "--1", "++1", "+",
                  "-", "1a", "0x1.0", "1,000"):
            self.bad("a = " + v)


class Req05_Floats(TomlCase):
    """Floats: fraction/exponent/underscores, `inf`, `nan` with optional sign."""

    def test_floats(self):
        self.ok("a = +1.0\nb = 3.1415\nc = -0.01\nd = 5e+22\ne = 1e06\nf = -2E-2\ng = 6.626e-34\n"
                "h = 224_617.445_991_228\ni = 0.0\nj = 1e1_0\nk = 0e0\nl = 1.5E3\nm = 0.1",
                {"a": 1.0, "b": 3.1415, "c": -0.01, "d": 5e22, "e": 1e6, "f": -2e-2, "g": 6.626e-34,
                 "h": 224617.445991228, "i": 0.0, "j": 1e10, "k": 0.0, "l": 1500.0, "m": 0.1})

    def test_signed_zero(self):
        d = _loads("a = -0.0\nb = +0.0")
        self.assertEqual(math.copysign(1, d["a"]), -1.0)
        self.assertEqual(math.copysign(1, d["b"]), 1.0)

    def test_inf_nan(self):
        d = _loads("a = inf\nb = +inf\nc = -inf\nd = nan\ne = +nan\nf = -nan")
        self.assertEqual(d["a"], float("inf"))
        self.assertEqual(d["b"], float("inf"))
        self.assertEqual(d["c"], float("-inf"))
        for k in "def":
            self.assertIsInstance(d[k], float)
            self.assertTrue(math.isnan(d[k]))

    def test_invalid(self):
        for v in (".7", "7.", "3.e+20", "+.1", "1._0", "1_.0", "1.0_", "1e", "1e+", "1e_1",
                  "1e1_", "1.e1", "Inf", "NaN", "INF", "infinity", "nan1", "-+1.0", "1.0.0",
                  "01.5", "00.0", "-01.0", "1e2.0", "1.2e", "0x1.0p3", "1__0.0", "._1", "e1"):
            self.bad("a = " + v)


class Req06_Booleans(TomlCase):
    """Booleans."""

    def test_booleans(self):
        d = _loads("t = true\nf = false")
        self.assertIs(d["t"], True)
        self.assertIs(d["f"], False)

    def test_invalid(self):
        for v in ("True", "FALSE", "tru", "truee", "yes", "on"):
            self.bad("a = " + v)


class Req07_Arrays(TomlCase):
    """Arrays (any mix of types, newlines, comments and a trailing comma allowed)."""

    def test_arrays(self):
        self.ok("a = [ 1, 2, 3 ]\nb = []\nc = [ \"red\", 'yellow' ]\nd = [[1, 2], [3]]",
                {"a": [1, 2, 3], "b": [], "c": ["red", "yellow"], "d": [[1, 2], [3]]})

    def test_mixed_types(self):
        self.ok('a = [ 0.1, 0.2, 1, "s", true, [], { x = 1 }, [ "a" ] ]',
                {"a": [0.1, 0.2, 1, "s", True, [], {"x": 1}, ["a"]]})
        self.ok('contributors = [\n  "Foo Bar <foo@example.com>",\n  { name = "Baz Qux", email = "bazqux@example.com", url = "https://example.com/bazqux" }\n]',
                {"contributors": ["Foo Bar <foo@example.com>",
                                  {"name": "Baz Qux", "email": "bazqux@example.com",
                                   "url": "https://example.com/bazqux"}]})

    def test_newlines_comments_trailing_comma(self):
        self.ok("a = [\n  1,\n  2, # comment\n  # another\n  3,\n]\nb = [\n]\nc = [1,]\nd = [ # c\n # c\n]",
                {"a": [1, 2, 3], "b": [], "c": [1], "d": []})
        self.ok('a = [\n"""x\ny""", \'\'\'z\'\'\'\n\n,\n\n4\n\n]', {"a": ["x\ny", "z", 4]})

    def test_invalid(self):
        for text in ("a = [", "a = [1", "a = [1,", "a = [,]", "a = [1,,2]", "a = [,1]", "a = [1 2]",
                     "a = [1]]", "a = [1\n2]", "a = [1,\n", "a = ]", "a = [a]", "a = [1, # ]"):
            self.bad(text)


class Req08_InlineTables(TomlCase):
    """Inline tables (one line, no trailing comma)."""

    def test_inline_tables(self):
        self.ok('name = { first = "Tom", last = "Preston-Werner" }\npoint = { x = 1, y = 2 }\n'
                'animal = { type.name = "pug" }\ne = {}\nn = { a = { b = [1, { c = 2 }] } }',
                {"name": {"first": "Tom", "last": "Preston-Werner"}, "point": {"x": 1, "y": 2},
                 "animal": {"type": {"name": "pug"}}, "e": {},
                 "n": {"a": {"b": [1, {"c": 2}]}}})
        self.ok("a = {b.c = 1, b.d = 2,  \"q k\" = 3}", {"a": {"b": {"c": 1, "d": 2}, "q k": 3}})

    def test_invalid(self):
        for text in ("a = {x = 1,}", "a = {,}", "a = {x = 1\n}", "a = {\nx = 1}", "a = {x = 1,\ny = 2}",
                     "a = {x = 1, x = 2}", "a = {x}", "a = {x = 1", "a = {x = 1 y = 2}",
                     "a = {x = 1,, y = 2}", "a = {x = 1} b = 1", "a = {b = {}, b.c = 1}",
                     "a = {b.c = 1, b = 2}", "a = {b.c = 1, b.c.d = 2}", "a = {x = 1 # c\n}",
                     "a = {b = 1, b.c = 2}"):
            self.bad(text)


class Req09_TableHeaders(TomlCase):
    """`[table]` and `[[array of tables]]` headers."""

    def test_tables(self):
        self.ok('[table-1]\nkey1 = "some string"\nkey2 = 123\n\n[table-2]\nkey1 = "another string"\nkey2 = 456',
                {"table-1": {"key1": "some string", "key2": 123},
                 "table-2": {"key1": "another string", "key2": 456}})
        self.ok("[a.b.c]\n[ d.e.f ]\n[ g .  h  . i ]\n[ j . \"ʞ\" . 'l' ]\n['x.y']\n[\"\"]",
                {"a": {"b": {"c": {}}}, "d": {"e": {"f": {}}}, "g": {"h": {"i": {}}},
                 "j": {"ʞ": {"l": {}}}, "x.y": {}, "": {}})
        self.ok("top = 1\n[t] # comment\nk = 2\n  [t.u]\n  k = 3", {"top": 1, "t": {"k": 2, "u": {"k": 3}}})

    def test_implicit_then_explicit(self):
        self.ok("[x.y.z.w]\na = 1\n[x]\nb = 2", {"x": {"b": 2, "y": {"z": {"w": {"a": 1}}}}})
        self.ok("[a.b.c]\nx = 1\n[a.b]\ny = 2", {"a": {"b": {"y": 2, "c": {"x": 1}}}})
        self.ok('[fruit]\napple.color = "red"\napple.taste.sweet = true\n[fruit.apple.texture]\nsmooth = true',
                {"fruit": {"apple": {"color": "red", "taste": {"sweet": True}, "texture": {"smooth": True}}}})

    def test_array_of_tables(self):
        self.ok('[[products]]\nname = "Hammer"\nsku = 738594937\n\n[[products]]  # empty\n\n'
                '[[products]]\nname = "Nail"\nsku = 284758393\ncolor = "gray"',
                {"products": [{"name": "Hammer", "sku": 738594937}, {},
                              {"name": "Nail", "sku": 284758393, "color": "gray"}]})
        self.ok('[[fruits]]\nname = "apple"\n[fruits.physical]\ncolor = "red"\nshape = "round"\n'
                '[[fruits.varieties]]\nname = "red delicious"\n[[fruits.varieties]]\nname = "granny smith"\n'
                '[[fruits]]\nname = "banana"\n[[fruits.varieties]]\nname = "plantain"',
                {"fruits": [{"name": "apple", "physical": {"color": "red", "shape": "round"},
                             "varieties": [{"name": "red delicious"}, {"name": "granny smith"}]},
                            {"name": "banana", "varieties": [{"name": "plantain"}]}]})
        self.ok("[[ a . b ]]\nx = 1\n[[a.b]]\nx = 2", {"a": {"b": [{"x": 1}, {"x": 2}]}})
        self.ok("[a]\n[[a.b]]\n[[a.b]]", {"a": {"b": [{}, {}]}})

    def test_invalid_headers(self):
        for text in ("[]", "[a", "a]", "[a.]", "[.a]", "[a..b]", "[[]]", "[[a]", "[a]]", "[[a] ]",
                     "[ [a]]", "[a] b = 1", "[a] [b]", "[a b]", "[a]\n[a]", "[\na]", "[a\n]",
                     "[[a]] x", "[a = 1]", "[\"a]", "[a.\"b]"):
            self.bad(text)


class Req10_DatesUnsupported(TomlCase):
    """Deliberate exception: date, time and date-time values are not supported and raise `ParseError`."""

    def test_dates_raise(self):
        for v in ("1979-05-27T07:32:00Z", "1979-05-27T00:32:00-07:00", "1979-05-27T00:32:00.999999-07:00",
                  "1979-05-27 07:32:00Z", "1979-05-27T07:32:00", "1979-05-27T00:32:00.999999",
                  "1979-05-27", "07:32:00", "00:32:00.999999", "1979-05-27t07:32:00z"):
            self.bad("d = " + v)
            self.bad("a = [1, %s]" % v)
            self.bad("a = [%s]" % v)
            self.bad("t = { d = %s }" % v)

    def test_date_like_strings_are_fine(self):
        self.ok('d = "1979-05-27"', {"d": "1979-05-27"})
        self.ok("1979-05-27 = 1", {"1979-05-27": 1})


class Req11_ControlCharsAndLineEndings(TomlCase):
    """Control characters (other than tab, and newline where allowed) in strings and comments are
    errors; a `\\r\\n` line ending is treated exactly like `\\n` everywhere (also inside multi-line
    strings); a lone `\\r` is an error."""

    CONTROLS = [chr(c) for c in list(range(0, 9)) + list(range(0x0B, 0x0D)) + list(range(0x0E, 0x20)) + [0x7F]]

    def test_control_chars_in_strings(self):
        for ch in self.CONTROLS:
            self.bad('s = "a%sb"' % ch)
            self.bad("s = 'a%sb'" % ch)
            self.bad('s = """a%sb"""' % ch)
            self.bad("s = '''a%sb'''" % ch)

    def test_control_chars_in_comments(self):
        for ch in self.CONTROLS:
            self.bad("# a%sb\n" % ch)
            self.bad("a = 1 # a%sb" % ch)

    def test_tab_allowed(self):
        self.ok("s = \"a\tb\"\nt = 'a\tb'\nu = \"\"\"a\tb\"\"\"\nv = '''a\tb'''\n# tab\there\n",
                {"s": "a\tb", "t": "a\tb", "u": "a\tb", "v": "a\tb"})

    def test_newline_in_single_line_strings(self):
        self.bad('s = "a\nb"')
        self.bad("s = 'a\nb'")
        self.bad('s = "a\r\nb"')

    def test_crlf(self):
        self.ok("# comment\r\na = 1\r\n[t]\r\nb = [\r\n  1,\r\n  2, # c\r\n]\r\n[[arr]]\r\n",
                {"a": 1, "t": {"b": [1, 2]}, "arr": [{}]})
        self.ok('s = """\r\nx\r\ny\r\n"""', {"s": "x\ny\n"})
        self.ok("s = '''\r\nx\r\ny'''", {"s": "x\ny"})
        self.ok('s = """a \\\r\n   b"""', {"s": "a b"})
        self.ok('s = """a\\\r\n\r\n   b"""', {"s": "ab"})

    def test_lone_cr(self):
        for text in ("a = 1\rb = 2", "a = 1\r", "# comment\r", 's = "a\rb"', "s = 'a\rb'",
                     's = """a\rb"""', "s = '''a\rb'''", 's = """\rx"""', "a = [1,\r2]",
                     's = """a \\\r  b"""', "[t]\r", "\r"):
            self.bad(text)


class Req12_DefinitionRules(TomlCase):
    """Every TOML rule about what may be defined where: duplicate keys; redefining a table; tables
    created implicitly; dotted-key tables cannot be reopened with a `[header]` but sub-tables of
    them can be added; inline tables and static arrays are immutable; an `[[array of tables]]`
    header starts a new element and forgets the table flags of the previous element; a header
    cannot turn a value into a table, and so on."""

    def test_duplicate_keys(self):
        for text in ("a = 1\na = 2", 'a = 1\n"a" = 2', "a = 1\n'a' = 1", '"a b" = 1\n\'a b\' = 2',
                     "[t]\nx = 1\nx = 2", "a.b = 1\na.b = 2", "a = {}\na = 1", "a.b = 1\na = 2",
                     "[t]\n[t.u]\nk = 1\n[t]\nu.k = 2"):
            self.bad(text)

    def test_redefining_tables(self):
        for text in ("[a]\n[a]", "[a]\nb = 1\n[a]", "[a.b]\n[a]\n[a]", "[a]\n[a.b]\n[a]",
                     "[a]\nb = 1\n[a]\nc = 2", "[a]\n[\"a\"]", "[a.b]\n[a.b]", "[a.b.c]\n[a.b]\n[a.b]"):
            self.bad(text)

    def test_implicit_tables(self):
        self.ok("[a.b.c]\n[a]\n[a.b]", {"a": {"b": {"c": {}}}})
        self.ok("[a.b]\nc = 1\n[a.d]\ne = 2", {"a": {"b": {"c": 1}, "d": {"e": 2}}})
        self.ok("a.b.c = 1\na.b.d = 2\na.e = 3", {"a": {"b": {"c": 1, "d": 2}, "e": 3}})
        self.ok("[t]\na.b = 1\na.c = 2", {"t": {"a": {"b": 1, "c": 2}}})
        self.ok("[a]\nb.c.d = 1\n[a.b.c.e]\nx = 1", {"a": {"b": {"c": {"d": 1, "e": {"x": 1}}}}})

    def test_dotted_key_tables_cannot_be_reopened(self):
        for text in ("a.b = 1\n[a]", "a.b.c = 1\n[a.b]", "[fruit]\napple.color = 'red'\n[fruit.apple]",
                     "[fruit]\napple.taste.sweet = true\n[fruit.apple.taste]", "a.b = 1\n[[a]]",
                     "[t]\na.b = 1\n[[t.a]]"):
            self.bad(text)

    def test_dotted_key_subtables_can_be_added(self):
        self.ok("a.b = 1\n[a.c]\nx = 2", {"a": {"b": 1, "c": {"x": 2}}})
        self.ok("a.b.c = 1\n[a.b.d]\nx = 1", {"a": {"b": {"c": 1, "d": {"x": 1}}}})

    def test_header_tables_cannot_be_extended_by_dotted_keys(self):
        self.bad("[a.b]\nx = 1\n[a]\nb.y = 2")
        self.bad("[a.b.c]\n[a]\nb.c.z = 1")

    def test_inline_tables_immutable(self):
        for text in ("a = {x = 1}\na.y = 2", "a = {x = 1}\n[a]", "a = {x = 1}\n[a.b]",
                     "a = {x = 1}\n[[a]]", "a = {b = {}}\n[a.b]", "a = {b = {}}\na.b.c = 1",
                     "a = {}\na.b = 1", "a = {}\n[a]", "a = {b.c = 1}\n[a.b.d]",
                     "[t]\na = {}\n[t.a.b]", "a = {x = {y = 1}}\na.x.z = 2",
                     "a = [{b = 1}]\n[a.c]", "a = [{b = 1}]\n[[a]]", "a = [{}]\n[[a.b]]"):
            self.bad(text)

    def test_static_arrays_immutable(self):
        for text in ("a = []\n[[a]]", "a = [1]\n[[a]]", "a = [1]\n[a]", "a = []\na.b = 1",
                     "a = [[]]\n[[a]]", "[t]\na = []\n[[t.a]]", "a = [{}]\n[a]"):
            self.bad(text)

    def test_array_of_tables_conflicts(self):
        for text in ("[[a]]\n[a]", "[a]\n[[a]]", "[a]\nb = 1\n[[a.b]]",
                     "[fruit.physical]\ncolor = 'red'\n[[fruit]]",
                     "[[fruits]]\n[fruits.varieties]\n[[fruits.varieties]]",
                     "[[a]]\nb = 1\n[a.b]", "[[a]]\n[a.b]\n[[a.b]]", "[[a.b]]\n[a]\n[a.b]",
                     "[[a]]\nx = 1\nx = 2"):
            self.bad(text)

    def test_new_element_forgets_flags(self):
        self.ok("[[a]]\n[a.b]\nx = 1\n[[a]]\n[a.b]\nx = 2",
                {"a": [{"b": {"x": 1}}, {"b": {"x": 2}}]})
        self.ok("[[a]]\nb.c = 1\n[[a]]\nb.c = 2", {"a": [{"b": {"c": 1}}, {"b": {"c": 2}}]})
        self.ok("[[a]]\nx = 1\n[[a]]\nx = 2", {"a": [{"x": 1}, {"x": 2}]})
        self.ok("[[a]]\n[[a.b]]\n[a.b.c]\nx = 1\n[[a.b]]\n[a.b.c]\nx = 2",
                {"a": [{"b": [{"c": {"x": 1}}, {"c": {"x": 2}}]}]})
        self.ok("[[a]]\n[a.b.c]\n[[a]]\n[a.b]\n[a.b.c]",
                {"a": [{"b": {"c": {}}}, {"b": {"c": {}}}]})

    def test_header_cannot_turn_value_into_table(self):
        for text in ("a = 1\n[a]", "a = 1\n[a.b]", "a = 'x'\n[[a]]", "a = true\n[[a.b]]",
                     "[a]\nb = 1\n[a.b]", "[a]\nb = 1\n[a.b.c]", "a.b = 1\n[a.b]",
                     "a.b = 1\n[a.b.c]", "a = 1\na.b = 2", "a.b = 1\na.b.c = 2",
                     "[a]\nb = 1\nb.c = 2", "[[a]]\nb = 1\n[a.b.c]"):
            self.bad(text)


class Req13_PlainReturnTypes(unittest.TestCase):
    """Return plain `dict`/`list`/`str`/`int`/`float`/`bool` objects (an integer never becomes a float)."""

    def test_types(self):
        d = _loads('i = 1\nh = 0x10\no = 0o7\nb = 0b1\nf = 1.0\ne = 1e2\ns = "x"\nl = \'y\'\n'
                   'm = """z"""\nt = true\na = [1, [2]]\nn = {x = 1}\nd.e = 1\n[tab]\n[[aot]]\n'
                   '[huge]\nv = 123456789012345678901234567890')
        self.assertIs(type(d), dict)
        for k, typ in (("i", int), ("h", int), ("o", int), ("b", int), ("f", float), ("e", float),
                       ("s", str), ("l", str), ("m", str), ("t", bool), ("a", list), ("n", dict),
                       ("d", dict), ("tab", dict), ("aot", list)):
            self.assertIs(type(d[k]), typ, k)
        self.assertIs(type(d["a"][1]), list)
        self.assertIs(type(d["aot"][0]), dict)
        self.assertIs(type(d["huge"]["v"]), int)
        self.assertEqual(d["huge"]["v"], 123456789012345678901234567890)
        self.assertEqual(d["h"], 16)

    def test_key_types(self):
        d = _loads("1 = 2\n'2' = 3")
        self.assertEqual(d, {"1": 2, "2": 3})
        for k in d:
            self.assertIs(type(k), str)


class Req14_ErrorsAndLineNumbers(TomlCase):
    """Any problem raises `cfgkit.ParseError` whose `.line` is the 1-based line on which the
    statement containing the problem STARTS (the line of the key or the `[` of the header,
    counted after treating `\\r\\n` as a newline), also for errors inside a multi-line string,
    array or on a later line of the same statement."""

    def test_is_cfgkit_parse_error(self):
        with self.assertRaises(cfgkit.ParseError) as cm:
            _loads("a = @")
        self.assertIsInstance(cm.exception, ConfigError)
        self.assertIsInstance(cm.exception.line, int)

    def test_simple_lines(self):
        self.bad_line("a = @", 1)
        self.bad_line("a = 1\nb = 2\nc = @", 3)
        self.bad_line("a = 1\n\n\n# c\nb = 01", 5)
        self.bad_line("a = 1\n\n\na = 2", 4)
        self.bad_line("[t]\n\n[t]", 3)
        self.bad_line("a = 1\n  [a]", 2)
        self.bad_line("a.b = 1\n[a]", 2)
        self.bad_line("x = 1\nd = 1979-05-27", 2)
        self.bad_line("x = 1\nt = {x = 1, x = 2}", 2)
        self.bad_line("x = 1\ny = 1 2", 2)
        self.bad_line("x = 1\n[t] junk", 2)
        self.bad_line("x = 1\n# bad \x01 comment", 2)
        self.bad_line("x = 1\n[[a]]\n[[a]]\nk = 1\nk = 2", 5)

    def test_multiline_string(self):
        self.bad_line('a = 1\nb = """x\n\ny\\q"""', 2)
        self.bad_line('a = 1\nb = """\nline\nline\x01\n"""', 2)
        self.bad_line("a = 1\nb = '''\nok\n\x7f'''", 2)
        self.bad_line('a = 1\nb = """abc\n\n', 2)
        self.bad_line('a = 1\nb = """x\ny""" z', 2)

    def test_array(self):
        self.bad_line("x = 1\narr = [\n 1,\n 2,\n oops\n]", 2)
        self.bad_line("x = 1\narr = [\n 1,\n 2,\n", 2)
        self.bad_line("x = 1\narr = [\n 1,\n [ 2,\n  { a = 1, a = 2 } ]\n]", 2)
        self.bad_line("x = 1\narr = [\n # c\x01\n]", 2)
        self.bad_line("x = 1\narr = [\n '''a\nb\\u'''\n,\n'b\x00'\n]", 2)

    def test_lines_counted_after_multiline_constructs(self):
        self.bad_line('s = """\n1\n2\n"""\nbad', 5)
        self.bad_line("a = [\n1,\n2\n]\n\nb = 1\nb = 2", 7)
        self.bad_line("s = '''\na\nb'''\nt = {}\nt.x = 1", 5)

    def test_crlf_counts_as_newline(self):
        self.bad_line("a = 1\r\nb = 2\r\nc = @", 3)
        self.bad_line('a = 1\r\ns = """\r\nx\r\n"""\r\n\r\na = 2', 6)
        self.bad_line("x = 1\r\ns = 'a\rb'", 2)

    def test_lone_cr_in_string_line(self):
        self.bad_line('a = 1\nb = "x\ry"', 2)

    def test_header_line(self):
        self.bad_line("a = 1\n\n[[a]]", 3)
        self.bad_line("[a]\nb = 1\n\n  [a.b.c]", 4)
        self.bad_line("[a]\n[b]\n[a]", 3)


class Req15_NonStringInput(unittest.TestCase):
    """Parsing a non-`str` raises `ParseError`."""

    def test_non_str(self):
        for value in (b"a = 1", bytearray(b"a = 1"), None, 1, ["a = 1"], {"a": 1}):
            with self.assertRaises(ParseError, msg=repr(value)):
                _loads(value)

    def test_non_str_via_other_entry_points(self):
        with self.assertRaises(ParseError):
            cfgkit.loads_toml(b"a = 1")
        with self.assertRaises(ParseError):
            load_text(b"a = 1", "toml")
        with self.assertRaises(ParseError):
            Config.from_toml(None)


class Req16_Performance(TomlCase):
    """The parser must be linear-time enough to read a document of 60,000 lines (and keep a line
    counter that is not quadratic) within a few seconds."""

    LIMIT = 10.0

    def timed(self, func):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, self.LIMIT)
        return result

    def test_many_tables(self):
        parts = []
        for i in range(20000):
            parts.append('[section_%d]\nname = "item %d" # c\nvalue.x = %d\n' % (i, i, i))
        text = "".join(parts)
        self.assertEqual(text.count("\n"), 60000)
        d = self.timed(lambda: _loads(text))
        self.assertEqual(len(d), 20000)
        self.assertEqual(d["section_19999"], {"name": "item 19999", "value": {"x": 19999}})

    def test_many_keys_crlf(self):
        text = "".join("key%d = %d\r\n" % (i, i) for i in range(60000))
        d = self.timed(lambda: _loads(text))
        self.assertEqual(len(d), 60000)
        self.assertEqual(d["key59999"], 59999)

    def test_long_array_and_array_of_tables(self):
        text = "a = [\n" + "".join("  %d,\n" % i for i in range(30000)) + "]\n" + \
               "".join("[[t]]\nk = %d\n" % i for i in range(15000))
        d = self.timed(lambda: _loads(text))
        self.assertEqual(d["a"], list(range(30000)))
        self.assertEqual(len(d["t"]), 15000)
        self.assertEqual(d["t"][-1], {"k": 14999})

    def test_long_multiline_string(self):
        text = 's = """\n' + "line\n" * 60000 + '"""\n'
        d = self.timed(lambda: _loads(text))
        self.assertEqual(d["s"], "line\n" * 60000)

    def test_error_at_end_of_long_document(self):
        text = "".join("k%d = 'v'\n" % i for i in range(59999)) + "k0 = 1\n"

        def run():
            with self.assertRaises(ParseError) as cm:
                _loads(text)
            return cm.exception

        exc = self.timed(run)
        self.assertEqual(exc.line, 60000)

    def test_error_at_end_of_long_crlf_document(self):
        text = '# start\r\nm = """\r\n' + "x\r\n" * 59996 + '"""\r\nbad = \r\n'

        def run():
            with self.assertRaises(ParseError) as cm:
                _loads(text)
            return cm.exception

        exc = self.timed(run)
        self.assertEqual(exc.line, 60000)


class Req17_LoadText(unittest.TestCase):
    """Integration: `load_text(text, "toml")`."""

    def test_load_text(self):
        self.assertEqual(load_text('a = 1\n[s]\nk = "v"\n', "toml"), {"a": 1, "s": {"k": "v"}})
        self.assertEqual(load_text("", "toml"), {})

    def test_load_text_errors(self):
        with self.assertRaises(ParseError) as cm:
            load_text("a = 1\na = 2", "toml")
        self.assertEqual(cm.exception.line, 2)
        with self.assertRaises(ParseError):
            load_text("d = 1979-05-27", "toml")


class Req18_LoadFile(unittest.TestCase):
    """`load_file` for the suffix `.toml` (case-insensitive, UTF-8, like the existing formats, so
    `load_layers` can mix ini/json/toml files)."""

    def test_load_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "app.toml"
            p.write_bytes('name = "café ✓"\n[server]\nport = 8080\n'.encode("utf-8"))
            c = load_file(p)
            self.assertIsInstance(c, Config)
            self.assertEqual(c.as_dict(), {"name": "café ✓", "server": {"port": 8080}})
            self.assertEqual(c.get("server.port"), 8080)
            c2 = load_file(str(p))
            self.assertEqual(c2.get("name"), "café ✓")

    def test_suffix_case_insensitive(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.TOML", "b.Toml", "c.tOmL"):
                p = Path(d) / name
                p.write_bytes(b"x = 1\n")
                self.assertEqual(load_file(p).as_dict(), {"x": 1})

    def test_crlf_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.toml"
            p.write_bytes(b'a = 1\r\ns = """\r\nx\r\n"""\r\n')
            self.assertEqual(load_file(p).as_dict(), {"a": 1, "s": "x\n"})

    def test_file_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.toml"
            p.write_bytes(b"a = 1\n\nb = [\n1,,\n]\n")
            with self.assertRaises(ParseError) as cm:
                load_file(p)
            self.assertEqual(cm.exception.line, 3)

    def test_load_layers_mix(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.ini").write_text("[s]\nk = 1\ni = x\n", encoding="utf-8")
            (Path(d) / "b.json").write_text('{"s": {"j": 2}, "top": "json"}', encoding="utf-8")
            (Path(d) / "c.toml").write_text('top = "toml"\n[s]\nk = 3\n[[servers]]\nhost = "h"\n',
                                            encoding="utf-8")
            c = load_layers([Path(d) / "a.ini", Path(d) / "b.json", Path(d) / "c.toml"])
            self.assertEqual(c.as_dict(), {"s": {"k": 3, "i": "x", "j": 2}, "top": "toml",
                                           "servers": [{"host": "h"}]})
            c = load_layers([Path(d) / "c.toml", Path(d) / "a.ini"])
            self.assertEqual(c.get("s.k"), "1")
            self.assertEqual(c.get("top"), "toml")


class Req19_ConfigFromToml(unittest.TestCase):
    """`Config.from_toml(text)`."""

    def test_from_toml(self):
        c = Config.from_toml('[server]\nhost = "x"\nport = 80\n')
        self.assertIsInstance(c, Config)
        self.assertEqual(c.as_dict(), {"server": {"host": "x", "port": 80}})
        self.assertEqual(c.get("server.port"), 80)

    def test_from_toml_error(self):
        with self.assertRaises(ParseError) as cm:
            Config.from_toml("a = 1\n[a]")
        self.assertEqual(cm.exception.line, 2)


class Req20_PackageExport(unittest.TestCase):
    """`cfgkit.loads_toml` exported from the package."""

    def test_exported(self):
        from cfgkit import loads_toml
        self.assertEqual(loads_toml('a = "b"\n[t]\nn = 1.5'), {"a": "b", "t": {"n": 1.5}})
        self.assertIn("loads_toml", cfgkit.__all__)
        ns = {}
        exec("from cfgkit import *", ns)
        self.assertIn("loads_toml", ns)

    def test_same_behaviour_as_module(self):
        with self.assertRaises(ParseError) as cm:
            cfgkit.loads_toml("x = 1\ny = [\n1,\n@]")
        self.assertEqual(cm.exception.line, 2)
        with self.assertRaises(ParseError):
            cfgkit.loads_toml("t = 07:32:00")


class Req21_ConfigGetWalksLists(unittest.TestCase):
    """`Config.get(path, default)` now also walks lists: a path component made only of decimal
    digits indexes a list (`"servers.1.host"`), an out-of-range index or a non-numeric component
    on a list counts as missing (default / `KeyError`)."""

    def make(self):
        return Config({"servers": [{"host": "a", "ports": [80, 443]}, {"host": "b"}],
                       "matrix": [[1, 2], [3, 4]], "d": {"0": "zero"}, "s": "str"})

    def test_index(self):
        c = self.make()
        self.assertEqual(c.get("servers.1.host"), "b")
        self.assertEqual(c.get("servers.0.host"), "a")
        self.assertEqual(c.get("servers.0.ports.1"), 443)
        self.assertEqual(c.get("matrix.1.0"), 3)
        self.assertEqual(c.get("servers.1"), {"host": "b"})
        self.assertEqual(c.get("servers.1.host", "dflt"), "b")
        self.assertEqual(c.get("d.0"), "zero")

    def test_out_of_range(self):
        c = self.make()
        self.assertEqual(c.get("servers.2.host", "dflt"), "dflt")
        self.assertEqual(c.get("servers.2", None), None)
        self.assertEqual(c.get("servers.0.ports.2", 0), 0)
        with self.assertRaises(KeyError):
            c.get("servers.2")
        with self.assertRaises(KeyError):
            c.get("servers.99.host")

    def test_non_numeric_on_list(self):
        c = self.make()
        for path in ("servers.host", "servers.-1", "servers.-1.host", "servers.+1", "servers.1.5",
                     "servers.", "servers.0x1", "servers. 1", "matrix.a.0"):
            self.assertEqual(c.get(path, "dflt"), "dflt", path)
            with self.assertRaises(KeyError, msg=path):
                c.get(path)

    def test_indexing_into_scalars_is_missing(self):
        c = self.make()
        self.assertEqual(c.get("servers.0.host.0", "dflt"), "dflt")
        self.assertEqual(c.get("s.0", "dflt"), "dflt")
        with self.assertRaises(KeyError):
            c.get("servers.1.host.x")

    def test_from_toml_array_of_tables(self):
        c = Config.from_toml('[[servers]]\nhost = "a"\n[[servers]]\nhost = "b"\n')
        self.assertEqual(c.get("servers.1.host"), "b")
        self.assertEqual(c.get("servers.2.host", 5), 5)


class Req22_ConfigContainsWalksLists(unittest.TestCase):
    """`Config.__contains__` follows the same rule as `get` for lists."""

    def test_contains(self):
        c = Config({"servers": [{"host": "a"}, {"host": "b"}], "x": 1})
        self.assertIn("servers.1.host", c)
        self.assertIn("servers.0", c)
        self.assertIn("servers", c)
        self.assertNotIn("servers.2", c)
        self.assertNotIn("servers.2.host", c)
        self.assertNotIn("servers.host", c)
        self.assertNotIn("servers.-1", c)
        self.assertNotIn("servers.0.port", c)
        self.assertNotIn("x.0", c)


class Req23_ExistingBehaviourUnchanged(unittest.TestCase):
    """Existing INI/JSON/Config behaviour is unchanged."""

    def test_ini(self):
        self.assertEqual(parse_ini("top = 1\n[a]\nx = y # not a comment\n; c\n[b]\nk=v"),
                         {"top": "1", "a": {"x": "y # not a comment"}, "b": {"k": "v"}})
        self.assertEqual(load_text("[s]\nk = 1\n", "ini"), {"s": {"k": "1"}})
        with self.assertRaises(ParseError) as cm:
            parse_ini("[a]\nx = 1\noops\n")
        self.assertEqual(cm.exception.line, 3)

    def test_json(self):
        self.assertEqual(load_text('{"a": {"b": 1}}', "json"), {"a": {"b": 1}})
        with self.assertRaises(ParseError):
            load_text("[1]", "json")
        with self.assertRaises(ParseError):
            load_text("{bad", "json")
        with self.assertRaises(ConfigError):
            load_text("x", "yaml")

    def test_config(self):
        c = Config({"a": {"b": 1, "c": {"d": 2}}, "x": 1})
        self.assertEqual(c.get("a.c.d"), 2)
        self.assertEqual(c.get("a.zz", 7), 7)
        self.assertIn("a.b", c)
        self.assertNotIn("a.b.c", c)
        with self.assertRaises(KeyError):
            c.get("nope")
        m = c.merge(Config({"a": {"c": {"e": 3}}, "x": [1]}))
        self.assertEqual(m.as_dict(), {"a": {"b": 1, "c": {"d": 2, "e": 3}}, "x": [1]})
        with self.assertRaises(ConfigError):
            c.section("x")
        self.assertEqual(c.section("a.c").as_dict(), {"d": 2})
        self.assertEqual(Config().as_dict(), {})

    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.ini").write_text("[s]\nk = 1\n", encoding="utf-8")
            (Path(d) / "b.json").write_text('{"s": {"j": 2}}', encoding="utf-8")
            c = load_layers([Path(d) / "a.ini", Path(d) / "b.json"])
            self.assertEqual(c.as_dict(), {"s": {"k": "1", "j": 2}})
            (Path(d) / "c.INI").write_text("[s]\nk = 3\n", encoding="utf-8")
            self.assertEqual(load_file(Path(d) / "c.INI").get("s.k"), "3")
            (Path(d) / "d.JSON").write_text('{"é": 1}', encoding="utf-8")
            self.assertEqual(load_file(Path(d) / "d.JSON").as_dict(), {"é": 1})


if __name__ == "__main__":
    unittest.main()
