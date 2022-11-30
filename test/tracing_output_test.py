import subprocess

# This is rather hacky

TEX_TEMPLATE = r"""\hsize=5cm
\hyphenpenalty=10000
\exhyphenpenalty=10000
\tracingoutput=1
\showboxbreadth=1000
\pretolerance=10000

a\kern%(width)dsp b

\vbox{a\hrule width%(width)dsp b}

\vbox{a\hrule height%(width)dsp b}

\vbox{a\hrule depth%(width)dsp b}

\bye
"""

YEX_TEMPLATE = r"""\hsize=5cm
\hyphenpenalty=10000
\exhyphenpenalty=10000
\tracingoutput=1
\showboxbreadth=1000
\pretolerance=10000

a\kern%(width)dsp b

\vbox{a\hrule height%(width)dsp b}
"""

def test_widths_in_tex(widths):
    for w in widths:
        with open('width.tex', 'w') as f:
            f.write(TEX_TEMPLATE % {
                'width': w,
                })

        subprocess.run(args=["tex", "width.tex"], stdout=subprocess.PIPE)

        """
        result = f'{w}'

        with open('width.log', 'r') as f:
            for line in f:
                line = line.rstrip()
                for keyword in [
                        'hbox', 'vbox', 'rule', 'kern',
                        ]:
                    if keyword in line:
                        result += f'\n{line}'
                        break

        result += '\n\n'
        with open('found-tex.log', 'a') as found:
            found.write(result)
            """

def analyse_line(which):

    start_run = None
    previous_line = None
    with open('found.log', 'r') as f:
        while True:
            try:
                number = int(f.readline())
            except ValueError:
                print(f"{start_run} - end: {previous_line}")
                return

            lines = []
            while True:
                line = f.readline()[:-1]
                if not line:
                    break
                else:
                    lines.append(line)

            this_line = lines[which]

            if this_line!=previous_line:
                if previous_line is not None:
                    print(f"{start_run} - {number-1}: {previous_line}")

                start_run = number

            previous_line = this_line

def analyse_log():
    for i in range(21):
        print()
        print(f"== Line {i} ==")
        print()
        analyse_line(i)

def test_widths_in_yex(widths):

    for w in widths:
        with open('yex-test.tex', 'w') as f:
            f.write(YEX_TEMPLATE % {
                'width': w,
                })

        with open('width-yex.log', 'w') as f:
            subprocess.run(args=[
                "python",
                '-m', 'yex',
                '-o', 'test.svg',
                'yex-test.tex',
                ],
                stdout=f,
                )

def show_diff():
    subprocess.run(args=[
        'diff',
        'width.log',
        'width-yex.log',
        ])

def main():
    #test_widths_in_tex(range(-10, 68000))
    # analyse_log()
    test_widths_in_tex([1])
    test_widths_in_yex([1])
    show_diff()

if __name__=='__main__':
    main()
