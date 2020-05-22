from . import (
    catalogs,
    client,
    config,
    compat,
    item_packages,
)

from catalogs import *
from client import *
from item_packages import *

__version__ = '2.0.0'
__all__ = (
    [
        'catalogs',
        'client',
        'config',
        'compat',
        'item_packages',
    ]
    + catalogs.__all__
    + client.__all__
    + item_packages.__all__
)
