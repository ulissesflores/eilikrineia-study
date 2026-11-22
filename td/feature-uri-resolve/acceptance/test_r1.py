"""Acceptance tests for the RFC 3986 rework of urikit.

The package is accessed as ``urikit.<name>`` inside each test so that a
missing name fails only the tests that need it.
"""
import unittest

import urikit


BASE = "http://a/b/c/d;p?q"


class _Base(unittest.TestCase):
    def assertInvalid(self, text):
        with self.assertRaises(urikit.UriError, msg=repr(text)):
            urikit.parse(text)

    def assertValid(self, text):
        try:
            u = urikit.parse(text)
        except urikit.UriError as e:  # pragma: no cover - reported as failure
            self.fail("%r rejected: %s" % (text, e))
        self.assertEqual(str(u), text)
        return u


class Req01_parse_raises_UriError(_Base):
    """parse(text) validates and raises UriError (a ValueError) for text that is
    not a valid URI-reference; a non-string is a UriError."""

    def test_uri_error_is_value_error(self):
        self.assertTrue(issubclass(urikit.UriError, ValueError))

    def test_non_strings(self):
        for value in (None, 123, b"http://a/", ["http://a/"], 1.5):
            with self.subTest(value=value):
                with self.assertRaises(urikit.UriError):
                    urikit.parse(value)

    def test_invalid_text_raises(self):
        self.assertInvalid("http://a b/")


class Req02_split_and_recompose(_Base):
    """The split is still RFC appendix B; Uri stays a namedtuple of (scheme,
    authority, path, query, fragment) with None for absent and "" for present but
    empty parts; str(uri) recomposes per 5.3 so str(parse(s)) == s for every valid s."""

    def test_components(self):
        u = urikit.parse("http://user@example.com:8080/a/b?x=1#frag")
        self.assertIsInstance(u, tuple)
        self.assertEqual(u, urikit.Uri("http", "user@example.com:8080", "/a/b", "x=1", "frag"))
        self.assertEqual(
            (u.scheme, u.authority, u.path, u.query, u.fragment),
            ("http", "user@example.com:8080", "/a/b", "x=1", "frag"),
        )

    def test_absent_vs_empty(self):
        self.assertEqual(urikit.parse(""), urikit.Uri(None, None, "", None, None))
        self.assertEqual(urikit.parse("//h?#"), urikit.Uri(None, "h", "", "", ""))
        self.assertEqual(urikit.parse("a/b"), urikit.Uri(None, None, "a/b", None, None))
        self.assertEqual(urikit.parse("//"), urikit.Uri(None, "", "", None, None))
        self.assertEqual(urikit.parse("x:"), urikit.Uri("x", None, "", None, None))
        self.assertEqual(urikit.parse("?a?b#c"), urikit.Uri(None, None, "", "a?b", "c"))

    def test_roundtrip(self):
        for s in [
            "", "#", "?", "?#", "//", "///", "a", "./a:b", "x:", "x://",
            "http://u:p@h:8080/p?q#f", "http://[::1]:80/", "http://[v7.a:b!]/",
            "http://[::FFFF:1.2.3.4]/", "foo+bar-1.x:rest", "http://h:/", "http://@h/",
            "mailto:a@b", "urn:a:b:c", "http://h/%41%a1", "http://!$&'()*+,;=:x@h/",
            "http://h/?a/b?c:d@#f/?:@", "file:///x", "http://h/a//b", "//h", "?a?b",
            "HTTP://Example.COM/%7e", "g;x=1/../y", "../../g", "a/b:c",
            "http://h/-._~!$&'()*+,;=:@",
        ]:
            with self.subTest(s=s):
                self.assertValid(s)


