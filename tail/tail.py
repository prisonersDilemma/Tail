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

import offset
import superlist
import yyyymmdd

from logging import basicConfig, getLogger

basicConfig(filename=f'{getcwd()}/tail-dev.log', filemode='w',)
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
        self.pos = offset.NegativeOffset(self._stat.st_size, bufsz)
        self.buffer = b''
        self.lines_cache = superlist.SuperList()


    def __repr__(self):
        """Return information on the current buffer and file position."""
        return 'Tail(prev={}, crnt={}, next={}, bufsz={}, buflen={})'.format(
                self.pos.prev, self.pos.crnt, self.pos.next, self.pos.bufsz, len(self.buffer))


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


    # make sure we can handle nlines > lines in file
    def __next__(self):
        """Return a 'chunk' of nlines as a list of decoded strings, without newlines."""

        if self.buffer is None:
            #logger.debug('Raising StopIteration.')
            raise StopIteration


        try: # Raises StopIteration for us.
            next(self.pos)
        except StopIteration:
            logger.debug('self.pos raised StopIteration. Buffer still has len %s. Emptying the buffer.', len(self.buffer))
            # Return what remains in the buffer.
            return self.empty_buffer()


        #logger.debug('%r\n', self)
        self.stream.seek(self.pos.crnt)


        # Reading the file in reverse, so prepend new data.
        delta = self.pos._delta()
        #logger.debug('delta: %s', delta)

        #logger.debug('Reading pos %r delta %s', self.pos, delta)
        _delta = self.stream.read(delta)

        #logger.debug('%s bytes read. Prepending to (%s) to buffer: (%s)', self.pos._delta(), _delta, self.buffer)
        self.buffer = _delta + self.buffer
        logger.debug('Buffer + %s bytes read: %s', self.pos._delta(), self.buffer)


        # It's our first read (from the end of the file to bufsz). Strip final
        # newline in file.
        if self.pos.prev is self._stat.st_size:
            self.buffer = self.buffer.rstrip(self.newline)


        # Try to take an extra line to get rid of fragments. But will consume all
        # the lines if there are too few. Take nlines and put the extra back in
        # the buffer b/c it's probably a fragment.

        cache = self.buffer.rsplit(self.newline, self.nlines+1)
        self.lines_cache.lextend(cache[1:]) # prepend the lines
        self.buffer = cache[0]
        logger.debug('lines_cache (len(%s)) after rsplit: %s', len(self.lines_cache), self.lines_cache)


        if len(self.lines_cache) < (self.nlines):
            logger.debug('Lines_cache (chunk) len (%s) < (%s). Recursing!\n', len(self.lines_cache), self.nlines)
            return next(self)
        else:
            nlines = self.lines_cache.rsplit(-self.nlines) # idx at 10 lines
            logger.debug('Remaining lines_cache len(%s): %s', len(self.lines_cache), self.lines_cache)
            logger.debug('Returning nlines (%s): %s.\n\n', len(nlines), nlines)
            chunk = self.newline.join(nlines).decode(self.encoding).splitlines() # Faster than listcomp! I timed it. decoding is expensive!
            return chunk




    def empty_buffer(self):
        self.lines_cache.lextend(self.buffer.splitlines())
        nlines = self.lines_cache[:] # copy
        chunk = self.newline.join(nlines).decode(self.encoding).splitlines()
        logger.debug('Returning final chunk of len %s', len(chunk))
        self.lines_cache = self.buffer = None
        return chunk

# I wonder if the recursion is causing chunks to be reconstructed out of order?
# But still don't know how to account for fragments.

    def stop(self):
        """Close the stream opened during instantiation at *fpath*."""
        try:
            if not self.stream.closed:
                self.stream.close()
        except AttributeError: pass




if __name__ == '__main__':
    testpath2 = '/home/na/testing/seek-test2'    # 30 lines,
    for chunk in Tail(testpath2, nlines=10, bufsz=64, newline='\n'):
        print('--chunk--')
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
