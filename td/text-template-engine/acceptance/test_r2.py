"""Acceptance tests for the extended tplr template engine."""

import unittest

from tplr import (
    Template,
    TemplateError,
    TemplateRenderError,
    TemplateSyntaxError,
    render,
)


class _Helpers:
    def assertSyntaxErrorAt(self, source, line, **ctx):
        """Template(source) must raise TemplateSyntaxError at ``line``."""
        with self.assertRaises(TemplateSyntaxError, msg=repr(source)) as cm:
            Template(source)
        self.assertEqual(cm.exception.line, line, msg=repr(source))

    def assertSyntaxError(self, source):
        with self.assertRaises(TemplateSyntaxError, msg=repr(source)):
            Template(source)

    def assertRenders(self, source, expected, **ctx):
        self.assertEqual(render(source, **ctx), expected, msg=repr(source))
        self.assertEqual(Template(source).render(**ctx), expected, msg=repr(source))

    def assertRenderError(self, source, **ctx):
        tpl = Template(source)  # must compile fine
        with self.assertRaises(TemplateRenderError, msg=repr(source)):
            tpl.render(**ctx)


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------


class Req01_public_api(_Helpers, unittest.TestCase):
    """Keep `Template(source).render(**ctx)`, `render(source, **ctx)` and the
    three exception classes."""

    def test_template_and_render(self):
        self.assertEqual(Template("Hi {{ name }}").render(name="Ada"), "Hi Ada")
        self.assertEqual(render("Hi {{ name }}", name="Ada"), "Hi Ada")

    def test_template_reusable(self):
        t = Template("{{ n }}")
        self.assertEqual(t.render(n=1), "1")
        self.assertEqual(t.render(n=2), "2")

    def test_exception_classes(self):
        self.assertTrue(issubclass(TemplateSyntaxError, TemplateError))
        self.assertTrue(issubclass(TemplateRenderError, TemplateError))
        self.assertTrue(issubclass(TemplateError, Exception))
        with self.assertRaises(TemplateError):
            Template("{% bogus %}")


class Req02_existing_templates(_Helpers, unittest.TestCase):
    """Existing templates must keep rendering as before."""

    def test_readme_example(self):
        self.assertEqual(
            render(
                "Hello {{ user.name|title }}!{% if admin %} (admin){% endif %}",
                user={"name": "ada"},
                admin=True,
            ),
            "Hello Ada! (admin)",
        )

    def test_vars_and_paths(self):
        self.assertRenders("Hi {{ name }}!", "Hi Ada!", name="Ada")
        self.assertRenders("{{ a.b.c }}", "5", a={"b": {"c": 5}})
        self.assertRenders("{{ xs.1 }}{{ xs.9 }}", "b", xs=["a", "b"])

        class Obj:
            title = "T"

        self.assertRenders("{{ o.title }}", "T", o=Obj())

    def test_filters(self):
        self.assertRenders(
            "{{ n|upper }} {{ n|title }}", "ADA LOVELACE Ada Lovelace", n="ada lovelace"
        )
        self.assertRenders("{{ xs|join }} {{ xs|length }}", "1, 2, 3 3", xs=[1, 2, 3])

    def test_blocks(self):
        t = Template("{% if x %}yes{% else %}no{% endif %}")
        self.assertEqual(t.render(x=1), "yes")
        self.assertEqual(t.render(x=0), "no")
        self.assertEqual(t.render(), "no")
        self.assertRenders("{% for x in xs %}<{{ x }}>{% endfor %}", "<1><2>", xs=[1, 2])
        self.assertRenders("{% for x in xs %}<{{ x }}>{% endfor %}", "")
        src = "{% for r in rows %}{% if r.ok %}{{ r.n }}{% else %}-{% endif %}{% endfor %}"
        self.assertRenders(src, "a-", rows=[{"ok": 1, "n": "a"}, {"ok": 0, "n": "b"}])

    def test_comment_and_plain_whitespace(self):
        self.assertRenders("a{# hidden #}b", "ab")
        self.assertRenders("a {{ x }} b\n", "a X b\n", x="X")

    def test_errors(self):
        self.assertSyntaxErrorAt("one\ntwo\n{% bogus %}", 3)
        self.assertSyntaxErrorAt("{% if x %}\nbody", 1)
        for bad in ["{% endif %}", "{% else %}", "{{ x|nope }}", "{% for x xs %}{% endfor %}"]:
            self.assertSyntaxError(bad)


# ---------------------------------------------------------------------------
# Lexing
# ---------------------------------------------------------------------------


