"""Acceptance tests for the extended tplr template engine."""

import unittest

from tplr import (
    Template,
    TemplateError,
    TemplateRenderError,
    TemplateSyntaxError,
    render,
)


class _Base(unittest.TestCase):
    def assertSyntaxError(self, source, line=None):
        with self.assertRaises(TemplateSyntaxError, msg=repr(source)) as ctx:
            Template(source)
        if line is not None:
            self.assertEqual(ctx.exception.line, line, msg=repr(source))
        return ctx.exception

    def assertRenderError(self, source, **ctx):
        t = Template(source)  # must parse fine
        with self.assertRaises(TemplateRenderError, msg=repr(source)):
            t.render(**ctx)


class Req01_existing_api_and_templates(_Base):
    """Keep `Template(source).render(**ctx)`, `render(source, **ctx)` and the three
    exception classes; existing templates must keep rendering as before."""

    def test_exception_hierarchy(self):
        self.assertTrue(issubclass(TemplateSyntaxError, TemplateError))
        self.assertTrue(issubclass(TemplateRenderError, TemplateError))

    def test_template_and_render(self):
        self.assertEqual(Template("Hi {{ name }}!").render(name="Ada"), "Hi Ada!")
        self.assertEqual(render("Hi {{ name }}!", name="Ada"), "Hi Ada!")

    def test_readme_example(self):
        self.assertEqual(
            render(
                "Hello {{ user.name|title }}!{% if admin %} (admin){% endif %}",
                user={"name": "ada"},
                admin=True,
            ),
            "Hello Ada! (admin)",
        )

    def test_old_features(self):
        self.assertEqual(render("{{ a.b.c }}", a={"b": {"c": 5}}), "5")
        self.assertEqual(render("[{{ missing }}][{{ n }}]", n=None), "[][]")
        self.assertEqual(render("{{ xs.1 }}{{ xs.9 }}", xs=["a", "b"]), "b")
        self.assertEqual(render("{{ xs|join }} {{ xs|length }}", xs=[1, 2, 3]), "1, 2, 3 3")
        t = Template("{% if x %}yes{% else %}no{% endif %}")
        self.assertEqual(t.render(x=1), "yes")
        self.assertEqual(t.render(x=0), "no")
        self.assertEqual(t.render(), "no")
        self.assertEqual(render("{% for x in xs %}<{{ x }}>{% endfor %}", xs=[1, 2]), "<1><2>")
        self.assertEqual(render("{% for x in xs %}<{{ x }}>{% endfor %}"), "")
        self.assertEqual(render("a{# hidden #}b"), "ab")
        self.assertEqual(render("line1\n  {{ x }}  \nline3\n", x="v"), "line1\n  v  \nline3\n")

    def test_attribute_paths(self):
        class Obj:
            title = "T"

        self.assertEqual(render("{{ o.title }}", o=Obj()), "T")


class Req02_tag_ends_outside_quotes(_Base):
    """A tag ends at the first closing delimiter (`}}`, `%}`, `#}`) that is not inside a
    quoted string. Quotes are `"` or `'`; a backslash inside a string escapes the next
    character."""

    def test_double_quoted_close_delimiter(self):
        self.assertEqual(render('{{ x|default("}}") }}'), "}}")

    def test_single_quoted_close_delimiter(self):
        self.assertEqual(render("{{ x|default('}}') }}"), "}}")

    def test_block_tag_with_quoted_delimiter(self):
        self.assertEqual(render('{% if x == "%}" %}yes{% else %}no{% endif %}', x="%}"), "yes")
        self.assertEqual(render('{% if x == "%}" %}yes{% else %}no{% endif %}', x="a"), "no")

    def test_backslash_escaped_quote(self):
        self.assertEqual(render(r'{{ "a\"}}" }}'), 'a"}}')
        self.assertEqual(render(r"{{ 'it\'s }}' }}"), "it's }}")

    def test_other_quote_inside_string(self):
        self.assertEqual(render("""{{ "it's" }}"""), "it's")
        self.assertEqual(render("""{{ 'say "hi"' }}"""), 'say "hi"')


