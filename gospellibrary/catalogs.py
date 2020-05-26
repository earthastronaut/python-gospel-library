from io import BytesIO
import os
import sqlite3

from . import config
from .compat import lzma, urljoin
from .client import create_session


__all__ = [
    'get_languages',
    'current_catalog_version',
    'CatalogDB',
]


def get_languages(schema_version=None, base_url=None, session=None):
    schema_version = (schema_version or config.DEFAULT_SCHEMA_VERSION)
    base_url = (base_url or config.DEFAULT_BASE_URL)
    session = (session or create_session())

    languages_url = urljoin(
        base_url,
        '{schema_version}/languages/languages.json'.format(
            schema_version=schema_version)
    )
    r = session.get(languages_url)
    if r.status_code == 200:
        return r.json()


def current_catalog_version(
        iso639_3_code=None,
        schema_version=None,
        base_url=None,
        session=None
):
    iso639_3_code = (iso639_3_code or config.DEFAULT_ISO639_3_CODE)
    schema_version = (schema_version or config.DEFAULT_SCHEMA_VERSION)
    base_url = (base_url or config.DEFAULT_BASE_URL)
    session = (session or create_session())

    index_url = urljoin(
        base_url,
        '{schema_version}/languages/{iso639_3_code}/index.json'.format(
            schema_version=schema_version,
            iso639_3_code=iso639_3_code,
        )
    )
    r = session.get(index_url)
    if r.status_code == 200:
        return r.json().get('catalogVersion', None)


def transform_renditions(cover_renditions, base_url=None):
    """ Converts the flat renditions string to individual objects
    """
    renditions = []
    for rendition in cover_renditions.splitlines():
        size, url = rendition.split(',', 1)
        width, height = size.split('x', 1)
        if not url.startswith('http'):
            if not base_url:
                raise ValueError(
                    'Base URL must be passed when url is not complete: {}'
                    .format(rendition)
                )
            url = urljoin(base_url, url)

        renditions.append(dict(
            width=int(width),
            height=int(height),
            url=url,
        ))
    return renditions


class CatalogDB:
    def __init__(
            self,
            iso639_3_code=None,
            catalog_version=None,
            schema_version=None,
            base_url=None,
            session=None,
            cache_path=None,
    ):
        iso639_3_code = (iso639_3_code or config.DEFAULT_ISO639_3_CODE)
        schema_version = (schema_version or config.DEFAULT_SCHEMA_VERSION)
        base_url = (base_url or config.DEFAULT_BASE_URL)
        cache_path = (cache_path or config.DEFAULT_CACHE_PATH)
        session = (session or create_session())
        if catalog_version is None:
            catalog_version = current_catalog_version(
                iso639_3_code=iso639_3_code,
                schema_version=schema_version,
                base_url=base_url,
                session=session,
            )

        self.iso639_3_code = iso639_3_code
        self.catalog_version = catalog_version
        self.schema_version = schema_version
        self.base_url = base_url
        self.session = session
        self.cache_path = cache_path

    def exists(self):
        return self._fetch_catalog() is not None

    def _fetch_catalog(self):
        catalog_path = os.path.join(
            self.cache_path,
            self.schema_version,
            'languages',
            self.iso639_3_code,
            'catalogs',
            str(self.catalog_version),
            'Catalog.sqlite'
        )
        if not os.path.isfile(catalog_path):
            catalog_xz_url = urljoin(
                self.base_url,
                '{schema_version}/languages/{iso639_3_code}/catalogs/{catalog_version}.xz'.format(
                    schema_version=self.schema_version,
                    iso639_3_code=self.iso639_3_code,
                    catalog_version=self.catalog_version,
                )
            )
            r = self.session.get(catalog_xz_url)
            if r.status_code == 200:
                try:
                    os.makedirs(os.path.dirname(catalog_path))
                except OSError:
                    pass

                with lzma.open(BytesIO(r.content)) as catalog_xz_file:
                    with open(catalog_path, 'wb') as f:
                        f.write(catalog_xz_file.read())

        if os.path.isfile(catalog_path):
            return catalog_path

        return None

    def dict_factory(self, cursor, row):
        obj = {}
        for i, column in enumerate(cursor.description):
            name = column[0]
            value = row[i]
            if value is None:
                continue

            if name in obj:
                continue

            if name in ['version', 'latest_version']:
                obj['version'] = value
            if name in ['cover_renditions', 'item_cover_renditions', 'image_renditions']:
                base_url = urljoin(self.base_url, self.schema_version)
                obj[name] = transform_renditions(value, base_url=base_url)
                obj['raw_' + name] = value
            else:
                obj[name] = value
        return obj

    def execute(self, query, params=None):
        catalog_path = self._fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as conn:
            conn.row_factory = self.dict_factory
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            finally:
                cursor.close()

    def languages(self):
        return self.execute("""
            SELECT language.*, language_name.*
            FROM
                language
                LEFT OUTER JOIN (
                    SELECT *
                    FROM language_name
                    WHERE localization_language_id=1
                ) language_name ON language.id=language_name.language_id
            ORDER BY lds
        """)

    def language_name(self, language_id):
        rows = self.execute("""
            SELECT name FROM language_name WHERE language_id=? LIMIT 1
        """, [language_id])
        return rows[0]['name'] if rows else None

    def item_categories(self):
        return self.execute("""SELECT * FROM item_category""")

    def collection(self, collection_id):
        rows = self.execute("""SELECT * FROM library_collection WHERE id=? LIMIT 1""", [collection_id])
        return rows[0] if rows else None

    def sections(self, collection_id):
        return self.execute("""
            SELECT *
            FROM library_section
            WHERE library_collection_id=?
            ORDER BY position
        """, [collection_id])

    def collections(self, section_ids):
        section_ids = (section_ids or [])
        query = """
            SELECT *
            FROM library_collection
            WHERE library_section_id IN ({})
            ORDER BY position
        """.format(','.join('?' * len(section_ids)))
        return self.execute(query, section_ids)

    def items(self, section_ids=None):
        if section_ids is not None:
            query = """
                SELECT item.*, library_item.*
                FROM
                    library_item
                    INNER JOIN item ON library_item.item_id=item.id
                WHERE library_section_id IN ({})
                ORDER BY position
            """.format(','.join('?' * len(section_ids)))
            return self.execute(query, section_ids)
        else:
            query = """
                SELECT item.*, library_item.*
                FROM
                    library_item
                    INNER JOIN item ON library_item.item_id=item.id
                ORDER BY external_id
            """
            return self.execute(query)

    def nodes(self, section_ids):
        """ When viewing a collection there are either references to other
        collections or references to items. The combination of these
        two are nodes.

        """
        return sorted(
            self.collections(section_ids) + self.items(section_ids),
            key=lambda node: node['position']
        )

    def item(self, item_id=None, uri=None):
        if item_id:
            rows = self.execute("""SELECT * FROM item WHERE id=? LIMIT 1""", [item_id])
        else:
            rows = self.execute("""SELECT * FROM item WHERE uri=? LIMIT 1""", [uri])
        return rows[0] if rows else None
