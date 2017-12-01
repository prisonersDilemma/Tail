#!/usr/bin/env python3.6
"""Incrementally "walk" backwards through a file, reading "blocks" of bufsz,
yielding chunks of nlines."""
__date__ = '2017-11-22'
__version__ = (0,3,1)
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


    def __next__(self):
        """Return a 'chunk' of nlines as a list of decoded strings, without newlines."""
        #if self.buffer is None:
        #    #logger.debug('Raising StopIteration.')
        #    raise StopIteration


        #try: # Raises StopIteration for us.
        next(self.pos)
        if self.pos.prev is 0: #empty_buffer or next iter? may have one last read.
        #except StopIteration:
        #   logger.debug('StopIteration raised by self.pos %r.', self.pos)
        #   logger.debug('Buffer still has len %s. Emptying the buffer.', len(self.buffer))
            # Return what remains in the buffer.
            #print('Emptying buffer.')
            return self.empty_buffer()

        self.stream.seek(self.pos.crnt)

        chunk = self.stream.read(self.pos._delta())

        # Reading the file in reverse, so prepend new data.
        self.buffer = chunk + self.buffer
        #logger.debug('Buffer + %s bytes read: %s', self.pos._delta(), self.buffer)


        # Strip the final newline from file if it's our first read.
        if self.pos.prev is self._stat.st_size:
            self.buffer = self.buffer.rstrip(self.newline)


        # Split an extra line so we can save it for later b/c it's probably
        # a fragment. Consume all the lines if nlines+1 are NOT present.
        cache = self.buffer.rsplit(self.newline, self.nlines+1)
        self.lines_cache.lextend(cache[1:]) # "prepend" to SuperList
        self.buffer = cache[0] # Everything remaining beyond nlines+1.
        #logger.debug('lines_cache (len(%s)) after rsplit: %s', len(self.lines_cache), self.lines_cache)


        # Recurse if we don't have enough lines, yet.
        if len(self.lines_cache) < (self.nlines):
            #logger.debug('Lines_cache (chunk) len (%s) < (%s). Recursing!\n', len(self.lines_cache), self.nlines)
            return next(self)
        else: # Shouldn't need an explicit 'else' here.
            nlines = self.lines_cache.rsplit(-self.nlines) # idx at 10 lines
            #logger.debug('Remaining lines_cache len(%s): %s', len(self.lines_cache), self.lines_cache)
            #logger.debug('Returning nlines (%s): %s.\n\n', len(nlines), nlines)
            return self.newline.join(nlines).decode(self.encoding).splitlines() # Faster than listcomp! I timed it. decoding is expensive!


    def empty_buffer(self):
        self.stream.seek(self.pos.crnt)
        chunk = self.stream.read(self.pos._delta())
        #chunk = chunk if chunk is not None else b''
        #self.buffer = self.buffer if self.buffer is not None else b''
        #print(type(chunk))
        #print(type(self.buffer))
        self.buffer = chunk + self.buffer

        self.lines_cache.lextend(self.buffer.splitlines())
        nlines = self.lines_cache[:] # Copy. Don't mutate the list!
        chunk = self.newline.join(nlines).decode(self.encoding).splitlines()
        logger.debug('Returning final chunk of len %s', len(chunk))
        self.lines_cache = self.buffer = None
        return chunk


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
# Changelog:
#
# Notes:
# Appears to handle nlines > lines in file.
#
# Todo:
#
