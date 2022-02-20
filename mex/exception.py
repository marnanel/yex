class MexError(Exception):

    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message

class ParseError(MexError):
    pass

class MacroError(MexError):
    pass
