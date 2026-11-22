"""Acceptance tests for the extended tplr engine."""

import unittest

from tplr import (
    Template,
    TemplateError,
    TemplateRenderError,
    TemplateSyntaxError,
    render,
)


class _Base(unittest.TestCase):
    def assertRenders(self, src, expected, **ctx):
        self.assertEqual(render(src, **ctx), expected, msg=repr(src))

    def assertSyntaxError(self, src, line=None):
        with self.assertRaises(TemplateSyntaxError, msg=repr(src)) as cm:
            Template(src)
        if line is not None:
            self.assertEqual(cm.exception.line, line, msg=repr(src))
        return cm.exception

    def assertRenderError(self, src, **ctx):
        t = Template(src)
        with self.assertRaises(TemplateRenderError, msg=repr(src)):
            t.render(**ctx)


class Req01_public_api_and_compatibility(_Base):
    """Keep `Template(source).render(**ctx)`, `render(source, **ctx)` and the three
    exception classes; existing templates must keep rendering as before."""

    def test_api(self):
        self.assertEqual(Template("Hi {{ n }}").render(n="A"), "Hi A")
        self.assertEqual(render("Hi {{ n }}", n="A"), "Hi A")
        self.assertTrue(issubclass(TemplateSyntaxError, TemplateError))
        self.assertTrue(issubclass(TemplateRenderError, TemplateError))

    def test_existing_templates(self):
        self.assertRenders("Hi {{ name }}!", "Hi Ada!", name="Ada")
        self.assertRenders("{{ a.b.c }}", "5", a={"b": {"c": 5}})
        self.assertRenders("[{{ missing }}]", "[]")
        self.assertRenders("{{ xs.1 }}{{ xs.9 }}", "b", xs=["a", "b"])
        self.assertRenders("{{ n|upper }} {{ n|title }}", "ADA LOVELACE Ada Lovelace", n="ada lovelace")
        self.assertRenders("{{ xs|join }} {{ xs|length }}", "1, 2, 3 3", xs=[1, 2, 3])
        t = Template("{% if x %}yes{% else %}no{% endif %}")
        self.assertEqual(t.render(x=1), "yes")
        self.assertEqual(t.render(x=0), "no")
        self.assertEqual(t.render(), "no")
        self.assertRenders("{% for x in xs %}<{{ x }}>{% endfor %}", "<1><2>", xs=[1, 2])
        self.assertRenders("{% for x in xs %}<{{ x }}>{% endfor %}", "")
        src = "{% for r in rows %}{% if r.ok %}{{ r.n }}{% else %}-{% endif %}{% endfor %}"
        self.assertRenders(src, "a-", rows=[{"ok": 1, "n": "a"}, {"ok": 0, "n": "b"}])
        self.assertRenders("a{# hidden #}b", "ab")
        self.assertRenders(
            "Hello {{ user.name|title }}!{% if admin %} (admin){% endif %}",
            "Hello Ada! (admin)", user={"name": "ada"}, admin=True,
        )

    def test_attribute_lookup(self):
        class Obj:
            title = "T"

        self.assertRenders("{{ o.title }}", "T", o=Obj())


class Req02_closing_delimiter_outside_quotes(_Base):
    """A tag ends at the first closing delimiter (`}}`, `%}`, `#}`) that is not inside a
    quoted string, so `{{ x|default("}}") }}` works. Quotes are `"` or `'`; a backslash
    inside a string escapes the next character."""

    def test_default_with_braces(self):
        self.assertRenders('{{ x|default("}}") }}', "}}")
        self.assertRenders('{{ x|default("}}") }}', "v", x="v")

    def test_single_quotes(self):
        self.assertRenders("[{{ '}}' }}]", "[}}]")

    def test_block_tag_with_delimiter_in_string(self):
        self.assertRenders('{% if x == "%}" %}yes{% else %}no{% endif %}', "yes", x="%}")
        self.assertRenders('{% if x == "%}" %}yes{% else %}no{% endif %}', "no", x="a")

    def test_escaped_quote_in_string(self):
        self.assertRenders(r'{{ "a\"}}" }}', 'a"}}')
        self.assertRenders(r"{{ 'a\'}}' }}", "a'}}")

    def test_other_quote_kind_inside_string(self):
        self.assertRenders("""{{ "it's }}" }}""", "it's }}")


