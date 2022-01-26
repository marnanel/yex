import copy

class ControlsTable(dict):
    def __setitem__(self, field, value):
        self[field].value = value

    def set_from(self, field, tokens):
        self[field].set_from(tokens)

    def __deepcopy__(self, memo):
        # This is slightly reimplemented only to avoid
        # copy.deepcopy() deciding to call our __setitem__.
        newbie = ControlsTable([
            (f,copy.deepcopy(v, memo))
            for f,v in self.items()])
        return newbie