class Req03_tag_ends_outside_quotes(_Helpers, unittest.TestCase):
    """A tag ends at the first closing delimiter (`}}`, `%}`, `#}`) that is not
    inside a quoted string, so `{{ x|default("}}") }}` works. Quotes are `"` or
    `'`; a backslash inside a string escapes the next character."""

    def test_double_quoted_delimiter(self):
        self.assertRenders('{{ x|default("}}") }}', "}}")

    def test_single_quoted_delimiter(self):
        self.assertRenders("{{ x|default('%}') }}", "%}")
        self.assertRenders("{{ x|default('#}') }}", "#}")

    def test_delimiter_in_block_tag(self):
        self.assertRenders('{% if x == "%}" %}yes{% endif %}', "yes", x="%}")
        self.assertRenders('{% if x == "%}" %}yes{% endif %}', "", x="y")

    def test_backslash_escapes_quote(self):
        self.assertRenders(r'{{ "a\"}}" }}', 'a"}}')
        self.assertRenders(r"{{ 'it\'s }}' }}", "it's }}")

    def test_backslash_escapes_backslash(self):
        self.assertRenders(r'{{ "a\\" }}b', "a\\b")

    def test_other_quote_kind_inside_string(self):
        self.assertRenders("""{{ "it's" }}""", "it's")
        self.assertRenders("""{{ 'say "hi"' }}""", 'say "hi"')


class Req04_comment_end(_Helpers, unittest.TestCase):
    """Comments (`{# ... #}`) end at the first `#}`."""

    def test_quotes_in_comment(self):
        self.assertRenders("a{# it's #}b", "ab")
        self.assertRenders('a{# "#} b', "a b")

    def test_other_delimiters_in_comment(self):
        self.assertRenders("a{# {{ x }} %} }} #}b", "ab")

    def test_multiline_comment(self):
        self.assertRenders("a{# one\ntwo #}b", "ab")


class Req05_unterminated_tag(_Helpers, unittest.TestCase):
    """An unterminated `{{`, `{%` or `{#` raises `TemplateSyntaxError` whose
    `line` is the line where it starts."""

    def test_unterminated_var(self):
        self.assertSyntaxErrorAt("{{ x", 1)
        self.assertSyntaxErrorAt("ab\n{{ x", 2)

    def test_unterminated_block_tag(self):
        self.assertSyntaxErrorAt("\n\n{% if x", 3)

    def test_unterminated_comment(self):
        self.assertSyntaxErrorAt("a\n{# c", 2)
        self.assertSyntaxErrorAt("a\n{# c\n\n", 2)

    def test_delimiter_hidden_in_string(self):
        self.assertSyntaxErrorAt('x\n{{ "}}" ', 2)
        self.assertSyntaxErrorAt("{{ '}} }}", 1)

    def test_after_multiline_tag(self):
        self.assertSyntaxErrorAt("{{\nx\n}}\n{{ y", 4)
        self.assertSyntaxErrorAt("{{ x }}\n{{ y\n\n", 2)


class Req06_whitespace_control(_Helpers, unittest.TestCase):
    """A `-` directly after the opening delimiter removes all whitespace at the
    end of the text just before the tag; a `-` directly before the closing
    delimiter removes whitespace at the start of the text just after it. Only
    adjacent literal text is affected. `line` numbers still refer to the
    original source."""

    def test_left_trim_var(self):
        self.assertRenders("a  \n\t{{- x }}", "aX", x="X")

    def test_right_trim_var(self):
        self.assertRenders("{{ x -}}  \n\t b", "Xb", x="X")

    def test_block_tags(self):
        src = "a \n {%- if t -%} \n yes \n {%- endif -%} \n b"
        self.assertRenders(src, "ayesb", t=True)
        self.assertRenders(src, "ab", t=False)

    def test_for_loop(self):
        src = "{% for x in xs -%}\n  {{ x }}\n{%- endfor %}"
        self.assertRenders(src, "12", xs=[1, 2])

    def test_comment(self):
        self.assertRenders("a \n{#- c -#}\n b", "ab")

    def test_only_trailing_whitespace_removed(self):
        self.assertRenders("a b {{- x }} c d", "a bX c d", x="X")
        self.assertRenders("a b {{ x -}} c d", "a b Xc d", x="X")

    def test_only_adjacent_text(self):
        self.assertRenders("a {{ y }}{{- x }}", "a YX", x="X", y="Y")
        self.assertRenders("{{ x -}}{{ y }} b", "XY b", x="X", y="Y")

    def test_values_not_trimmed(self):
        self.assertRenders(" {{- x -}} ", " v ", x=" v ")

    def test_no_dash_no_trim(self):
        self.assertRenders(" \n{{ x }} \n", " \nX \n", x="X")

    def test_line_numbers_original(self):
        self.assertSyntaxErrorAt("a\n\n  {{- x }}\n{% bogus %}", 4)
        self.assertSyntaxErrorAt("a\n  {%- if x -%}\n\n{% bogus %}{% endif %}", 4)
        self.assertSyntaxErrorAt("a\n\n{{- x|nope }}", 3)
        self.assertSyntaxErrorAt("x \n{{- y -}}\n\n{{ z", 4)


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