class Req03_scheme_syntax(_Base):
    """The scheme (text before the first ':' when that comes before any / ? #)
    must match ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )."""

    def test_valid_schemes(self):
        for s in ["a:b", "Z:x", "a1+-.:x", "svn+ssh://h/", "HTTP://h/"]:
            with self.subTest(s=s):
                self.assertValid(s)
        self.assertEqual(urikit.parse("a1+-.:x").scheme, "a1+-.")

    def test_invalid_schemes(self):
        for s in ["1http://a/", "-a:b", "+a:b", ".a:b", "a_b:c", "a%41:b", "a b:c",
                  ":", ":a", "://h/"]:
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req04_first_segment_colon(_Base):
    """Without a scheme and authority the first path segment must not contain ':'."""

    def test_allowed(self):
        for s in ["./a:b", "a/b:c", "/a:b", "//h/a:b", "?a:b", "#a:b"]:
            with self.subTest(s=s):
                self.assertValid(s)

    def test_rejected(self):
        # The text before ":" is not a valid scheme, so there is no scheme and
        # the first segment contains ":".
        for s in ["1a:b", "_x:y/z"]:
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req05_userinfo_syntax(_Base):
    """userinfo is *( unreserved / pct-encoded / sub-delims / ":" )."""

    def test_valid(self):
        for s in ["http://u:p@h/", "http://@h/", "http://a-._~%20!$&'()*+,;=::@h/",
                  "http://:@h/"]:
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ["http://u p@h/", "http://u[@h/", "http://u]@h/", "http://u%@h/",
                  "http://u%zz@h/", "http://u<@h/", "http://a@b@c/"]:
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req06_host_syntax(_Base):
    """The host is a reg-name (unreserved / pct-encoded / sub-delims) or an
    IP-literal in brackets: IPv6-ish (only hex digits, ':' and '.', at least two
    ':') or IPvFuture ('v' HEXDIG+ '.' then 1+ of unreserved / sub-delims / ':');
    '[' / ']' outside an IP literal and '@' in the host are errors."""

    def test_valid(self):
        for s in ["http://example.com/", "http://h%41-._~!$&'()*+,;=/", "file:///x",
                  "http://[::1]/", "http://[::]/", "http://[1:2:3:4:5:6:7.8.9.10]/",
                  "http://[ABCD:ef01::]:8/", "http://[v1.x]/", "http://[vF0.a:b!$_~]/",
                  "http://[V1.x]/"]:
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ["http://[1.2.3]/", "http://[:1]/", "http://[g::1]/", "http://[::1/",
                  "http://::1]/", "http://[]/", "http://[v.x]/", "http://[v1.]/",
                  "http://[v1x]/", "http://[vg.x]/", "http://[v1.x/y]/", "http://h[1]/",
                  "http://[::1]x/", "http://h]/", "http://a@b@c/", "http://h:80:90/",
                  "http://h st/", "http://%zz/"]:
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req07_port_syntax(_Base):
    """The port is digits only (possibly empty)."""

    def test_valid(self):
        for s in ["http://h:80/", "http://h:/", "http://h:00081/", "http://[::1]:/",
                  "http://[::1]:443"]:
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ["http://h:8a/", "http://h:-1/", "http://h: 80/", "http://h:+80/",
                  "http://[::1]:x/"]:
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req08_path_query_fragment_chars(_Base):
    """Path characters are pchar and '/'; query and fragment are pchar, '/' and '?'."""

    def test_valid(self):
        for s in ["/a:b@c!$&'()*+,;=-._~%41/", "http://h/x?a/b?c:@!$&'()*+,;=",
                  "http://h/x#a/b?c:@!$&'()*+,;=", "a?b?c#d?e/f"]:
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ["/a[b", "/a]b", "http://h?[", "http://h?]", "http://h#[", "http://h#]",
                  "http://h##", "http://h/x#a#b", "/a?b#c#d"]:
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req09_percent_encoding(_Base):
    """Every '%' must be followed by two hex digits."""

    def test_valid(self):
        for s in ["/%41%a1%FF", "http://%41/", "?%2f", "#%2F", "http://%7e@h/"]:
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ["/%", "/%4", "/%4g", "/%g4", "http://h?%zz", "http://h#%", "http://%/",
                  "http://u%2@h/", "/%%41"]:
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req10_forbidden_characters(_Base):
    """Anything else (spaces, < > " { } | ^, backslash, backtick, non-ASCII
    characters, ...) is a UriError."""

    def test_forbidden_chars_everywhere(self):
        for c in [" ", "<", ">", '"', "{", "}", "|", "^", "\\", "`", "\u00e9", "\u20ac",
                  "\t", "\n", "\x00", "\x7f"]:
            for template in ["http://h/a%sb", "http://h?a%sb", "http://h#a%sb",
                             "http://a%sb/", "http://u%sx@h/", "a%sb"]:
                s = template % c
                with self.subTest(s=s):
                    self.assertInvalid(s)

    def test_leading_trailing_space(self):
        self.assertInvalid(" http://h/")
        self.assertInvalid("http://h/ ")


