class Output:

    filename_extension = None

    def __init__(self,
            filename):
        pass

    def render(self,
            boxes):
        raise NotImplementedError()
