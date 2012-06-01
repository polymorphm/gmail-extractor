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

import functools, re
import tornado.ioloop, tornado.stack_context, tornado.gen

BLOCK_SIZE = 1000

def read_block(fd, on_read=None):
    on_read = tornado.stack_context.wrap(on_read)
    io_loop = tornado.ioloop.IOLoop.instance()
    
    def do_read_block():
        buf = fd.read(BLOCK_SIZE)
        
        if on_read is not None:
            io_loop.add_callback(functools.partial(on_read, buf))
    
    io_loop.add_callback(do_read_block)

@tornado.gen.engine
def address_extract(fd, address_list, on_address=None, on_final=None):
    on_address = tornado.stack_context.wrap(on_address)
    on_final = tornado.stack_context.wrap(on_final)
    
    last_buf = b''
    
    while True:
        read_block_key = object()
        read_block(fd, on_read=(yield tornado.gen.Callback(read_block_key)))
        buf = yield tornado.gen.Wait(read_block_key)
        this_last_buf, last_buf = last_buf, buf
        
        if not buf:
            if on_final is not None:
                on_final()
            
            return
        
        big_buf = this_last_buf + buf
        text = big_buf.decode(encoding='ascii', errors='replace')
        
        for match in re.finditer(r'[A-Za-z][A-Za-z0-9\.\+]*\@gmail\.com', text, flags=re.M + re.S):
            address = match.group()
            
            if address in address_list:
                continue
            
            address_list.append(address)
            
            if on_address is not None:
                on_address(address)
