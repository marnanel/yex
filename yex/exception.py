class YexError(Exception):

    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message

class ParseError(YexError):
    pass

class MacroError(YexError):
    pass

class RunawayExpansionError(ParseError):
    pass
