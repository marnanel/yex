"""
Miscellaneous controls.

These should find a home somewhere else. But for now, they live here.
"""
import logging
from yex.control.control import Expandable, Unexpandable
import yex
import itertools

logger = logging.getLogger('yex.general')

@yex.decorator.control()
def The(tokens):
    r"""
    Takes an argument, one of many kinds (see the TeXbook p212ff)
    and returns a representation of that argument.

    For example, \the\count100 returns a series of character
    tokens representing the contents of count100.
    """

    logger.debug(r"\the: looking for a subject")
    subject = tokens.next(
            level='querying',
            on_eof='raise',
            )

    if isinstance(subject, yex.parse.Token):
        logger.debug(r"\the: found token, looking it up: %s", subject)
        handler = tokens.doc.get(subject.identifier,
                default=None,
                tokens=tokens)

        if handler is None:
            raise yex.exception.TheUnknownError(
                    subject = subject,
                    )
    else:
        handler = subject

    logger.debug(r"\the: found: %s", handler)

    if hasattr(handler, 'get_the'):
        logger.debug(r"\the: calling: %s", handler.get_the)
        representation = handler.get_the(tokens)

    else:
        representation = str(handler)

    logger.debug(r'\the for %s is %s',
            subject, representation)

    tokens.push(representation,
            clean_char_tokens=True,
            is_result=True,
            )

class Show(Unexpandable): pass
class Showthe(Unexpandable): pass

class Let(Unexpandable):
    """
    TODO
    """ # TODO


    def __call__(self, tokens):

        lhs = self.get_lhs(tokens)
        rhs = self.get_rhs(tokens)

        logger.debug("%s: will set %s=%s",
                self, lhs, rhs)

        self.redefine(tokens, lhs, rhs)

    def get_lhs(self, tokens):

        result = tokens.next(
                level='deep',
                on_eof='raise',
                )

        if not isinstance(result, (yex.parse.Control, yex.parse.Active)):
            raise yex.exception.LetInvalidLhsError(
                    name = self.__class__.__name__,
                    subject = result,
                    )

        tokens.eat_optional_char('=')

        return result

    def get_rhs(self, tokens):

        result = tokens.next(
                level='deep',
                on_eof='raise',
                )

        return result

    def redefine(self, tokens, lhs, rhs):
        if isinstance(rhs, yex.parse.Control):
            self.redefine_to_control(lhs, rhs, tokens)
        else:
            self.redefine_to_ordinary_token(lhs, rhs, tokens)

    def redefine_to_control(self, lhs, rhs, tokens):

        rhs_referent = tokens.doc.get(rhs.identifier,
                        default=None,
                        param_control = True,
                        )

        logger.debug(r"%s: %s = %s, which is %s",
                self, lhs, rhs, rhs_referent)

        tokens.doc.__setitem__(
                field = lhs.identifier,
                value = rhs_referent,
                param_control = True,
                )

    def redefine_to_ordinary_token(self, lhs, rhs, tokens):

        class Redefined_by_let(Unexpandable):

            is_queryable = True

            def __call__(self, tokens):
                tokens.push(rhs, is_result=True)

            def __repr__(self):
                return f"[{rhs}]"

            def __str__(self):
                return str(rhs)

            @property
            def value(self):
                return rhs

        logger.debug(r"%s: %s = %s",
                self, lhs, rhs)

        tokens.doc[lhs.identifier] = Redefined_by_let()

class Futurelet(Let):

    def __call__(self, tokens):

        lhs = self.get_lhs(tokens)
        rhs1 = self.get_rhs(tokens)
        rhs2 = self.get_rhs(tokens)

        logger.debug("%s: will set %s=%s, "
                "then run %s, but push %s immediately before its result.",
                self, lhs, rhs2, rhs1, rhs2)

        self.redefine(tokens, lhs, rhs2)

        tokens.push(rhs1)

        inside = tokens.another(
                on_push = yex.parse.Afterwards(
                    item = rhs2,
                    ),
                level = 'executing',
                )

        first = inside.next()
        tokens.push(first)

##############################

class Meaning(Unexpandable): pass

##############################

@yex.decorator.control()
def Relax():
    """
    Does nothing.

    See the TeXbook, p275.
    """
    def __call__(self, tokens):
        pass

##############################

