import yex

def start_logging(doc):
    for name in doc.controls.keys():
        if name.startswith(r'\tracing'):
            doc.controls[name] = 2

def test_triptest():
    print("Triptest begins!")
    print()
    doc = yex.Document()

    start_logging(doc)

    with open('test/triptest/trip.tex', 'r') as f:
        doc.read(f)

    print()
    print("Triptest ends.")