class Req03_comments(_Base):
    """Comments (`{# ... #}`) end at the first `#}`."""

    def test_comment_ends_at_first_close(self):
        self.assertRenders('a{# "x #}b', "ab")
        self.assertRenders("a{# one #}b{# two #}c", "abc")
        self.assertRenders("a{# x #} #}", "a #}")

    def test_multiline_comment(self):
        self.assertRenders("a{# line\nline #}b", "ab")


class Req04_unterminated_tags(_Base):
    """An unterminated `{{`, `{%` or `{#` raises `TemplateSyntaxError` whose `line` is the
    line where it starts."""

    def test_unterminated_var(self):
        self.assertSyntaxError("a\n\nb {{ x", line=3)

    def test_unterminated_block(self):
        self.assertSyntaxError("{% if x", line=1)
        self.assertSyntaxError("one\n{% if x\n\n", line=2)

    def test_unterminated_comment(self):
        self.assertSyntaxError("x\n{# comment\nmore", line=2)

    def test_unterminated_because_of_open_string(self):
        self.assertSyntaxError('a\n{{ "}} }}', line=2)


class Req05_whitespace_control(_Base):
    """`{{-`, `{%-`, `{#-` remove all whitespace at the end of the preceding text; `-}}`,
    `-%}`, `-#}` remove whitespace at the start of the following text. Only adjacent
    literal text is affected. `line` numbers still refer to the original source."""

    def test_left_strip(self):
        self.assertRenders("a \t\n  {{- x }} b", "aX b", x="X")

    def test_right_strip(self):
        self.assertRenders("a {{ x -}} \n\t b", "a Xb", x="X")

    def test_both_sides(self):
        self.assertRenders("a \n {{- x -}} \n b", "aXb", x="X")

    def test_block_tags(self):
        src = "<ul>\n  {%- for i in xs -%}\n  <li>{{ i }}</li>\n  {%- endfor -%}\n</ul>"
        self.assertRenders(src, "<ul><li>1</li><li>2</li></ul>", xs=[1, 2])

    def test_comments(self):
        self.assertRenders("a \n {#- c -#} \n b", "ab")

    def test_only_affects_matching_side(self):
        self.assertRenders("a {{- x }} b", "aX b", x="X")
        self.assertRenders("a {{ x -}} b", "a Xb", x="X")

    def test_only_adjacent_text(self):
        self.assertRenders("a {{ x }}{{- y }}", "a XY", x="X", y="Y")
        self.assertRenders("{{ x -}}{{ y }} b", "XY b", x="X", y="Y")

    def test_line_numbers_original_source(self):
        self.assertSyntaxError("a\n  {{- x -}}\n\n{% bogus %}", line=4)
        self.assertSyntaxError("a\n\n\n{%- bogus %}", line=4)
        self.assertSyntaxError("{{ x -}}\n\n{% bogus %}", line=3)


class Req06_operands(_Base):
    """Operands: variable paths (missing -> None, printed as ""), string literals with
    escapes `\\n`, `\\t`, and `\\x` -> `x`, integers, floats (`-3`, `2.5`), and `true`,
    `false`, `none`."""

    def test_paths(self):
        self.assertRenders("{{ user.name }}", "Ada", user={"name": "Ada"})
        self.assertRenders("{{ items.0 }}", "a", items=["a", "b"])
        self.assertRenders("[{{ user.nope }}][{{ nope.x.y }}][{{ items.5 }}]", "[][][]", user={}, items=[])

    def test_strings(self):
        self.assertRenders('{{ "abc" }}', "abc")
        self.assertRenders("{{ 'abc' }}", "abc")
        self.assertRenders(r'{{ "a\nb" }}', "a\nb")
        self.assertRenders(r'{{ "a\tb" }}', "a\tb")
        self.assertRenders(r'{{ "a\qb" }}', "aqb")
        self.assertRenders(r'{{ "a\\b" }}', "a\\b")
        self.assertRenders(r"{{ 'it\'s' }}", "it's")
        self.assertRenders('{{ "" }}', "")

    def test_numbers(self):
        self.assertRenders("{{ 42 }}", "42")
        self.assertRenders("{{ -3 }}", "-3")
        self.assertRenders("{{ 2.5 }}", "2.5")
        self.assertRenders("{{ 1 == 1.0 }}", "True")
        self.assertRenders('{{ "3" == 3 }}', "False")
        self.assertRenders("{{ x == -3 }}", "True", x=-3)
        self.assertRenders("{{ x == 2.5 }}", "True", x=2.5)

    def test_keywords(self):
        self.assertRenders("{{ true }}", "True")
        self.assertRenders("{{ false }}", "False")
        self.assertRenders("[{{ none }}]", "[]")
        self.assertRenders("{{ x == none }}", "True")
        self.assertRenders("{{ x == true }}", "True", x=True)
        self.assertRenders("{{ x == false }}", "True", x=False)


