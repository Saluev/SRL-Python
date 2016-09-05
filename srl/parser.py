import functools
import logging
import re
from srl import ast


word = re.compile(r"(\w+)\s+(.*)", re.DOTALL)
string_literal = re.compile(r"""('(?:[^'\\]|\\.)*?'|"(?:[^"\\]|\\.)*?")\s*(.*)""", re.DOTALL)


def return_none_on_unpack_fail(func):
    @functools.wraps(func)
    def my_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError as err:
            if "NoneType" in str(err):
                return None
            raise err


def autolog(func):
    @functools.wraps(func)
    def logged_func(src):
        logging.getLogger("srl.parser").debug("%s <- %s", func.__name__, src)
        result = list(func(src))
        logging.getLogger("srl.parser").debug("%s -> %r", func.__name__, list(result))
        return result
    return logged_func


def join(*funcs):
    if len(funcs) == 1 and hasattr(funcs[0], "next"):
        funcs = tuple(funcs[0])
    if len(funcs) == 0:
        def result(src):
            yield (), src
        return result
    def result(src):
        for arg1, src in funcs[0](src):
            for others, src in join(*funcs[1:])(src):
                yield (arg1,) + others, src
    return result


@autolog
def parse_srl(src):
    for expression, src in parse_expression(src):
        break
    else:
        return
    settings = None
    for (_, settings), src in join(parse_comma, parse_settings)(src):
        pass  # do something with settings
    yield ast.SimpleRegularExpression(expression, settings), src


@autolog
def parse_atomic_expression(src):
    for (_, literal), src in join(parse_word("literally"), parse_string_literal)(src):
        yield ast.LiterallyExpression(literal), src
        return
    for (_, list_of_expressions, _), src in join(
        parse_words("any of ("), parse_list_of_expressions, parse_word(")"))(src):
        yield ast.AnyOfExpressions(list_of_expressions), src
        return
    for (_, literal), src in join(parse_words("one of"), parse_string_literal)(src):
        yield ast.OneOfCharacters(literal), src
        return
    for (_, expression), src in join(parse_word("not"), parse_atomic_expression)(src):
        yield ast.NotExpression(expression), src
        return
    for (_, list_of_expressions, _), src in join(
        parse_word("("), parse_list_of_expressions, parse_word(")"))(src):
        yield list_of_expressions, src
        return
    for name, src in parse_any_word(src):
        yield ast.Reference(name), src  # TODO create reference-to-expression
        return


@autolog
def parse_any_word(src):
    match = word.match(src)
    if match:
        yield match.groups()


@autolog
def parse_comma(src):
    if src.startswith(","):
        yield ",", src[1:].lstrip()


@autolog
def parse_expression(src):
    if not src:
        # empty expression
        yield None, src
    begins_with = False
    for token, src in parse_words("begins with")(src):
        begins_with = True
    for list_of_expressions, src in parse_list_of_expressions(src):
        if begins_with and not list_of_expressions:
            return  # empty list is not acceptable after `begins with`
        break
    else:
        return
    must_end = False
    for _, src in parse_comma(src):
        for token, src in parse_words("must end")(src):
            must_end = True
    yield ast.Expression(begins_with, list_of_expressions, must_end), src


@autolog
def parse_list_of_expressions(src):
    result = []
    # first expression is not preceded with comma (if present at all)
    for expression, src in parse_repeated_expression(src):
        result.append(expression)
        break
    else:
        yield ast.ListOfExpressions(result), src

    # further expressions are preceded with comma
    failed = False
    while src and not failed:
        for (_, expression), src in join(parse_comma, parse_repeated_expression)(src):
            result.append(expression)
            break
        else:
            failed = True
    yield ast.ListOfExpressions(result), src


@autolog
def parse_repeated_expression(src):
    for expression, src in parse_atomic_expression(src):
        for modifier, src in parse_repetition_modifier(src):
            yield ast.RepeatedExpression(expression, modifier), src
            return
        yield expression, src


@autolog
def parse_repetition_modifier(src):
    # once or more, at least n, at most n, ...
    for words, src in parse_words("once or more")(src):
        yield "once or more", src  # TODO return ast.OnceOrMoreModifier()
        return
    # TODO at lest, once, ...


@autolog
def parse_settings(src):
    # TODO comma-separated list of specifiers
    for (_, sensitivity), src in parse_words("case insensitive"):
        yield {"sensitive": False}, src
        return
    for (_, sensitivity), src in parse_words("case sensitive"):
        yield {"sensitive": True}, src
        return


@autolog
def parse_string_literal(src):
    match = string_literal.match(src)
    if match:
        yield match.groups()


def parse_word(word):
    if word is any:
        return parse_any_word
    def result(src):
        l = len(word)
        if src[:l].lower() == word.lower():
            yield src[:l], src[l:].lstrip()
    result.__name__ = "parse_word_%s" % word
    return autolog(result)


def parse_words(words):
    if isinstance(words, basestring):
        words = filter(None, map(str.strip, words.split(" ")))
    result = join(parse_word(word) for word in words)
    result.__name__ = "parse_words_%s" % ("_".join(w.lower() for w in words) or "EMPTY")
    return autolog(result)
