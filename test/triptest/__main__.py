import yex

def start_logging(doc):
    for name in doc.controls.keys():
        if name.startswith(r'\tracing'):
            doc.controls[name] = 2

def main():
    print("Triptest begins!")
    print()
    doc = yex.Document()

    start_logging(doc)

    doc.read("triptex/trip.tex")

    print()
    print("Triptest ends.")

if __name__=='__main__':
    main()