class Req07_operands(_Helpers, unittest.TestCase):
    """Operands: variable paths (`user.name`, `items.0`; missing -> `None`,
    printed as empty string), string literals with escapes `\\n`, `\\t` and
    `\\x` -> `x`, integers, floats (`-3`, `2.5`), and `true`, `false`, `none`.
    Expressions are used by `{{ }}`, `{% if %}`, `{% elif %}` and `{% for %}`."""

    def test_paths(self):
        self.assertRenders("{{ user.name }}", "Ada", user={"name": "Ada"})
        self.assertRenders("{{ items.0 }}", "a", items=["a", "b"])
        self.assertRenders("[{{ missing }}][{{ a.b.c }}]", "[][]")
        self.assertRenders("[{{ user.nope }}]", "[]", user={"name": "Ada"})

    def test_string_literals(self):
        self.assertRenders('{{ "abc" }}', "abc")
        self.assertRenders("{{ 'abc' }}", "abc")
        self.assertRenders(r'{{ "a\nb" }}', "a\nb")
        self.assertRenders(r"{{ 'a\tb' }}", "a\tb")
        self.assertRenders(r'{{ "\q\"\\" }}', 'q"\\')

    def test_numbers(self):
        self.assertRenders("{{ 42 }}", "42")
        self.assertRenders("{{ -3 }}", "-3")
        self.assertRenders("{{ 2.5 }}", "2.5")
        self.assertRenders("{{ -0.5 }}", "-0.5")

    def test_number_types(self):
        self.assertRenders("{{ x == 3 }}", "True", x=3)
        self.assertRenders("{{ x == 3 }}", "False", x="3")
        self.assertRenders("{{ x == 2.5 }}", "True", x=2.5)
        self.assertRenders("{{ x == -3 }}", "True", x=-3)

    def test_keywords(self):
        self.assertRenders("{{ true }}", "True")
        self.assertRenders("{{ false }}", "False")
        self.assertRenders("[{{ none }}]", "[]")
        self.assertRenders("{{ x == none }}", "True")
        self.assertRenders("{{ x == true }}", "True", x=True)
        self.assertRenders("{{ x == false }}", "True", x=False)

    def test_in_if_elif_for(self):
        self.assertRenders("{% if true %}y{% endif %}", "y")
        self.assertRenders("{% if false %}a{% elif 1 %}b{% endif %}", "b")
        self.assertRenders('{% for c in "ab" %}<{{ c }}>{% endfor %}', "<a><b>")


class Req08_filter_syntax(_Helpers, unittest.TestCase):
    """Filters: `operand|name` or `operand|name(arg, ...)` with literal
    arguments, chainable (`x|trim|upper`), binding tighter than anything else."""

    def test_chain(self):
        self.assertRenders("{{ x|trim|upper }}", "ADA", x="  ada ")

    def test_arguments(self):
        self.assertRenders('{{ x|replace("a", "o") }}', "bob", x="bab")
        self.assertRenders("{{ x|default('d') }}", "d")
        self.assertRenders("{{ x|default(-1) }}", "-1")
        self.assertRenders("{{ x|default(2.5) }}", "2.5")
        self.assertRenders("{{ x|default(true) }}", "True")

    def test_filter_on_literal(self):
        self.assertRenders('{{ "abc"|upper }}', "ABC")

    def test_binds_tighter_than_comparison(self):
        self.assertRenders("{{ xs|length > 2 }}", "True", xs=[1, 2, 3])
        self.assertRenders('{{ "b" in xs|join("") }}', "True", xs=["a", "b"])
        self.assertRenders('{% if name|lower == "ada" %}y{% endif %}', "y", name="ADA")

    def test_binds_tighter_than_not(self):
        self.assertRenders("{{ not x|length }}", "True", x="")

    def test_in_for(self):
        self.assertRenders(
            "{% for x in rows|first %}{{ x }}{% endfor %}", "12", rows=[[1, 2], [3]]
        )


class Req09_text_filters(_Helpers, unittest.TestCase):
    """`upper lower title trim` (a `None` input counts as `""`)."""

    def test_values(self):
        self.assertRenders("{{ x|upper }}", "ABC", x="aBc")
        self.assertRenders("{{ x|lower }}", "abc", x="aBc")
        self.assertRenders("{{ x|title }}", "Ada Lovelace", x="ada lovelace")
        self.assertRenders("[{{ x|trim }}]", "[a b]", x=" \t a b \n")

    def test_none(self):
        for name in ("upper", "lower", "title", "trim"):
            self.assertRenders("{{ x|%s == '' }}" % name, "True")
            self.assertRenders("{{ x|%s|length }}" % name, "0")


class Req10_length_filter(_Helpers, unittest.TestCase):
    """`length` (`None` -> 0)."""

    def test_length(self):
        self.assertRenders("{{ x|length }}", "3", x="abc")
        self.assertRenders("{{ x|length }}", "2", x=[1, 2])
        self.assertRenders("{{ x|length }}", "1", x={"a": 1})
        self.assertRenders("{{ x|length }}", "0")
        self.assertRenders("{{ x|length == 0 }}", "True", x=None)


