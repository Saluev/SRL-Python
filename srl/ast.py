import abc
import six


@six.add_metaclass(abc.ABCMeta)
class Node(object):
    @abc.abstractmethod
    def translate(self, context):
        pass


class AnyOfExpressions(Node):
    def __init__(self, choices):
        self.choices = choices

    def __str__(self):
        return "any of (%s)" % self.choices

    def translate(self, context):
        translated_choices = "|".join(
            choice.translate(context)
            for choice in self.choices
        )
        return "(?:%s)" % translated_choices


class Digit(Node):
    def __str__(self):
        return "digit"

    def __invert__(self):
        return NotDigit()

    def translate(self, context):
        return "\d"


class Expression(Node):
    def __init__(self, begins_with, expressions, must_end):
        self.begins_with = begins_with
        self.expressions = expressions
        self.must_end = must_end

    def __str__(self):
        begins_with = "begins_with " if self.begins_with else ""
        must_end = ", must end" if self.must_end else ""
        return "%s%s%s" % (begins_with, self.expressions, must_end)

    def translate(self, context):
        begins_with = "^" if self.begins_with else ""
        must_end = "$" if self.must_end else ""
        expressions = self.expressions.translate(context)
        return "%s%s%s" % (begins_with, expressions, must_end)


class Letter(Node):
    def __str__(self):
        return "letter"

    def __invert__(self):
        return NotLetter()

    def translate(self, context):
        return r"[^\W\d_]"


class ListOfExpressions(Node):
    def __init__(self, expressions):
        self.expressions = expressions

    def __str__(self):
        return ", ".join(map(str, self.expressions))

    def translate(self, context):
        return "".join(expr.translate(context) for expr in self.expressions)


class LiterallyExpression(Node):
    def __init__(self, literal):
        self.raw_literal = literal
        self.literal = literal  # TODO escape symbols and shit

    def __str__(self):
        return "literally %s" % self.raw_literal

    def translate(self, context):
        return self.literal


class NotDigit(Node):
    def __str__(self):
        return "not digit"

    def __invert__(self):
        return Digit()

    def translate(self, context):
        return "\D"


class NotExpression(Node):
    def __init__(self, expression):
        self.expression = expression

    def __str__(self):
        return "not %s" % self.expression

    def translate(self, context):
        if hasattr(self.expression, "__invert__"):
            return (~self.expression).translate(context)
        return "(?!%s)" % self.expression.translate(context)


class NotLetter(Node):
    def __str__(self):
        return "letter"

    def __invert__(self):
        return Letter()

    def translate(self, context):
        return r"[\W\d_]"


class NotOneOfCharacters(Node):
    def __init__(self, characters):
        self.raw_characters = characters
        self.characters = characters  # TODO

    def __str__(self):
        return "not one of %s" % self.raw_characters

    def __invert__(self):
        return OneOfCharacters(self.raw_characters)

    def translate(self, context):
        return "[^%s]" % self.characters


class NotWhitespace(Node):
    def __str__(self):
        return "whitespace"

    def __invert__(self):
        return Whitespace()

    def translate(self, context):
        return "\S"


class OneOfCharacters(Node):
    def __init__(self, characters):
        self.raw_characters = characters
        self.characters = characters  # TODO

    def __str__(self):
        return "one of %s" % self.raw_characters

    def __invert__(self):
        return NotOneOfCharacters(self.raw_characters)

    def translate(self, context):
        return "[%s]" % self.characters


class Reference(Node):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def translate(self, context):
        return context.get(self.name).translate(context)


class RepeatedExpression(Node):
    def __init__(self, expression, modifier):
        self.expression = expression
        self.modifier = modifier

    def __str__(self):
        return "%s %s" % (self.expression, self.modifier)

    def translate(self, context):
        return self.expression.translate(context) # TODO modifiers


class SimpleRegularExpression(Node):
    def __init__(self, expression, settings):
        self.expression = expression
        self.settings = settings

    def __str__(self):
        return ", ".join([str(self.expression), str(self.settings)])

    def translate(self, context):
        code = self.expression.translate(context)
        # TODO compile settings into (?iLmsux) construction?


class Whitespace(Node):
    def __str__(self):
        return "whitespace"

    def __invert__(self):
        return NotWhitespace()

    def translate(self, context):
        return "\s"
