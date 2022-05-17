import logging
from yex.control.parameter import C_Parameter
import yex.exception

logger = logging.getLogger('yex.general')

# This file is for the data structure that holds the controls.
# You might be looking for yex.control.tab, which defines
# controls that typeset tablature.

class ControlsTable:
    """
    A set of named commands.

    Initially the set is empty; you can add to it either using
    the `insert` method, or the `|=` operator.
    """

    def __init__(self):
        self.contents = {}

    def __getitem__(self, field,
            ):
        """
        Returns the control with the given name.

        Raises KeyError if there's no such control.
        """
        if field not in self.contents:
            raise KeyError(field)

        result = self.contents[field]

        if isinstance(result, C_Parameter):
            logger.debug(
                    "get value of parameter %s==%s",
                    field, result)

            return result
        else:
            logger.debug(
                    "get value of control %s==%s",
                    field, result)
            return result

    def __setitem__(self, field, value):
        """
        If "field" is a Parameter, sets its value to
        "value".

        Otherwise, sets the control "field" to "value".
        If "value" is not callable, raises ValueError.
        Setting a control to None deletes it.
        """

        current = self.contents.get(field, None)

        if current is not None and isinstance(current, C_Parameter):

            logger.debug("setting parameter %s=%s",
                    field, value)
            current.value = value
            return

        logger.debug("setting control %s=%s",
                field, value)

        if value is None:
            try:
                del self.contents[field]
            except KeyError:
                raise yex.exception.YexError(
                        f"can't remove control {field}, "
                        "because it doesn't exist anyway")
            return

        if current:
            logger.debug("  -- overwriting %s",
                    current)

        try:
            value.__call__ # just lookup, don't call it
        except AttributeError:
            raise ValueError(
                    f"Can't set control {field} to {value} "
                    f"because that's not a control but a {type(value)}.")

        self.contents[field] = value

    def __ior__(self, to_merge):
        """
        The |= operator. It merges us with
        another ControlTable, or a dict mapping strings to commands.
        """
        if not isinstance(to_merge, dict):
            to_merge = to_merge.contents

        self.contents |= to_merge
        return self

    def __contains__(self, field):
        """
        Checks whether there's a control with a particular name.
        """
        return field in self.contents

    def keys(self):
        return self.contents.keys()

def display_keywords():
    def screen_width():
        try:
            import sys,fcntl,termios,struct
            data = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, '1234')
            return struct.unpack('hh',data)[1]
        except:
            return 80

    count = 0
    s = yex.document.Document()

    header_line = FORMAT % (
            '= keyword =',
            ''.join([x[0].upper() for x in MODES])+'x',
            '= module =',
            '= value =',
            )

    for i, k in enumerate(KEYWORDS):

        if i%10==0:
            print()
            print(header_line)
            print()

        result = s.get(k)

        if result is None:
            # maybe a register
            result = s.get(k+'1')

        if result is None:
            module = ' * MISSING * '
        else:
            module = result.__class__.__module__.split('.')[-1]

        if isinstance(result, yex.control.C_Expandable):
            flags = '-'*len(MODES)+'x'
        else:
            flags = ''

            for mode in [
                    'vertical',
                    'horizontal',
                    'math',
                    ]:

                try:
                    modeflag = getattr(result, mode)
                except AttributeError:
                    flags += '?'
                    continue

                if modeflag==True:
                    flags += '*'
                elif modeflag==False:
                    flags += ' '
                elif modeflag==None:
                    flags += '^'
                else:
                    flags += mode[0].upper()

            flags += '-'

        print(FORMAT % (
            k,
            flags,
            module,
            result
            ))

        if result is not None:
            count += 1

    print()
    print('Keywords:', len(KEYWORDS))
    print('Found: %d (%g%%)' % (
        count,
        (count/len(KEYWORDS))*100
        ))
