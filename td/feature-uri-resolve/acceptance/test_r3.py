"""Acceptance tests for the RFC 3986 version of urikit."""
import unittest

import urikit
from urikit import Uri, UriError, parse


def resolve(base, ref):
    return urikit.resolve(base, ref)


def normalize(text):
    return urikit.normalize(text)


def equivalent(a, b):
    return urikit.equivalent(a, b)


def remove_dot_segments(path):
    return urikit.remove_dot_segments(path)


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


class _Helpers(unittest.TestCase):
    def assertValid(self, text):
        try:
            u = parse(text)
        except UriError as e:  # pragma: no cover - failure path
            self.fail("parse(%r) raised UriError: %s" % (text, e))
        return u

    def assertInvalid(self, text):
        with self.assertRaises(UriError, msg="parse(%r) should raise UriError" % (text,)):
            parse(text)


class Req01_parse_validates(_Helpers):
    """parse(text) validates and raises UriError (a ValueError) for text that is not a valid
    URI-reference; a non-string is a UriError."""

    def test_uri_error_is_value_error(self):
        self.assertTrue(issubclass(UriError, ValueError))

    def test_invalid_text_raises(self):
        self.assertInvalid("http://a/b c")
        with self.assertRaises(ValueError):
            parse("http://a/b c")

    def test_non_string_raises_uri_error(self):
        for value in (None, 42, b"http://a/", ["http://a/"], 3.5):
            with self.subTest(value=value):
                with self.assertRaises(UriError):
                    parse(value)

    def test_valid_text_parses(self):
        self.assertIsInstance(self.assertValid("http://a/b"), Uri)


class Req02_split_and_recompose(_Helpers):
    """The split is RFC appendix B; Uri is a namedtuple (scheme, authority, path, query,
    fragment) with None for absent and "" for present-but-empty parts; str(uri) recomposes per
    5.3 so str(parse(s)) == s for every valid s."""

    def test_components(self):
        self.assertEqual(
            parse("foo://example.com:8042/over/there?name=ferret#nose"),
            Uri("foo", "example.com:8042", "/over/there", "name=ferret", "nose"),
        )
        self.assertEqual(parse("urn:example:animal:ferret:nose"),
                         Uri("urn", None, "example:animal:ferret:nose", None, None))
        self.assertEqual(parse(""), Uri(None, None, "", None, None))
        self.assertEqual(parse("//h?#"), Uri(None, "h", "", "", ""))
        self.assertEqual(parse("http://h?a/b?c#d/e?f"), Uri("http", "h", "", "a/b?c", "d/e?f"))
        self.assertEqual(parse("file:///etc"), Uri("file", "", "/etc", None, None))

    def test_namedtuple_fields(self):
        u = parse("http://a/b?c#d")
        self.assertIsInstance(u, tuple)
        self.assertEqual(Uri._fields, ("scheme", "authority", "path", "query", "fragment"))
        self.assertEqual((u.scheme, u.authority, u.path, u.query, u.fragment),
                         ("http", "a", "/b", "c", "d"))

    def test_roundtrip(self):
        samples = [
            "", "#", "?", "?#", "//", "///", "a", "a/b:c", "./a:b", "?a:b", "#a:b",
            "http://a/b/c/d;p?q", "mailto:John.Doe@example.com",
            "urn:oasis:names:specification:docbook:dtd:xml:4.1.2",
            "tel:+1-816-555-1212", "ldap://[2001:db8::7]/c=GB?objectClass?one",
            "news:comp.infosystems.www.servers.unix", "telnet://192.0.2.16:80/",
            "foo://example.com:8042/over/there?name=ferret#nose", "http://h?a/b?c#d/e?f",
            "//u:p@h:/p", "http://[v7.a:b]/", "HTTP://EXAMPLE.com/%7e%41", "http:", "http:g",
            "file:///x", "//@:/", "a+b-c.d:x", "http://h/?#",
        ]
        for s in samples:
            with self.subTest(s=s):
                self.assertEqual(str(self.assertValid(s)), s)


