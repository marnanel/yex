from yex.box import *

def pretty_list_dump(items):
    class ListDumper:
        def __init__(self, items):
            self.items = items

        def __str__(self):
            result = []

            glue = [x for x in self.items if isinstance(x, Leader)]
            if glue:
                first_glue = glue[0]
            else:
                first_glue = None

            for item in self.items:
                if hasattr(item, 'ch'):
                    result.append(item.ch)
                elif item==first_glue:
                    result.append('_')
                elif isinstance(item, Breakpoint) and item.number is None:
                    result.append('^')
                else:
                    result.append(str(item))

            return ' '.join([str(x) for x in result])

    return ListDumper(items)