class Indent(Unexpandable):

    vertical = True
    horizontal = True
    math = True

    def __call__(self, tokens):

        if tokens.doc.mode.is_vertical:
            self._in_vertical_mode(tokens)
        else:
            self._in_horizontal_and_math_modes(tokens)

    def _in_vertical_mode(self, tokens):

        doc = tokens.doc
        mode = doc['_mode']

        # see the TeXbook, p278
        if not mode.list:
            logger.debug("indent: not adding parskip glue because "
                    "list is empty")
        elif isinstance(mode, yex.mode.Internal_Vertical):
            logger.debug("indent: not adding parskip glue because "
                    "this is internal vertical mode")
        else:
            mode.append(
                    yex.box.Leader(
                        glue=tokens.doc[r'\parskip']
                        ))
            logger.debug("indent: added parskip glue: %s",
                    tokens.doc[r'\parskip'])

        logger.debug("indent: switching to horizontal mode")

        doc['_mode'] = 'horizontal'

        for item in reversed(doc[r'\everypar']):
            tokens.push(item)

        self._maybe_add_indent(doc)

        doc.mode.exercise_page_builder()

    def _in_horizontal_and_math_modes(self, tokens):
        # see the TeXbook, p282
        doc = tokens.doc

        self._maybe_add_indent(doc)
        doc[r'\spacefactor'] = 1000

        # TODO: math mode is slightly more complicated than this

    def _maybe_add_indent(self, doc):
        logger.debug("indent: adding indent of width %s",
                doc[r'\parindent'])
        doc.mode.append(
                yex.box.HBox(width=doc[r'\parindent'])
                )

class Noindent(Indent):

    def _maybe_add_indent(self, doc):
        pass # no, not here

##############################

@yex.decorator.control(
        expandable = True,
        )
def Begingroup(doc):
    r"""
    Begins a group, like `{`.

    The group must be ended with `\endgroup`.
    """
    doc.begin_group(
            from_begingroup = True,
            )

@yex.decorator.control(
        expandable = True,
        )
def Endgroup(doc):
    r"""
    Ends a group, like `}`.

    The group must have been created with `\begingroup`.
    """
    doc.end_group(
            from_endgroup = True,
            )

##############################

@yex.decorator.control(
        expandable = True,
        push_result = False,
        )
def Noexpand(tokens):
    """
    The argument is not expanded.
    """

    t = tokens.next(level='deep')
    logger.debug(r'\noexpand: not expanding %s', t)
    return t

@yex.decorator.control(
        expandable = True,
        even_if_not_expanding = True,
        )
def Expandafter(tokens):
    r"""
    Process the argument, then give the result to the previous control.

    For example, in

        \def\spong{spong}
        \uppercase{\spong}

    firstly \uppercase runs on "\spong", which gives "\spong" (since it's a
    control, not a series of letters). Then \spong is run, so we end up
    with "spong".

    But in

        \def\spong{spong}
        \uppercase\expandafter{\spong}

    \expandafter runs "\spong" and gets "spong", then passes it to
    \uppercase. So we end up with "SPONG".
    """

    opening = tokens.next(
            level = 'deep',
            on_eof = 'raise',
            )

    # Right, let's read our argument.

    argument = [token for token in tokens.another(
        level = 'executing',
        bounded ='single',
        on_eof = 'exhaust',
        )]

    rerun_tokens = [t for t in tokens.another(
            source = argument,
            on_eof = 'exhaust',
            )]

    tokens.push(rerun_tokens)
    tokens.push(opening)

##############################

@yex.decorator.control()
def Showlists(doc):
    doc.showlists()

##############################

@yex.decorator.control(even_if_not_expanding=True)
def String(tokens):

    result = []

    location = tokens.location

    def add(ch, with_escapechar=False):
        if with_escapechar:
            escapechar = tokens.doc[r'\escapechar']
            if escapechar>=0 and escapechar<=255:
                add(chr(escapechar))

        for c in ch:
            result.append(
                    yex.parse.Token.get(
                        ch = c,
                        category = None, # i.e. Other or Space
                        location = location,
                        )
                    )

    t = tokens.next(level='deep')

    logger.debug(
            r'\string: token was %s of class %s',
            t, t.__class__.__name__)

    if isinstance(t, yex.parse.Control):
        add(t.name, with_escapechar=True)
    elif hasattr(t, 'identifier'):
        add(t.identifier[1:], with_escapechar=True)
    elif hasattr(t, 'ch'):
        add(t.ch)
    else:
        add(str(t))

    return result

##############################