class Req03_comments_end_at_first_close(_Base):
    """Comments (`{# ... #}`) end at the first `#}`."""

    def test_comment_ends_at_first_close_even_with_quote(self):
        self.assertEqual(render('a{# " #}b'), "ab")
        self.assertEqual(render("a{# ' #}b{# x #}c"), "abc")

    def test_multiline_comment(self):
        self.assertEqual(render("a{# line\n{{ x }} {% if %}\n #}b"), "ab")

    def test_comment_close_inside_quotes_still_closes(self):
        self.assertEqual(render('a{# "#}" #}b'), 'a" #}b')


class Req04_unterminated_tags(_Base):
    """An unterminated `{{`, `{%` or `{#` raises `TemplateSyntaxError` whose `line` is the
    line where it starts."""

    def test_unterminated_var(self):
        self.assertSyntaxError("a\nb {{ x", line=2)

    def test_unterminated_block_tag(self):
        self.assertSyntaxError("a\n\n{% if x\n\nmore", line=3)

    def test_unterminated_comment(self):
        self.assertSyntaxError("{# comment\nstill\n", line=1)

    def test_close_delimiter_only_inside_string(self):
        self.assertSyntaxError('one\ntwo {{ "}}', line=2)
        self.assertSyntaxError('one\ntwo {{ x|default("}}")\nthree', line=2)

    def test_after_valid_tags(self):
        self.assertSyntaxError("{{ a }}\n{% if b %}x{% endif %}\n\n{{ c", line=4)


class Req05_whitespace_control(_Base):
    """A `-` right after the opening delimiter removes all whitespace at the end of the text
    just before the tag; a `-` right before the closing delimiter removes whitespace at the
    start of the text just after it. Only adjacent literal text is affected. `line` numbers
    still refer to the original source."""

    def test_var_left(self):
        self.assertEqual(render("a \n\t {{- x }} b", x="X"), "aX b")

    def test_var_right(self):
        self.assertEqual(render("a {{ x -}} \n\t b", x="X"), "a Xb")

    def test_var_both(self):
        self.assertEqual(render("a \n {{- x -}} \n b", x="X"), "aXb")

    def test_block_tags(self):
        src = "<ul>\n  {%- for i in xs %}\n  <li>{{ i }}</li>\n  {%- endfor %}\n</ul>"
        self.assertEqual(render(src, xs=[1, 2]), "<ul>\n  <li>1</li>\n  <li>2</li>\n</ul>")
        self.assertEqual(render("a {%- if true -%} b {%- endif -%} c"), "abc")

    def test_comment(self):
        self.assertEqual(render("a  \n{#- c -#}\n  b"), "ab")
        self.assertEqual(render("a  {#- c #}  b"), "a  b")

    def test_only_adjacent_text(self):
        self.assertEqual(render("{{ x -}}{{ y }}", x="X ", y=" Y"), "X  Y")
        self.assertEqual(render("{{ x }}{{- y }}", x="X ", y=" Y"), "X  Y")
        self.assertEqual(render("a {{- x }} b {{ y }} c", x="X", y="Y"), "aX b Y c")

    def test_without_dash_whitespace_kept(self):
        self.assertEqual(render("a {{ x }} b", x="X"), "a X b")

    def test_line_numbers_original_source(self):
        self.assertSyntaxError("a\n\n{{- x -}}\n\n{% bogus %}", line=5)
        self.assertSyntaxError("a\n  \n{%- if x -%}\n\n{% bogus %}{% endif %}", line=5)
        self.assertSyntaxError("a\n{#- c\nc -#}\n\n{{ x|nope }}", line=5)


class Req06_operands(_Base):
    """Operands: variable paths (missing -> None, printed as empty string), string literals
    with escapes `\\n`, `\\t`, `\\x` -> `x`, integers, floats (`-3`, `2.5`), and `true`,
    `false`, `none`."""

    def test_paths(self):
        self.assertEqual(render("{{ user.name }}", user={"name": "Ada"}), "Ada")
        self.assertEqual(render("{{ items.0 }}", items=["first"]), "first")
        self.assertEqual(render("[{{ user.missing.deep }}][{{ nope }}]", user={}), "[][]")

    def test_string_literals(self):
        self.assertEqual(render('{{ "a" }}{{ \'b\' }}'), "ab")
        self.assertEqual(render(r'{{ "a\nb" }}'), "a\nb")
        self.assertEqual(render(r'{{ "a\tb" }}'), "a\tb")
        self.assertEqual(render(r'{{ "a\qb" }}'), "aqb")
        self.assertEqual(render(r'{{ "a\\b" }}'), "a\\b")
        self.assertEqual(render(r"{{ 'a\'b' }}"), "a'b")
        self.assertEqual(render('{{ "" }}'), "")

    def test_numbers(self):
        self.assertEqual(render("{{ 42 }}"), "42")
        self.assertEqual(render("{{ -3 }}"), "-3")
        self.assertEqual(render("{{ 2.5 }}"), "2.5")
        self.assertEqual(render("{{ 10 > 9 }}"), "True")
        self.assertEqual(render("{{ -3 < 0 }}"), "True")
        self.assertEqual(render("{{ 3 == 3.0 }}"), "True")
        self.assertEqual(render("{{ x == 2.5 }}", x=2.5), "True")

    def test_constants(self):
        self.assertEqual(render("{{ true }}"), "True")
        self.assertEqual(render("{{ false }}"), "False")
        self.assertEqual(render("[{{ none }}]"), "[]")
        self.assertEqual(render("{{ x == none }}"), "True")
        self.assertEqual(render("{{ x == true }}", x=True), "True")


