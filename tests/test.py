import logging
from srl import parser
logging.basicConfig(level=logging.DEBUG)
#print list(parser.parse_words("a b")("a b c"))
result = list(parser.parse_srl("""
    literally 'shit',
    literally 'hell',
    not literally 'whoa',
    one of 'abcdef',
    any of (
        literally 'hell',
        literally 'shit'
    )
""".strip()))
print result
print result[0][0]
