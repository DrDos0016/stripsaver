import unittest
import warnings

from stripsaver import *

"""
1 Panel: http://www.stripcreator.com/comics/bencomic/300194
2 Panels: http://www.stripcreator.com/comics/bencomic/300196
3 Panels + Obscenities: http://www.stripcreator.com/comics/bencomic/300197
Issue w/ overlapping text: http://www.stripcreator.com/comics/benco/96977
Text running out of panel 1: http://www.stripcreator.com/comics/benco/97088/
"""

class TestStripsaver(unittest.TestCase):
    def test_basic_comic(self):
        account = "bencomic"
        id = "296258"
        details = True
        obscenities = False

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="unclosed file")
            output = save_comic(account, id, details, obscenities)

        answer = True
        self.assertEqual(output, answer)

    def test_single_panel(self):
        account = "bencomic"
        id = "300194"
        details = True
        obscenities = True

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="unclosed file")
            output = save_comic(account, id, details, obscenities)
        answer = True
        self.assertEqual(output, answer)

    def test_double_panel(self):
        account = "bencomic"
        id = "300196"
        details = True
        obscenities = True

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="unclosed file")
            output = save_comic(account, id, details, obscenities)
        answer = True
        self.assertEqual(output, answer)

    def test_overlapping_text(self):
        account = "benco"
        id = "96977"
        details = True
        obscenities = True

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="unclosed file")
            output = save_comic(account, id, details, obscenities)
        answer = True
        self.assertEqual(output, answer)


if __name__ == "__main__":
    unittest.main()
