"""Acceptance tests for the RFC 3986 rework of urikit."""
import unittest

import urikit
from urikit import Uri, UriError, collect_links, join, parse


def _api(name):
    return getattr(urikit, name)


RFC_BASE = "http://a/b/c/d;p?q"

RFC_EXAMPLES = [
    # 5.4.1 normal examples
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
    # 5.4.2 abnormal examples
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

EXTRA_RESOLVE = [
    ("http://a", "g", "http://a/g"),
    ("http://a/b#f", "", "http://a/b"),
    ("http://a/b#f", "#g", "http://a/b#g"),
    ("http://a/b?q", "?", "http://a/b?"),
    ("http://a/b?q", "/c", "http://a/c"),
    ("http://a/b?q#f", "#", "http://a/b?q#"),
    ("http://a/b", "//h/./x/../y?q", "http://h/y?q"),
    ("http://a/b", "ftp://x/a/../b", "ftp://x/b"),
    ("HTTP://A/b", "c", "HTTP://A/c"),
    ("http://a/b", "HTTP://X/%7e/./y", "HTTP://X/%7e/y"),
    ("http://a/%7e/b", "c%2f", "http://a/%7e/c%2f"),
    ("http://a:80/b", "c", "http://a:80/c"),
    ("mailto:x", "y", "mailto:y"),
    ("foo:a/b", "../../c", "foo:/c"),
]

VALID = [
    "",
    "#",
    "?",
    "//",
    "///",
    "a:",
    "a:b:c",
    "x+y-z.w9:p",
    "./a:b",
    "a/b;c=d",
    "/a@b:c!$&'()*+,;=",
    "%41%2f%2F",
    "http://h:",
    "http://@h",
    "http://a:b:c@h/",
    "http://u%41!$&'()*+,;=-._~@h/",
    "http://a!$&'()*+,;=b/",
    "http://a-b_c~d.e/",
    "http://%41/",
    "http://[::]/",
    "http://[::1]/",
    "http://[::1]:/",
    "http://[1:2:3:4:5:6:7:8]:8080/",
    "http://[::ffff:1.2.3.4]/",
    "http://[FE80::1]/",
    "http://[v1.x]/",
    "http://[vA1.a:b!$-._~]/",
    "http://h/?a?b/:@#c?/:@",
    "http://user@example.com:8080/a/b?x=1#frag",
    "file:///etc/hosts",
    "mailto:me@example.com",
    "urn:isbn:0451450523",
]

INVALID = [
    "http://a b",
    " http://a/",
    "http://a/<",
    "http://a/>",
    'http://a/"',
    "http://a/{",
    "http://a/}",
    "http://a/|",
    "http://a/^",
    "http://a/\\",
    "http://a/`",
    "http://a/\u00e9",
    "http://\u00e9/",
    "\u00e9",
    "http://a/\n",
    "1a:b",
    "a_b:c",
    "+a:b",
    ":foo",
    "a:b/c d",
    "http://u[@h/",
    "http://a@b@c/",
    "http://h:8a/",
    "http://h:-1/",
    "http://h:+1/",
    "http://h:1:2/",
    "http://[1:2]/",
    "http://[1.2.3.4]/",
    "http://[::g]/",
    "http://[]/",
    "http://[v1.]/",
    "http://[v.x]/",
    "http://[vg.x]/",
    "http://[v1x]/",
    "http://[::1/",
    "http://::1]/",
    "http://[::1]x/",
    "http://h[::1]/",
    "http://[::1]]/",
    "http://h/[x]",
    "http://h/?[",
    "http://h/#[",
    "http://h/#a#b",
    "[",
    "a]",
    "%",
    "%2",
    "%zz",
    "http://h/%g0",
    "http://%2/",
    "http://h/?%",
    "http://h/#%4",
]


class Req01_parse_split_and_recompose(unittest.TestCase):
    """`parse(text)`: the split is still RFC 3986 appendix B, `Uri` stays a namedtuple of
    (scheme, authority, path, query, fragment) with None for absent parts and "" for present
    but empty ones, and `str(uri)` recomposes per section 5.3 (so `str(parse(s)) == s` for
    every valid `s`)."""

    def test_components(self):
        self.assertEqual(parse("http://user@example.com:8080/a/b?x=1#frag"),
                         Uri("http", "user@example.com:8080", "/a/b", "x=1", "frag"))
        self.assertEqual(parse("http://[::1]:80/p?q#f"), Uri("http", "[::1]:80", "/p", "q", "f"))

    def test_absent_vs_empty(self):
        self.assertEqual(parse(""), Uri(None, None, "", None, None))
        self.assertEqual(parse("//h?#"), Uri(None, "h", "", "", ""))
        self.assertEqual(parse("a:b:c"), Uri("a", None, "b:c", None, None))
        self.assertEqual(parse("./a:b"), Uri(None, None, "./a:b", None, None))
        self.assertEqual(parse("file:///x"), Uri("file", "", "/x", None, None))

    def test_is_namedtuple(self):
        u = parse("http://h/p?q#f")
        self.assertIsInstance(u, Uri)
        self.assertIsInstance(u, tuple)
        self.assertEqual(Uri._fields, ("scheme", "authority", "path", "query", "fragment"))
        self.assertEqual((u.scheme, u.authority, u.path, u.query, u.fragment),
                         ("http", "h", "/p", "q", "f"))

    def test_round_trip(self):
        for s in VALID:
            with self.subTest(s=s):
                self.assertEqual(str(parse(s)), s)


class Req02_parse_validation(unittest.TestCase):
    """`parse(text)` validates and raises `UriError` (a `ValueError`) for text that is not a
    valid URI-reference: non-strings; bad scheme; ':' in the first segment of a scheme- and
    authority-less path; bad userinfo / host (reg-name or bracketed IPv6-ish / IPvFuture) /
    port; path chars other than pchar and '/'; query/fragment chars other than pchar, '/', '?';
    '%' not followed by two hex digits; spaces, < > " { } | ^ \\ `, non-ASCII, stray [ ],
    '@' in the host, ..."""

    def test_urierror_is_valueerror(self):
        self.assertTrue(issubclass(UriError, ValueError))

    def test_non_string(self):
        for value in (None, 42, b"http://a/", ["http://a/"]):
            with self.subTest(value=value):
                with self.assertRaises(UriError):
                    parse(value)

    def test_invalid(self):
        for s in INVALID:
            with self.subTest(s=s):
                with self.assertRaises(UriError):
                    parse(s)

    def test_valid_accepted(self):
        for s in VALID:
            with self.subTest(s=s):
                self.assertIsInstance(parse(s), Uri)


class Req03_uri_properties(unittest.TestCase):
    """`Uri` gains properties `userinfo`, `host` (as written, brackets included for IP literals;
    "" for an empty host), `port` (an int; None if absent or empty) - all None when there is no
    authority - and keeps `is_absolute`."""

    def test_full_authority(self):
        u = parse("http://u:p@[::1]:8080/")
        self.assertEqual(u.userinfo, "u:p")
        self.assertEqual(u.host, "[::1]")
        self.assertEqual(u.port, 8080)
        self.assertIsInstance(u.port, int)

    def test_host_as_written(self):
        self.assertEqual(parse("http://ExAmple.COM/").host, "ExAmple.COM")
        self.assertEqual(parse("http://%41b/").host, "%41b")
        self.assertEqual(parse("http://[v1.x]:9/").host, "[v1.x]")

    def test_no_userinfo_no_port(self):
        u = parse("http://h/x")
        self.assertIsNone(u.userinfo)
        self.assertEqual(u.host, "h")
        self.assertIsNone(u.port)

    def test_empty_parts(self):
        u = parse("file:///x")
        self.assertEqual(u.host, "")
        self.assertIsNone(u.userinfo)
        self.assertIsNone(u.port)
        u = parse("http://@h:/")
        self.assertEqual(u.userinfo, "")
        self.assertEqual(u.host, "h")
        self.assertIsNone(u.port)

    def test_port_values(self):
        self.assertEqual(parse("http://h:0080/").port, 80)
        self.assertEqual(parse("http://h:0/").port, 0)

    def test_no_authority(self):
        for s in ("mailto:me@example.com", "a/b", "", "/x:y@z"):
            with self.subTest(s=s):
                u = parse(s)
                self.assertIsNone(u.userinfo)
                self.assertIsNone(u.host)
                self.assertIsNone(u.port)

    def test_is_absolute(self):
        self.assertTrue(parse("http://a/b").is_absolute)
        self.assertTrue(parse("mailto:x").is_absolute)
        self.assertFalse(parse("a/b").is_absolute)
        self.assertFalse(parse("//a/b").is_absolute)


class Req04_remove_dot_segments(unittest.TestCase):
    """`remove_dot_segments(path)`: exactly the input-buffer/output-buffer algorithm of section
    5.2.4 (including its behaviour on rootless paths: `a/../../b` becomes `/b`)."""

    CASES = [
        ("/a/b/c/./../../g", "/a/g"),
        ("mid/content=5/../6", "mid/6"),
        ("a/../../b", "/b"),
        ("", ""),
        ("/", "/"),
        (".", ""),
        ("..", ""),
        ("../a", "a"),
        ("./a", "a"),
        ("../../a", "a"),
        ("/..", "/"),
        ("/.", "/"),
        ("/../a", "/a"),
        ("/./a", "/a"),
        ("/a/..", "/"),
        ("a/..", "/"),
        ("/a/b/..", "/a/"),
        ("/a/b/c/.", "/a/b/c/"),
        ("/a/./b", "/a/b"),
        ("/a/.b", "/a/.b"),
        ("/a/..b", "/a/..b"),
        ("/a/b..", "/a/b.."),
        (".../a", ".../a"),
        ("/a//../b", "/a/b"),
        ("a/./b/../c", "a/c"),
        ("/a/b/c", "/a/b/c"),
    ]

    def test_cases(self):
        rds = _api("remove_dot_segments")
        for given, expected in self.CASES:
            with self.subTest(path=given):
                self.assertEqual(rds(given), expected)


class Req05_resolve(unittest.TestCase):
    """`resolve(base, ref)` (strings): strict algorithm of section 5.2.2 with merge (5.2.3) and
    recomposition (5.3). Both are validated (UriError); base must have a scheme (fragment
    ignored). Scheme/host case, percent-encoding etc. are NOT touched. All examples of RFC
    section 5.4 hold (including `http:g` staying `http:g` in strict mode)."""

    def test_rfc_examples(self):
        resolve = _api("resolve")
        for ref, expected in RFC_EXAMPLES:
            with self.subTest(ref=ref):
                self.assertEqual(resolve(RFC_BASE, ref), expected)

    def test_more(self):
        resolve = _api("resolve")
        for base, ref, expected in EXTRA_RESOLVE:
            with self.subTest(base=base, ref=ref):
                self.assertEqual(resolve(base, ref), expected)

    def test_base_without_scheme(self):
        resolve = _api("resolve")
        for base in ("//a/b", "/a/b", "a/b", ""):
            with self.subTest(base=base):
                with self.assertRaises(UriError):
                    resolve(base, "c")



class Req06_join_identical_to_resolve(unittest.TestCase):
    """`join(base, ref)` stays and is now identical to `resolve`."""

    def test_rfc_examples(self):
        for ref, expected in RFC_EXAMPLES:
            with self.subTest(ref=ref):
                self.assertEqual(join(RFC_BASE, ref), expected)

    def test_more(self):
        for base, ref, expected in EXTRA_RESOLVE:
            with self.subTest(base=base, ref=ref):
                self.assertEqual(join(base, ref), expected)

    def test_errors(self):
        with self.assertRaises(UriError):
            join("//a/b", "c")
        with self.assertRaises(UriError):
            join("http://a/b", "c d")
        with self.assertRaises(UriError):
            join("http://a b/", "c")


class Req07_normalize(unittest.TestCase):
    """`normalize(text)` (input must be an absolute URI, else UriError): (1) lowercase scheme;
    (2) uppercase percent-encoding hex, decode those encoding unreserved chars, then lowercase
    the host's letters except pct hex digits (userinfo, path, query, fragment keep case);
    (3) remove_dot_segments on the path; (4) drop empty port or the scheme's default port
    (http 80, https 443, ftp 21, ws 80, wss 443; other ports kept as written) and for those
    five schemes an empty path becomes '/' when an authority is present. Empty '?' / '#' are
    kept. Percent-decoding happens before dot-segment removal."""

    def check(self, cases):
        normalize = _api("normalize")
        for given, expected in cases:
            with self.subTest(uri=given):
                self.assertEqual(normalize(given), expected)

    def test_scheme_and_host_case(self):
        self.check([
            ("HTTP://Example.COM/", "http://example.com/"),
            ("HtTp://a/", "http://a/"),
            ("http://[::ABCD]/", "http://[::abcd]/"),
            ("http://[v1.AB]/", "http://[v1.ab]/"),
        ])

    def test_other_components_keep_case(self):
        self.check([
            ("http://User:PW@h/A/B?Q=X#Frag", "http://User:PW@h/A/B?Q=X#Frag"),
            ("mailto:A@B.COM", "mailto:A@B.COM"),
            ("URN:ISBN:%7e", "urn:ISBN:~"),
        ])

    def test_percent_encoding(self):
        self.check([
            ("http://a/%7e%7Efoo", "http://a/~~foo"),
            ("http://a/%2f", "http://a/%2F"),
            ("http://a/a%c3%a9", "http://a/a%C3%A9"),
            ("http://a/%25%7e", "http://a/%25~"),
            ("http://a/%41%5a%61%7a%30%39%2d%2e%5f%7e", "http://a/AZaz09-._~"),
            ("http://a/%3a%40%21", "http://a/%3A%40%21"),
            ("http://a/?A=%7a&b=%3d", "http://a/?A=z&b=%3D"),
            ("http://a/#X%2d%2f", "http://a/#X-%2F"),
            ("http://User%7e%2f:PW@h/", "http://User~%2F:PW@h/"),
        ])

    def test_host_percent_encoding(self):
        self.check([
            ("http://%41%62c.com/", "http://abc.com/"),
            ("http://A%2fB/", "http://a%2Fb/"),
            ("http://%c3%a9X/", "http://%C3%A9x/"),
        ])

    def test_dot_segments(self):
        self.check([
            ("http://a/b/../c/./d", "http://a/c/d"),
            ("http://a/b/%2e%2e/c", "http://a/c"),
            ("http://a/b/%2E/c", "http://a/b/c"),
            ("http://a/b/c/%2E%2e", "http://a/b/"),
            ("http://a/../../x", "http://a/x"),
            ("http://a/b?x/../y", "http://a/b?x/../y"),
        ])

    def test_ports(self):
        self.check([
            ("http://a:80/", "http://a/"),
            ("http://a:/", "http://a/"),
            ("http://a:0080/", "http://a/"),
            ("http://a:00081/", "http://a:00081/"),
            ("http://a:8080/x", "http://a:8080/x"),
            ("https://a:443/x", "https://a/x"),
            ("https://a:80/", "https://a:80/"),
            ("http://a:443/", "http://a:443/"),
            ("ftp://a:21/", "ftp://a/"),
            ("ws://a:80/", "ws://a/"),
            ("wss://a:443/", "wss://a/"),
            ("foo://a:80/x", "foo://a:80/x"),
            ("http://u@h:80/", "http://u@h/"),
            ("HTTP://a:80", "http://a/"),
            ("http://[::1]:80/", "http://[::1]/"),
        ])

    def test_empty_path(self):
        self.check([
            ("http://a", "http://a/"),
            ("http://a?q", "http://a/?q"),
            ("http://a#f", "http://a/#f"),
            ("http://a:8080", "http://a:8080/"),
            ("https://a", "https://a/"),
            ("ftp://a", "ftp://a/"),
            ("ws://a", "ws://a/"),
            ("wss://a", "wss://a/"),
            ("foo://a", "foo://a"),
        ])

    def test_empty_query_fragment_kept(self):
        self.check([
            ("http://a/?#", "http://a/?#"),
            ("http://a/?", "http://a/?"),
            ("http://a/#", "http://a/#"),
        ])

    def test_requires_absolute(self):
        normalize = _api("normalize")
        for s in ("//a/b", "a/b", "/a", "", "http://a b/", "%zz", None):
            with self.subTest(s=s):
                with self.assertRaises(UriError):
                    normalize(s)


class Req08_equivalent(unittest.TestCase):
    """`equivalent(a, b)` is `normalize(a) == normalize(b)`."""

    def test_equivalent(self):
        equivalent = _api("equivalent")
        self.assertIs(equivalent("HTTP://a:80/%7e", "http://A/~"), True)
        self.assertIs(equivalent("http://a", "http://a/"), True)
        self.assertIs(equivalent("http://a/b/../c", "http://a/c"), True)
        self.assertIs(equivalent("http://a/%2f", "http://a/%2F"), True)

    def test_not_equivalent(self):
        equivalent = _api("equivalent")
        self.assertIs(equivalent("http://a/b", "http://a/B"), False)
        self.assertIs(equivalent("http://a/?", "http://a/"), False)
        self.assertIs(equivalent("http://a/%2F", "http://a//"), False)
        self.assertIs(equivalent("foo://a", "foo://a/"), False)
        self.assertIs(equivalent("https://a:80/", "https://a/"), False)

    def test_errors(self):
        equivalent = _api("equivalent")
        with self.assertRaises(UriError):
            equivalent("a/b", "a/b")
        with self.assertRaises(UriError):
            equivalent("http://a/", "http://a b/")


class Req09_collect_links(unittest.TestCase):
    """`collect_links(base, hrefs)`: base must be a valid absolute URI (UriError otherwise); each
    href is stripped of leading/trailing ASCII whitespace (space, tab, LF, CR, FF), resolved
    against base, has its fragment removed, and is normalised; invalid hrefs are silently
    skipped, as are links whose (normalised) scheme is not http/https; duplicates (after
    normalisation) are dropped keeping the first occurrence."""

    def test_invalid_base(self):
        for base in ("http://a b/", "/x", "//a/b", "", "%zz", None):
            with self.subTest(base=base):
                with self.assertRaises(UriError):
                    collect_links(base, ["a"])

    def test_basic(self):
        got = collect_links("http://a/x/y", ["z", "/z#top", "mailto:me@x", "http://b/", "z"])
        self.assertEqual(got, ["http://a/x/z", "http://a/z", "http://b/"])

    def test_dot_segments_resolved(self):
        self.assertEqual(collect_links("http://a/b/c/d", ["../g", "../../../../h"]),
                         ["http://a/b/g", "http://a/h"])

    def test_whitespace_stripped(self):
        got = collect_links("http://a/x/y", [" \t\n\r\fz \n\r\t\f", "  /q  "])
        self.assertEqual(got, ["http://a/x/z", "http://a/q"])

    def test_non_ascii_whitespace_not_stripped(self):
        got = collect_links("http://a/x/y", ["\u00a0z", "\x0bz", "z\u3000", "ok"])
        self.assertEqual(got, ["http://a/x/ok"])

    def test_fragment_removed(self):
        got = collect_links("http://a/x/y", ["p#frag", "q#", "#only"])
        self.assertEqual(got, ["http://a/x/p", "http://a/x/q", "http://a/x/y"])

    def test_empty_href_and_base_fragment(self):
        self.assertEqual(collect_links("http://a/b#f", ["", "   "]), ["http://a/b"])

    def test_normalised(self):
        got = collect_links("http://a/x/y", ["HTTP://B:80/%7e/./c", "HTTPS://C", "/%2e%2e/%7a"])
        self.assertEqual(got, ["http://b/~/c", "https://c/", "http://a/z"])

    def test_invalid_hrefs_skipped(self):
        got = collect_links("http://a/x/y", ["a b", "http://[x]/", "%zz", "<p>", "good", "x|y"])
        self.assertEqual(got, ["http://a/x/good"])

    def test_scheme_filter(self):
        got = collect_links("http://a/x/y",
                            ["mailto:me@x", "ftp://f/", "javascript:void(0)", "HTTPS://s/",
                             "Http://h/", "ws://w/", "urn:x:y"])
        self.assertEqual(got, ["https://s/", "http://h/"])

    def test_non_http_base(self):
        got = collect_links("ftp://a/b", ["c", "http://x"])
        self.assertEqual(got, ["http://x/"])

    def test_strict_http_g(self):
        self.assertEqual(collect_links("http://a/b/c", ["http:g"]), ["http:g"])

    def test_duplicates_after_normalisation(self):
        got = collect_links("http://a/x/y",
                            ["z", "./z#f", "HTTP://A:80/x/z", "http://a/x/%7a", "w",
                             "http://a/x/../x/z", "w#2"])
        self.assertEqual(got, ["http://a/x/z", "http://a/x/w"])

    def test_empty(self):
        self.assertEqual(collect_links("http://a/", []), [])


class Req10_package_exports(unittest.TestCase):
    """Export `resolve`, `normalize`, `equivalent` and `remove_dot_segments` from the package."""

    def test_exports(self):
        for name in ("resolve", "normalize", "equivalent", "remove_dot_segments"):
            with self.subTest(name=name):
                self.assertTrue(hasattr(urikit, name))
                self.assertTrue(callable(getattr(urikit, name)))

    def test_from_import(self):
        from urikit import equivalent, normalize, remove_dot_segments, resolve  # noqa: F401


if __name__ == "__main__":
    unittest.main()