class Req11_join_filter(_Helpers, unittest.TestCase):
    """`join` (optional separator argument, default `", "`; `None` -> `""`)."""

    def test_default_separator(self):
        self.assertRenders("{{ x|join }}", "a, b, c", x=["a", "b", "c"])

    def test_separator(self):
        self.assertRenders('{{ x|join("-") }}', "a-b", x=["a", "b"])
        self.assertRenders('{{ x|join("") }}', "ab", x=["a", "b"])

    def test_none(self):
        self.assertRenders('{{ x|join == "" }}', "True")
        self.assertRenders('{{ x|join("-") == "" }}', "True")


class Req12_default_filter(_Helpers, unittest.TestCase):
    """`default(v)` returns `v` when the input is `None` or `""`, otherwise the
    input, so `0` and `false` are kept."""

    def test_replaced(self):
        self.assertRenders('{{ x|default("d") }}', "d")
        self.assertRenders('{{ x|default("d") }}', "d", x=None)
        self.assertRenders('{{ x|default("d") }}', "d", x="")
        self.assertRenders("{{ x|default(5) == 5 }}", "True")

    def test_kept(self):
        self.assertRenders('{{ x|default("d") }}', "0", x=0)
        self.assertRenders('{{ x|default("d") }}', "False", x=False)
        self.assertRenders('{{ x|default("d") }}', "v", x="v")
        self.assertRenders('{{ x|default("d")|length }}', "0", x=[])


class Req13_truncate_filter(_Helpers, unittest.TestCase):
    """`truncate(n)`: unchanged if it fits, else the first `n-3` characters +
    `"..."`, with `n-3` floored at 0."""

    def test_fits(self):
        self.assertRenders("{{ x|truncate(5) }}", "hello", x="hello")
        self.assertRenders("{{ x|truncate(10) }}", "hello", x="hello")
        self.assertRenders("{{ x|truncate(3) }}", "abc", x="abc")

    def test_truncated(self):
        self.assertRenders("{{ x|truncate(4) }}", "h...", x="hello")
        self.assertRenders("{{ x|truncate(8) }}", "hello...", x="hello world")
        self.assertRenders("{{ x|truncate(3) }}", "...", x="hello")


class Req14_replace_filter(_Helpers, unittest.TestCase):
    """`replace(old, new)`."""

    def test_replace(self):
        self.assertRenders('{{ x|replace("-", "+") }}', "a+b+c", x="a-b-c")
        self.assertRenders('{{ x|replace("z", "+") }}', "abc", x="abc")
        self.assertRenders('{{ x|replace("ab", "") }}', "c", x="ababc")


class Req15_first_last_filters(_Helpers, unittest.TestCase):
    """`first`, `last` (first/last element, `None` when empty or `None`)."""

    def test_values(self):
        self.assertRenders("{{ x|first }}", "1", x=[1, 2, 3])
        self.assertRenders("{{ x|last }}", "3", x=[1, 2, 3])
        self.assertRenders("{{ x|first }}{{ x|last }}", "77", x=[7])

    def test_empty_and_none(self):
        for name in ("first", "last"):
            self.assertRenders("{{ x|%s == none }}" % name, "True", x=[])
            self.assertRenders("{{ x|%s == none }}" % name, "True", x=None)
            self.assertRenders("{{ x|%s == none }}" % name, "True")
            self.assertRenders('{{ x|%s|default("d") }}' % name, "d", x=[])


class Req16_filter_syntax_errors(_Helpers, unittest.TestCase):
    """Wrong argument counts and unknown filters are a `TemplateSyntaxError` (at
    parse time, with the tag's line)."""

    def test_wrong_arg_counts(self):
        for src in [
            "{{ x|upper(1) }}",
            "{{ x|lower(1) }}",
            "{{ x|title(1) }}",
            "{{ x|trim(1) }}",
            "{{ x|length(1) }}",
            "{{ x|join(',', 1) }}",
            "{{ x|default }}",
            "{{ x|default() }}",
            "{{ x|default(1, 2) }}",
            "{{ x|truncate }}",
            "{{ x|truncate(1, 2) }}",
            "{{ x|replace('a') }}",
            "{{ x|replace }}",
            "{{ x|replace('a', 'b', 'c') }}",
            "{{ x|first(1) }}",
            "{{ x|last(1) }}",
        ]:
            self.assertSyntaxErrorAt(src, 1)
            self.assertSyntaxErrorAt("a\n\n" + src, 3)

    def test_unknown_filters(self):
        self.assertSyntaxErrorAt("{{ x|nope }}", 1)
        self.assertSyntaxErrorAt("a\n{{ x|upper|nope }}", 2)
        self.assertSyntaxErrorAt("\n\n{% if x|nope %}{% endif %}", 3)
        self.assertSyntaxErrorAt("\n{% if a %}{% elif x|nope %}{% endif %}", 2)
        self.assertSyntaxErrorAt("\n{% for a in xs|nope %}{% endfor %}", 2)
        self.assertSyntaxErrorAt("{% if x|upper(1) %}\n{% endif %}", 1)

    def test_errors_in_unrendered_branches(self):
        # parse time: even code that would never run is checked
        self.assertSyntaxErrorAt("{% if false %}\n{{ x|nope }}{% endif %}", 2)


