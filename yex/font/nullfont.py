from yex.font.font import Font, Metrics, Character

class NullfontMetrics(Metrics):
    def __init__(self,
                 font:'Font',
                 ):
        import yex
        self.dimens = dict([
            (f, yex.value.Dimen()) for f in range(1, 8)])

class Nullfont(Font):
    """
    A font that does nothing much.
    """

    metrics_class = NullfontMetrics

    def __init__(self,
            *args, **kwargs,
            ):

        super().__init__(
                name = 'nullfont',
                source = 'nullfont',
                *args, **kwargs)

        self.size = None
        self.scale = None

    def __getstate__(self) -> dict:
        return super().__getstate__(name = ['nullfont'])

    def __getitem__(self, v):
        if isinstance(v, str):
            return None
        else:
            return __super__().__getitem__(v)