class Req03_scheme_syntax(_Helpers):
    """The scheme (text before the first ':' when it comes before any / ? #) must match
    ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )."""

    def test_valid_schemes(self):
        for s in ("http://h", "HTTP://h", "a:", "a1+-.z:x", "z.9:b"):
            with self.subTest(s=s):
                self.assertValid(s)
        self.assertEqual(parse("a1+-.z:x").scheme, "a1+-.z")

    def test_invalid_schemes(self):
        for s in ("1a:b", "-a:b", "+a:b", ".a:b", "a_b:c", "a b:c", "a%41:b", "\u00e9:x", ":foo"):
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req04_first_segment_colon(_Helpers):
    """Without a scheme and authority the first path segment must not contain ':'."""

    def test_colon_in_later_segment_ok(self):
        for s in ("a/b:c", "./a:b", "/a:b", "?x:y", "#x:y", "//h/a:b"):
            with self.subTest(s=s):
                self.assertValid(s)

    def test_colon_in_first_segment_rejected(self):
        for s in (":a", ":", "1a:b", "_x:y/z", "9:00"):
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req05_userinfo(_Helpers):
    """userinfo is *( unreserved / pct-encoded / sub-delims / ":" )."""

    def test_valid(self):
        for s in ("http://u@h", "http://u:p@h", "http://@h", "http://a-._~%41!$&'()*+,;=:@h",
                  "http://::@h"):
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ("http://u p@h", "http://u[@h", "http://u]@h", "http://u%@h",
                  "http://u%4@h", "http://u<@h", "http://\u00fc@h", "http://u^@h"):
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req06_host(_Helpers):
    """The host is a reg-name (unreserved / pct-encoded / sub-delims) or an IP-literal in
    brackets whose content is IPv6-ish (only hex digits, ':' and '.', with at least two ':') or
    IPvFuture ('v' HEXDIG+ '.' then one or more of unreserved / sub-delims / ':')."""

    def test_valid_reg_names(self):
        for s in ("http://example.com", "http://a-b.c_d~e!$&'()*+,;=%41", "http://", "http:///p",
                  "http://192.0.2.16", "http://EX%c3%a9"):
            with self.subTest(s=s):
                self.assertValid(s)


    def test_invalid_ip_literals(self):
        for s in ("http://[]", "http://[1]", "http://[1:2]x", "http://[::g]", "http://[::1",
                  "http://::1]", "http://[fe80::1%25eth0]", "http://[v.x]", "http://[v1.]",
                  "http://[v1x.a]", "http://[vg.a]", "http://[v1.a/b]", "http://[v1.%41]",
                  "http://[ ::1]", "http://[[::1]]", "http://a[::1]"):
            with self.subTest(s=s):
                self.assertInvalid(s)

    def test_invalid_reg_names(self):
        for s in ("http://a@b@c", "http://h b", "http://h]", "http://h[", "http://h%", "http://h%g0",
                  "http://h\u00e9", "http://h<", "http://h|"):
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req07_port(_Helpers):
    """The port is digits only (possibly empty)."""

    def test_valid(self):
        for s in ("http://h:80", "http://h:", "http://h:/", "http://h:00081", "http://[::1]:8080/",
                  "//u@:8"):
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ("http://h:80a", "http://h:a", "http://h:-1", "http://h: 80", "http://h:+80",
                  "http://h:1:2", "http://h:%38%30", "http://h:\u0661"):
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req08_path_query_fragment_chars(_Helpers):
    """Path characters are pchar and '/'; query and fragment are pchar, '/' and '?'."""

    def test_valid(self):
        for s in ("/a-._~%41!$&'()*+,;=:@/b", "a//b", "http://h/@:", "?/?:@!$&'()*+,;=-._~%20",
                  "#/?:@!$&'()*+,;=-._~%20", "http://h/p?a?b/c#d?e/f"):
            with self.subTest(s=s):
                self.assertValid(s)

    def test_hash_not_allowed_in_fragment(self):
        self.assertInvalid("http://h/#a#b")

    def test_brackets_outside_ip_literal(self):
        for s in ("/a[b", "/a]b", "?a[0]=1", "#[x]", "http://h/[::1]"):
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req09_percent_encoding(_Helpers):
    """Every '%' must be followed by two hex digits."""

    def test_valid(self):
        for s in ("/%41%7e%7E%fF", "?%00", "#%2f", "http://%41@%42/%43?%44#%45"):
            with self.subTest(s=s):
                self.assertValid(s)

    def test_invalid(self):
        for s in ("%", "/%", "/%4", "/%4g", "/%g4", "?%", "?%zz", "#%1", "/a%2", "/%%41", "http://u%@h"):
            with self.subTest(s=s):
                self.assertInvalid(s)


