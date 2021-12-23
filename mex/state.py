import collections
import copy

class State:

    def __init__(self):
        self.values = [{
                'count': [0] * 256,
                'dimen': [0] * 256,
                'skip': [0] * 256,
                'muskip': [0] * 256,
                'charcode': self.default_code_table(),
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

        raise ValueError(f"Unknown field: {field}")

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

        raise ValueError(f"Unknown field: {field}")

    def begin_group(self):
        self.values.append(copy.copy(self.values[-1]))

    def end_group(self):
        self.values.pop()

    def default_code_table(self):

        result = {
                "\\":  0, # Escape character
                '{':   1, # Beginning of group
                '}':   2, # Beginning of group
                '$':   3, # Beginning of group
                '&':   4, # Beginning of group
                '\n':  5, # End of line
                '#':   6, # Parameter
                '^':   7, # Superscript
                '_':   8, # Subscript
                '\0':  9, # Ignored character
                ' ':  10, # Space
                # 11: Letter
                # 12: Other
                '~':  13, # Active character
                '%':  14, # Comment character
                chr(127): 15, # Invalid character,
                }

        for pair in [
                ('a', 'z'),
                ('A', 'Z'),
            ]:

            for c in range(ord(pair[0]), ord(pair[1])):
                result[chr(c)] = 11 # Letter

        return collections.defaultdict(
                lambda: 12, # Other
                result)
