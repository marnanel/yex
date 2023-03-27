import logging
from yex.control.control import Control
from yex.control.parameter import Parameter
import yex.exception

logger = logging.getLogger('yex.general')

# This file is for the data structure that holds the controls.
# You might be looking for yex.control.keyword.tab, which defines
# controls that typeset tablature.

class ControlsTable:
    """
    A set of named commands.

    Initially the set is empty; you can add to it either using
    the `insert` method, or the `|=` operator.
    """

    def __init__(self, **kwargs):
        self.contents = {}
        self.kwargs = kwargs

    def __getitem__(self, field):
        return self.get(field=field)

    def get(self,
            field,
            param_control = False,
            ):
        r"""
        Returns the control with the given name.

        Args:
            field (`str`): the name of the control to find.
            param_control (bool): if True, requests for parameter controls
                return the control object itself, as with any other control.
                If False, which is the default, they return the value
                stored in the control object; this is probably what
                you wanted.

        Raises:
            KeyError: if there's no such control.
        """

        if field not in self.contents:
            raise KeyError(field)

        result = self._get_and_maybe_instantiate(field)

        if isinstance(result, Parameter):

            if param_control:
                logger.debug(
                        "get parameter control %s==%s (rather than its value)",
                        field, result)
                return result
            else:
                logger.debug(
                        "get value of parameter %s==%s",
                        field, result)
                return result.value
        else:
            logger.debug(
                    "get control %s==%s",
                    field, str(result))
            return result

    def _get_and_maybe_instantiate(self, field):
        result = self.contents[field]

        if hasattr(result, '__subclasses__'):
            # this is a type object; instantiate it
            try:
                result = result(**self.kwargs)
            except TypeError as te:
                raise yex.exception.YexInternalError(
                        f"Couldn't initialise {result} "
                        f"with {self.kwargs} "
                        f"for {field}: {te}")
            self.contents[field] = result

            logger.debug('instantiated %s: %s', field, result)

        return result

    def __setitem__(self, field, value):
        """
        If "value" is a dict, use it to set the value of the control
        named "field". Possible fields in this dict are described below.

        If "value" is a control, give it the name "field".

        If "value" is None, delete the name "field" from the list.

        Otherwise, if "field" is the name of a control, and that
        control is a parameter, set the value of the parameter to "value".
        If not, raises ValueError.

        Possible fields in "value", hereinafter "v", if "value" is a dict:

        If v['control'] exists, it's the name of the class to be
        instantiated. If that's a parameter, v['value'] can optionally
        be used to set its value at the same time.

        Otherwise, if v['font'] exists, this is a FontSetter, and
        v['font'] is the name of the font.

        Otherwise, if v['macro'] exists, this is a Macro, and
            v['macro'] is the macro definition.
        v['flags'] is an optional string, a space-separated list
            of one or more of ("long", "outer").
        v['starts_at'] is the position of the start of the macro definition
            and is optional.
        v['parameters'] is optional and describes the parameters. If it's
            an integer, it's the number of parameters. Otherwise, it's a list
            of the strings which delimit the arguments on a call; there's
            one more string than there are parameters, because there may
            be delimiters between the macro name and its first parameter.

        Otherwise, we raise ValueError.

        We may also raise KeyError if, for example, v['control'] is not
        the name of a control.
        """

        if isinstance(value, dict):

            if 'control' in value:
                item = yex.control.Control.from_serial(value)
            elif 'font' in value:
                item = yex.control.Font.from_serial(value)
            elif 'macro' in value:
                item = yex.control.Macro.from_serial(value)
            else:
                raise ValueError(
                        "Don't know how to deserialise this: %s" % (
                            value,))

            logger.debug("setting control %s=%s, from: %s",
                field, item, value,
                )

            self.contents[field] = item

            return

        elif value is None:
            try:
                del self.contents[field]
            except KeyError:
                raise yex.exception.YexError(
                        f"can't remove control {field}, "
                        "because it doesn't exist anyway")
            return

        if field in self.contents:
            current = self._get_and_maybe_instantiate(field)
        else:
            current = None

        if isinstance(current, Parameter):

            logger.debug("setting parameter %s=%s",
                    field, value)
            current.value = value
            return

        try:
            value.__call__ # just lookup, don't call it
        except AttributeError:
            raise ValueError(
                    f"Can't set control {field} to {value} "
                    f"because that's not a control but a {type(value)}.")

        logger.debug("setting control %s=%s",
                field, value)

        if current is None:
            logger.debug("  -- overwriting %s",
                    current)

        self.contents[field] = value

    def __delitem__(self, field):
        del self.contents[field]

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

    def items(self):
        return self.contents.items()

    def keys(self):
        return self.contents.keys()

    def value(self):
        """
        All the items in this table which don't have the default value.

        This can be used to recreate the table.
        """
        raise NotImplementedError()

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

        if isinstance(result, yex.control.Expandable):
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