class Req07_filter_syntax(_Base):
    """Filters: `operand|name` or `operand|name(arg, ...)` with literal arguments,
    chainable (`x|trim|upper`), binding tighter than anything else."""

    def test_chain(self):
        self.assertRenders("[{{ x|trim|upper }}]", "[AB C]", x="  ab c ")

    def test_args(self):
        self.assertRenders('{{ x|replace("a", "o")|upper }}', "FOO", x="faa")
        self.assertRenders("{{ x|truncate(5) }}", "he...", x="hello world")
        self.assertRenders("{{ x|default(2.5) }}", "2.5")
        self.assertRenders("{{ x|default(true) }}", "True")

    def test_on_literals(self):
        self.assertRenders('{{ "abc"|upper }}', "ABC")
        self.assertRenders("{{ none|default('d') }}", "d")

    def test_binds_tighter_than_operators(self):
        self.assertRenders('{{ "A" == x|upper }}', "True", x="a")
        self.assertRenders("{{ xs|length > 1 }}", "True", xs=[1, 2])
        self.assertRenders("{{ not xs|length }}", "True", xs=[])
        self.assertRenders('{{ "b" in xs|join }}', "True", xs=["a", "b"])


class Req08_filter_behaviour(_Base):
    """upper lower title trim (None -> ""), length (None -> 0), join (optional separator,
    default ", "; None -> ""), default(v) (v when input is None or "", else input; 0 and
    false kept), truncate(n), replace(old, new), first, last (None when empty or None)."""

    def test_case_and_trim(self):
        self.assertRenders("{{ x|upper }}|{{ x|lower }}|{{ x|title }}|{{ x|trim }}",
                           " HELLO WORLD | hello world | Hello World |hEllo wOrld",
                           x=" hEllo wOrld ")

    def test_none_as_empty_string(self):
        self.assertRenders("[{{ x|upper }}{{ x|lower }}{{ x|title }}{{ x|trim }}]", "[]")
        self.assertRenders("[{{ x|upper }}{{ x|lower }}{{ x|title }}{{ x|trim }}]", "[]", x=None)

    def test_length(self):
        self.assertRenders("{{ x|length }}", "3", x="abc")
        self.assertRenders("{{ x|length }}", "2", x={"a": 1, "b": 2})
        self.assertRenders("{{ x|length }}", "0")
        self.assertRenders("{{ x|length == 0 }}", "True")

    def test_join(self):
        self.assertRenders("{{ xs|join }}", "1, 2, 3", xs=[1, 2, 3])
        self.assertRenders('{{ xs|join("-") }}', "a-b", xs=["a", "b"])
        self.assertRenders("{{ xs|join('') }}", "ab", xs=["a", "b"])
        self.assertRenders("[{{ xs|join }}]", "[]")
        self.assertRenders('[{{ xs|join("-") }}]', "[]")

    def test_default(self):
        self.assertRenders('{{ x|default("d") }}', "d")
        self.assertRenders('{{ x|default("d") }}', "d", x=None)
        self.assertRenders('{{ x|default("d") }}', "d", x="")
        self.assertRenders('{{ x|default("d") }}', "0", x=0)
        self.assertRenders('{{ x|default("d") }}', "False", x=False)
        self.assertRenders('{{ x|default("d") }}', "v", x="v")
        self.assertRenders('{{ x|default("d") }}', "[]", x=[])
        self.assertRenders("{{ x|default(3) == 3 }}", "True")

    def test_truncate(self):
        self.assertRenders("{{ x|truncate(5) }}", "hello", x="hello")
        self.assertRenders("{{ x|truncate(10) }}", "hello", x="hello")
        self.assertRenders("{{ x|truncate(8) }}", "hello...", x="hello world")
        self.assertRenders("{{ x|truncate(4) }}", "h...", x="hello")
        self.assertRenders("{{ x|truncate(3) }}", "...", x="hello")

    def test_replace(self):
        self.assertRenders('{{ x|replace("l", "L") }}', "heLLo", x="hello")
        self.assertRenders("{{ x|replace('world', '') }}", "hello ", x="hello world")

    def test_first_last(self):
        self.assertRenders("{{ xs|first }}-{{ xs|last }}", "1-3", xs=[1, 2, 3])
        self.assertRenders("[{{ xs|first }}][{{ xs|last }}]", "[][]", xs=[])
        self.assertRenders("[{{ xs|first }}][{{ xs|last }}]", "[][]")
        self.assertRenders("{{ xs|first == none }}{{ xs|last == none }}", "TrueTrue", xs=[])
        self.assertRenders("{{ xs|first == none }}{{ xs|last == none }}", "TrueTrue")


