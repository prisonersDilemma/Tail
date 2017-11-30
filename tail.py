#!/usr/bin/env python3.6
"""Incrementally "walk" backwards through a file, reading "blocks" of bufsz,
yielding chunks of nlines."""
__date__ = '2017-11-22'
__version__ = (0,2,1)
from codecs import lookup
from os import getcwd
from os import SEEK_CUR
from os import SEEK_END
from os import stat
from os.path import exists

import bytepos # RevBytePosition is a dependency.
import yyyymmdd

from logging import basicConfig, getLogger

basicConfig(filename=f'{getcwd()}/tail.log', filemode='w',)
logger = getLogger('Tail')
logger.setLevel('DEBUG') # str -> int


class Tail:
    """Return an instance of Tail with an open stream at *fpath*."""

    def __init__(self, fpath, nlines=10, bufsz=1024, encoding='utf-8', newline='\n'):
        if not isinstance(bufsz, int):
            raise TypeError(f'{__class__.__name__}: expected int, got type {type(bufsz)}')
        elif not isinstance(nlines, int):
            raise TypeError(f'{__class__.__name__}: expected int, got type {type(nlines)}')
        elif not isinstance(encoding, str):
            raise TypeError(f'{__class__.__name__}: expected str, got type {type(encoding)}')
            lookup(encoding) # Does nothing if valid, else raises LookupError.
        elif not exists(fpath):
            raise FileNotFoundError(f'{__class__.__name__}: [Errno 2] No such file or directory: {fpath!s}')

        self.nlines = nlines
        self.encoding = encoding
        self.newline = newline.encode(self.encoding)
        self._stat = stat(fpath)
        self.stream = open(fpath, mode='rb')
        bufsz = bufsz if self._stat.st_size > bufsz else self._stat.st_size
        self.pos = bytepos.RevBytePosition(self._stat.st_size, bufsz)
        self.buffer = b''


    def __repr__(self):
        """Return information on the current buffer and file position."""
        return 'Tail(ppos={}, cpos={}, npos={}, bufsz={}, buflen={})'.format(
                self.pos.prv, self.pos.cur, self.pos.nxt, self.pos.bufsz, len(self.buffer))


    def __str__(self):
        """Return the current buffer, decoded."""
        return self.buffer.decode(self.encoding)


    def __del__(self):
        """Have Python close the stream during garbage collection."""
        try:
            if not self.stream.closed:
                self.stream.close()
        except AttributeError: pass


    def __iter__(self):
        """Yield chunks of nlines till the file is consumed, whence the final chunk will be the remaining lines."""
        return self


    def __next__(self):
        """Return a 'chunk' of nlines as a list of decoded strings, without newlines."""
        # try/except KeyboardInterrupt and exit gracefully (close stream)?
        if self.buffer is None:
            logger.debug('Buffer is empty. Raising StopIteration.')
            raise StopIteration('Tail: buffer is empty')

        for pos in self.pos:
            # repr(Tail) -> 'Tail(ppos={}, cpos={}, npos={}, bufsz={}, buflen={})'
            logger.debug('%r', self)
            self.stream.seek(pos.cur)
            buf = self.stream.read(pos._delta()) + self.buffer

            if len(self.buffer) is 0:
                self.buffer = buf.rstrip(self.newline)
                logger.debug('Stripped a newline from the buffer.')
            else: self.buffer = buf

            # Why not split nlines+1 to get rid of fragments?
            chunk = self.buffer.rsplit(self.newline, self.nlines)
            if len(chunk) is not (self.nlines + 1):
                logger.debug('Chunk len (%s) is not nlines+1 (%s). Continuing.', len(chunk), self.nlines + 1)
                continue

            self.buffer, nlines = chunk[0], chunk[-self.nlines:]
            # Faster than listcomp! I timed it. decoding is expensive!
            chunk = self.newline.join(nlines).decode(self.encoding).splitlines()
            logger.debug('Returning chunk of len %s', len(chunk))
            return chunk

        # Somehow, if a chunk ends with several blank lines (newline only) a
        # line(s) may be lost here. The line exists after splitlines, but is
        # probably 'squeezed' in the join and (second) splitlines. I do not
        # know whether this same issue can occur in an earlier chunk, which
        # would be handled (in the same manner) take place above.

        # Test whether the line is still lost with splitlines vs rsplit.
        #nlines = self.buffer.rsplit(self.newline, self.nlines)
        # splitlines must automatically perform newline conversion.
        nlines = self.buffer.splitlines()
        logger.debug(f'Len of final nlines, before chunk: {len(nlines)}. See if a line is lost in the translation from this...')
        self.buffer = None
        chunk = self.newline.join(nlines).decode(self.encoding).splitlines()
        logger.debug(f'...to this: len of chunk {len(chunk)}')
        #logger.debug('Returning chunk of len %s', len(chunk))
        return chunk


    def stop(self):
        """Close the stream opened during instantiation at *fpath*."""
        try:
            if not self.stream.closed:
                self.stream.close()
        except AttributeError: pass



#===============================================================================
#def tail_while(filter_func, *args, **kwargs):
#    """Apply a filter."""
#
#    # can't use get or None will overwrite defaults.
#    #fpath, nlines=10, bufsz=1024, encoding='utf-8', newline=b'\n'
#    _tail = Tail(fpath=kwargs.get('fpath'),
#                 nlines=kwargs.get('nlines'),
#                 bufsz=kwargs.get('bufsz'),
#                 encoding='')
#
#
#    def _filter(*args, **kwargs):
#        # if results of filter < chunk, return
#
#        targets = {}
#        for chunk in _tail:
#            chunk_len = len(chunk)
#            result = filter(filter_func(*args, **kwargs), chunk)
#
#            # Found non-matching lines in chunk. Add any lines that may have
#            # matched and return.
#            if len(result) < chunk_len:
#                targets.update(result)
#                return targets
#
#            # All the lines in the chunk matched. Continue with the next chunk.
#            results.update(result)
#
#    return _filter
#
#
#
# check for a date with regex; if no date, quit; else, convert date to DateComp
# if targetdatecomp == currentdatecomp, add to dict; if targetdatecomp >
# currentdatecomp, finish chunk, and quit
#
#
#@tail_while
#def date_filter(line, trgtdatecomp,):
#    currdate = yyyymmdd.date(line)
#    currdatecomp = yyyymmdd.DateComp(currdate.group('date'))
#    if trgtdatecomp == currdatecomp:
#        ipaddr, tmstmp = line.split(',')
#        ipaddr, tmstmp = ipaddr.strip('"'), tmstmp.rstrip().strip('"')
#        return {ipadd: {'timestamp': tmstmp}}
#===============================================================================


if __name__ == '__main__':
    pass

    testpath2 = '/home/na/testing/seek-test2'    # 30 lines,
    for chunk in Tail(testpath2, nlines=10, bufsz=64, newline='\n'):
        for line in chunk:
            print(line)


#===============================================================================
# Removed assertions in __init__ for better tests and error messages.
# Added a test for codec name checking (e.g., the value passed for *encoding*).
# Changed newline parameter to take type str, which is then converted to binary
# during construction.
# Added an explict 'stop' method, which closes the stream at *fpath*.
# Added fix for AttributeError, raised when trying to close a stream if it
#   was never opened in the first place, in __del__.
#===============================================================================
