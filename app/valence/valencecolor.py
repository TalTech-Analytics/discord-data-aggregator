# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
from optparse import OptionParser
from .valence.valencecolor import *


def getValence(text):
    """Standalone"""
    load()
    t = mark(text)
    return emotionBayes(t[3], t[1], t[2])


def main():
    parser = OptionParser(usage='Usage: %prog file')
    parser.add_option('-s', '--silent', action="store_true", dest="silent", help='Silent: no html file')
    opts, args = parser.parse_args()
    if len(args) != 1:  # or not opts.segment:
        parser.print_help()
        sys.exit(1)

    fi = codecs.open(args[0], 'r', encoding='utf-8')
    text = fi.read()
    fi.close()
    print(getValence(text))


if __name__ == '__main__':
    main()
