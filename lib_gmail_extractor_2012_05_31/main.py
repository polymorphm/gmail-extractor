# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2012 Andrej A Antonov <polymorphm@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

assert str is not bytes

import sys, functools, argparse
import tornado.ioloop, tornado.stack_context, tornado.gen
from .safe_print import safe_print as print
from . import address_extract

class UserError(Exception):
    pass

def on_error(type, value, traceback):
    if isinstance(value, UserError):
        print('user error: {}'.format(value), file=sys.stderr)
    else:
        from traceback import print_exception
        print_exception(type, value, traceback)
    
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
            description='utility for extracting gmail addresses from files')
    
    parser.add_argument('source', metavar='SOURCE-FILE', nargs='+',
            help='path to source file')
    
    parser.add_argument('--out', metavar='OUTPUT-FILE',
            help='path to output result file')
    
    args = parser.parse_args()
    
    io_loop = tornado.ioloop.IOLoop.instance()
    with tornado.stack_context.ExceptionStackContext(on_error):
        address_list = []
        
        def on_address_show(address):
            print('found: {!r}'.format(address))
        
        @tornado.stack_context.wrap
        def on_final():
            print('done!')
            io_loop.stop()
        
        if args.out is not None:
            o_fd = open(args.out, 'w', encoding='utf-8', newline='\n')
            
            def on_address(address):
                on_address_show(address)
                
                o_fd.write('{}\n'.format(address))
                o_fd.flush()
        else:
            on_address = on_address_show
        
        @tornado.gen.engine
        def do_extract():
            for source in args.source:
                s_fd = open(source, 'rb')
                address_extract_key = object()
                address_extract(s_fd, address_list,
                        on_address=on_address,
                        on_final=(yield tornado.gen.Callback(address_extract_key)))
                yield tornado.gen.Wait(address_extract_key)
            
            on_final()
        
        io_loop.add_callback(do_extract)
    io_loop.start()
