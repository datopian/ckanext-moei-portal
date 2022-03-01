import json
import logging
from unittest import result
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.logic as logic
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.plugins.toolkit import ValidationError
_get_or_bust = logic.get_or_bust

log = logging.getLogger(__name__)

def extras_save(extra_dicts, tag, context):
    model = context['model']
    extras = extra_dicts
    new_extras = {i['key'] for i in extras}
    if extras:
        old_extras = tag.extras
        for key in set(old_extras) - new_extras:
            del tag.extras[key]
        for x in extras:
            if 'deleted' in x and x['key'] in old_extras:
                del tag.extras[x['key']]
                continue
            tag.extras[x['key']] = x['value']
    if not context.get('defer_commit'):
        model.repo.commit()


@p.toolkit.chained_action
def package_create(up_func, context, data_dict):
    # Get the translated title field value in the original title field so that 
    # core features do not break. eg. solr search with title
    data_dict['title'] =  data_dict.get('title_translated-en', '')
    data_dict['notes'] =  data_dict.get('notes_translated-en', '')

    keywords =  [tag.strip() \
                for tag in data_dict.get('keywords-en', '').split(',') \
                if tag.strip()]
    tags = [{ 'name': word, 'state': 'active'} for word in keywords ]
    if tags:
        data_dict['tags'] = tags 
    result = up_func(context, data_dict)
    return result

@p.toolkit.chained_action
def package_update(up_func, context, data_dict):
    # Get the translated title field value in the original title field so that 
    # core features do not break. eg. solr search with title 
    if data_dict.get('title_translated-en', False):
        data_dict['title'] =  data_dict.get('title_translated-en', '')
        
    if data_dict.get('notes_translated-en', False):
        data_dict['notes'] =  data_dict.get('notes_translated-en', '')

    if data_dict.get('keywords-en', False):
        keywords =  [tag.strip() \
                    for tag in data_dict.get('keywords-en', '').split(',') \
                    if tag.strip()]
        tags = [{ 'name': word, 'state': 'active'} for word in keywords ]
        data_dict['tags'] = tags
    if data_dict.get('resources', False):
        for resources in data_dict['resources']:
            resources['description'] =  resources.get('notes_translated-en', '')
    result = up_func(context, data_dict)
    return result

