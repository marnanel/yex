# This will be a proper template later, but at present I need to hack it around

DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   width="%(docwidth)s"
   height="%(docheight)s"
   version="1.1"
   >
   <title>yex test output</title>
   <style>
    svg {
        viewport-fill: #228;
    }
    rect {
        stroke: #00F;
        stroke-width: 1px;
        stroke-opacity: 0.4;
        fill-opacity: 0;
    }
    rect.page {
        fill-opacity: 1;
        stroke: #000;
        fill: #fff;
    }
    rect.box {
        stroke: #F00;
    }
    rect.hbox {
        stroke: #0FF;
    }
    rect.vbox {
        stroke: #0F0;
    }
    rect.char {
        stroke: #FF0;
    }
    rect.kern {
        stroke: none;
        fill: #F70;
        fill-opacity: 0.6;
    }
    rect.leader {
        stroke: none;
        fill: #000;
        fill-opacity: 0.3;
    }
    rect.rule {
        stroke: none;
        fill: #000;
        opacity: 1;
        fill-opacity: 1;
    }
    </style>
  <g>
%(contents)s
  </g>
</svg>
"""

PAGE = """
    <rect id="page%(number)s" class="page" width="%(pagewidth)s" height="%(pageheight)s" x="%(x)s" y="%(y)s" />
%(contents)s
"""

BOX = """
    <rect id="%(id)s" class="%(class)s" width="%(width)s" height="%(height)s" x="%(x)s" y="%(y)s" />
%(contents)s
"""

CHAR = """
    <rect id="%(id)s" class="%(class)s" width="%(width)s" height="%(height)s" x="%(x)s" y="%(y)s" />
    <image id="i%(id)s" class="%(class)s" width="%(width)s" height="%(height)s" x="%(x)s" y="%(y)s"
        xlink:href="%(href)s"
        />

"""
