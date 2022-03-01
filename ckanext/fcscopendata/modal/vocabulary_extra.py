# encoding: utf-8

from sqlalchemy import orm, types, Column, Table, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from six import text_type

from ckan.model import (
    vocabulary,
    meta,
    core,
    types as _types,
    domain_object
)


__all__ = ['VocabularyExtra', 'vocabulary_extra_table']

vocabulary_extra_table = Table('vocabulary_extra', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
    Column('vocabulary_id', types.UnicodeText, ForeignKey('vocabulary.id')),
    Column('key', types.UnicodeText),
    Column('value', types.UnicodeText),
    Column('state', types.UnicodeText, default=core.State.ACTIVE),
)


class VocabularyExtra(core.StatefulObjectMixin,
                 domain_object.DomainObject):
    pass

meta.mapper(VocabularyExtra, vocabulary_extra_table, properties={
    'vocabulary': orm.relation(vocabulary.Vocabulary,
        backref=orm.backref('_extras',
            collection_class=orm.collections.attribute_mapped_collection(u'key'),
            cascade='all, delete, delete-orphan',
            ),
        )
    },
    order_by=[vocabulary_extra_table.c.vocabulary_id, vocabulary_extra_table.c.key],
)

def _create_extra(key, value):
    return VocabularyExtra(key=text_type(key), value=value)

vocabulary.Vocabulary.extras = association_proxy(
    '_extras', 'value', creator=_create_extra)


