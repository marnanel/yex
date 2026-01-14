"""
Macro controls.

These are controls for creating macros-- TeX's name for subroutines.
"""
from yex.control.control import Unexpandable
from yex.keyword.arithmetic import Arithmetic
from yex.control.macro import *
from contextlib import contextmanager
import yex
import string
import yex.logging

logger = yex.logging.getLogger('control')

@contextmanager
def global_assignments(doc):
    v = doc[r'\globaldefs']
    if v<0:
        changed = False
    else:
        doc[r'\globaldefs'] = v+1
        changed = True
        logger.debug("globaldefs value changed to %s; will change it back",
                     v+1)

    yield

    if changed:
        v = doc[r'\globaldefs']
        doc[r'\globaldefs'] = v-1
        logger.debug("globaldefs value changed back to %s",
                     v-1)

class Def(Unexpandable):

    settings = set(('def',))

    def __call__(self, parser):
        self._parse_def(parser)

    def _parse_def(self, parser):

        # Firstly, what flags have been used? There's a lot of them,
        # and they all have "settings" fields. We union them all together.
        # The ones with "def" in the settings field are terminal.

        settings = set(self.settings)

        while 'def' not in settings:

            token = parser.next(
                    level = 'deep',
                    on_eof='raise',
                    )

            if not isinstance(token, yex.parse.ControlName):
                raise yex.exception.ExpectedDefError(
                        problem = token,
                        )

            flag = parser.doc.get(token.identifier,
                    default=None)

            if isinstance(flag, (Def, Global)):
                settings |= flag.settings
            else:
                raise yex.exception.ExpectedDefError(
                        problem = flag,
                        )

        settings.remove('def')

        token = parser.next(
                level = 'deep',
                on_eof='raise',
                )
        macro_name = token.ch

        logger.debug("defining new macro: %s; settings=%s",
                macro_name, settings,
                )

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

        deep = parser.another(level='deep',
                on_eof='raise',
                )

        for token in deep:
            logger.debug("  -- param token: %s", token)

            if isinstance(token, yex.parse.BeginningGroup):
                deep.push(token)
                break
            elif isinstance(token, yex.parse.ControlName):
                try:
                    if parser.doc.controls[token.identifier].is_outer:
                        raise yex.exception.OuterInParamsError()
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
                    raise yex.exception.WeirdParamSymbolError(
                            problem = which,
                            )

                elif int(which.ch) != param_count+1:
                    raise yex.exception.ParamsNotInOrderError(
                            found = which.ch,
                            expected = param_count+1,
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
        def_parser = parser.another(
                bounded='single',
                on_eof='exhaust',
                level = level,
                no_outer=True,
                )

        for token in def_parser:

            logger.debug("  -- definition token: %s", token)

            if isinstance(token, yex.parse.Parameter):
                second = def_parser.next()

                replace = token.handle_second(second,
                        max_index = len(parameter_text),
                        )

                if replace is not None:
                    definition.append(replace)
                else:
                    definition.append(token)
                    definition.append(second)

            else:
                token.implicit = True
                definition.append(token)

            if starts_at is None:
                starts_at = parser.location

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

        parser.doc.set_control(
                field = macro_name,
                value = new_macro,
                )

# These are all forms of definition,
# so they're handled as Def.

class Outer(Def):
    settings = set(('outer',))

class Gdef(Def):
    def __call__(self, parser):
        with global_assignments(parser.doc):
            self._parse_def(parser)

class Long(Def):
    settings = set(('long',))

class Edef(Def):
    settings = set(('expanded', 'def'))

class Xdef(Def):
    settings = set(('expanded', 'global', 'def'))

class Global(Unexpandable):

    def __call__(self, parser):

        forthcoming = parser.another(
                level = 'reading',
                on_eof='raise',
                ).peek()

        if not isinstance(forthcoming, (
            yex.control.register.Array,
            Arithmetic,
            Def,
            Control,
            )):
            raise ValueError(str(type(token)))

        class ParserThatDoesntNoticeItems(yex.parse.Parser):
            def _notice_item(self, item:Any)->None:
                pass

        # This is so that
        #   \global\advance
        # doesn't make the tracingcommands log say
        #   {\global}
        #   {\advance}
        # because TeX only shows the "{\global}" part.
        parser_that_doesnt_notice_items = parser.another(
                subclass = ParserThatDoesntNoticeItems,
                )

        with global_assignments(parser.doc):
            try:
                result = parser_that_doesnt_notice_items.next(
                        bounded = 'step',
                        on_eof = 'exhaust',
                        )
            except StopIteration:
                raise yex.exception.UnexpectedEOFError()

        return result
