import sys
import logging

from .py3compat import SocketServer
from .utils import autolog
from .core import logger, EPCCore
from .handler import EPCHandler, ThreadingEPCHandler


def setuplogfile(logger=logger, filename='python-epc.log'):
    ch = logging.FileHandler(filename=filename, mode='w')
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


class EPCClientManager:

    def __init__(self):
        self.clients = []
        """
        A list of :class:`EPCHandler` object for connected clients.
        """

    def add_client(self, handler):
        self.clients.append(handler)
        self.handle_client_connect(handler)

    def remove_client(self, handler):
        self.clients.remove(handler)
        self.handle_client_disconnect(handler)

    def handle_client_connect(self, handler):
        """
        Handler which is called with a newly connected `client`.

        :type  handler: :class:`EPCHandler`
        :arg   handler: Object for handling request from the client.

        Default implementation does nothing.

        """

    def handle_client_disconnect(self, handler):
        """
        Handler which is called with a disconnected `client`.

        :type  handler: :class:`EPCHandler`
        :arg   handler: Object for handling request from the client.

        Default implementation does nothing.

        """


class EPCServer(SocketServer.TCPServer, EPCClientManager,
                EPCCore):

    """
    A server class to publish functions and call functions via EPC protocol.

    To publish Python functions, all you need is
    :meth:`register_function`,
    :meth:`print_port` and
    :meth:`serve_forever() <SocketServer.BaseServer.serve_forever>`.

    >>> server = EPCServer(('localhost', 0))
    >>> def echo(*a):
    ...     return a
    >>> server.register_function(echo)                 #doctest: +ELLIPSIS
    <function echo at 0x...>
    >>> server.print_port()                                #doctest: +SKIP
    9999
    >>> server.serve_forever()                             #doctest: +SKIP

    To call client's method, use :attr:`clients <EPCClientManager.clients>`
    attribute to get client handler and use its :meth:`EPCHandler.call` and
    :meth:`EPCHandler.methods` methods to communicate with connected client.

    >>> handler = server.clients[0]                        #doctest: +SKIP
    >>> def callback(reply):
    ...     print(reply)
    >>> handler.call('method_name', ['arg-1', 'arg-2', 'arg-3'],
    ...              callback)                             #doctest: +SKIP

    See :class:`SocketServer.TCPServer` and :class:`SocketServer.BaseServer`
    for other usable methods.

    """

    logger = logger

    def __init__(self, server_address,
                 RequestHandlerClass=EPCHandler,
                 bind_and_activate=True,
                 debugger=None):
        # `BaseServer` (super class of `SocketServer`) will set
        # `RequestHandlerClass` to the attribute `self.RequestHandlerClass`.
        # This class is initialize in `BaseServer.finish_request` by
        # `self.RequestHandlerClass(request, client_address, self)`.
        SocketServer.TCPServer.__init__(
            self, server_address, RequestHandlerClass, bind_and_activate)
        EPCClientManager.__init__(self)
        EPCCore.__init__(self, debugger)
        self.logger.debug('-' * 75)
        self.logger.debug(
            "EPCServer is initialized: server_address = %r",
            self.server_address)

    @autolog('debug')
    def handle_error(self, request, client_address):
        self.logger.error('handle_error: trying to get traceback.format_exc')
        try:
            import traceback
            self.logger.error('handle_error: \n%s', traceback.format_exc())
        except:
            self.logger.error('handle_error: OOPS')

    def print_port(self, stream=sys.stdout):
        """
        Print port this EPC server runs on.

        As Emacs client reads port number from STDOUT, you need to
        call this just before calling :meth:`serve_forever`.

        :type stream: text stream
        :arg  stream: A stream object to write port on.
                      Default is :data:`sys.stdout`.

        """
        stream.write(str(self.server_address[1]))
        stream.write("\n")
        stream.flush()

# see also: SimpleXMLRPCServer.SimpleXMLRPCDispatcher


class ThreadingEPCServer(SocketServer.ThreadingMixIn, EPCServer):

    """
    Class :class:`EPCServer` mixed with :class:`SocketServer.ThreadingMixIn`.

    Use this class when combining EPCServer with other Python module
    which has event loop, such as GUI modules.  For example, see
    `examples/gtk/server.py`_ for how to use this class with GTK

    .. _examples/gtk/server.py:
       https://github.com/tkf/python-epc/blob/master/examples/gtk/server.py

    """

    def __init__(self, *args, **kwds):
        kwds.update(RequestHandlerClass=ThreadingEPCHandler)
        EPCServer.__init__(self, *args, **kwds)


def echo_server(address='localhost', port=0):
    server = EPCServer((address, port))
    server.logger.setLevel(logging.DEBUG)
    setuplogfile()

    def echo(*a):
        """Return argument unchanged."""
        return a
    server.register_function(echo)
    return server


if __name__ == '__main__':
    server = echo_server()
    server.print_port()  # needed for Emacs client

    server.serve_forever()
    server.logger.info('exit')