class Req07_filter_syntax(_Base):
    """Filters: `operand|name` or `operand|name(arg, ...)` with literal arguments, chainable
    (`x|trim|upper`), binding tighter than anything else."""

    def test_chain(self):
        self.assertEqual(render("{{ x|trim|upper }}", x="  ada  "), "ADA")
        self.assertEqual(render('{{ x|default("  z ")|trim|upper }}'), "Z")

    def test_filter_on_literal(self):
        self.assertEqual(render('{{ "abc"|upper }}'), "ABC")

    def test_arguments(self):
        self.assertEqual(render('{{ xs|join("-") }}', xs=[1, 2]), "1-2")
        self.assertEqual(render("{{ xs|join('-') }}", xs=[1, 2]), "1-2")
        self.assertEqual(render('{{ x|replace("a", "o") }}', x="banana"), "bonono")
        self.assertEqual(render("{{ x|default(0) }}"), "0")
        self.assertEqual(render("{{ x|default(2.5) }}"), "2.5")
        self.assertEqual(render("{{ x|default(true) }}"), "True")

    def test_binds_tighter(self):
        self.assertEqual(render("{{ xs|length == 3 }}", xs=[1, 2, 3]), "True")
        self.assertEqual(render("{{ not xs|length }}", xs=[]), "True")
        self.assertEqual(render('{{ x|upper in xs }}', x="a", xs=["A"]), "True")
        self.assertEqual(render('{{ a|length > 0 and b|length > 0 }}', a="x", b=""), "False")
        self.assertEqual(render('{% if x|lower == "yes" %}ok{% endif %}', x="YES"), "ok")


class Req08_text_filters(_Base):
    """`upper lower title trim` (a `None` input counts as `""`)."""

    def test_values(self):
        self.assertEqual(render("{{ x|upper }}", x="aBc"), "ABC")
        self.assertEqual(render("{{ x|lower }}", x="aBc"), "abc")
        self.assertEqual(render("{{ x|title }}", x="ada lovelace"), "Ada Lovelace")
        self.assertEqual(render("[{{ x|trim }}]", x=" \t a b \n"), "[a b]")

    def test_none(self):
        for f in ("upper", "lower", "title", "trim"):
            self.assertEqual(render("[{{ x|%s }}]" % f), "[]", msg=f)
            self.assertEqual(render("[{{ x|%s }}]" % f, x=None), "[]", msg=f)
            self.assertEqual(render("{{ x|%s == '' }}" % f), "True", msg=f)


class Req09_length_and_join(_Base):
    """`length` (`None` -> 0), `join` (optional separator argument, default `", "`;
    `None` -> `""`)."""

    def test_length(self):
        self.assertEqual(render("{{ x|length }}", x=[1, 2]), "2")
        self.assertEqual(render("{{ x|length }}", x="abc"), "3")
        self.assertEqual(render("{{ x|length }}"), "0")
        self.assertEqual(render("{{ x|length }}", x=None), "0")

    def test_join(self):
        self.assertEqual(render("{{ x|join }}", x=["a", "b"]), "a, b")
        self.assertEqual(render("{{ x|join(' / ') }}", x=["a", 1]), "a / 1")
        self.assertEqual(render("{{ x|join('') }}", x=["a", "b"]), "ab")
        self.assertEqual(render("[{{ x|join }}]"), "[]")
        self.assertEqual(render("{{ x|join == '' }}", x=None), "True")
        self.assertEqual(render("{{ x|join('-') == '' }}"), "True")


