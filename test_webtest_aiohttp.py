# -*- coding: utf-8 -*-
import asyncio
import json

import pytest
from aiohttp import web
from aiohttp.web import json_response

from webtest_aiohttp import TestApp as WebTestApp

@pytest.fixture()
def app():
    async def handler(request):
        return json_response({'message': 'Hello world'})

    async def echo_post(request):
        form_body = await request.post()
        return json_response(dict(form_body))

    async def echo_json(request):
        json_body = await request.json()
        return json_response(json_body)

    async def echo_headers(request):
        return json_response(dict(request.headers))

    async def echo_params(request):
        return json_response(dict(request.query))

    app_ = web.Application()
    app_.router.add_route('GET', '/', handler)
    app_.router.add_route('POST', '/echo_post', echo_post)
    app_.router.add_route('POST', '/echo_json', echo_json)
    app_.router.add_route('GET', '/echo_headers', echo_headers)
    app_.router.add_route('GET', '/echo_params', echo_params)
    return app_


@pytest.fixture()
def wt(app, loop):
    return WebTestApp(app, loop=loop)

def test_get(wt):
    res = wt.get('/')
    assert res.status_code == 200
    expected = {'message': 'Hello world'}
    assert res.json == expected
    assert res.text == json.dumps(expected)

def test_post_form(wt):
    res = wt.post('/echo_post', {'name': 'Steve'})
    assert res.json == {'name': 'Steve'}

def test_post_json(wt):
    res = wt.post_json('/echo_json', {'name': 'Steve'})
    assert res.json == {'name': 'Steve'}

def test_headers(wt):
    res = wt.get('/echo_headers', headers={'X-Foo': 'Bar'})
    assert res.json['X-Foo'] == 'Bar'

def test_params(wt):
    res = wt.get('/echo_params?foo=bar')
    assert res.json == {'foo': 'bar'}
