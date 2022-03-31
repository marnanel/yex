from yex.font.font import Font

class Nullfont(Font):
    """
    A font that does nothing much.
    """

    def __init__(self,
            *args, **kwargs,
            ):

        super().__init__(*args, **kwargs)

        class NullfontMetrics:
            def __init__(self):
                self.dimens = {}

        self.metrics = NullfontMetrics()
        self.scale = None
        self.name = 'nullfont'
