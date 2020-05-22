try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

try:
    import lzma
except ImportError:
    from backports import lzma


__all__ = [
    'lzma',
    'urljoin',
]
