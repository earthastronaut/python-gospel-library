import requests
from requests.adapters import HTTPAdapter

from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

from . import config


__all__ = [
    'requests',
    'create_session',
]


class TimeoutHttpAdapter(HTTPAdapter):
    """ Adapter to add default timeout to requests

    > You can tell Requests to stop waiting for a response after a given number
    > of seconds with the timeout parameter. Nearly all production code should use
    > this parameter in nearly all requests. Failure to do so can cause your
    > program to hang indefinitely

    [requests timeout](https://2.python-requests.org/en/master/user/quickstart/#timeouts)

    """
    def __init__(self, *args, **kwargs):
        timeout_default = 60
        self.timeout = kwargs.pop('timeout', timeout_default)
        HTTPAdapter.__init__(self, *args, **kwargs)

    def send(self, *args, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return HTTPAdapter.send(self, *args, **kwargs)


def create_session(cache_path=None, http_adapter_kws=None):
    """ Create a session object with some enhanced features.

    Features include:

        * Default timeout
        * Default retry
        * Request file caching

    Notes:

        * Call this within functions, not globally. Session objects should
            be instantiated once per thread.

    Parameters:

        cache_path (str): File path for caching, uses config.DEFAULT_CACHE_PATH
            as default.

        http_adapter_kws (dict): keyword arguments passed to TimeoutHTTPAdapter

    Returns:

        requests.Session: Session with enhanced features.

    """
    cache_path = (cache_path or config.DEFAULT_CACHE_PATH)

    defaults = {
        'timeout': config.DEFAULT_CLIENT_TIMEOUT,
        'max_retries': config.DEFAULT_CLIENT_MAX_RETRIES,
    }
    defaults.update(http_adapter_kws or {})
    http_adapter = TimeoutHttpAdapter(**defaults)

    requests_session = requests.session()
    requests_session.mount('http://', http_adapter)
    requests_session.mount('https://', http_adapter)
    if cache_path is None:
        return requests_session
    else:
        session = CacheControl(requests_session, cache=FileCache(cache_path))
        return session