def _uppercase_or_lowercase(tokens, block):

    result = []
    mapping = tokens.doc[block]

    for token in tokens.another(
            bounded='single',
            on_eof='exhaust',
            level='reading'):

        replacement_code = None

        if not isinstance(token, yex.parse.Token):
            logger.debug("  -- %s is not a token but a %s",
                    token, type(token))

        elif isinstance(token, yex.parse.Control):
            logger.debug("  -- %s is a control token",
                    token)

        elif isinstance(token, (
            yex.parse.Letter,
            yex.parse.Other,
            )):

            replacement_code = mapping.get_element(ord(token.ch))


        if replacement_code and replacement_code.value:
            replacement = yex.parse.Token.get(
                    ch = chr(int(replacement_code)),
                    category = token.category,
                    )
        else:
            replacement = token

        logger.debug("  -- s: %s -> %s",
                token, replacement)
        result.append(replacement)

    return result

@yex.decorator.control()
def Uppercase(tokens):
    return _uppercase_or_lowercase(tokens=tokens, block=r'\uccode')

@yex.decorator.control()
def Lowercase(tokens):
    return _uppercase_or_lowercase(tokens=tokens, block=r'\lccode')

##############################

@yex.decorator.control()
def Csname(tokens):
    r"""
    Creates new control tokens.

    \csname must be followed by a series of tokens of any of the basic
    categories. Expandable controls will be expanded; unexpandable controls
    aren't allowed. The series must end with \endcsname.

    This series will become the name of a new control token, which will
    initially point at \relax. See p40 of the TeXbook for more details.

    You can use this to create control tokens with weird names-- even
    the empty string. Note that if you create a token with a name
    beginning with an underscore, that underscore will
    be doubled in doc[name] so that it doesn't conflict with yex's internal
    settings.
    """

    logger.debug(r'\csname: reading name of new control')

    location = tokens.location

    name = ''
    try:
        while True:
            item = tokens.next(level='executing', on_eof='raise')

            if isinstance(item, yex.parse.Token) and item.is_from_tex:
                name += item.ch
            else:
                raise yex.exception.CsnameWeirdFollowingError(
                        problem = item,
                        )
    except yex.exception.EndcsnameError:
        pass

    if name.startswith('_'):
        name = f'_{name}'

    logger.debug(r'\csname: new control will be called %s', name)

    result = yex.parse.Control(
            name = name,
            doc = tokens.doc,
            location = location,
            )

    logger.debug(r'\csname: new control is %s', result)

    name_with_backslash = '\\'+name
    if name_with_backslash not in tokens.doc.controls:
        tokens.doc.controls[name_with_backslash] = Relax()
        logger.debug(r'\csname: added to controls table')

    return result

@yex.decorator.control()
def Endcsname():
    r"""
    Ends a \csname sequence.

    This is special-cased by \csname, and in any other context it
    raises an exception.
    """
    raise yex.exception.EndcsnameError()

##############################

@yex.decorator.control()
def Parshape(count: int, tokens):

    if count==0:
        tokens.doc.parshape = None
        return
    elif count<0:
        raise yex.exception.ParshapeNegativeError(
                count = count,
                )

    tokens.doc.parshape = []

    for i in range(count):
        length = yex.value.Dimen.from_tokens(tokens)
        indent = yex.value.Dimen.from_tokens(tokens)
        tokens.doc.parshape.append(
                (length, indent),
                )
        logger.debug(r"\parshape: %s/%s = (%s,%s)",
                i+1, count, length, indent)

    logger.debug(r"\parshape: done")

@Parshape.on_query()
def Parshape(doc):
    if doc.parshape is None:
        result = 0
    else:
        result = len(doc.parshape)

    return str(result)

##############################

@yex.decorator.control(
    vertical = False,
    horizontal = True,
    math = False,
    )
def S_0020(): # Space
    """
    Add an unbreakable space.
    """
    return yex.parse.token.Other(ch=chr(32))

@yex.decorator.control(
    vertical = False,
    horizontal = None,
    math = False,
    )
def Par():
    """
    Add a paragraph break.
    """
    return yex.parse.token.Paragraph()

##############################

class Noboundary(Unexpandable):
    vertical = False
    horizontal = True
    math = False

class Unhbox(Unexpandable):
    vertical = False
    horizontal = True
    math = True

class Unhcopy(Unexpandable):
    vertical = False
    horizontal = True
    math = True

class Valign(Unexpandable):
    vertical = False
    horizontal = True
    math = False

class Accent(Unexpandable):
    vertical = False
    horizontal = True
    math = False

