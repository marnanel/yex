"""
Macro controls.

These are controls for creating macros-- TeX's name for subroutines.
"""
import logging
from yex.control.control import Unexpandable
from yex.control.macro import *
import yex
import string

logger = logging.getLogger('yex.general')

class Def(Expandable):

    settings = set(('def',))

    def __call__(self, tokens):

        # Firstly, what flags have been used? There's a lot of them,
        # and they all have "settings" fields. We union them all together.
        # The ones with "def" in the settings field are terminal.

        settings = set(self.settings)

        while 'def' not in settings:

            token = tokens.next(
                    level = 'deep',
                    on_eof='raise',
                    )

            if not isinstance(token, yex.parse.Control):
                raise yex.exception.YexError(
                        fr"expected \def or similar, "
                        f"but got {token}")

            flag = tokens.doc.get(token.identifier,
                    default=None)

            if isinstance(flag, (Def, Global)):
                settings |= flag.settings
            else:
                raise yex.exception.YexError(
                        fr"expected \def or similar, "
                        f"but got {flag}")

        settings.remove('def')

        token = tokens.next(
                level = 'deep',
                on_eof='raise',
                )
        macro_name = token.ch

        logger.debug("defining new macro: %s; settings=%s",
                macro_name, settings,
                )

        if 'global' in settings:
            tokens.doc.next_assignment_is_global = True

        # Next, let's find the parameters.

        definition_extension = []

        try:
            macro_name = token.identifier
        except NotImplementedError:
            raise yex.exception.WeirdDefNameError(
                    problem = token,
                    )

        logger.debug("  -- macro name: %s", macro_name)
        parameter_text = [ [] ]
        param_count = 0

        deep = tokens.another(level='deep',
                on_eof='raise',
                )

        for token in deep:
            logger.debug("  -- param token: %s", token)

            if isinstance(token, yex.parse.BeginningGroup):
                deep.push(token)
                break
            elif isinstance(token, yex.parse.Control):
                try:
                    if tokens.doc.controls[token.identifier].is_outer:
                        raise yex.exception.MacroError(
                                "outer macros not allowed in param lists")
                except KeyError:
                    pass # Control doesn't exist, so can't be outer

                parameter_text[-1].append(token)

            elif isinstance(token, yex.parse.Parameter):

                which = deep.next()

                if isinstance(which, yex.parse.BeginningGroup):
                    # Special case. See "A special extension..." on
                    # p204 of the TeXbook.
                    logger.debug(
                            "  -- #{ -- see TeXbook p204: %s", token)
                    parameter_text[-1].append(which)
                    definition_extension.append(which)
                    deep.push(which)
                    break

                elif which.ch not in string.digits:
                    raise yex.exception.ParseError(
                            f"parameters can only be named with digits "
                            f"(not {which})"
                            )

                elif int(which.ch) != param_count+1:
                    raise yex.exception.ParseError(
                            rf"{self.name}\{macro_name}: "
                            "parameters must occur in ascending order "
                            f"(found {which.ch}, needed {param_count+1})"
                            )
                else:
                    parameter_text.append( [] )
                    param_count += 1
            else:
                parameter_text[-1].append(token)

        logger.debug("  -- parameter_text: %s", parameter_text)

        # now the definition
        definition = []

        if 'expanded' in settings:
            level = 'expanding'
        else:
            level = 'deep'

        starts_at = None
        def_tokens = tokens.another(
                bounded='single',
                on_eof='exhaust',
                level = level,
                no_outer=True,
                )

        for token in def_tokens:

            logger.debug("  -- definition token: %s", token)

            if isinstance(token, yex.parse.Parameter):
                second = def_tokens.next()

                replace = token.handle_second(second,
                        max_index = len(parameter_text),
                        )

                if replace is not None:
                    definition.append(replace)
                else:
                    definition.append(token)
                    definition.append(second)

            else:
                definition.append(token)

            if starts_at is None:
                starts_at = tokens.location

        definition.extend(definition_extension)
        logger.debug("  -- definition: %s", definition)

        new_macro = Macro(
                doc = self.doc,
                name = macro_name,
                definition = definition,
                parameter_text = parameter_text,
                starts_at = starts_at,
                is_outer = 'outer' in settings,
                is_expanded = 'expanded' in settings,
                is_long = 'long' in settings,
                )

        logger.debug("  -- object: %s", new_macro)

        tokens.doc[macro_name] = new_macro

# These are all forms of definition,
# so they're handled as Def.

class Outer(Def):
    settings = set(('outer',))

class Gdef(Def):
    settings = set(('global', 'def'))

class Long(Def):
    settings = set(('long',))

class Edef(Def):
    settings = set(('expanded', 'def'))

class Xdef(Def):
    settings = set(('expanded', 'global', 'def'))

class Global(Expandable):
    settings = set(('global', ))
    def __call__(self, tokens):
        tokens.doc.next_assignment_is_global = True
