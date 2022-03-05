class Gismo:
    def show(self, f, depth):
        raise NotImplementedError()

# TODO leaders

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

    def __repr__(self):
        return (
                f'[discretionary break: pre={self.prebreak} '
                f'post={self.postbreak} / no={self.nobreak}]'
                )

class Whatsit(Gismo):
    discardable = False

    def __init__(self, distance):
        raise NotImplementedError()

class VerticalMaterial(Gismo):
    discardable = False

    def __repr__(self):
        return f'[Vertical material]'

class C_Box(Gismo):
    discardable = False

class Kern(Gismo):
    discardable = True

    def __init__(self, distance):
        self.distance = distance

    def __repr__(self):
        return f'[kern: {self.distance.value}]'

class Penalty(Gismo):
    discardable = True

    def __init__(self, demerits):
        self.demerits = demerits

    def __repr__(self):
        return f'[penalty: {self.demerits}]'

class MathSwitch(Gismo):
    discardable = True

    def __init__(self, which):
        self.which = which

    def __repr__(self):
        if self.which:
            return '[math on]'
        else:
            return '[math off]'
