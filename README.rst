***************
webtest-aiohttp
***************

.. image:: https://badge.fury.io/py/webtest-aiohttp.svg
    :target: http://badge.fury.io/py/webtest-aiohttp
    :alt: Latest version

.. image:: https://travis-ci.org/sloria/webtest-aiohttp.svg
    :target: https://travis-ci.org/sloria/webtest-aiohttp
    :alt: Travis-CI

webtest-aiohttp provides integration of WebTest with aiohttp.web applications.

Supports aiohttp>=2.3.8.

.. code-block:: python

    from aiohttp import web
    from webtest_aiohttp import TestApp

    app = web.Application()

    async def hello(request):
        return web.json_response({'message': 'Hello world'})

    app.router.add_route('GET', '/', handler)

    def test_hello(loop):
        client = TestApp(app, loop=loop)
        res = client.get('/')
        assert res.status_code == 200
        assert res.json == {'message': 'Hello world'}

Installation
============
::

    pip install webtest-aiohttp


**Note: If you are using aiohttp<2.0.0, you will need to install webtest-aiohttp 1.x.**

::

    pip install 'webtest-aiohttp<2.0.0'


Usage with pytest
=================

If you are using pytest and pytest-aiohttp, you can make your tests more
concise with a fixture.


.. code-block:: python

    from aiohttp import web
    from webtest_aiohttp import TestApp as WebTestApp

    app = web.Application()

    async def hello(request):
        return web.json_response({'message': 'Hello world'})

    app.router.add_route('GET', '/', handler)

    @pytest.fixture()
    def testapp(loop):
        return WebTestApp(app, loop=loop)

    def test_get(testapp):
        assert testapp.get('/').json == {'message': 'Hello world'}

Project Links
=============

- PyPI: https://pypi.python.org/pypi/webtest-aiohttp
- Issues: https://github.com/sloria/webtest-aiohttp/issues

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/webtest-aiohttp/blob/master/LICENSE>`_ file for more details.
