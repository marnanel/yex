import mex.value

class Gismo:

    shifted_by = mex.value.Dimen()

    def __init__(self, width=0, height=0, depth=0):
        self.width = width
        self.height = height
        self.depth = depth

    def showbox(self):
        r"""
        Returns a list of strings which should be displayed by \showbox
        for this gismo.
        """
        return ['\\'+self.__class__.__name__.lower()]

class DiscretionaryBreak(Gismo):

    discardable = False
    width = height = depth = mex.value.Dimen(0)

    def __init__(self,
            prebreak,
            postbreak,
            nobreak,
            ):
        self.prebreak = prebreak
        self.postbreak = postbreak
        self.nobreak = nobreak

    def __repr__(self):
        return (
                f'[discretionary break: pre={self.prebreak} '
                f'post={self.postbreak} / no={self.nobreak}]'
                )

class Whatsit(Gismo):

    discardable = False
    width = height = depth = mex.value.Dimen(0)

    def __call__(self):
        raise NotImplementedError()

class VerticalMaterial(Gismo):

    discardable = False
    width = height = depth = mex.value.Dimen(0)

    def __repr__(self):
        return f'[Vertical material]'

class C_Box(Gismo):
    """
    Superclass of all Boxes.
    """
    discardable = False

class Leader(Gismo):
    """
    Leaders, although at present this only wraps Glue.
    """

    discardable = True
    height = depth = mex.value.Dimen(0)
    # width passes through to contents

    def __init__(self, *args, **kwargs):
        self.contents = mex.value.Glue(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self.contents, attr)

    def __repr__(self):
        return '[...]'

class Kern(Gismo):

    discardable = True
    width = height = depth = mex.value.Dimen(0)

    def __init__(self, width):
        self.width = width

    def __repr__(self):
        return f'[kern: {self.width.value}]'

    def showbox(self):
        return [r'\kern %.5g' % (
            float(self.width/65536.0),)]

class Penalty(Gismo):

    discardable = True
    width = height = depth = mex.value.Dimen(0)

    def __init__(self, demerits):
        self.demerits = demerits

    def __repr__(self):
        return f'[penalty: {self.demerits}]'

class MathSwitch(Gismo):

    discardable = True
    width = height = depth = mex.value.Dimen(0)

    def __init__(self, which):
        self.which = which

    def __repr__(self):
        if self.which:
            return '[math on]'
        else:
            return '[math off]'