class Req10_default(_Base):
    """`default(v)` returns `v` when the input is `None` or `""`, otherwise the input, so
    `0` and `false` are kept."""

    def test_default(self):
        self.assertEqual(render('{{ x|default("d") }}'), "d")
        self.assertEqual(render('{{ x|default("d") }}', x=None), "d")
        self.assertEqual(render('{{ x|default("d") }}', x=""), "d")
        self.assertEqual(render('{{ x|default("d") }}', x="v"), "v")
        self.assertEqual(render('{{ x|default("d") }}', x=0), "0")
        self.assertEqual(render('{{ x|default("d") }}', x=False), "False")
        self.assertEqual(render('{{ false|default("d") }}'), "False")
        self.assertEqual(render('{{ x|default("d") }}', x=[]), "[]")


class Req11_truncate(_Base):
    """`truncate(n)`: unchanged if it fits, else the first `n-3` characters + `"..."`,
    with `n-3` floored at 0."""

    def test_fits(self):
        self.assertEqual(render("{{ x|truncate(5) }}", x="hello"), "hello")
        self.assertEqual(render("{{ x|truncate(10) }}", x="hello"), "hello")
        self.assertEqual(render("[{{ x|truncate(3) }}]", x=""), "[]")

    def test_truncated(self):
        self.assertEqual(render("{{ x|truncate(4) }}", x="hello"), "h...")
        self.assertEqual(render("{{ x|truncate(8) }}", x="hello world"), "hello...")
        self.assertEqual(render("{{ x|truncate(3) }}", x="hello"), "...")

    def test_floor_at_zero(self):
        self.assertEqual(render("{{ x|truncate(2) }}", x="hello"), "...")
        self.assertEqual(render("{{ x|truncate(0) }}", x="hello"), "...")


class Req12_replace(_Base):
    """`replace(old, new)`."""

    def test_replace(self):
        self.assertEqual(render('{{ x|replace("l", "L") }}', x="hello"), "heLLo")
        self.assertEqual(render('{{ x|replace("world", "") }}', x="hello world"), "hello ")
        self.assertEqual(render('{{ x|replace("z", "y") }}', x="abc"), "abc")


class Req13_first_last(_Base):
    """`first`, `last` (first/last element, `None` when empty or `None`)."""

    def test_values(self):
        self.assertEqual(render("{{ x|first }}-{{ x|last }}", x=[1, 2, 3]), "1-3")
        self.assertEqual(render("{{ x|first }}", x=["only"]), "only")

    def test_empty_or_none(self):
        self.assertEqual(render("[{{ x|first }}][{{ x|last }}]", x=[]), "[][]")
        self.assertEqual(render("[{{ x|first }}][{{ x|last }}]"), "[][]")
        self.assertEqual(render("{{ x|first == none }}", x=[]), "True")
        self.assertEqual(render("{{ x|last == none }}", x=None), "True")

    def test_chain(self):
        self.assertEqual(render("{{ x|first|upper }}", x=["ab", "cd"]), "AB")


class Req14_filter_errors(_Base):
    """Wrong argument counts and unknown filters are a `TemplateSyntaxError` (at parse time,
    with the tag's line); an exception inside a filter is a `TemplateRenderError`."""

    def test_unknown_filter(self):
        self.assertSyntaxError("a\n\n{{ x|nope }}", line=3)
        self.assertSyntaxError("a\n{% if x|nope %}y{% endif %}", line=2)
        self.assertSyntaxError("{% for i in x|nope %}{% endfor %}", line=1)

    def test_wrong_arg_counts(self):
        cases = [
            "{{ x|upper(1) }}",
            "{{ x|lower('a') }}",
            "{{ x|title(1) }}",
            "{{ x|trim(1) }}",
            "{{ x|length(1) }}",
            "{{ x|join(',', ',') }}",
            "{{ x|default }}",
            "{{ x|default(1, 2) }}",
            "{{ x|truncate }}",
            "{{ x|truncate(1, 2) }}",
            "{{ x|replace('a') }}",
            "{{ x|replace }}",
            "{{ x|replace('a', 'b', 'c') }}",
            "{{ x|first(1) }}",
            "{{ x|last(1) }}",
        ]
        for src in cases:
            self.assertSyntaxError("one\ntwo " + src, line=2)

    def test_error_at_parse_time_even_if_not_rendered(self):
        self.assertSyntaxError("{% if false %}\n{{ x|nope }}\n{% endif %}", line=2)
        self.assertSyntaxError("{% if false %}\n\n{{ x|truncate }}{% endif %}", line=3)

    def test_exception_in_filter(self):
        self.assertRenderError("{{ x|length }}", x=5)
        self.assertRenderError("{{ x|join }}", x=5)


