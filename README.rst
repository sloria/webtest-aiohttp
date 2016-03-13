***************
webtest-aiohttp
***************

.. image:: https://badge.fury.io/py/webtest-aiohttp.png
    :target: http://badge.fury.io/py/webtest-aiohttp
    :alt: Latest version

.. image:: https://travis-ci.org/sloria/webtest-aiohttp.png
    :target: https://travis-ci.org/sloria/webtest-aiohttp
    :alt: Travis-CI

webtest-aiohttp provides integration of WebTest with aiohttp.web applications.

Supports aiohttp>=0.21.0.


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

Installation
============
::

    pip install webtest-aiohttp

Project Links
=============

- PyPI: https://pypi.python.org/pypi/webtest-aiohttp
- Issues: https://github.com/sloria/webtest-aiohttp/issues

Credits
=======

This code was adapted from Kirill Klenov's `muffin <https://github.com/klen/muffin>`_ library.

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/webtest-aiohttp/blob/master/LICENSE>`_ file for more details.
