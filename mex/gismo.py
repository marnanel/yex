class Gismo:
    def show(self, f, depth):
        raise NotImplementedError()

# XXX what is \leaders ?

class DiscretionaryBreak(Gismo):
    discardable = False

    def __init__(self,
            prebreak,
            postbreak,
            nobreak,
            ):
        self.prebreak = prebreak
        self.postbreak = postbreak
        self.nobreak = nobreak

class Whatsit(Gismo):
    discardable = False

class VerticalMaterial(Gismo):
    discardable = False

class Kern(Gismo):
    discardable = True

class Penalty(Gismo):
    discardable = True

class MathSwitch(Gismo):
    discardable = True

    def __init__(self, which):
        self.which = which

    def __repr__(self):
        if self.which:
            return '[math on]'
        else:
            return '[math off]'