@p.toolkit.chained_action                                                                                                                                                    
def organization_create(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict['notes_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-en', '')  
                                                                                          
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@p.toolkit.chained_action                                                                                                                                                    
def organization_update(up_func,context,data_dict):
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict['notes_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-en', '')  
                                                                                                          
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@p.toolkit.chained_action                                                                                                                                                    
def group_create(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict['description_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('description_translated-en', '')  
                                                                                          
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@p.toolkit.chained_action                                                                                                                                                    
def group_update(up_func,context,data_dict):
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict['description_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('description_translated-en', '')  
                                                                                                          
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@p.toolkit.chained_action                                                                                                                                                    
def tag_create(up_func,context,data_dict):
    '''
    :param name: the name for the new tag, a string between 2 and 100
        characters long containing only alphanumeric characters and ``-``,
        ``_`` and ``.``, e.g. ``'Jazz'``
    :type name: string
    :param vocabulary_id: the id of the vocabulary that the new tag
        should be added to, e.g. the id of vocabulary ``'Genre'``
    :type vocabulary_id: string

    :returns: the newly-created tag
    :rtype: dictionary
    '''
    model = context['model']
    tag = context.get('tag')
    data_dict['name'] = data_dict.get('name_translated-en', data_dict['name'])
    result = up_func(context, data_dict)  
    name_translated = {
        'en' : data_dict.get('name_translated-en', data_dict['name']), 
        'ar': data_dict.get('name_translated-ar', '')
    }
    data_dict["extras"] = [{"key": "name_translated", 
            "value": json.dumps(name_translated, ensure_ascii=False)
            }]
    if tag:
        data_dict['id'] = tag.id
    tag = model.tag.Tag.get(_get_or_bust(result, 'id'))
    extras_save(data_dict["extras"], tag, context)
    result["name_translated"] = name_translated
    return result
    
@p.toolkit.chained_action                                                                                                                                                    
def tag_show(up_func,context,data_dict):
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    result = up_func(context, data_dict)  
    query = model.Session.query(model.tag.Tag).filter(model.tag.Tag.id == id)
    tag = query.first()
    if tag is None:
        query = model.Session.query(model.tag.Tag).filter(model.tag.Tag.name == id)
        tag = query.first()

    if tag._extras:
        extras = model_dictize.extras_dict_dictize(
                tag._extras, context)
        translated = list(filter(lambda d: d['key'] in ['name_translated'], extras))
        if translated:   
            prefix = 'name_translated'
            field_value = json.loads(translated[0].get('value', {}))
            result[prefix] = field_value
    return result

@p.toolkit.chained_action                                                                                                                                                    
def vocabulary_show(up_func,context,data_dict):
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    result = up_func(context, data_dict)
    query = model.Session.query(model.vocabulary.Vocabulary).filter(model.vocabulary.Vocabulary.id == id)
    vocabulary = query.first()
    if vocabulary is None:
        query = model.Session.query(model.vocabulary.Vocabulary).filter(model.vocabulary.Vocabulary.name == id)
        vocabulary = query.first()

    if vocabulary._extras:
        extras = model_dictize.extras_dict_dictize(
         vocabulary._extras, context)
        translated = list(filter(lambda d: d['key'] in ['name_translated'], extras))
        if translated:   
            prefix = 'name_translated'
            field_value = json.loads(translated[0].get('value', {}))
            result[prefix] = field_value
        
        for idx, tag in enumerate(result['tags']): 
            result['tags'][idx] = logic.get_action('tag_show')(context, {'id': tag['id']})
    return result


@p.toolkit.chained_action                                                                                                                                                    
def vocabulary_create(up_func,context,data_dict):
    '''Create a new tag vocabulary.
    You must be a sysadmin to create vocabularies.
    :param name: the name of the new vocabulary, e.g. ``'Genre'``
    :type name: string
    :param name_translated-en: translated name in English
    :type name: string
     :param name_translated-ar: translated name in Aragic
    :type name: string
    :param tags: the new tags to add to the new vocabulary, for the format of
        tag dictionaries see :py:func:`tag_create`
    :type tags: list of tag dictionaries

    :returns: the newly-created vocabulary
    :rtype: dictionary
    '''
    if data_dict.get('tags', False):
        tags = data_dict.pop('tags')

    name_translated = {
        'en' : data_dict.get('name_translated-en', data_dict['name']), 
        'ar': data_dict.get('name_translated-ar', '')
    }
    data_dict["extras"] = [{"key": "name_translated", 
        "value": json.dumps(name_translated, ensure_ascii=False)
        }]
        
    result = up_func(context, data_dict)  
    model = context['model']
    vocabulary = model.vocabulary.Vocabulary.get(_get_or_bust(result, 'id'))
    extras_save(data_dict["extras"], vocabulary, context)
    # Create tags if tags is given in request payload
    if tags: 
        result['tags'] = []
        for tag in tags:
            if isinstance(tag, dict):
                tag_dict = logic.get_action('tag_create')(context,
                {**tag,'vocabulary_id': _get_or_bust(result, 'id')})
                result['tags'].append(tag_dict)
            else:
                raise ValidationError({'message': 'Provied list of tags doesn\'t have valid dictionaries.'})
    return result

def get_actions():
    return {
        'package_create': package_create,
        'package_update': package_update,
        'organization_create': organization_create,
        'organization_update': organization_update,
        'group_create': group_create,
        'group_update': group_update,
        'tag_create': tag_create,
        'tag_show': tag_show,
        'vocabulary_create': vocabulary_create,
        'vocabulary_show': vocabulary_show
    }