class Req10_forbidden_characters(_Helpers):
    """Anything else (spaces, < > " { } | ^, backslash, backtick, non-ASCII, [ ] outside an IP
    literal, @ in the host, ...) is a UriError."""

    def test_forbidden_characters_everywhere(self):
        for ch in " <>\"{}|^\\`\t\n\r\x00\x7f\u00e9\u20ac[]":
            for template in ("http://h/a%sb", "http://h/?a%sb", "http://h/#a%sb", "a%sb"):
                s = template % ch
                with self.subTest(s=s):
                    self.assertInvalid(s)

    def test_at_in_host(self):
        self.assertInvalid("http://a@b@c/")

    def test_trailing_whitespace(self):
        self.assertInvalid("http://h/ ")
        self.assertInvalid(" http://h/")
        self.assertInvalid("http://h/\n")


class Req11_component_properties(_Helpers):
    """Uri gains userinfo, host (as written, brackets included; "" for an empty host), port (int;
    None if absent or empty) - all None without an authority - and keeps is_absolute."""

    def test_full_authority(self):
        u = parse("http://User:Pw@ExAmple.COM:8080/p")
        self.assertEqual(u.userinfo, "User:Pw")
        self.assertEqual(u.host, "ExAmple.COM")
        self.assertEqual(u.port, 8080)
        self.assertIsInstance(u.port, int)

    def test_ip_literal_host(self):
        u = parse("http://u@[::1]:8/")
        self.assertEqual(u.host, "[::1]")
        self.assertEqual(u.port, 8)
        self.assertEqual(parse("http://[v1.fe]").host, "[v1.fe]")

    def test_port_values(self):
        self.assertIsNone(parse("http://h").port)
        self.assertIsNone(parse("http://h:").port)
        self.assertIsNone(parse("http://h:/x").port)
        self.assertEqual(parse("http://h:0080").port, 80)
        self.assertEqual(parse("http://h:0").port, 0)

    def test_userinfo_absent_or_empty(self):
        self.assertIsNone(parse("http://h/").userinfo)
        self.assertEqual(parse("http://@h/").userinfo, "")

    def test_empty_host(self):
        self.assertEqual(parse("file:///x").host, "")
        u = parse("//u@:8")
        self.assertEqual((u.userinfo, u.host, u.port), ("u", "", 8))
        self.assertEqual(parse("http://").host, "")

    def test_no_authority(self):
        for s in ("mailto:a@b", "/a", "a", "", "?q", "http:g"):
            u = parse(s)
            with self.subTest(s=s):
                self.assertIsNone(u.userinfo)
                self.assertIsNone(u.host)
                self.assertIsNone(u.port)

    def test_is_absolute(self):
        self.assertTrue(parse("http://a").is_absolute)
        self.assertTrue(parse("mailto:x").is_absolute)
        self.assertFalse(parse("//a/b").is_absolute)
        self.assertFalse(parse("a/b").is_absolute)