class Req17_filter_runtime_errors(_Helpers, unittest.TestCase):
    """An exception inside a filter is a `TemplateRenderError`."""

    def test_render_errors(self):
        self.assertRenderError("{{ x|length }}", x=5)
        self.assertRenderError("{{ x|join }}", x=5)
        self.assertRenderError("{{ x|first }}", x=5)
        self.assertRenderError("{% if x|length %}{% endif %}", x=5)
        self.assertRenderError("{% for a in x|last %}{% endfor %}", x=5)


class Req18_operator_precedence(_Helpers, unittest.TestCase):
    """Operators from lowest to highest precedence: `or`; `and`; `not`; one
    comparison (`== != < <= > >= in` or `not in`); parentheses group."""

    def test_comparisons(self):
        cases = [
            ("1 == 1", "True"), ("1 == 2", "False"),
            ("1 != 2", "True"), ("1 != 1", "False"),
            ("1 < 2", "True"), ("2 < 1", "False"),
            ("2 <= 2", "True"), ("3 <= 2", "False"),
            ("3 > 2", "True"), ("2 > 3", "False"),
            ("2 >= 2", "True"), ("1 >= 2", "False"),
            ('"a" < "b"', "True"),
            ('"b" in "abc"', "True"), ('"z" in "abc"', "False"),
            ('"z" not in "abc"', "True"), ('"a" not in "abc"', "False"),
        ]
        for expr, expected in cases:
            self.assertRenders("{{ %s }}" % expr, expected)

    def test_in_collections(self):
        self.assertRenders('{{ "a" in xs }}', "True", xs=["a", "b"])
        self.assertRenders('{{ "c" not in xs }}', "True", xs=["a", "b"])
        self.assertRenders('{{ "k" in d }}', "True", d={"k": 1})
        self.assertRenders("{{ x in xs }}", "True", x=2, xs=[1, 2])

    def test_or_lower_than_and(self):
        self.assertRenders("{{ true or true and false }}", "True")
        self.assertRenders("{{ false and true or true }}", "True")

    def test_not_higher_than_and(self):
        self.assertRenders("{{ not false and false }}", "False")
        self.assertRenders("{{ not true or true }}", "True")

    def test_comparison_higher_than_not(self):
        self.assertRenders("{{ not 1 == 2 }}", "True")
        self.assertRenders('{{ not "a" in xs }}', "True", xs=["b"])

    def test_comparison_higher_than_and_or(self):
        self.assertRenders("{{ 1 < 2 and 2 < 3 }}", "True")
        self.assertRenders("{{ 1 > 2 or 3 == 3 }}", "True")

    def test_parentheses(self):
        self.assertRenders("{{ (true or false) and false }}", "False")
        self.assertRenders("{{ not (true and false) }}", "True")
        self.assertRenders("{{ (1 == 1) }}", "True")

    def test_in_if(self):
        t = Template("{% if a and (b or c) %}y{% else %}n{% endif %}")
        self.assertEqual(t.render(a=1, b=0, c=1), "y")
        self.assertEqual(t.render(a=1, b=0, c=0), "n")
        self.assertEqual(t.render(a=0, b=1, c=1), "n")


class Req19_chained_comparison(_Helpers, unittest.TestCase):
    """Chained comparisons (`a < b < c`) are a `TemplateSyntaxError`."""

    def test_chained(self):
        self.assertSyntaxErrorAt("{{ 1 < 2 < 3 }}", 1)
        self.assertSyntaxErrorAt("{{ 1 < 2 > 1 }}", 1)
        self.assertSyntaxErrorAt("a\n{% if a == b == c %}{% endif %}", 2)
        self.assertSyntaxErrorAt("{{ x in xs in ys }}", 1)
        self.assertSyntaxErrorAt("{{ x not in xs == ys }}", 1)


class Req20_boolean_results(_Helpers, unittest.TestCase):
    """`and`, `or`, `not` and comparisons yield `True`/`False` (printed as such
    by `{{ }}`)."""

    def test_and_or_not(self):
        self.assertRenders('{{ 1 and "x" }}', "True")
        self.assertRenders('{{ 0 or "" }}', "False")
        self.assertRenders('{{ "a" or 0 }}', "True")
        self.assertRenders("{{ 1 and 0 }}", "False")
        self.assertRenders("{{ none or none }}", "False")
        self.assertRenders("{{ not 0 }}", "True")
        self.assertRenders('{{ not "x" }}', "False")
        self.assertRenders("{{ a or b }}", "True", a=None, b=[1])

    def test_comparisons(self):
        self.assertRenders("{{ 1 < 2 }}", "True")
        self.assertRenders('{{ "a" in "abc" }}', "True")
        self.assertRenders("{{ x == y }}", "False", x=1, y=2)