class Req15_operators_and_precedence(_Base):
    """Operators from lowest to highest precedence: `or`; `and`; `not`; one comparison
    (`== != < <= > >= in` or `not in`); parentheses group."""

    def test_comparisons(self):
        cases = {
            "1 == 1": "True",
            "1 == 2": "False",
            "1 != 2": "True",
            "1 != 1": "False",
            "1 < 2": "True",
            "2 < 1": "False",
            "2 <= 2": "True",
            "3 <= 2": "False",
            "3 > 2": "True",
            "2 > 2": "False",
            "2 >= 2": "True",
            "1 >= 2": "False",
            "'a' in 'cat'": "True",
            "'z' in 'cat'": "False",
            "'z' not in 'cat'": "True",
            "'a' not in 'cat'": "False",
            "'a' == 'a'": "True",
        }
        for expr, want in cases.items():
            self.assertEqual(render("{{ %s }}" % expr), want, msg=expr)

    def test_in_with_variables(self):
        self.assertEqual(render("{{ x in xs }}", x=2, xs=[1, 2]), "True")
        self.assertEqual(render("{{ x not in xs }}", x=3, xs=[1, 2]), "True")
        self.assertEqual(render("{{ k in d }}", k="a", d={"a": 1}), "True")

    def test_and_binds_tighter_than_or(self):
        self.assertEqual(render("{{ true or false and false }}"), "True")
        self.assertEqual(render("{{ false and false or true }}"), "True")

    def test_parentheses(self):
        self.assertEqual(render("{{ (true or false) and false }}"), "False")
        self.assertEqual(render("{{ not (1 == 1 or false) }}"), "False")
        self.assertEqual(render("{{ ((1 < 2)) }}"), "True")

    def test_not_precedence(self):
        self.assertEqual(render("{{ not 1 == 1 }}"), "False")
        self.assertEqual(render("{{ not 1 == 2 }}"), "True")
        self.assertEqual(render("{{ not false and false }}"), "False")
        self.assertEqual(render("{{ not true or true }}"), "True")
        self.assertEqual(render("{{ not not true }}"), "True")
        self.assertEqual(render("{{ not x in xs }}", x=1, xs=[2]), "True")

    def test_in_if_and_elif(self):
        src = "{% if n < 0 %}neg{% elif n == 0 or n == none %}zero{% else %}pos{% endif %}"
        self.assertEqual(render(src, n=-1), "neg")
        self.assertEqual(render(src, n=0), "zero")
        self.assertEqual(render(src), "zero")
        self.assertEqual(render(src, n=5), "pos")

    def test_comparison_with_paths(self):
        self.assertEqual(render("{{ user.age >= 18 }}", user={"age": 20}), "True")


class Req16_chained_comparisons(_Base):
    """Chained comparisons (`a < b < c`) are a `TemplateSyntaxError`."""

    def test_chained(self):
        self.assertSyntaxError("x\n{{ 1 < 2 < 3 }}", line=2)
        self.assertSyntaxError("{{ a == b == c }}", line=1)
        self.assertSyntaxError("{% if a in b in c %}{% endif %}", line=1)
        self.assertSyntaxError("{{ a not in b == c }}", line=1)

    def test_parenthesised_is_fine(self):
        self.assertEqual(render("{{ (1 < 2) == true }}"), "True")


class Req17_boolean_results(_Base):
    """`and`, `or`, `not` and comparisons yield `True`/`False` (printed as such by `{{ }}`)."""

    def test_and_or_not(self):
        self.assertEqual(render("{{ 1 and 2 }}"), "True")
        self.assertEqual(render("{{ 'a' and '' }}"), "False")
        self.assertEqual(render("{{ 0 or '' }}"), "False")
        self.assertEqual(render("{{ 0 or 'x' }}"), "True")
        self.assertEqual(render("{{ x or y }}", x="a", y="b"), "True")
        self.assertEqual(render("{{ not none }}"), "True")
        self.assertEqual(render("{{ not 'x' }}"), "False")

    def test_comparison(self):
        self.assertEqual(render("{{ x == 'a' }}", x="a"), "True")
        self.assertEqual(render("{{ x == 'a' }}", x="b"), "False")


