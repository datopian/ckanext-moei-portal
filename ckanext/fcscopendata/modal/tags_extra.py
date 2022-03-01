# encoding: utf-8

from sqlalchemy import orm, types, Column, Table, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from six import text_type

from ckan.model import (
    tag,
    meta,
    core,
    types as _types,
    domain_object
)


__all__ = ['TagExtra', 'tag_extra_table']

tag_extra_table = Table('tag_extra', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
    Column('tag_id', types.UnicodeText, ForeignKey('tag.id')),
    Column('key', types.UnicodeText),
    Column('value', types.UnicodeText),
    Column('state', types.UnicodeText, default=core.State.ACTIVE),
)


class TagExtra(core.StatefulObjectMixin,
                 domain_object.DomainObject):
    pass

meta.mapper(TagExtra, tag_extra_table, properties={
    'tag': orm.relation(tag.Tag,
        backref=orm.backref('_extras',
            collection_class=orm.collections.attribute_mapped_collection(u'key'),
            cascade='all, delete, delete-orphan',
            ),
        )
    },
    order_by=[tag_extra_table.c.tag_id, tag_extra_table.c.key],
)

def _create_extra(key, value):
    return TagExtra(key=text_type(key), value=value)

tag.Tag.extras = association_proxy(
    '_extras', 'value', creator=_create_extra)

