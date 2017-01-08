# -*- coding: utf-8 -*-
"""
webtest-aiohttp provides integration of WebTest with aiohttp.web applications

.. code-block:: python

    import asyncio

    from aiohttp import web
    from webtest_aiohttp import TestApp

    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    app = web.Application(loop=loop)

    @asyncio.coroutine
    def hello(request):
        return web.Response(body=json.dumps(
            {'message': 'Hello world'}
        ).encode('utf-8'), content_type='application/json')

    app.router.add_route('GET', '/', handler)


    def test_hello():
        client = TestApp(app)
        res = client.get('/')
        assert res.status_code == 200
        assert res.json == {'message': 'Hello world'}
"""
import io

import aiohttp
from aiohttp import (
    hdrs, web_reqrep, web_exceptions
)
from aiohttp.abc import AbstractMatchInfo
from aiohttp.helpers import TimeService
import asyncio
from aiohttp.server import ServerHttpProtocol
import webob
import webtest

__version__ = '1.1.1'

class RequestHandler(ServerHttpProtocol):

    _request = None

    def __init__(self, manager, app, router, time_service, *,
                 secure_proxy_ssl_header=None, **kwargs):
        super().__init__(**kwargs)

        self._manager = manager
        self._app = app
        self._router = router
        self._secure_proxy_ssl_header = secure_proxy_ssl_header
        self._time_service = time_service

    def __repr__(self):
        if self._request is None:
            meth = 'none'
            path = 'none'
        else:
            meth = self._request.method
            path = self._request.rel_url.raw_path
        return "<{} {}:{} {}>".format(
            self.__class__.__name__, meth, path,
            'connected' if self.transport is not None else 'disconnected')

    def connection_made(self, transport):
        super().connection_made(transport)

        self._manager.connection_made(self, transport)

    def connection_lost(self, exc):
        self._manager.connection_lost(self, exc)

        super().connection_lost(exc)

    @asyncio.coroutine
    def handle_request(self, message, payload):
        self._manager._requests_count += 1
        if self.access_log:
            now = self._loop.time()

        try:
            request = web_reqrep.Request(
                message, payload,
                self.transport, self.reader, self.writer,
                self._time_service, task=None,
                secure_proxy_ssl_header=self._secure_proxy_ssl_header)
        except TypeError:  # no task argument in older versions of aiohttp
            request = web_reqrep.Request(
                message, payload,
                self.transport, self.reader, self.writer,
                self._time_service,
                secure_proxy_ssl_header=self._secure_proxy_ssl_header)
        self._request = request
        try:
            match_info = yield from self._router.resolve(request)
            assert isinstance(match_info, AbstractMatchInfo), match_info
            match_info.add_app(self._app)
            match_info.freeze()

            resp = None
            request._match_info = match_info
            expect = request.headers.get(hdrs.EXPECT)
            if expect:
                resp = (
                    yield from match_info.expect_handler(request))

            if resp is None:
                handler = match_info.handler
                for app in match_info.apps:
                    for factory in reversed(app.middlewares):
                        handler = yield from factory(app, handler)
                resp = yield from handler(request)

            assert isinstance(resp, web_reqrep.StreamResponse), \
                ("Handler {!r} should return response instance, "
                 "got {!r} [middlewares {!r}]").format(
                     match_info.handler, type(resp), self._middlewares)
        except web_exceptions.HTTPException as exc:
            resp = exc

        resp_msg = yield from resp.prepare(request)
        yield from resp.write_eof()

        # notify server about keep-alive
        self.keep_alive(resp.keep_alive)

        # Restore default state.
        # Should be no-op if server code didn't touch these attributes.
        self.writer.set_tcp_cork(False)
        self.writer.set_tcp_nodelay(True)

        # log access
        if self.access_log:
            self.log_access(message, None, resp_msg, self._loop.time() - now)

        # for repr
        self._request = None


class RequestHandlerFactory:

    def __init__(self, app, router, *,
                 handler=RequestHandler, loop=None,
                 secure_proxy_ssl_header=None, **kwargs):
        self._app = app
        self._router = router
        self._handler = handler
        self._loop = loop
        self._connections = {}
        self._secure_proxy_ssl_header = secure_proxy_ssl_header
        self._kwargs = kwargs
        self._kwargs.setdefault('logger', app.logger)
        self._requests_count = 0
        self._time_service = TimeService(self._loop)

    @property
    def requests_count(self):
        """Number of processed requests."""
        return self._requests_count

    @property
    def secure_proxy_ssl_header(self):
        return self._secure_proxy_ssl_header

    @property
    def connections(self):
        return list(self._connections.keys())

    def connection_made(self, handler, transport):
        self._connections[handler] = transport

    def connection_lost(self, handler, exc=None):
        if handler in self._connections:
            del self._connections[handler]

    @asyncio.coroutine
    def finish_connections(self, timeout=None):
        coros = [conn.shutdown(timeout) for conn in self._connections]
        yield from asyncio.gather(*coros, loop=self._loop)
        self._connections.clear()
        self._time_service.stop()

    def __call__(self):
        return self._handler(
            self, self._app, self._router, self._time_service, loop=self._loop,
            secure_proxy_ssl_header=self._secure_proxy_ssl_header,
            **self._kwargs)

# from https://github.com/klen/muffin/blob/develop/muffin/pytest.py
def WSGIHandler(app):
    """Return a wsgi application given an `aiohttp.web.Application`."""
    loop = app.loop
    assert loop is not None, 'Application must have an event loop'

    def handle(environ, start_response):

        req = webob.Request(environ)
        vers = aiohttp.HttpVersion10 if req.http_version == 'HTTP/1.0' else aiohttp.HttpVersion11
        message = aiohttp.RawRequestMessage(
            req.method, req.path_qs, vers, aiohttp.CIMultiDict(req.headers), False, False, False)
        payload = aiohttp.StreamReader(loop=loop)
        payload.feed_data(req.body)
        payload.feed_eof()
        factory = RequestHandlerFactory(
            app, app.router, loop=loop, keep_alive_on=False)
        handler = factory()
        handler.transport = io.BytesIO()
        handler.transport.is_closing = lambda: False
        handler.transport._conn_lost = 0
        handler.transport.get_extra_info = lambda s: {
            'peername': ('127.0.0.1', 80)
        }.get(s)
        handler.writer = aiohttp.parsers.StreamWriter(
            handler.transport, handler, handler.reader, handler._loop)
        coro = handler.handle_request(message, payload)
        if loop.is_running():
            raise RuntimeError('Client cannot start during another coroutine is running.')

        loop.run_until_complete(coro)
        handler.transport.seek(9)
        res = webob.Response.from_file(handler.transport)
        start_response(res.status, res.headerlist)
        return res.app_iter
    return handle

class TestApp(webtest.TestApp):
    """A modified `webtest.TestApp` that can wrap an `aiohttp.web.Application`. Takes the same
    arguments as `webtest.TestApp`.
    """
    def __init__(self, app, *args, **kwargs):
        self.aiohttp_app = None
        if isinstance(app, aiohttp.web.Application):
            self.aiohttp_app = app = WSGIHandler(app)
        super().__init__(app, *args, **kwargs)