class Req12_remove_dot_segments(unittest.TestCase):
    """remove_dot_segments(path) is exactly the algorithm of section 5.2.4 (a/../../b -> /b)."""

    def test_cases(self):
        cases = [
            ("/a/b/c/./../../g", "/a/g"),
            ("mid/content=5/../6", "mid/6"),
            ("a/../../b", "/b"),
            ("a/b/../../../c", "/c"),
            ("/a/b/../../../c", "/c"),
            ("../a", "a"),
            ("./a", "a"),
            ("../../a", "a"),
            (".", ""),
            ("..", ""),
            ("/.", "/"),
            ("/..", "/"),
            ("/a/..", "/"),
            ("a/..", "/"),
            ("a/.", "a/"),
            ("/a/b/..", "/a/"),
            ("/a/./b", "/a/b"),
            ("/../a", "/a"),
            ("/a//../b", "/a/b"),
            ("/a/.../b", "/a/.../b"),
            ("/a/..b/.c", "/a/..b/.c"),
            (".../a", ".../a"),
            ("", ""),
            ("/", "/"),
            ("abc", "abc"),
            ("/a/b/c", "/a/b/c"),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                self.assertEqual(remove_dot_segments(path), expected)


class Req13_resolve_strict(unittest.TestCase):
    """resolve(base, ref) on strings: strict 5.2.2 with merge (5.2.3) and recomposition (5.3);
    base fragment ignored."""

    def test_returns_string(self):
        self.assertIsInstance(resolve("http://a/b", "c"), str)

    def test_base_fragment_ignored(self):
        self.assertEqual(resolve("http://a/b?q#f", ""), "http://a/b?q")
        self.assertEqual(resolve("http://a/b#f", "#s"), "http://a/b#s")
        self.assertEqual(resolve("http://a/b#f", "c"), "http://a/c")

    def test_ref_paths_get_dot_segments_removed(self):
        self.assertEqual(resolve("http://a/b", "//g/a/../b"), "http://g/b")
        self.assertEqual(resolve("http://a/b", "/a/./b/../c"), "http://a/a/c")
        self.assertEqual(resolve("http://a/b", "x:/a/./b/../c"), "x:/a/c")

    def test_merge(self):
        self.assertEqual(resolve("http://a", "g"), "http://a/g")
        self.assertEqual(resolve("http://a?q", "g"), "http://a/g")
        self.assertEqual(resolve("foo:a/b", "c"), "foo:a/c")
        self.assertEqual(resolve("foo:a", "c"), "foo:c")
        self.assertEqual(resolve("foo:", "c"), "foo:c")
        self.assertEqual(resolve("foo:a/b", "../../c"), "foo:/c")

    def test_empty_ref_and_query(self):
        self.assertEqual(resolve("http://a/b?q", "?"), "http://a/b?")
        self.assertEqual(resolve("http://a/b?q", "#"), "http://a/b?q#")
        self.assertEqual(resolve("http://a/b", "//h"), "http://h")


class Req14_resolve_validation(unittest.TestCase):
    """Both base and ref are validated (UriError); base must have a scheme."""

    def test_invalid_ref(self):
        for ref in ("a b", "%zz", "http://[::1", ":x"):
            with self.subTest(ref=ref):
                with self.assertRaises(UriError):
                    resolve("http://a/b", ref)

    def test_invalid_base(self):
        with self.assertRaises(UriError):
            resolve("http://a/ b", "c")
        with self.assertRaises(UriError):
            resolve(None, "c")

    def test_base_without_scheme(self):
        for base in ("//a/b", "/a/b", "a/b", ""):
            with self.subTest(base=base):
                with self.assertRaises(UriError):
                    resolve(base, "c")


class Req15_resolve_does_not_normalize(unittest.TestCase):
    """Scheme and host case, percent-encoding and so on are NOT touched by resolve."""

    def test_untouched(self):
        self.assertEqual(resolve("HTTP://A.COM/b/%7e", "c"), "HTTP://A.COM/b/c")
        self.assertEqual(resolve("http://a/b", "%7e/%41"), "http://a/%7e/%41")
        self.assertEqual(resolve("http://a/b", "HTTPS://X.Y:443/%7E?%41#%42"),
                         "HTTPS://X.Y:443/%7E?%41#%42")
        self.assertEqual(resolve("HTTP://A:80/b?Q", ""), "HTTP://A:80/b?Q")
        self.assertEqual(resolve("http://a/b", "/%2e%2e/x"), "http://a/%2e%2e/x")
        self.assertEqual(resolve("http://a", ""), "http://a")


class Req16_join_is_resolve(unittest.TestCase):
    """join(base, ref) stays and is now identical to resolve."""

    def test_same_results(self):
        pairs = [("http://a/b/c/d", "../e"), ("http://a/b", "HTTP://X/./y"), ("foo:a/b", "../../c"),
                 ("http://a/b#f", "")] + [(RFC_BASE, r) for r, _ in RFC_EXAMPLES]
        for base, ref in pairs:
            with self.subTest(base=base, ref=ref):
                self.assertEqual(urikit.join(base, ref), resolve(base, ref))
        self.assertEqual(urikit.join("http://a/b/c/d", "../e"), "http://a/b/e")

    def test_same_errors(self):
        with self.assertRaises(UriError):
            urikit.join("//a/b", "c")
        with self.assertRaises(UriError):
            urikit.join("http://a/", "a b")


class Req17_rfc_examples(unittest.TestCase):
    """All examples of RFC 3986 section 5.4 hold (http:g stays http:g in strict mode)."""

    def test_examples(self):
        for ref, expected in RFC_EXAMPLES:
            with self.subTest(ref=ref):
                self.assertEqual(resolve(RFC_BASE, ref), expected)


class Req18_normalize_requires_absolute(unittest.TestCase):
    """normalize(text): input must be an absolute URI, else UriError."""

    def test_rejects(self):
        for s in ("/a", "//h/a", "a", "", "?q", "#f", "http://h/ x", "http://[::1", None):
            with self.subTest(s=s):
                with self.assertRaises(UriError):
                    normalize(s)

    def test_accepts(self):
        self.assertIsInstance(normalize("http://h/"), str)


class Req19_normalize_scheme_case(unittest.TestCase):
    """(1) lowercase the scheme."""

    def test_scheme(self):
        self.assertEqual(normalize("HTTP://h/"), "http://h/")
        self.assertEqual(normalize("MailTo:A@B"), "mailto:A@B")
        self.assertEqual(normalize("X-Y+Z.1:a"), "x-y+z.1:a")


class Req20_normalize_percent_and_host_case(unittest.TestCase):
    """(2) in every component uppercase percent-encoding hex digits and decode unreserved
    characters, then lowercase the host (percent hex stays uppercase); userinfo, path, query,
    fragment keep their case."""

    def test_path(self):
        self.assertEqual(normalize("http://h/%7e%41%2f%2F%3a"), "http://h/~A%2F%2F%3A")
        self.assertEqual(normalize("http://h/%2D%2e%5f%7E%30%7a"), "http://h/-._~0z")
        self.assertEqual(normalize("http://h/%20%25%c3%a9"), "http://h/%20%25%C3%A9")
        self.assertEqual(normalize("http://h/A/B"), "http://h/A/B")

    def test_query_and_fragment(self):
        self.assertEqual(normalize("http://h/?Q=%7e%3d%41#F%41%2f%7e"), "http://h/?Q=~%3DA#FA%2F~")

    def test_userinfo(self):
        self.assertEqual(normalize("http://%41b%3a:Pw@h/"), "http://Ab%3A:Pw@h/")

    def test_host(self):
        self.assertEqual(normalize("http://ExAmple.COM/"), "http://example.com/")
        self.assertEqual(normalize("http://%41.com/"), "http://a.com/")
        self.assertEqual(normalize("http://%7EA%c3%a9.COM/"), "http://~a%C3%A9.com/")
        self.assertEqual(normalize("http://[::ABCD]/"), "http://[::abcd]/")
        self.assertEqual(normalize("http://[vF.AB]/"), "http://[vf.ab]/")

    def test_other_scheme_without_authority(self):
        self.assertEqual(normalize("urn:A%3a%62"), "urn:A%3Ab")


class Req21_normalize_dot_segments(unittest.TestCase):
    """(3) remove_dot_segments on the path; percent-decoding happens before (/%2e%2e/ is a dot
    segment)."""

    def test_dot_segments(self):
        self.assertEqual(normalize("http://h/a/./b/../c"), "http://h/a/c")
        self.assertEqual(normalize("http://h/../../x"), "http://h/x")
        self.assertEqual(normalize("http://h/a/b/.."), "http://h/a/")

    def test_decoded_dots(self):
        self.assertEqual(normalize("http://h/%2e%2e/a"), "http://h/a")
        self.assertEqual(normalize("http://h/a/%2E%2e/b"), "http://h/b")
        self.assertEqual(normalize("http://h/a/%2E"), "http://h/a/")
        self.assertEqual(normalize("http://h/a/.%2e/b"), "http://h/b")

    def test_query_fragment_not_touched(self):
        self.assertEqual(normalize("http://h/a?/./b/../c#/./x/.."), "http://h/a?/./b/../c#/./x/..")


class Req22_normalize_default_port(unittest.TestCase):
    """(4) drop the port when empty or equal to the scheme default (http 80, https 443, ftp 21,
    ws 80, wss 443); other ports kept exactly as written."""

    def test_defaults_dropped(self):
        cases = [
            ("http://h:80/", "http://h/"),
            ("https://h:443/x", "https://h/x"),
            ("ftp://h:21/", "ftp://h/"),
            ("ws://h:80/", "ws://h/"),
            ("wss://h:443/", "wss://h/"),
            ("http://h:080/", "http://h/"),
            ("HTTP://h:80/", "http://h/"),
            ("http://u@h:80/p", "http://u@h/p"),
            ("http://[::1]:80/", "http://[::1]/"),
        ]
        for s, expected in cases:
            with self.subTest(s=s):
                self.assertEqual(normalize(s), expected)

    def test_empty_port_dropped(self):
        for s, expected in (("http://h:/", "http://h/"), ("https://h:/a", "https://h/a"),
                            ("ws://h:/", "ws://h/")):
            with self.subTest(s=s):
                self.assertEqual(normalize(s), expected)

    def test_other_ports_kept(self):
        cases = [
            ("http://h:443/", "http://h:443/"),
            ("https://h:80/", "https://h:80/"),
            ("http://h:00081/", "http://h:00081/"),
            ("http://h:8080/", "http://h:8080/"),
            ("ftp://h:80/", "ftp://h:80/"),
            ("foo://h:80/", "foo://h:80/"),
        ]
        for s, expected in cases:
            with self.subTest(s=s):
                self.assertEqual(normalize(s), expected)


class Req23_normalize_empty_path(unittest.TestCase):
    """(4) for http, https, ftp, ws, wss an empty path becomes '/' when an authority is present."""

    def test_empty_path(self):
        cases = [
            ("http://h", "http://h/"),
            ("https://h:443", "https://h/"),
            ("ftp://h", "ftp://h/"),
            ("ws://h", "ws://h/"),
            ("WSS://H", "wss://h/"),
            ("http://h?q", "http://h/?q"),
            ("http://h#f", "http://h/#f"),
            ("foo://h", "foo://h"),
            ("http:", "http:"),
            ("http:?x", "http:?x"),
        ]
        for s, expected in cases:
            with self.subTest(s=s):
                self.assertEqual(normalize(s), expected)


class Req24_normalize_keeps_empty_query_fragment(unittest.TestCase):
    """An empty query '?' / empty fragment '#' are kept."""

    def test_kept(self):
        self.assertEqual(normalize("http://h/?"), "http://h/?")
        self.assertEqual(normalize("http://h/#"), "http://h/#")
        self.assertEqual(normalize("http://h?#"), "http://h/?#")
        self.assertEqual(normalize("foo:x?"), "foo:x?")


class Req25_equivalent(unittest.TestCase):
    """equivalent(a, b) is normalize(a) == normalize(b)."""

    def test_true(self):
        self.assertIs(equivalent("HTTP://Example.COM:80/%7euser/./x", "http://example.com/~user/x"), True)
        self.assertIs(equivalent("http://h", "http://h:/"), True)
        self.assertIs(equivalent("http://h/%2e%2e/a", "http://h/a"), True)

    def test_false(self):
        self.assertIs(equivalent("http://h/a", "http://h/A"), False)
        self.assertIs(equivalent("http://h/%2F", "http://h//"), False)
        self.assertIs(equivalent("http://h/", "http://h/?"), False)
        self.assertIs(equivalent("http://h:81/", "http://h/"), False)

    def test_invalid_input(self):
        with self.assertRaises(UriError):
            equivalent("/a", "/a")


class Req26_collect_links_base(unittest.TestCase):
    """collect_links: base must be a valid absolute URI (UriError otherwise)."""

    def test_invalid_base(self):
        for base in ("/rel", "//h/a", "http://h/ x", "http://[::1"):
            with self.subTest(base=base):
                with self.assertRaises(UriError):
                    urikit.collect_links(base, ["a"])

    def test_valid_non_http_base(self):
        self.assertEqual(urikit.collect_links("ftp://h/d/", ["x", "http://a/"]), ["http://a/"])


class Req27_collect_links_whitespace(unittest.TestCase):
    """Each href is stripped of leading/trailing ASCII whitespace (space, tab, newline,
    carriage return, form feed)."""

    def test_stripped(self):
        got = urikit.collect_links("http://a/x/y", [" \t\n\r\fz\f\r\n\t ", "  /q  "])
        self.assertEqual(got, ["http://a/x/z", "http://a/q"])

    def test_other_whitespace_not_stripped(self):
        self.assertEqual(urikit.collect_links("http://a/x/y", ["\x0bz", "\u00a0z", "z\u3000"]), [])

    def test_inner_whitespace_invalid(self):
        self.assertEqual(urikit.collect_links("http://a/x/y", ["a b"]), [])


class Req28_collect_links_resolve_defrag_normalize(unittest.TestCase):
    """Each href is resolved against base, has its fragment removed and is normalised."""

    def test_pipeline(self):
        base = "http://a/x/y"
        self.assertEqual(urikit.collect_links(base, ["../Z/./%7e#f"]), ["http://a/Z/~"])
        self.assertEqual(urikit.collect_links(base, ["z#"]), ["http://a/x/z"])
        self.assertEqual(urikit.collect_links(base, ["HTTPS://Ex.COM:443"]), ["https://ex.com/"])
        self.assertEqual(urikit.collect_links(base, ["?"]), ["http://a/x/y?"])
        self.assertEqual(urikit.collect_links(base, ["/%2e%2e/q"]), ["http://a/q"])

    def test_base_normalised_through_result(self):
        self.assertEqual(urikit.collect_links("HTTP://A.com:80/x/y", ["z"]), ["http://a.com/x/z"])
        self.assertEqual(urikit.collect_links("http://a/b#f", [""]), ["http://a/b"])
        self.assertEqual(urikit.collect_links("http://a", ["#top"]), ["http://a/"])

    def test_existing_example(self):
        got = urikit.collect_links("http://a/x/y", ["z", "/z#top", "mailto:me@x", "http://b/", "z"])
        self.assertEqual(got, ["http://a/x/z", "http://a/z", "http://b/"])


class Req29_collect_links_skip_invalid(unittest.TestCase):
    """Hrefs that are invalid are silently skipped."""

    def test_skipped(self):
        got = urikit.collect_links("http://a/", ["ok", "a b", "%zz", "http://[::1", "http://h:x/",
                                                 "<x>", "\u00e9", ":x", "also"])
        self.assertEqual(got, ["http://a/ok", "http://a/also"])


class Req30_collect_links_scheme_filter(unittest.TestCase):
    """Links whose scheme (after normalisation) is not http or https are skipped."""

    def test_filter(self):
        got = urikit.collect_links("http://a/", ["mailto:a@b", "ftp://h/", "javascript:void(0)",
                                                 "file:///x", "ws://h/", "HTTP://h/x", "Https://h/y"])
        self.assertEqual(got, ["http://h/x", "https://h/y"])


class Req31_collect_links_dedup(unittest.TestCase):
    """Duplicates (after normalisation) are dropped keeping the first occurrence."""

    def test_dedup(self):
        got = urikit.collect_links("http://a/", ["http://a/x", "HTTP://A:80/x#y", "/x", "./x", "%78"])
        self.assertEqual(got, ["http://a/x"])

    def test_first_occurrence_order(self):
        got = urikit.collect_links("http://a/", ["b", "c", "B", "b#1", "c", "/b"])
        self.assertEqual(got, ["http://a/b", "http://a/c", "http://a/B"])


class Req32_exports(unittest.TestCase):
    """Export resolve, normalize, equivalent and remove_dot_segments from the package."""

    def test_exports(self):
        for name in ("resolve", "normalize", "equivalent", "remove_dot_segments", "join",
                     "parse", "Uri", "UriError", "collect_links"):
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(urikit, name, None)))

    def test_from_import(self):
        from urikit import equivalent, normalize, remove_dot_segments, resolve  # noqa: F401


if __name__ == "__main__":
    unittest.main()
