import logging
import mex.parameter

commands_logger = logging.getLogger('mex.commands')

class ControlsTable:
    """
    A set of named commands.

    Initially the set is empty; you can add to it either using
    the insert() method, or the |= operator.
    """

    def __init__(self):
        self.contents = {}

    def __getitem__(self, field,
            the_object_itself=True,
            ):
        """
        Returns the control with the given name.

        Raises KeyError and logs a warning if there's no such control.
        """
        if field not in self.contents:
            commands_logger.warning(
                    "get value of control %s, which doesn't exist",
                    field)
            raise KeyError(field)

        result = self.contents[field]

        if isinstance(result, mex.parameter.Parameter):
            commands_logger.debug(
                    "get value of parameter %s==%s",
                    field, result)

            if the_object_itself:
                return result
            else:
                return result.value
        else:
            commands_logger.debug(
                    "get value of control %s==%s",
                    field, result)
            if not the_object_itself:
                commands_logger.warning(
                        "the_object_itself is not honoured for controls: %s",
                        field)

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

        if current is not None and isinstance(current,
                mex.parameter.Parameter):

            commands_logger.debug("setting parameter %s=%s",
                    field, value)
            current.value = value
            return

        commands_logger.debug("setting control %s=%s",
                field, value)

        if value is None:
            del self.contents[field]
            return

        if current:
            commands_logger.debug("  -- overwriting %s",
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
