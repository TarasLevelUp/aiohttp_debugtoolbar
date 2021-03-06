import asyncio
import aiohttp_debugtoolbar
import aiohttp_mako

from aiohttp import web


@aiohttp_mako.template('index.html')
def basic_handler(request):
    return {'title': 'example aiohttp_debugtoolbar!',
            'text': 'Hello aiohttp_debugtoolbar!',
            'app': request.app}


@asyncio.coroutine
def exception_handler(request):
    raise NotImplementedError


@asyncio.coroutine
def init(loop):
    # add aiohttp_debugtoolbar middleware to you application
    app = web.Application(loop=loop, middlewares=[aiohttp_debugtoolbar
                          .toolbar_middleware_factory])
    # install aiohttp_debugtoolbar
    aiohttp_debugtoolbar.setup(app)

    # install mako templates
    lookup = aiohttp_mako.setup(app, input_encoding='utf-8',
                                output_encoding='utf-8',
                                default_filters=['decode.utf8'])
    template = """
    <html>
        <head>
            <title>${title}</title>
        </head>
        <body>
            <h1>${text}</h1>
            <p>
              <a href="${app.router['exc_example'].url()}">
              Exception example</a>
            </p>
        </body>
    </html>
    """
    lookup.put_string('index.html', template)

    app.router.add_route('GET', '/', basic_handler, name='index')
    app.router.add_route('GET', '/exc', exception_handler, name='exc_example')

    handler = app.make_handler()
    srv = yield from loop.create_server(handler, '127.0.0.1', 9000)
    print("Server started at http://127.0.0.1:9000")
    return srv, handler


loop = asyncio.get_event_loop()
srv, handler = loop.run_until_complete(init(loop))
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(handler.finish_connections())