class Req18_comparison_type_errors(_Base):
    """A comparison that raises `TypeError` in Python (e.g. `none < 3`, `5 in 3`) is
    `False`; `x in none` is `False` and `x not in none` is `True`."""

    def test_type_errors_false(self):
        self.assertEqual(render("{{ none < 3 }}"), "False")
        self.assertEqual(render("{{ 5 in 3 }}"), "False")
        self.assertEqual(render("{{ x > 3 }}"), "False")
        self.assertEqual(render("{{ 'a' >= 1 }}"), "False")
        self.assertEqual(render("{% if x < 3 %}y{% else %}n{% endif %}"), "n")

    def test_in_none(self):
        self.assertEqual(render("{{ x in none }}", x=1), "False")
        self.assertEqual(render("{{ x not in none }}", x=1), "True")
        self.assertEqual(render("{{ 'a' in xs }}"), "False")
        self.assertEqual(render("{{ 'a' not in xs }}"), "True")


class Req19_malformed_expressions(_Base):
    """Empty or malformed expressions raise `TemplateSyntaxError`."""

    def test_empty(self):
        self.assertSyntaxError("a\n{{ }}", line=2)
        self.assertSyntaxError("{{}}", line=1)
        self.assertSyntaxError("a\n{% if %}{% endif %}", line=2)
        self.assertSyntaxError("{% if x %}\n{% elif %}{% endif %}", line=2)
        self.assertSyntaxError("{% for x in %}{% endfor %}", line=1)

    def test_malformed(self):
        cases = [
            "{{ a b }}",
            "{{ x| }}",
            "{{ |upper }}",
            "{{ (1 }}",
            "{{ 1) }}",
            "{{ () }}",
            "{{ 1 == }}",
            "{{ == 1 }}",
            "{{ and }}",
            "{{ a and }}",
            "{{ or b }}",
            "{{ not }}",
            "{{ a not b }}",
            "{{ x|upper( }}",
            "{{ x|default(y) }}",
            "{{ x|join(,) }}",
            "{{ a..b }}",
            "{{ 'abc' 'def' }}",
            "{% if a b %}{% endif %}",
            "{% for x in a b %}{% endfor %}",
        ]
        for src in cases:
            self.assertSyntaxError("one\n" + src, line=2)


class Req20_if_elif_else(_Base):
    """`{% if %}`, any number of `{% elif %}`, optional `{% else %}`, `{% endif %}`."""

    def test_if_only(self):
        self.assertEqual(render("{% if x %}a{% endif %}", x=1), "a")
        self.assertEqual(render("{% if x %}a{% endif %}", x=0), "")

    def test_elif_chain(self):
        src = "{% if x == 1 %}one{% elif x == 2 %}two{% elif x == 3 %}three{% endif %}"
        self.assertEqual(render(src, x=1), "one")
        self.assertEqual(render(src, x=2), "two")
        self.assertEqual(render(src, x=3), "three")
        self.assertEqual(render(src, x=4), "")

    def test_elif_else(self):
        src = "{% if a %}A{% elif b %}B{% elif c %}C{% else %}E{% endif %}"
        self.assertEqual(render(src, a=1, b=1, c=1), "A")
        self.assertEqual(render(src, b=1, c=1), "B")
        self.assertEqual(render(src, c=1), "C")
        self.assertEqual(render(src), "E")

    def test_nested(self):
        src = "{% if a %}{% if b %}ab{% else %}a{% endif %}{% elif c %}c{% endif %}!"
        self.assertEqual(render(src, a=1, b=1), "ab!")
        self.assertEqual(render(src, a=1), "a!")
        self.assertEqual(render(src, c=1), "c!")
        self.assertEqual(render(src), "!")


