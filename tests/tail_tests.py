#!/usr/bin/env python3.6

from unittest import TestCase

import tail

testpath1 = '/home/na/testing/seek-test'     # 284 lines, 1007 words, 8751 chars
testpath2 = '/home/na/testing/seek-test2'    # 30 lines,
testpath3 = '/home/na/testing/seek-test-css' # 1 line, 10k+ chars
testpath4 = '/home/na/git/prisonersDilemma/orionscripts/whois/whois/dontpush/samples/02-splunk-export.csv' # 90k+ lines, '\r\n' (Windows newlines)

tail1 = tail.Tail(testpath1, nlines=100)
tail2 = tail.Tail(testpath2, nlines=10, bufsz=64)
#tail3 = tail.Tail(testpath3)
#tail4 = tail.Tail(fpath=testpath4, nlines=300, bufsz=4096, newline='\r\n')


class TailTest(TestCase):


    def test_newline_attr_is_bin(self):
        self.assertTrue(isinstance(tail1.newline, bytes))

    def test_small_file_num_chunks(self):
        num_chunks = len([chunk for chunk in tail2])
        self.assertEqual(num_chunks, 3)



#0 first line
#0 second line
#0 third line
#0 fourth line
#0 fifth line
#0 sixth line
#0 seventh line
#0 eighth line
#0 nineth line
#0 tenth line
#1 first line
#1 second line
#1 third line
#1 fourth line
#1 fifth line
#1 sixth line
#1 seventh line
#1 eighth line
#1 nineth line
#1 tenth line
#2 first line
#2 second line
#2 third line
#2 fourth line
#2 fifth line
#2 sixth line
#2 seventh line
#2 eighth line
#2 nineth line
#2 tenth line


if __name__ == '__main__':
    pass

    # At the command-line:
    # $ python -m unittest tail.tests.tail_test
