class Debug_Plot:

    SCALE = 20.0

    def __init__(self, filename):
        self.output = open(filename, 'w')

        self.output.write("""<!DOCTYPE html>
<html>
    <head>
<style>
html, body {
    background-color: #333;
    position: absolute;
}

.page {
    background-color: #FFD;
    width: 210mm;
    height: 297mm;
    z-index: -10;
}

.box {
    background-color: #F88;
    border: 2px solid #005;
    position: absolute;
}
.baseline {
    border: 1px dashed #005;
    height: 0px;
    z-order: 10;
    position: absolute;
}
</style>
    </head>
    <body>


        <div class="page"
             style="left: 0mm; top:0mm; width: 210mm; height: 297mm;"
            >
            Hello world.
        </div>
    """)

    def draw(self, *args, **kwargs):

        for f in ['x', 'y', 'height', 'depth', 'width']:
            kwargs[f] *= self.SCALE

        kwargs['boxy'] = kwargs['y'] - kwargs['height']
        kwargs['tall'] = kwargs['height'] + kwargs['depth']

        self.output.write("""<div class="box %(kind)s"
            style="left: %(x)dmm; top:%(boxy)dmm; width: %(width)dmm; height: %(tall)dmm"
            >
            %(ch)s
        </div>
            <div class="baseline"
                 style="left: %(x)dmm; top:%(y)dmm; width: %(width)dmm">
            </div>
            """ % kwargs)


    def close(self):
        self.output.write("""</body>
</html>""")
        self.output.close()


