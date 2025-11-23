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

        test.run_code(
                source,
                )
        assert False