class Req11_component_properties(_Base):
    """Uri gains userinfo, host (as written, brackets included; "" for an empty
    host), port (int; None if absent or empty) - all None without authority - and
    keeps is_absolute."""

    def test_full(self):
        u = urikit.parse("http://u:p@H.Example.com:8080/x")
        self.assertEqual(u.userinfo, "u:p")
        self.assertEqual(u.host, "H.Example.com")
        self.assertEqual(u.port, 8080)
        self.assertIsInstance(u.port, int)

    def test_ip_literal(self):
        u = urikit.parse("http://[::1]:80/")
        self.assertEqual(u.host, "[::1]")
        self.assertEqual(u.port, 80)
        self.assertEqual(urikit.parse("http://[v1.X]/").host, "[v1.X]")

    def test_empty_host_and_port(self):
        u = urikit.parse("file:///x")
        self.assertEqual(u.host, "")
        self.assertIsNone(u.port)
        self.assertIsNone(urikit.parse("http://h:/").port)
        self.assertEqual(urikit.parse("http://h:/").host, "h")
        self.assertIsNone(urikit.parse("http://h/").port)

    def test_port_with_leading_zeros(self):
        u = urikit.parse("http://h:00081/")
        self.assertEqual(u.port, 81)
        self.assertIsInstance(u.port, int)

    def test_empty_userinfo(self):
        u = urikit.parse("http://@h/")
        self.assertEqual(u.userinfo, "")
        self.assertEqual(u.host, "h")
        u = urikit.parse("http://a:b@")
        self.assertEqual(u.userinfo, "a:b")
        self.assertEqual(u.host, "")

    def test_no_authority(self):
        for s in ["mailto:a@b", "/x", "", "a:b:80"]:
            with self.subTest(s=s):
                u = urikit.parse(s)
                self.assertIsNone(u.userinfo)
                self.assertIsNone(u.host)
                self.assertIsNone(u.port)

    def test_is_absolute(self):
        self.assertTrue(urikit.parse("a:b").is_absolute)
        self.assertTrue(urikit.parse("http://h/").is_absolute)
        self.assertFalse(urikit.parse("//h/").is_absolute)
        self.assertFalse(urikit.parse("/x").is_absolute)


