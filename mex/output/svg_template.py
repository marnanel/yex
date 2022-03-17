# This will be a proper template later, but at present I need to hack it around

DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   width="%(docwidth)smm"
   height="%(docheight)smm"
   viewBox="%(viewbox)s"
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
        width="%(pagewidth)smm"
        height="%(pageheight)smm"
        x="%(x)smm"
        y="%(y)smm" />

        %(contents)s

        </g>
"""
