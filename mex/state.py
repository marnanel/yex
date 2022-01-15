import copy

class State:

    def __init__(self):
        self.values = [{
                'count': [0] * 256,
                'dimen': [0] * 256,
                'skip': [0] * 256,
                'muskip': [0] * 256,
                }]

    def __setitem__(self, field, value,
            use_global = False):

        if use_global:
            values_number = 0
        else:
            values_number = -1

        for prefix in [
                'count',
                'dimen',
                'skip',
                'muskip',
                ]:

            if field.startswith(prefix):
                index = int(field[len(prefix):])

                if value<-2**31 or value>2**31:
                    raise ValueError(
                            f"Assignment to {field} is out of range: "+\
                                    "{value}")

                self.values[values_number][prefix][index] = value

                return

        if field.startswith('charcode'):
            index = int(field[9:])
            self.values[-1]['charcode'][chr(index)] = value
            return

        if ' ' in field:
            result = self.values[-1]
            parts = field.split(' ')
            for part in parts[:-1]:
                result = result[part]
            result[parts[-1]] = value
            return

        raise KeyError(f"Unknown field: {field}")

    def __getitem__(self, field,
            use_global = False):

        if use_global:
            values_number = 0
        else:
            values_number = -1

        for prefix in [
                'count',
                'dimen',
                'skip',
                'muskip',
                ]:

            if field.startswith(prefix):
                index = int(field[len(prefix):])

                return self.values[values_number][prefix][index]

        if field.startswith('charcode'):
            index = int(field[9:])
            return self.values[-1]['charcode'][chr(index)]

        if ' ' in field:
            try:
                result = self.values[-1]
                for part in field.split(' '):
                    result = result[part]
                return result
            except KeyError:
                return None

        return None

    def begin_group(self):
        self.values.append(copy.deepcopy(self.values[-1]))

    def end_group(self):
        self.values.pop()

    def add_state(self, name, value):
        self.values[-1][name] = value
