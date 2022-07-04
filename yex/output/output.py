class Output:

    filename_extension = None

    def __init__(self,
            filename):
        pass

    def render(self,
            boxes):
        raise NotImplementedError()

    @classmethod
    def can_handle(cls, file_extension):
        raise NotImplementedError()
