# -*- coding: utf-8 -*-
import asyncio
import json

import pytest
from aiohttp import web

from webtest_aiohttp import TestApp

@pytest.fixture(scope='session')
def loop():
    loop_ = asyncio.get_event_loop()
    asyncio.set_event_loop(loop_)
    return loop_

@pytest.fixture()
def app(loop):
    @asyncio.coroutine
    def handler(request):
        return web.Response(body=json.dumps(
            {'message': 'Hello world'}
        ).encode('utf-8'), content_type='application/json', charset='utf8')
    app_ = web.Application(loop=loop)

    app_.router.add_route('GET', '/', handler)
    return app_

def test_testapp(app):
    testapp = TestApp(app)
    res = testapp.get('/')
    assert res.status_code == 200
    expected = {'message': 'Hello world'}
    assert res.json == expected
    assert res.text == json.dumps(expected)
