import os
import aiohttp_mako

from . import views
from . import panels
from .utils import APP_KEY, TEMPLATE_KEY, STATIC_ROUTE_NAME, hexlify, \
    ToolbarStorage, ExceptionHistory
from .views import ExceptionDebugView

default_panel_names = [
    panels.HeaderDebugPanel,
    panels.PerformanceDebugPanel,
    panels.RequestVarsDebugPanel,
    panels.TracebackPanel,
    ]


default_global_panel_names = [
    panels.RoutesDebugPanel,
    panels.SettingsDebugPanel,
    panels.MiddlewaresDebugPanel,
    panels.VersionDebugPanel,
]


default_settings = {
    'enabled': True,
    'intercept_exc': 'debug',  # display or debug or False
    'intercept_redirects': True,
    'panels': default_panel_names,
    'extra_panels': [],
    'global_panels': default_global_panel_names,
    'extra_global_panels': [],
    'hosts': ['127.0.0.1'],
    'exclude_prefixes': [],
    'button_style': '',
    'max_request_history': 100,
    'max_visible_requests':  10,
}


def setup(app, **kw):
    config = {}
    config.update(default_settings)
    config.update(kw)

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    app[APP_KEY] = {}
    templates_app = os.path.join(APP_ROOT, 'templates')
    templates_panels = os.path.join(APP_ROOT, 'panels/templates')

    app[APP_KEY]['settings'] = config

    aiohttp_mako.setup(app, input_encoding='utf-8',
                       output_encoding='utf-8',
                       default_filters=['decode.utf8'],
                       directories=[templates_app, templates_panels],
                       app_key=TEMPLATE_KEY)

    static_location = os.path.join(APP_ROOT, 'static')

    exc_handlers = ExceptionDebugView()

    app.router.add_static('/_debugtoolbar/static', static_location,
                          name=STATIC_ROUTE_NAME)

    app.router.add_route('GET', '/_debugtoolbar/source', exc_handlers.source,
                         name='debugtoolbar.source')
    app.router.add_route('GET', '/_debugtoolbar/execute', exc_handlers.execute,
                         name='debugtoolbar.execute')
    # app.router.add_route('GET', '/_debugtoolbar/console',
    # exc_handlers.console,
    #                      name='debugtoolbar.console')
    app.router.add_route('GET', '/_debugtoolbar/exception',
                         exc_handlers.exception,
                         name='debugtoolbar.exception')
    # TODO: fix when sql will be ported
    # app.router.add_route('GET', '_debugtoolbar/sqlalchemy/sql_select',
    #                      name='debugtoolbar.sql_select')
    # app.router.add_route('GET', '_debugtoolbar/sqlalchemy/sql_explain',
    #                      name='debugtoolbar.sql_explain')

    app.router.add_route('GET', '/_debugtoolbar/sse', views.sse,
                         name='debugtoolbar.sse')

    app.router.add_route('GET', '/_debugtoolbar/{request_id}',
                         views.request_view, name='debugtoolbar.request')
    app.router.add_route('GET', '/_debugtoolbar', views.request_view,
                         name='debugtoolbar.main')
    app.router.add_route('GET', '/_debugtoolbar', views.request_view,
                         name='debugtoolbar')

    def settings_opt(name):
        return app[APP_KEY]['settings'][name]

    max_request_history = settings_opt('max_request_history')

    app[APP_KEY]['request_history'] = ToolbarStorage(max_request_history)
    app[APP_KEY]['exc_history'] = ExceptionHistory()
    app[APP_KEY]['pdtb_token'] = hexlify(os.urandom(10))
    intercept_exc = settings_opt('intercept_exc')
    if intercept_exc:
        app[APP_KEY]['exc_history'].eval_exc = intercept_exc == 'debug'
