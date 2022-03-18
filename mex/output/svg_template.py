# This will be a proper template later, but at present I need to hack it around

DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   width="%(docwidth)s"
   height="%(docheight)s"
   version="1.1"
   >
   <title>mex test output</title>
   <style>
    svg {
        viewport-fill: #228;
    }
    rect.pageback {
        stroke: #00F;
        stroke-width: 1px;
        fill: #fff;
        opacity: 1;
    }
    rect.boxback {
        opacity: 0.7;
        stroke-width: 1px;
        fill: #F00;
    }
    rect.hboxback {
        stroke: #0FF;
        fill: #AAA;
    }
    rect.vboxback {
        stroke: #0FF;
        fill: #AAA;
    }
    rect.ruleback {
        stroke: none;
        fill: #000;
        opacity: 1;
    }
    </style>
  <g>
    %(contents)s
  </g>
</svg>"""

PAGE = """
    <g class="page"
        id="page%(number)s">
    <rect
        class="pageback"
        id="pageback%(number)s"
        width="%(pagewidth)s"
        height="%(pageheight)s"
        x="%(x)s"
        y="%(y)s" />

        %(contents)s

        </g>
"""

BOX = """
    <g class="%(class)s"><rect
        class="%(class)sback boxback"
        width="%(width)s"
        height="%(height)s"
        x="%(x)s"
        y="%(y)s" />

%(contents)s
        </g> <!-- %(class)s -->
"""
