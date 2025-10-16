from yex.font.font import Font, _Metrics, _Character, _Charset

class _NullfontMetrics(_Metrics):
    def __init__(self,
                 font:'Font',
                 ):
        import yex
        self.dimens = dict([
            (f, yex.value.Dimen()) for f in range(1, 8)])

class _NullfontCharset(_Charset):
    def __init__(self,
                 font:'Font',
                 ):
        pass

    def __getitem__(self,
                     codepoint: int,
                     ) -> 'Character':
        raise KeyError()

class Nullfont(Font):
    """
    A font that does nothing much.
    """

    metrics_class = _NullfontMetrics
    charset_class = _NullfontCharset

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
