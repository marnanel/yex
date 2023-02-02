from yex.font.font import Font

class NullfontMetrics:
    def __init__(self):
        import yex
        self.dimens = dict([
            (f, yex.value.Dimen()) for f in range(1, 8)])

    def get_character(self, n):
        raise KeyError("nullfont has no characters")

class Nullfont(Font):
    """
    A font that does nothing much.
    """

    def __init__(self,
            *args, **kwargs,
            ):

        super().__init__(
                name = 'nullfont',
                source = 'nullfont',
                *args, **kwargs)

        self.metrics = NullfontMetrics()
        self.size = None
        self.scale = None

    def __getstate__(self):
        return super().__getstate__(name = ['nullfont'])
