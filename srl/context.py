class Context(dict):
    def __init__(self, content=None, parent=None):
        self.parent = parent
        if content is None:
            content = {}
        dict.__init__(self, content)

    def __getitem__(self, which):
        try:
            return dict.__getitem__(self, which)
        except KeyError as err:
            if self.parent is not None:
                return self.parent[which]
            raise err

    def child(self):
        return Context(parent=self)

    def get(self, what, default=None):
        result = dict.get(self, what, default)
        if result is None and self.parent is not None:
            result = self.parent.get(what, default)
        return result


def default_context():
    from srl import ast
    return {
        "digit": ast.Digit(),
        "letter": ast.Letter(),
        "whitespace": ast.Whitespace(),
    }