class Req09_filter_errors(_Base):
    """Wrong argument counts and unknown filters are a `TemplateSyntaxError` (at parse
    time, with the tag's line); an exception inside a filter is a `TemplateRenderError`."""

    def test_unknown_filter(self):
        self.assertSyntaxError("{{ x|nope }}", line=1)
        self.assertSyntaxError("a\nb\n{{ x|nope }}", line=3)
        self.assertSyntaxError("a\n{% if x|nope %}{% endif %}", line=2)

    def test_wrong_argument_counts(self):
        for src in [
            "{{ x|upper(1) }}",
            "{{ x|lower('a') }}",
            "{{ x|title(1) }}",
            "{{ x|trim(1) }}",
            "{{ x|length(1) }}",
            "{{ x|join('a', 'b') }}",
            "{{ x|default }}",
            "{{ x|default(1, 2) }}",
            "{{ x|truncate }}",
            "{{ x|truncate(1, 2) }}",
            "{{ x|replace('a') }}",
            "{{ x|replace }}",
            "{{ x|replace('a', 'b', 'c') }}",
            "{{ x|first(1) }}",
            "{{ x|last(1) }}",
        ]:
            self.assertSyntaxError("\n\n" + src, line=3)

    def test_exception_inside_filter(self):
        self.assertRenderError("{{ x|length }}", x=5)
        self.assertRenderError("{{ x|first }}", x=5)


