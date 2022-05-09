# Controls in yex

```{eval-rst}
.. include:: control-keywords-table.rst

Parameters are listed with their type name in the group column, in italics.

.. list-table:: Key
  :header-rows: 1

  * - Symbol
    - Meaning
  * - 🤸
    - Active character. Whenever the character appears in
      ordinary text, this routine will be called.
  * - 🪗
    - Expandable control. These controls work at a low level, because they
      deal with the flow of control. For example, ``\if`` falls into this
      group. Unless you're messing with the parser, you may never
      run into these.
  * - 👻
    - Appears in the controls table, but is not visible from TeX code.
  * - 👽
    - Not currently implemented. Eventually, everything will be implemented,
      but at present this isn't. (Parameters are not marked.)

```

```{eval-rst}
.. autoclass:: yex.control.C_Control
  :members:
  :show-inheritance:
```

```{eval-rst}

            ".. list-table:: Control keywords\n"
            "  :header-rows: 1\n"
            "\n"
            "  * - Keyword\n"
            "    - Group\n"
            "    - Notes\n"
            "    - Purpose\n"