class Req21_comparison_type_errors(_Helpers, unittest.TestCase):
    """A comparison that raises `TypeError` in Python (e.g. `none < 3`,
    `5 in 3`) is `False`; `x in none` is `False` and `x not in none` is `True`."""

    def test_type_errors(self):
        self.assertRenders("{{ none < 3 }}", "False")
        self.assertRenders("{{ 5 in 3 }}", "False")
        self.assertRenders('{{ "a" < 1 }}', "False")
        self.assertRenders("{{ x >= 1 }}", "False")
        self.assertRenders("{{ not none < 3 }}", "True")
        self.assertRenders("{% if none < 3 %}y{% else %}n{% endif %}", "n")

    def test_in_none(self):
        self.assertRenders("{{ 1 in none }}", "False")
        self.assertRenders("{{ 1 not in none }}", "True")
        self.assertRenders('{{ "a" in missing }}', "False")
        self.assertRenders('{{ "a" not in missing }}', "True")
        self.assertRenders("{{ x in y }}", "False", x="a", y=None)
        self.assertRenders("{{ x not in y }}", "True", x="a", y=None)


class Req22_malformed_expressions(_Helpers, unittest.TestCase):
    """Empty or malformed expressions raise `TemplateSyntaxError`."""

    def test_malformed(self):
        for src in [
            "{{ }}",
            "{{   }}",
            "{{ x| }}",
            "{{ x|upper( }}",
            "{{ x|default(1 }}",
            "{{ (x }}",
            "{{ x) }}",
            "{{ () }}",
            "{{ x == }}",
            "{{ == x }}",
            "{{ x y }}",
            "{{ 1 2 }}",
            "{{ not }}",
            "{{ x and }}",
            "{{ or x }}",
            "{% if %}{% endif %}",
            "{% if x %}{% elif %}{% endif %}",
            "{% for x in %}{% endfor %}",
            "{% for in xs %}{% endfor %}",
            "{% for x in xs == %}{% endfor %}",
        ]:
            self.assertSyntaxError(src)

    def test_line(self):
        self.assertSyntaxErrorAt("a\n{{ x == }}", 2)
        self.assertSyntaxErrorAt("a\n\n{% if (x %}{% endif %}", 3)


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------


class Req23_if_elif_else(_Helpers, unittest.TestCase):
    """`{% if %}`, any number of `{% elif %}`, optional `{% else %}`, `{% endif %}`."""

    def test_chain(self):
        t = Template(
            "{% if n == 1 %}one{% elif n == 2 %}two{% elif n == 3 %}three"
            "{% else %}many{% endif %}"
        )
        self.assertEqual(t.render(n=1), "one")
        self.assertEqual(t.render(n=2), "two")
        self.assertEqual(t.render(n=3), "three")
        self.assertEqual(t.render(n=4), "many")
        self.assertEqual(t.render(), "many")

    def test_elif_without_else(self):
        t = Template("{% if a %}A{% elif b %}B{% endif %}")
        self.assertEqual(t.render(), "")
        self.assertEqual(t.render(b=1), "B")
        self.assertEqual(t.render(a=1, b=1), "A")

    def test_first_true_wins(self):
        t = Template("{% if a %}A{% elif b %}B{% elif c %}C{% endif %}")
        self.assertEqual(t.render(b=1, c=1), "B")

    def test_nested(self):
        t = Template(
            "{% if a %}{% if b %}AB{% else %}A{% endif %}"
            "{% elif c %}{% if d %}CD{% elif e %}CE{% endif %}{% else %}-{% endif %}"
        )
        self.assertEqual(t.render(a=1, b=1), "AB")
        self.assertEqual(t.render(a=1), "A")
        self.assertEqual(t.render(c=1, e=1), "CE")
        self.assertEqual(t.render(c=1), "")
        self.assertEqual(t.render(), "-")