class Req10_operators(_Base):
    """Operators from lowest to highest precedence: `or`; `and`; `not`; one comparison
    (`== != < <= > >= in`, `not in`); parentheses group. `and`, `or`, `not` and comparisons
    yield True/False (printed as such by `{{ }}`)."""

    def test_comparisons(self):
        cases = {
            "1 == 1": "True", "1 == 2": "False",
            "1 != 2": "True", "1 != 1": "False",
            "1 < 2": "True", "2 < 1": "False",
            "2 <= 2": "True", "3 <= 2": "False",
            "3 > 2": "True", "2 > 3": "False",
            "2 >= 2": "True", "1 >= 2": "False",
            '"b" in "abc"': "True", '"z" in "abc"': "False",
            '"z" not in "abc"': "True", '"b" not in "abc"': "False",
        }
        for expr, expected in cases.items():
            self.assertRenders("{{ %s }}" % expr, expected)

    def test_in_with_variables(self):
        self.assertRenders("{{ 2 in xs }}{{ 5 in xs }}", "TrueFalse", xs=[1, 2])
        self.assertRenders('{{ "k" in d }}{{ "q" not in d }}', "TrueTrue", d={"k": 1})

    def test_boolean_results(self):
        self.assertRenders("{{ 1 and 2 }}", "True")
        self.assertRenders('{{ 0 or "" }}', "False")
        self.assertRenders('{{ "a" or 0 }}', "True")
        self.assertRenders("{{ not 0 }}", "True")
        self.assertRenders('{{ not "x" }}', "False")
        self.assertRenders("{{ x and y }}", "False", x="a")

    def test_precedence(self):
        self.assertRenders("{{ true or false and false }}", "True")
        self.assertRenders("{{ (true or false) and false }}", "False")
        self.assertRenders("{{ not false and false }}", "False")
        self.assertRenders("{{ not (false and false) }}", "True")
        self.assertRenders("{{ not true or true }}", "True")
        self.assertRenders("{{ not 1 == 2 }}", "True")
        self.assertRenders("{{ not x in xs }}", "False", x=1, xs=[1])
        self.assertRenders("{{ 1 == 1 and 2 == 3 or 4 > 3 }}", "True")
        self.assertRenders("{{ ((1 < 2)) }}", "True")
        self.assertRenders("{{ (1 < 2) == true }}", "True")

    def test_in_if_and_elif(self):
        src = "{% if n > 10 %}big{% elif n > 5 and n != 7 %}mid{% else %}small{% endif %}"
        self.assertEqual(Template(src).render(n=11), "big")
        self.assertEqual(Template(src).render(n=6), "mid")
        self.assertEqual(Template(src).render(n=7), "small")

    def test_in_for(self):
        self.assertRenders("{% for x in (xs) %}{{ x }}{% endfor %}", "12", xs=[1, 2])
        self.assertRenders('{% for c in "ab" %}<{{ c }}>{% endfor %}', "<a><b>")


class Req11_chained_comparisons(_Base):
    """Chained comparisons (`a < b < c`) are a `TemplateSyntaxError`."""

    def test_chained(self):
        self.assertSyntaxError("{{ 1 < 2 < 3 }}", line=1)
        self.assertSyntaxError("\n{{ a == b == c }}", line=2)
        self.assertSyntaxError("{% if a in b in c %}{% endif %}", line=1)

    def test_parenthesised_is_fine(self):
        self.assertRenders("{{ (1 < 2) == true }}", "True")


class Req12_comparison_type_errors(_Base):
    """A comparison that raises `TypeError` in Python (e.g. `none < 3`, `5 in 3`) is False;
    `x in none` is False and `x not in none` is True."""

    def test_type_errors_false(self):
        self.assertRenders("{{ none < 3 }}", "False")
        self.assertRenders("{{ 5 in 3 }}", "False")
        self.assertRenders('{{ "a" < 1 }}', "False")
        self.assertRenders("{{ x >= 3 }}", "False")
        self.assertRenders("{% if x > 3 %}a{% else %}b{% endif %}", "b")

    def test_in_none(self):
        self.assertRenders('{{ "a" in none }}', "False")
        self.assertRenders('{{ "a" not in none }}', "True")
        self.assertRenders("{{ x in y }}{{ x not in y }}", "FalseTrue", x=1)


class Req13_malformed_expressions(_Base):
    """Empty or malformed expressions raise `TemplateSyntaxError`."""

    def test_malformed(self):
        for src in [
            "{{ }}",
            "{{  }}",
            "{{ x y }}",
            "{{ (x }}",
            "{{ x) }}",
            "{{ x == }}",
            "{{ == x }}",
            "{{ x and }}",
            "{{ or x }}",
            "{{ not }}",
            "{{ x| }}",
            "{{ x|upper( }}",
            "{{ x|default(y }}",
            "{{ 1 + 2 }}",
            "{{ () }}",
            "{% if %}{% endif %}",
            "{% if x %}{% elif %}{% endif %}",
            "{% for x in %}{% endfor %}",
            "{% for x in a b %}{% endfor %}",
        ]:
            self.assertSyntaxError(src)

    def test_line(self):
        self.assertSyntaxError("a\n\n{{ x y }}", line=3)