class Req21_for_unpacking(_Base):
    """`{% for x in seq %}` / `{% for k, v in seq %}` (names separated by commas, each item
    is unpacked; a wrong number of values or a non-iterable item raises
    `TemplateRenderError`)."""

    def test_single(self):
        self.assertEqual(render("{% for x in xs %}{{ x }};{% endfor %}", xs=["a", "b"]), "a;b;")

    def test_unpack_two(self):
        src = "{% for k, v in pairs %}{{ k }}={{ v }};{% endfor %}"
        self.assertEqual(render(src, pairs=[("a", 1), ["b", 2]]), "a=1;b=2;")

    def test_unpack_three(self):
        src = "{% for a, b, c in rows %}{{ a }}{{ b }}{{ c }}|{% endfor %}"
        self.assertEqual(render(src, rows=[(1, 2, 3), "xyz"]), "123|xyz|")

    def test_wrong_count(self):
        src = "{% for k, v in pairs %}{{ k }}{% endfor %}"
        self.assertRenderError(src, pairs=[(1, 2, 3)])
        self.assertRenderError(src, pairs=[(1,)])

    def test_non_iterable_item(self):
        self.assertRenderError("{% for k, v in pairs %}{{ k }}{% endfor %}", pairs=[5])

    def test_expression_iterable(self):
        self.assertEqual(render("{% for x in xs|default('ab') %}{{ x }}{% endfor %}"), "ab")


class Req22_for_else(_Base):
    """Optional `{% else %}` rendered when the sequence is empty or `None`, `{% endfor %}`."""

    def test_else(self):
        src = "{% for x in xs %}{{ x }}{% else %}empty{% endfor %}"
        self.assertEqual(render(src, xs=[1, 2]), "12")
        self.assertEqual(render(src, xs=[]), "empty")
        self.assertEqual(render(src, xs=None), "empty")
        self.assertEqual(render(src), "empty")
        self.assertEqual(render(src, xs=""), "empty")
        self.assertEqual(render(src, xs={}), "empty")

    def test_no_else_none(self):
        self.assertEqual(render("[{% for x in xs %}{{ x }}{% endfor %}]", xs=None), "[]")


class Req23_iteration_kinds(_Base):
    """Strings iterate characters and dicts iterate keys; any other non-iterable value
    (except `None`) raises `TemplateRenderError`."""

    def test_string(self):
        self.assertEqual(render("{% for c in s %}[{{ c }}]{% endfor %}", s="abc"), "[a][b][c]")

    def test_dict(self):
        self.assertEqual(render("{% for k in d %}{{ k }};{% endfor %}", d={"a": 1, "b": 2}), "a;b;")

    def test_other_iterables(self):
        self.assertEqual(render("{% for x in t %}{{ x }}{% endfor %}", t=(1, 2)), "12")
        self.assertEqual(render("{% for x in t %}{{ x }}{% endfor %}", t=range(3)), "012")

    def test_non_iterable(self):
        self.assertRenderError("{% for x in n %}{{ x }}{% endfor %}", n=5)
        self.assertRenderError("{% for x in n %}{{ x }}{% else %}e{% endfor %}", n=2.5)
        self.assertRenderError("{% for x in n %}{{ x }}{% endfor %}", n=True)
        self.assertRenderError("{% for x in 3 %}{{ x }}{% endfor %}")


class Req24_loop_variable(_Base):
    """Inside a loop `loop.index` (from 1), `loop.index0`, `loop.first`, `loop.last` and
    `loop.length` are available; in nested loops `loop` is the innermost one."""

    def test_loop_fields(self):
        src = "{% for x in xs %}{{ loop.index }}{{ loop.index0 }}{{ loop.first }}{{ loop.last }}{{ loop.length }};{% endfor %}"
        self.assertEqual(
            render(src, xs="abc"),
            "10TrueFalse3;21FalseFalse3;32FalseTrue3;",
        )

    def test_single_item(self):
        src = "{% for x in xs %}{{ loop.first }}{{ loop.last }}{% endfor %}"
        self.assertEqual(render(src, xs=[1]), "TrueTrue")

    def test_loop_in_conditions(self):
        src = "{% for x in xs %}{{ x }}{% if not loop.last %}, {% endif %}{% endfor %}"
        self.assertEqual(render(src, xs=[1, 2, 3]), "1, 2, 3")

    def test_nested_innermost(self):
        src = (
            "{% for a in xs %}{% for b in ys %}{{ loop.index }}/{{ loop.length }} {% endfor %}"
            "|{{ loop.index }}/{{ loop.length }}|{% endfor %}"
        )
        self.assertEqual(render(src, xs=[1, 2], ys="abc"), "1/3 2/3 3/3 |1/2|1/3 2/3 3/3 |2/2|")

    def test_unpacking_loop(self):
        src = "{% for k, v in ps %}{{ loop.index }}{{ k }}{{ v }}{% endfor %}"
        self.assertEqual(render(src, ps=[("a", 1), ("b", 2)]), "1a12b2")


