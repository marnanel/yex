from yex.font.font import Font

class NullfontMetrics:
    def __init__(self):
        self.dimens = {}

    def get_character(self, n):
        raise KeyError("nullfont has no characters")

class Nullfont(Font):
    """
    A font that does nothing much.
    """

    def __init__(self,
            *args, **kwargs,
            ):

        super().__init__(*args, **kwargs)

        self.metrics = NullfontMetrics()
        self.scaled = None
        self.size = None
        self.name = 'nullfont'

    def __getstate__(self):
        return super().__getstate__(name = ['nullfont'])