class Req14_if_elif_else(_Base):
    """`{% if %}`, any number of `{% elif %}`, optional `{% else %}`, `{% endif %}`."""

    def test_branches(self):
        t = Template("{% if a %}A{% elif b %}B{% elif c %}C{% else %}E{% endif %}")
        self.assertEqual(t.render(a=1, b=1, c=1), "A")
        self.assertEqual(t.render(b=1, c=1), "B")
        self.assertEqual(t.render(c=1), "C")
        self.assertEqual(t.render(), "E")

    def test_without_else(self):
        t = Template("[{% if a %}A{% elif b %}B{% endif %}]")
        self.assertEqual(t.render(b=1), "[B]")
        self.assertEqual(t.render(), "[]")

    def test_nested(self):
        t = Template("{% if a %}{% if b %}AB{% elif c %}AC{% endif %}{% elif c %}C{% endif %}")
        self.assertEqual(t.render(a=1, c=1), "AC")
        self.assertEqual(t.render(c=1), "C")


class Req15_for_unpacking_and_else(_Base):
    """`{% for x in seq %}` / `{% for k, v in seq %}`: each item is unpacked; a wrong number
    of values or a non-iterable item raises `TemplateRenderError`; optional `{% else %}`
    rendered when the sequence is empty or None."""

    def test_unpacking(self):
        self.assertRenders("{% for k, v in xs %}{{ k }}={{ v }};{% endfor %}", "a=1;b=2;",
                           xs=[("a", 1), ("b", 2)])
        self.assertRenders("{% for a, b, c in xs %}{{ c }}{{ b }}{{ a }}{% endfor %}", "321",
                           xs=[[1, 2, 3]])

    def test_unpacking_errors(self):
        self.assertRenderError("{% for k, v in xs %}{% endfor %}", xs=[(1, 2, 3)])
        self.assertRenderError("{% for k, v in xs %}{% endfor %}", xs=[(1,)])
        self.assertRenderError("{% for k, v in xs %}{% endfor %}", xs=[5])

    def test_else(self):
        src = "{% for x in xs %}{{ x }}{% else %}empty{% endfor %}"
        self.assertRenders(src, "12", xs=[1, 2])
        self.assertRenders(src, "empty", xs=[])
        self.assertRenders(src, "empty", xs=None)
        self.assertRenders(src, "empty")

    def test_none_without_else(self):
        self.assertRenders("[{% for x in xs %}{{ x }}{% endfor %}]", "[]", xs=None)


class Req16_for_iteration_values(_Base):
    """Strings iterate characters and dicts iterate keys; any other non-iterable value
    (except None) raises `TemplateRenderError`."""

    def test_string(self):
        self.assertRenders("{% for c in s %}<{{ c }}>{% endfor %}", "<a><b>", s="ab")

    def test_dict(self):
        self.assertRenders("{% for k in d %}{{ k }}{% endfor %}", "xy", d={"x": 1, "y": 2})

    def test_tuple(self):
        self.assertRenders("{% for x in t %}{{ x }}{% endfor %}", "12", t=(1, 2))

    def test_non_iterable(self):
        self.assertRenderError("{% for x in n %}{% endfor %}", n=5)
        self.assertRenderError("{% for x in n %}{% else %}e{% endfor %}", n=2.5)
        self.assertRenderError("{% for x in n %}{% endfor %}", n=True)


class Req17_loop_variable(_Base):
    """Inside a loop `loop.index` (from 1), `loop.index0`, `loop.first`, `loop.last` and
    `loop.length` are available; in nested loops `loop` is the innermost one."""

    def test_loop_attributes(self):
        src = "{% for x in xs %}{{ loop.index }}{{ loop.index0 }}{{ loop.first }}{{ loop.last }}{{ loop.length }};{% endfor %}"
        self.assertRenders(src, "10TrueFalse3;21FalseFalse3;32FalseTrue3;", xs="abc")

    def test_single_item(self):
        self.assertRenders("{% for x in xs %}{{ loop.first }}{{ loop.last }}{% endfor %}",
                           "TrueTrue", xs=[1])

    def test_in_conditions(self):
        src = "{% for x in xs %}{{ x }}{% if not loop.last %}, {% endif %}{% endfor %}"
        self.assertRenders(src, "a, b, c", xs=["a", "b", "c"])

    def test_nested_innermost(self):
        src = "{% for a in xs %}{% for b in ys %}{{ loop.index }}/{{ loop.length }} {% endfor %}{% endfor %}"
        self.assertRenders(src, "1/3 2/3 3/3 1/3 2/3 3/3 ", xs=[1, 2], ys=[1, 2, 3])

    def test_outer_loop_restored_after_inner(self):
        src = "{% for a in xs %}{% for b in ys %}{% endfor %}{{ loop.index }}{% endfor %}"
        self.assertRenders(src, "12", xs=["p", "q"], ys=[1, 2, 3])