@yex.decorator.control(
    vertical = False,
    horizontal = True,
    math = False,
    )
def Discretionary(tokens):
    "Adds a discretionary break."

    symbols = {}

    for name in ['prebreak', 'postbreak', 'nobreak']:
        symbols[name] = list(tokens.another(
            level='reading',
            on_eof='exhaust',
            bounded='balanced',
            ))

    return yex.box.DiscretionaryBreak(**symbols)

class S_002d(Unexpandable): # Hyphen
    vertical = False
    horizontal = True
    math = True

class Afterassignment(Unexpandable): pass
class Aftergroup(Unexpandable): pass

@yex.decorator.control()
def Penalty(tokens):
    demerits = yex.value.Number.from_tokens(
            tokens.another(level='executing')).value

    penalty = yex.box.Penalty(
            demerits = demerits,
            )

    return penalty

class Insert(Unexpandable): pass
class Vadjust(Unexpandable): pass

@yex.decorator.control()
def Char(tokens):
    codepoint = yex.value.Number.from_tokens(
            tokens.another(level='executing')).value

    if codepoint in range(32, 127):
        logger.debug(r"\char produces ascii %s (%s)",
            codepoint, chr(codepoint))
    else:
        logger.debug(r"\char produces ascii %s",
            codepoint)

    return chr(codepoint)

class Unvbox(Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Unvcopy(Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Halign(Unexpandable):
    horizontal = 'vertical'
    vertical = True

class Noalign(Unexpandable):
    pass

@yex.decorator.control(
    horizontal = 'vertical',
    vertical = True,
    math = True,
    )
def End(doc, tokens):

    mode = doc.outermost_mode

    deadcycles = doc[r'\deadcycles']

    logger.debug((
        r"\end: outermost mode is %s; "
        r"list empty? %s; deadcycles==0? %s"),
        mode, mode.list==[], deadcycles==0)

    if mode.list==[] and deadcycles==0:
        tokens.end()
        return

    logger.debug(r"\end: can't end yet; adding things to try to force an end")

    hsize = doc[r'\hsize']
    new_hbox = yex.box.HBox(to=hsize)
    mode.handle(new_hbox)

    new_vfill = yex.box.Leader(
            yex.value.Glue(space=0,
                stretch=1, stretch_unit='fill',
                )
            )
    mode.handle(new_vfill)

    new_penalty = yex.box.Penalty(demerits = 10000000000)
    mode.handle(new_penalty)

@yex.decorator.control(
    horizontal = True,
    vertical = True,
    math = True,
)
def Shipout(box: yex.box.Box, doc):
    r"""
    Sends a box to the output.
    """

    logger.debug(r'\shipout: shipping %s',
            box)

    doc.shipout(box)

##############################

@yex.decorator.control(
    horizontal = True,
    vertical = True,
    math = True,
)
def Ignorespaces(tokens):
    r"""
    Absorbs all space tokens which follow immediately.
    """
    while True:
        item = tokens.next(level='expanding', on_eof='none')

        if not isinstance(item, yex.parse.Space):
            return item

        logger.debug(r"\ignorespaces: ignoring %s", item)

##############################

class Special(Unexpandable):
    r"""
    An instruction to the output driver.

    This creates a yex.box.Whatsit which stores the instruction until
    it's shipped out. Bear in mind that it may never be shipped out.

    The argument is expanded when it's read. It consists of a keyword,
    followed optionally by a space and arguments to the keyword.
    The keyword isn't examined until the instruction is run.

    For the syntax of \special, see p276 of the TeXbook. For the syntax
    of its argument, see p225.
    """

    def __call__(self, tokens):

        inside = tokens.another(
                level='executing',
                bounded='single',
                on_eof="exhaust",
                )

        name = self._get_name(inside)
        args = self._get_args(inside)

        class SpecialWhatsit(yex.box.Whatsit):
            def render(self):
                return (name, args)
            def __str__(self):
                return f'[Special: {name} {args}]'

        result = SpecialWhatsit()

        logger.debug(r"special: created %s",
                result)

        tokens.push(result)

    def _get_name(self, tokens):
        result = ''

        for t in tokens:
            if isinstance(t, yex.parse.Space):
                break

            result += t.ch

        logger.debug(r"\special: name is %s", result)
        return result

    def _get_args(self, tokens):
        result = []

        for t in tokens:
            result.append(t)

        logger.debug(r"\special: args are %s", result)
        return result
