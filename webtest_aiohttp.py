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
import webob
import webtest

__version__ = '1.0.0'

# from https://github.com/klen/muffin/blob/develop/muffin/pytest.py
def WSGIHandler(app):
    """Return a wsgi application given an `aiohttp.web.Application`."""
    loop = app.loop
    assert loop is not None, 'Application must have an event loop'

    def handle(environ, start_response):

        req = webob.Request(environ)
        vers = aiohttp.HttpVersion10 if req.http_version == 'HTTP/1.0' else aiohttp.HttpVersion11
        message = aiohttp.RawRequestMessage(
            req.method, req.path_qs, vers, aiohttp.CIMultiDict(req.headers), False, False)
        payload = aiohttp.StreamReader(loop=loop)
        payload.feed_data(req.body)
        payload.feed_eof()
        factory = aiohttp.web.RequestHandlerFactory(
            app, app.router, loop=loop, keep_alive_on=False)
        handler = factory()
        handler.transport = io.BytesIO()
        handler.transport._conn_lost = 0
        handler.transport.get_extra_info = lambda s: ('127.0.0.1', 80)
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