class Req12_remove_dot_segments(unittest.TestCase):
    """remove_dot_segments(path): exactly the input/output-buffer algorithm of
    5.2.4, including rootless paths (a/../../b becomes /b)."""

    def test_cases(self):
        cases = {
            "/a/b/c/./../../g": "/a/g",
            "mid/content=5/../6": "mid/6",
            "a/../../b": "/b",
            "": "",
            ".": "",
            "..": "",
            "./": "",
            "../": "",
            "../a": "a",
            "./a": "a",
            "../../a/b": "a/b",
            "/.": "/",
            "/..": "/",
            "/./": "/",
            "/../": "/",
            "/a/b/..": "/a/",
            "/a/b/.": "/a/b/",
            "/a/./b/": "/a/b/",
            "/a/b/../../../c": "/c",
            "a/.": "a/",
            "a/..": "/",
            "/a/b": "/a/b",
            "a": "a",
            "/a/.b/..c/b.": "/a/.b/..c/b.",
            "/a/%2e/b": "/a/%2e/b",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(urikit.remove_dot_segments(path), expected)


class Req13_resolve(unittest.TestCase):
    """resolve(base, ref): strict 5.2.2 with merge (5.2.3) and recomposition
    (5.3). Both validated (UriError); base must have a scheme (fragment ignored).
    Scheme and host case, percent-encoding etc. are NOT touched."""


    def test_base_fragment_ignored(self):
        self.assertEqual(urikit.resolve("http://a/b#f", ""), "http://a/b")
        self.assertEqual(urikit.resolve("http://a/b?q#f", "?x"), "http://a/b?x")
        self.assertEqual(urikit.resolve("http://a/b#f", "#g"), "http://a/b#g")

    def test_nothing_normalised(self):
        self.assertEqual(urikit.resolve("HTTP://A.COM:80/%7e/x", "y"), "HTTP://A.COM:80/%7e/y")
        self.assertEqual(urikit.resolve("http://a/b", "HTTP://B/./c%7E"), "HTTP://B/c%7E")
        self.assertEqual(urikit.resolve("http://a/b", "//X:/%41"), "http://X:/%41")

    def test_merge_and_dots(self):
        self.assertEqual(urikit.resolve("http://a", "g"), "http://a/g")
        self.assertEqual(urikit.resolve("mailto:x", "y"), "mailto:y")
        self.assertEqual(urikit.resolve("foo:a/b", "../../c"), "foo:/c")
        self.assertEqual(urikit.resolve("http://a/b/c", "//x/../y"), "http://x/y")
        self.assertEqual(urikit.resolve("http://a/b/c", "http://x/./y/../z"), "http://x/z")

    def test_empty_query_and_fragment(self):
        self.assertEqual(urikit.resolve("http://a/b?q", "?"), "http://a/b?")
        self.assertEqual(urikit.resolve("http://a/b?q#f", "#"), "http://a/b?q#")

    def test_returns_str(self):
        self.assertIsInstance(urikit.resolve(BASE, "g"), str)


RFC_EXAMPLES = [
    ("g:h", "g:h"),
    ("g", "http://a/b/c/g"),
    ("./g", "http://a/b/c/g"),
    ("g/", "http://a/b/c/g/"),
    ("/g", "http://a/g"),
    ("//g", "http://g"),
    ("?y", "http://a/b/c/d;p?y"),
    ("g?y", "http://a/b/c/g?y"),
    ("#s", "http://a/b/c/d;p?q#s"),
    ("g#s", "http://a/b/c/g#s"),
    ("g?y#s", "http://a/b/c/g?y#s"),
    (";x", "http://a/b/c/;x"),
    ("g;x", "http://a/b/c/g;x"),
    ("g;x?y#s", "http://a/b/c/g;x?y#s"),
    ("", "http://a/b/c/d;p?q"),
    (".", "http://a/b/c/"),
    ("./", "http://a/b/c/"),
    ("..", "http://a/b/"),
    ("../", "http://a/b/"),
    ("../g", "http://a/b/g"),
    ("../..", "http://a/"),
    ("../../", "http://a/"),
    ("../../g", "http://a/g"),
    ("../../../g", "http://a/g"),
    ("../../../../g", "http://a/g"),
    ("/./g", "http://a/g"),
    ("/../g", "http://a/g"),
    ("g.", "http://a/b/c/g."),
    (".g", "http://a/b/c/.g"),
    ("g..", "http://a/b/c/g.."),
    ("..g", "http://a/b/c/..g"),
    ("./../g", "http://a/b/g"),
    ("./g/.", "http://a/b/c/g/"),
    ("g/./h", "http://a/b/c/g/h"),
    ("g/../h", "http://a/b/c/h"),
    ("g;x=1/./y", "http://a/b/c/g;x=1/y"),
    ("g;x=1/../y", "http://a/b/c/y"),
    ("g?y/./x", "http://a/b/c/g?y/./x"),
    ("g?y/../x", "http://a/b/c/g?y/../x"),
    ("g#s/./x", "http://a/b/c/g#s/./x"),
    ("g#s/../x", "http://a/b/c/g#s/../x"),
    ("http:g", "http:g"),
]


class Req14_join_identical_to_resolve(unittest.TestCase):
    """join(base, ref) stays and is now identical to resolve."""

    def test_same_results(self):
        for ref, expected in RFC_EXAMPLES:
            with self.subTest(ref=ref):
                self.assertEqual(urikit.join(BASE, ref), expected)
        self.assertEqual(urikit.join("foo:a/b", "../../c"), "foo:/c")
        self.assertEqual(urikit.join("HTTP://A/%7e/x", "y"), "HTTP://A/%7e/y")

    def test_same_errors(self):
        for base, ref in [("/a", "b"), ("http://a/", "x y"), ("http://a b/", "x")]:
            with self.subTest(base=base, ref=ref):
                with self.assertRaises(urikit.UriError):
                    urikit.join(base, ref)


class Req15_rfc_section_5_4_examples(unittest.TestCase):
    """All examples of RFC section 5.4 hold (including http:g staying http:g)."""

    def test_examples(self):
        for ref, expected in RFC_EXAMPLES:
            with self.subTest(ref=ref):
                self.assertEqual(urikit.resolve(BASE, ref), expected)


class Req16_normalize_scheme_case(unittest.TestCase):
    """normalize step (1): lowercase the scheme."""

    def test_scheme(self):
        self.assertEqual(urikit.normalize("HTTP://h/"), "http://h/")
        self.assertEqual(urikit.normalize("MaIlTo:Joe@Example.COM"), "mailto:Joe@Example.COM")
        self.assertEqual(urikit.normalize("Foo+Bar:X"), "foo+bar:X")


class Req17_normalize_percent_encoding_and_host_case(unittest.TestCase):
    """normalize step (2): in every component uppercase percent-encoding hex digits
    and decode those encoding unreserved characters; lowercase the host's letters
    except percent-encoding hex digits; userinfo, path, query, fragment keep case."""

    def test_path(self):
        self.assertEqual(urikit.normalize("http://h/a%7e%2fb"), "http://h/a~%2Fb")
        self.assertEqual(urikit.normalize("http://h/%c3%a9"), "http://h/%C3%A9")
        self.assertEqual(urikit.normalize("http://h/%41%5a%61%7A%30%2D%2E%5F%7E"),
                         "http://h/AZaz0-._~")
        self.assertEqual(urikit.normalize("http://h/%25%7e"), "http://h/%25~")
        self.assertEqual(urikit.normalize("http://h/Path/MiXed"), "http://h/Path/MiXed")

    def test_host(self):
        self.assertEqual(urikit.normalize("http://www.Example.COM/"), "http://www.example.com/")
        self.assertEqual(urikit.normalize("http://%41%3a.com/"), "http://a%3A.com/")
        self.assertEqual(urikit.normalize("http://%4A%2f/"), "http://j%2F/")
        self.assertEqual(urikit.normalize("http://[::A]/"), "http://[::a]/")
        self.assertEqual(urikit.normalize("http://[vF.ABC]/"), "http://[vf.abc]/")

    def test_userinfo(self):
        self.assertEqual(urikit.normalize("http://User%7e%3f%4A@Host/"), "http://User~%3FJ@host/")

    def test_query_fragment(self):
        self.assertEqual(urikit.normalize("http://h/P?Q=%7A%2f#F%2a%7e"),
                         "http://h/P?Q=z%2F#F%2A~")

    def test_whole(self):
        self.assertEqual(urikit.normalize("HTTP://www.Example.COM/a%7e%2fb"),
                         "http://www.example.com/a~%2Fb")


class Req18_normalize_dot_segments(unittest.TestCase):
    """normalize step (3): remove_dot_segments on the path; percent-decoding happens
    before dot-segment removal (/%2e%2e/ is a dot segment)."""

    def test_dots(self):
        self.assertEqual(urikit.normalize("http://h/a/./b/../c"), "http://h/a/c")
        self.assertEqual(urikit.normalize("http://h/a/../../b"), "http://h/b")
        self.assertEqual(urikit.normalize("file:///a/./b"), "file:///a/b")
        self.assertEqual(urikit.normalize("foo:a/../../b"), "foo:/b")

    def test_encoded_dots(self):
        self.assertEqual(urikit.normalize("http://h/a/%2e%2e/b"), "http://h/b")
        self.assertEqual(urikit.normalize("http://h/a/%2E%2e/b"), "http://h/b")
        self.assertEqual(urikit.normalize("http://h/a/%2e/b"), "http://h/a/b")

    def test_query_untouched(self):
        self.assertEqual(urikit.normalize("http://h/x?a/../b#c/./d"), "http://h/x?a/../b#c/./d")


class Req19_normalize_scheme_based_rules(unittest.TestCase):
    """normalize step (4): drop the port when empty or equal to the scheme default
    (http 80, https 443, ftp 21, ws 80, wss 443; other ports kept exactly as
    written); for those five schemes an empty path becomes / with an authority."""

    def test_default_ports_dropped(self):
        cases = {
            "http://h:80/": "http://h/",
            "http://h:0080/x": "http://h/x",
            "https://h:443/": "https://h/",
            "ftp://h:21/x": "ftp://h/x",
            "ws://h:80/": "ws://h/",
            "wss://h:443/": "wss://h/",
            "HTTP://H:80/": "http://h/",
            "http://[::1]:80/": "http://[::1]/",
            "http://u@h:80/": "http://u@h/",
        }
        for src, expected in cases.items():
            with self.subTest(src=src):
                self.assertEqual(urikit.normalize(src), expected)

    def test_empty_port_dropped(self):
        self.assertEqual(urikit.normalize("http://h:/"), "http://h/")
        self.assertEqual(urikit.normalize("https://h:/x"), "https://h/x")
        self.assertEqual(urikit.normalize("foo://h:/x"), "foo://h/x")

    def test_other_ports_kept(self):
        cases = {
            "http://h:00081/": "http://h:00081/",
            "http://h:8080/": "http://h:8080/",
            "https://h:80/": "https://h:80/",
            "http://h:443/": "http://h:443/",
            "ftp://h:80/": "ftp://h:80/",
            "foo://h:80/": "foo://h:80/",
            "ws://h:443/": "ws://h:443/",
        }
        for src, expected in cases.items():
            with self.subTest(src=src):
                self.assertEqual(urikit.normalize(src), expected)

    def test_empty_path(self):
        cases = {
            "http://h": "http://h/",
            "HTTP://H": "http://h/",
            "http://h?q": "http://h/?q",
            "http://h#f": "http://h/#f",
            "https://h:443": "https://h/",
            "ftp://h": "ftp://h/",
            "ws://h": "ws://h/",
            "wss://h": "wss://h/",
            "foo://h": "foo://h",
            "http://h:8080": "http://h:8080/",
        }
        for src, expected in cases.items():
            with self.subTest(src=src):
                self.assertEqual(urikit.normalize(src), expected)


class Req20_normalize_keeps_empty_query_fragment(unittest.TestCase):
    """An empty query '?' / empty fragment '#' are kept."""

    def test_kept(self):
        self.assertEqual(urikit.normalize("http://h/?#"), "http://h/?#")
        self.assertEqual(urikit.normalize("http://h?"), "http://h/?")
        self.assertEqual(urikit.normalize("http://h/x#"), "http://h/x#")


class Req21_normalize_requires_absolute(unittest.TestCase):
    """normalize(text): input must be an absolute URI, else UriError."""

    def test_errors(self):
        for s in ["//h/x", "/x", "", "x", "?q", "http://h /", "http://h/%zz", None]:
            with self.subTest(s=s):
                with self.assertRaises(urikit.UriError):
                    urikit.normalize(s)

    def test_returns_str(self):
        self.assertIsInstance(urikit.normalize("http://h/"), str)


class Req22_equivalent(unittest.TestCase):
    """equivalent(a, b) is normalize(a) == normalize(b)."""

    def test_true(self):
        self.assertTrue(urikit.equivalent("HTTP://Example.com:80/%7euser", "http://example.com/~user"))
        self.assertTrue(urikit.equivalent("http://h", "http://h/"))
        self.assertTrue(urikit.equivalent("http://h/a/%2e%2e/b", "http://h/b"))
        self.assertTrue(urikit.equivalent("http://h/%2f", "http://h/%2F"))

    def test_false(self):
        self.assertFalse(urikit.equivalent("http://h/a", "http://h/A"))
        self.assertFalse(urikit.equivalent("http://h/?", "http://h/"))
        self.assertFalse(urikit.equivalent("http://h/#", "http://h/"))
        self.assertFalse(urikit.equivalent("https://h:80/", "https://h/"))
        self.assertFalse(urikit.equivalent("http://h/%2f", "http://h//"))

    def test_errors(self):
        with self.assertRaises(urikit.UriError):
            urikit.equivalent("/x", "/x")
        with self.assertRaises(urikit.UriError):
            urikit.equivalent("http://h/", "http://h /")


class Req23_collect_links_base_validation(unittest.TestCase):
    """collect_links(base, hrefs): base must be a valid absolute URI (UriError otherwise)."""

    def test_bad_base(self):
        for base in ["/x", "//h/x", "x/y", "", "http://a b/", "http://h/%zz", None]:
            with self.subTest(base=base):
                with self.assertRaises(urikit.UriError):
                    urikit.collect_links(base, ["a"])


class Req24_collect_links_processing(unittest.TestCase):
    """Each href is stripped of leading/trailing ASCII whitespace (space, tab, LF,
    CR, FF), resolved against base, has its fragment removed and is normalised."""

    def test_basic(self):
        got = urikit.collect_links("http://a/x/y", ["z", "/z#top", "http://b/"])
        self.assertEqual(got, ["http://a/x/z", "http://a/z", "http://b/"])

    def test_whitespace_stripped(self):
        got = urikit.collect_links("http://a/x/y", [" \t\n\r\fz \t\n\r\f", "\n/q\n"])
        self.assertEqual(got, ["http://a/x/z", "http://a/q"])

    def test_non_listed_whitespace_not_stripped(self):
        got = urikit.collect_links("http://a/x/y", ["\vz", "\u00a0z", "z\x0b"])
        self.assertEqual(got, [])

    def test_resolve_and_normalise(self):
        got = urikit.collect_links(
            "http://a/x/y/z",
            ["../w", "HTTP://B:80/%7e", "//C.com", "./%2e%2e/v", "?q#f", "http://d/p?q#"],
        )
        self.assertEqual(got, ["http://a/x/w", "http://b/~", "http://c.com/",
                               "http://a/x/v", "http://a/x/y/z?q", "http://d/p?q"])

    def test_base_normalised_result(self):
        got = urikit.collect_links("HTTP://A.COM:80/x/y#frag", ["", "#t", "z"])
        self.assertEqual(got, ["http://a.com/x/y", "http://a.com/x/z"])

    def test_empty_query_kept(self):
        got = urikit.collect_links("http://a/x", ["?", "y?#"])
        self.assertEqual(got, ["http://a/x?", "http://a/y?"])


class Req25_collect_links_skipping(unittest.TestCase):
    """Invalid hrefs are silently skipped, as are links whose scheme (after
    normalisation) is not http or https."""

    def test_invalid_skipped(self):
        got = urikit.collect_links(
            "http://a/x", ["a b", "http://[x]/", "%zz", "1a:b", "<p>", "ok", "\u00e9"])
        self.assertEqual(got, ["http://a/ok"])

    def test_scheme_filter(self):
        got = urikit.collect_links(
            "http://a/x",
            ["mailto:me@x", "ftp://h/", "javascript:void(0)", "HTTPS://H", "Http://h/p",
             "ws://h/", "httpx://h/"])
        self.assertEqual(got, ["https://h/", "http://h/p"])

    def test_non_http_base(self):
        self.assertEqual(urikit.collect_links("ftp://h/d/f", ["g", "http://x/"]), ["http://x/"])


class Req26_collect_links_dedup(unittest.TestCase):
    """Duplicates (after normalisation) are dropped keeping the first occurrence."""

    def test_dedup(self):
        got = urikit.collect_links(
            "http://a/x/y",
            ["http://b/", "HTTP://B:80/#x", "http://b", "z", "./z", "z#f", "Z", "z"])
        self.assertEqual(got, ["http://b/", "http://a/x/z", "http://a/x/Z"])

    def test_order_first_seen(self):
        got = urikit.collect_links("http://a/", ["c", "b", "C", "b", "a", "%63"])
        self.assertEqual(got, ["http://a/c", "http://a/b", "http://a/C", "http://a/a"])


class Req27_package_exports(unittest.TestCase):
    """Export resolve, normalize, equivalent and remove_dot_segments from the package."""

    def test_exports(self):
        for name in ["resolve", "normalize", "equivalent", "remove_dot_segments",
                     "join", "parse", "Uri", "UriError", "collect_links"]:
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(urikit, name, None)))

    def test_from_import(self):
        ns = {}
        exec("from urikit import resolve, normalize, equivalent, remove_dot_segments", ns)
        self.assertEqual(ns["resolve"]("http://a/b", "c"), "http://a/c")


if __name__ == "__main__":
    unittest.main()