class Req24_for_unpacking(_Helpers, unittest.TestCase):
    """`{% for x in seq %}` / `{% for k, v in seq %}` (names separated by commas,
    each item is unpacked; a wrong number of values or a non-iterable item raises
    `TemplateRenderError`)."""

    def test_single_name(self):
        self.assertRenders(
            "{% for p in pairs %}{{ p.0 }}{% endfor %}", "ab", pairs=[("a", 1), ("b", 2)]
        )

    def test_two_names(self):
        self.assertRenders(
            "{% for k, v in pairs %}{{ k }}={{ v }};{% endfor %}",
            "a=1;b=2;",
            pairs=[("a", 1), ("b", 2)],
        )

    def test_three_names(self):
        self.assertRenders(
            "{% for a, b, c in rows %}{{ c }}{{ b }}{{ a }}{% endfor %}",
            "321654",
            rows=[[1, 2, 3], (4, 5, 6)],
        )

    def test_wrong_count(self):
        self.assertRenderError("{% for k, v in xs %}{% endfor %}", xs=[(1, 2, 3)])
        self.assertRenderError("{% for k, v in xs %}{% endfor %}", xs=[(1,)])
        self.assertRenderError("{% for a, b, c in xs %}{% endfor %}", xs=[(1, 2)])

    def test_non_iterable_item(self):
        self.assertRenderError("{% for k, v in xs %}{% endfor %}", xs=[5])
        self.assertRenderError("{% for k, v in xs %}{% endfor %}", xs=[None])


class Req25_for_else(_Helpers, unittest.TestCase):
    """Optional `{% else %}` in a for loop, rendered when the sequence is empty
    or `None`."""

    def test_else(self):
        t = Template("{% for x in xs %}<{{ x }}>{% else %}empty{% endfor %}")
        self.assertEqual(t.render(xs=[]), "empty")
        self.assertEqual(t.render(xs=None), "empty")
        self.assertEqual(t.render(), "empty")
        self.assertEqual(t.render(xs=""), "empty")
        self.assertEqual(t.render(xs={}), "empty")
        self.assertEqual(t.render(xs=[1, 2]), "<1><2>")

    def test_nested_if_with_else_inside_for(self):
        t = Template(
            "{% for x in xs %}{% if x %}a{% else %}b{% endif %}{% else %}E{% endfor %}"
        )
        self.assertEqual(t.render(xs=[1, 0]), "ab")
        self.assertEqual(t.render(xs=[]), "E")

    def test_for_inside_if_else(self):
        t = Template("{% if c %}{% for x in xs %}{{ x }}{% else %}-{% endfor %}{% else %}N{% endif %}")
        self.assertEqual(t.render(c=1, xs=[]), "-")
        self.assertEqual(t.render(c=1, xs=[3]), "3")
        self.assertEqual(t.render(c=0, xs=[3]), "N")


class Req26_for_iteration_kinds(_Helpers, unittest.TestCase):
    """Strings iterate characters and dicts iterate keys; any other
    non-iterable value (except `None`) raises `TemplateRenderError`."""

    def test_string(self):
        self.assertRenders("{% for c in s %}[{{ c }}]{% endfor %}", "[a][b]", s="ab")

    def test_dict(self):
        self.assertRenders("{% for k in d %}{{ k }}{% endfor %}", "ab", d={"a": 1, "b": 2})

    def test_tuple(self):
        self.assertRenders("{% for k in d %}{{ k }}{% endfor %}", "12", d=(1, 2))

    def test_none_is_empty(self):
        self.assertRenders("{% for x in xs %}{{ x }}{% endfor %}", "", xs=None)

    def test_non_iterable(self):
        self.assertRenderError("{% for x in xs %}{% endfor %}", xs=5)
        self.assertRenderError("{% for x in xs %}{% endfor %}", xs=2.5)
        self.assertRenderError("{% for x in 5 %}{% else %}e{% endfor %}")


class Req27_loop_variables(_Helpers, unittest.TestCase):
    """Inside a loop `loop.index` (from 1), `loop.index0`, `loop.first`,
    `loop.last` and `loop.length` are available; in nested loops `loop` is the
    innermost one."""

    def test_loop_vars(self):
        src = (
            "{% for x in xs %}{{ loop.index }}{{ loop.index0 }}{{ loop.first }}"
            "{{ loop.last }}{{ loop.length }}|{% endfor %}"
        )
        self.assertRenders(
            src,
            "10TrueFalse3|21FalseFalse3|32FalseTrue3|",
            xs=["a", "b", "c"],
        )
        self.assertRenders(src, "10TrueTrue1|", xs=["a"])

    def test_loop_vars_in_conditions(self):
        self.assertRenders(
            "{% for x in xs %}{{ x }}{% if not loop.last %}, {% endif %}{% endfor %}",
            "a, b, c",
            xs="abc",
        )

    def test_with_unpacking(self):
        self.assertRenders(
            "{% for k, v in d %}{{ loop.index }}{{ k }}{{ v }}{% endfor %}",
            "1ab2cd",
            d=[("a", "b"), ("c", "d")],
        )

    def test_nested_innermost(self):
        src = (
            "{% for a in xs %}{% for b in ys %}{{ loop.index }}/{{ loop.length }}"
            " {% endfor %}{% endfor %}"
        )
        self.assertRenders(src, "1/3 2/3 3/3 1/3 2/3 3/3 ", xs=[1, 2], ys=[1, 2, 3])

    def test_outer_loop_restored_after_inner(self):
        src = (
            "{% for a in xs %}{% for b in ys %}{{ loop.index }}{% endfor %}"
            "-{{ loop.index }}{{ loop.length }};{% endfor %}"
        )
        self.assertRenders(src, "123-12;123-22;", xs=[1, 2], ys=[1, 2, 3])


