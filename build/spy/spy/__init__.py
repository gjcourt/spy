import errno
import glob
import os
from functools import partial
from itertools import imap


# there must be no other files in this directory or shit gets fucked
BASE = os.environ['SPY_BASE']
try:
    os.makedirs(BASE)
except Exception, e:
    if e.errno != errno.EEXIST:
        raise

def parse_status():
    parse_file = lambda file_name: list(p.split(':') for p in open(file_name, 'r').read().strip().split('\n'))
    return list(imap(parse_file, glob.glob(os.path.join(BASE, '*'))))


def write(fd, name, time, percent_complete):
    eta = (1.0 * time / percent_complete) - time
    _format = (
        ('name', name),
        ('time', '%d seconds' % time),
        ('complete', '%0.0f%%' % (100.0 * percent_complete)), 
        ('eta', '%d seconds' % eta)
    )
    write_line = lambda fd, args: fd.write('%s:%s\n' % args)
    any(imap(partial(write_line, fd), _format))
    fd.close()

def serve(host='127.0.0.1', port=5000):
    server.app.run()

def test():
    files = ('one', 'two', 'three', 'four', 'five')
    args = (
        ('me', 69, 1),
        ('love', 96, 0.1),
        ('you', 0, 0.45),
        ('long', 999, 0.34),
        ('time', 42, .123123),
    )
    write_file = lambda args: write(open(os.path.join(BASE, args[0]), 'w'), *args[1])
    any(imap(write_file, zip(files, args)))
    return parse_status()

