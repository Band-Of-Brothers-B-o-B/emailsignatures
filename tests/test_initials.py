import sys, pathlib

# Add scripts directory to path to import gen_logos
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from gen_logos import initials_from_name

def test_camelcase_split():
    assert initials_from_name('AIVidz') == 'AV'

def test_non_letter_and_limit():
    assert initials_from_name('AI-Vidz') == 'AV'
    assert initials_from_name('OneTwoThreeFour') == 'OTT'