class Req28_loop_scoping(_Helpers, unittest.TestCase):
    """Loop variables disappear after the loop and do not overwrite outer
    variables permanently."""

    def test_disappear(self):
        self.assertRenders("{% for x in xs %}{{ x }}{% endfor %}[{{ x }}]", "12[]", xs=[1, 2])
        self.assertRenders(
            "{% for x in xs %}{% endfor %}[{{ loop.index }}]", "[]", xs=[1, 2]
        )
        self.assertRenders(
            "{% for k, v in ps %}{% endfor %}[{{ k }}{{ v }}]", "[]", ps=[(1, 2)]
        )

    def test_outer_restored(self):
        self.assertRenders(
            "{% for x in xs %}{{ x }}{% endfor %}[{{ x }}]", "12[o]", xs=[1, 2], x="o"
        )
        self.assertRenders(
            "{% for k, v in ps %}{{ k }}{{ v }}{% endfor %}[{{ k }}{{ v }}]",
            "12[KV]",
            ps=[(1, 2)],
            k="K",
            v="V",
        )

    def test_nested_shadowing(self):
        self.assertRenders(
            "{% for x in xs %}{% for x in ys %}{{ x }}{% endfor %}{{ x }}{% endfor %}",
            "12A12B",
            xs=["A", "B"],
            ys=[1, 2],
        )


class Req29_block_syntax_errors(_Helpers, unittest.TestCase):
    """Syntax errors (`.line` = line of the offending tag): unknown tag,
    `elif`/`else`/`endif`/`endfor` that do not match the innermost open block
    (including `elif` after `else` and a second `else`), and a block still open
    at the end of the template (line of its opening tag, innermost open block
    first)."""

    def test_unknown_tag(self):
        self.assertSyntaxErrorAt("a\n{% unknown %}", 2)
        self.assertSyntaxErrorAt("{% endblock %}", 1)
        self.assertSyntaxErrorAt("{% if x %}\n\n{% include y %}{% endif %}", 3)

    def test_unmatched_at_top_level(self):
        self.assertSyntaxErrorAt("{% elif x %}", 1)
        self.assertSyntaxErrorAt("a\n{% else %}", 2)
        self.assertSyntaxErrorAt("\n{% endif %}", 2)
        self.assertSyntaxErrorAt("\n\n{% endfor %}", 3)

    def test_elif_in_for(self):
        self.assertSyntaxErrorAt("{% for x in xs %}\n{% elif y %}\n{% endfor %}", 2)
        self.assertSyntaxErrorAt(
            "{% if a %}{% for x in xs %}\n{% elif b %}{% endfor %}{% endif %}", 2
        )

    def test_elif_after_else(self):
        self.assertSyntaxErrorAt("{% if x %}\n{% else %}\n{% elif y %}\n{% endif %}", 3)

    def test_second_else(self):
        self.assertSyntaxErrorAt("{% if x %}{% else %}\n{% else %}{% endif %}", 2)
        self.assertSyntaxErrorAt("{% for x in xs %}{% else %}\n{% else %}{% endfor %}", 2)
        self.assertSyntaxErrorAt(
            "{% if x %}{% elif y %}{% else %}\n{% else %}{% endif %}", 2
        )

    def test_mismatched_end(self):
        self.assertSyntaxErrorAt("{% if x %}\n{% endfor %}", 2)
        self.assertSyntaxErrorAt("{% for x in xs %}\n{% endif %}", 2)
        self.assertSyntaxErrorAt("{% for x in xs %}{% if y %}\n{% endfor %}{% endif %}", 2)
        self.assertSyntaxErrorAt("{% if y %}{% for x in xs %}\n\n{% endif %}{% endfor %}", 3)

    def test_unclosed_blocks(self):
        self.assertSyntaxErrorAt("{% if a %}\nbody", 1)
        self.assertSyntaxErrorAt("{% if a %}\n{% for x in y %}\n", 2)
        self.assertSyntaxErrorAt("{% for x in y %}\n{% if a %}{% endif %}\n", 1)
        self.assertSyntaxErrorAt("x\n{% if a %}\n{% elif b %}\n", 2)
        self.assertSyntaxErrorAt("x\n{% if a %}\n{% else %}\n", 2)
        self.assertSyntaxErrorAt("{% for x in y %}\n{% else %}\n", 1)
        self.assertSyntaxErrorAt("{% if a %}\n\n{% if b %}\n{% endif %}", 1)
        self.assertSyntaxErrorAt("{% for a in b %}\n{% for c in d %}\n{% if e %}\n", 3)


if __name__ == "__main__":
    unittest.main()
