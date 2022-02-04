class MexError(Exception):

    def __init__(self, message, tokeniser):
        self.message = message
        self.tokeniser = tokeniser

    def __str__(self):
        return self.tokeniser.error_position(
                message = self.message,
                )

    def __repr__(self):
        return self.__str__()

class ParseError(MexError):
    pass

class MacroError(MexError):
    pass
