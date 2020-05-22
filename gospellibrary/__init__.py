from . import (
    config,
    compat,
    catalogs,
    item_packages,
)

__version__ = '2.0.0'
__all__ = (
    [
        'config',
        'compat',
        'catalogs',
        'item_packages',
    ]
    + catalogs.__all__
    + item_packages.__all__
)
