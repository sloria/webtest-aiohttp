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
from aiohttp.test_utils import TestClient, TestServer
import aiohttp
import webob
import webtest

__version__ = '2.0.0'

def WSGIHandler(app, loop):
    """Return a wsgi application given an `aiohttp.web.Application`."""

    def handle(environ, start_response):
        server = TestServer(app, loop=loop)
        # aiohttp.test_utils.TestClient will do the heavy lifting
        client = TestClient(server, loop=loop)
        loop.run_until_complete(client.start_server())
        req = webob.Request(environ)
        coro = client.request(
            data=req.body,
            params=req.params,
            method=req.method,
            path=req.path,
            headers=dict(req.headers)
        )
        result = loop.run_until_complete(coro)
        body = loop.run_until_complete(result.read())
        raw_headers = list(result.raw_headers)
        headerlist = [(name.decode('latin1'), value.decode('latin1'))
                      for name, value in raw_headers]
        res = webob.Response(
            body=body,
            status=result.status,
            content_type=result.content_type,
            headerlist=headerlist,
            charset=result.charset
        )
        start_response(res.status, res.headerlist)
        loop.run_until_complete(client.close())
        return res.app_iter
    return handle

class TestApp(webtest.TestApp):
    """A modified `webtest.TestApp` that can wrap an `aiohttp.web.Application`. Takes the same
    arguments as `webtest.TestApp`.
    """
    def __init__(self, app, *args, **kwargs):
        self.aiohttp_app = None
        if isinstance(app, aiohttp.web.Application):
            if 'loop' in kwargs:
                loop = kwargs.pop('loop')
            elif app.loop:
                loop = app.loop
            else:
                raise ValueError('Must provide a loop to TestApp')
            self.aiohttp_app = app = WSGIHandler(app, loop)
        super().__init__(app, *args, **kwargs)
