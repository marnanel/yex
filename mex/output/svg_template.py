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
    rect {
        stroke: #00F;
        stroke-width: 1px;
        fill: #00F;
        opacity: 0.7;
    }
    rect.page {
        stroke: #000;
        fill: #fff;
    }
    rect.box {
        fill: #F00;
    }
    rect.hbox {
        stroke: #0FF;
        fill: #0FF;
    }
    rect.vbox {
        stroke: #0F0;
        fill: #0F0;
    }
    rect.char {
        stroke: #F0F;
        fill: #F0F;
    }
    rect.rule {
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
    <g class="page" id="page%(number)s">
    <rect class="page" width="%(pagewidth)s" height="%(pageheight)s" x="%(x)s" y="%(y)s" />

        %(contents)s

        </g>
"""

BOX = """
    <rect id="%(id)s" class="%(class)s" width="%(width)s" height="%(height)s" x="%(x)s" y="%(y)s" />
%(contents)s
"""
