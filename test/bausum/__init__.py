import test

class BausumTest(test.YexTest):

    def trim_string(self, s):

        assert '\t' not in s, "please stop using tabs"
        assert '\r' not in s, "please use Unix like a sensible person"

        s = s.split('\n')

        while not s[0]:
            s = s[1:]

        leading_spaces = 0
        while s[0] and s[0][0]==' ':
            leading_spaces += 1
            s[0] = s[0][1:]

        for i in range(1, len(s)):
            if not s[i]:
                continue
            assert s[i][:leading_spaces] == ' '*leading_spaces

            s[i] = s[i][leading_spaces:]

        return '\n'.join(s).strip()

    def test_control(self):
        source = self.trim_string(self.SOURCE)
        expected = self.trim_string(self.SOURCE)

        mocklogs = test.Mocklogs(self.doc)

        ran_code = test.run_code(
                source,
                )

        found = (
                flatten_boxes(self.doc[r'_output'].found).
                strip().
                split('\n\n')
                )

        found = [x.strip() for x in found]
        found_logs = mocklogs.found
        expected_logs = self.expected_logs()

        if found!=expected:
            print()
            for thing in ['source', 'setup', 'expected', 'found',
                          'found_logs', 'expected_logs',
                          ]:
                print(f'=== {thing} ===')
                value = locals()[thing]
                if value:
                    print('    ',repr(value))

            if os.environ.get(BAUSUM_LOG_ENVIRON, 0):
                with open(BAUSUM_LOG_FILENAME, 'a') as f:
                    f.write(f'{self.__class__.__name__}\n')
                    f.write(f'E: {repr(expected)}\n')
                    f.write(f'F: {repr(found)}\n')
                    f.write('\n')

        assert found==expected, (found, expected)
        assert expected_logs is None or found_logs==expected_logs, (
                found_logs, expected_logs)

    def expected_logs(self):
        return None

if os.environ.get(BAUSUM_LOG_ENVIRON, 0):
    with open(BAUSUM_LOG_FILENAME, 'w') as f:
        pass

class BausumTimeTest(BausumTest):
    def _prep_doc(self):
        import datetime
        self.doc.created_at = datetime.datetime(
                1975, 1, 30, 12, 34
                )

def flatten_boxes(boxes, depth=0):
    result = ''
    for item in boxes:
        if isinstance(item,
                      (yex.box.WordBox, yex.box.CharBox)):
            result += item.ch
        elif isinstance(item,
                      (yex.box.Kern, yex.box.Penalty)):
            pass
        elif isinstance(item,
                        yex.box.Leader):
            if item.vertical:
                result += '\n'
            else:
                result += ' '
        else:
            result += flatten_boxes(item, depth+1)

            if len(result)==0:
                result += ' '

    # Account for ligatures etc.
    for s, r in [
            (chr(11), 'ff'),
            (chr(12), 'fi'),
            (chr(13), 'fl'),
            (chr(15), 'ffl'),
            ('|',     '---'),
            ('{',     '--'),
            ]:
        result = result.replace(s, r)

    if result.strip():
        result += '\n'

    return result