class Req25_loop_scoping(_Base):
    """Loop variables disappear after the loop and do not overwrite outer variables
    permanently."""

    def test_disappear(self):
        self.assertEqual(render("{% for x in xs %}{% endfor %}[{{ x }}][{{ loop.index }}]", xs=[1, 2]), "[][]")
        self.assertEqual(render("{% for k, v in ps %}{% endfor %}[{{ k }}{{ v }}]", ps=[(1, 2)]), "[]")

    def test_outer_restored(self):
        src = "{{ x }}{% for x in xs %}{{ x }}{% endfor %}{{ x }}"
        self.assertEqual(render(src, x="o", xs=[1, 2]), "o12o")

    def test_outer_visible_inside(self):
        src = "{% for x in xs %}{{ y }}{{ x }}{% endfor %}"
        self.assertEqual(render(src, y="-", xs=[1, 2]), "-1-2")

    def test_nested_restores_outer_loop_var(self):
        src = "{% for x in xs %}{% for x in ys %}{{ x }}{% endfor %}{{ x }};{% endfor %}"
        self.assertEqual(render(src, xs=["A", "B"], ys=[1, 2]), "12A;12B;")

    def test_template_reusable(self):
        t = Template("{% for x in xs %}{{ x }}{% endfor %}[{{ x }}]")
        self.assertEqual(t.render(xs=[1]), "1[]")
        self.assertEqual(t.render(xs=[2], x="z"), "2[z]")


class Req26_block_syntax_errors(_Base):
    """Syntax errors (`.line` = line of the offending tag): unknown tag, `elif`/`else`/
    `endif`/`endfor` that do not match the innermost open block (including `elif` after
    `else` and a second `else`), and a block still open at the end of the template (line of
    its opening tag, innermost open block first)."""

    def test_unknown_tag(self):
        self.assertSyntaxError("one\ntwo\n{% bogus %}", line=3)
        self.assertSyntaxError("{% if x %}\n{% endblock %}{% endif %}", line=2)

    def test_unmatched_at_top_level(self):
        self.assertSyntaxError("a\n{% elif x %}", line=2)
        self.assertSyntaxError("a\n{% else %}", line=2)
        self.assertSyntaxError("a\n{% endif %}", line=2)
        self.assertSyntaxError("a\n{% endfor %}", line=2)

    def test_mismatched_innermost(self):
        self.assertSyntaxError("{% for x in xs %}\n{% endif %}\n{% endfor %}", line=2)
        self.assertSyntaxError("{% if x %}\n{% endfor %}\n{% endif %}", line=2)
        self.assertSyntaxError("{% for x in xs %}\n{% elif y %}\n{% endfor %}", line=2)
        self.assertSyntaxError(
            "{% if a %}{% for x in xs %}\n\n{% endif %}{% endfor %}", line=3
        )
        self.assertSyntaxError(
            "{% if a %}{% for x in xs %}\n{% elif b %}{% endfor %}{% endif %}", line=2
        )

    def test_elif_after_else(self):
        self.assertSyntaxError("{% if a %}\n{% else %}\n{% elif b %}\n{% endif %}", line=3)

    def test_second_else(self):
        self.assertSyntaxError("{% if a %}\n{% else %}\n\n{% else %}{% endif %}", line=4)
        self.assertSyntaxError(
            "{% for x in xs %}\n{% else %}\n{% else %}{% endfor %}", line=3
        )

    def test_unclosed(self):
        self.assertSyntaxError("x\n{% if a %}\nbody", line=2)
        self.assertSyntaxError("x\n{% for a in b %}\nbody{% else %}", line=2)
        self.assertSyntaxError("{% if a %}\n{% elif b %}\n{% else %}", line=1)

    def test_unclosed_innermost_first(self):
        self.assertSyntaxError("{% if a %}\n{% for x in y %}\n", line=2)
        self.assertSyntaxError("{% for x in y %}\n\n{% if a %}{% else %}\n", line=3)
        self.assertSyntaxError(
            "{% if a %}\n{% for x in y %}\n{% if b %}{% endif %}\n", line=2
        )


if __name__ == "__main__":
    unittest.main()
