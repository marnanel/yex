class Output:

    filename_extension = None

    def __init__(self,
            filename):
        pass

    def add_page(self,
            page):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