class Req18_loop_scoping(_Base):
    """Loop variables disappear after the loop and do not overwrite outer variables
    permanently."""

    def test_disappear(self):
        self.assertRenders("{% for x in xs %}{% endfor %}[{{ x }}][{{ loop.index }}]", "[][]", xs=[1, 2])
        self.assertRenders("{% for k, v in xs %}{% endfor %}[{{ k }}{{ v }}]", "[]", xs=[(1, 2)])

    def test_outer_restored(self):
        self.assertRenders("{{ x }}{% for x in xs %}{{ x }}{% endfor %}{{ x }}", "o12o", x="o", xs=[1, 2])
        self.assertRenders("{% for loop in xs %}{% endfor %}{{ loop }}", "L", loop="L", xs=[1])

    def test_outer_visible_inside(self):
        self.assertRenders("{% for x in xs %}{{ p }}{{ x }}{% endfor %}", "-1-2", p="-", xs=[1, 2])


class Req19_block_syntax_errors(_Base):
    """Syntax errors (`.line` = line of the offending tag): unknown tag, `elif`/`else`/
    `endif`/`endfor` that do not match the innermost open block (including `elif` after
    `else` and a second `else`), and a block still open at the end of the template (line of
    its opening tag, innermost open block first)."""

    def test_unknown_tag(self):
        self.assertSyntaxError("one\ntwo\n{% bogus %}", line=3)
        self.assertSyntaxError("{% endwhile %}", line=1)

    def test_unmatched_closers(self):
        self.assertSyntaxError("a\n{% endif %}", line=2)
        self.assertSyntaxError("a\n{% endfor %}", line=2)
        self.assertSyntaxError("a\n{% else %}", line=2)
        self.assertSyntaxError("a\n{% elif x %}", line=2)

    def test_mismatched_innermost(self):
        self.assertSyntaxError("{% if a %}\n{% for x in y %}\n{% endif %}\n{% endfor %}", line=3)
        self.assertSyntaxError("{% for x in y %}\n{% if a %}\n{% endfor %}\n{% endif %}", line=3)
        self.assertSyntaxError("{% for x in y %}\n{% elif a %}\n{% endfor %}", line=2)

    def test_elif_after_else(self):
        self.assertSyntaxError("{% if a %}\n{% else %}\n{% elif b %}\n{% endif %}", line=3)

    def test_second_else(self):
        self.assertSyntaxError("{% if a %}\n{% else %}\n{% else %}\n{% endif %}", line=3)
        self.assertSyntaxError("{% for x in y %}\n{% else %}\n{% else %}\n{% endfor %}", line=3)

    def test_for_else_then_elif(self):
        self.assertSyntaxError("{% for x in y %}\n{% else %}\n{% elif b %}\n{% endfor %}", line=3)

    def test_unclosed_blocks(self):
        self.assertSyntaxError("{% if x %}\nbody", line=1)
        self.assertSyntaxError("a\n{% for x in y %}\nbody", line=2)
        self.assertSyntaxError("{% if a %}\n{% for x in y %}\n", line=2)
        self.assertSyntaxError("{% for x in y %}\n{% if a %}\n{% elif b %}\n", line=2)
        self.assertSyntaxError("{% if a %}\n{% for x in y %}{% endfor %}\n", line=1)

    def test_valid_nesting_ok(self):
        Template("{% if a %}{% for x in y %}{% else %}{% endfor %}{% elif b %}{% else %}{% endif %}")


if __name__ == "__main__":
    unittest.main()
