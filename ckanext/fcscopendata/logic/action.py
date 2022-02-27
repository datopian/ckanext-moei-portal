import json
import logging
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.logic as logic
import ckanext.fcscopendata.modal.tags_extra as tags_extra
import ckan.lib.dictization as d
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
    model = context['model']
    tag = context.get('tag')
    data_dict['name'] = data_dict.get('name_translated-en', data_dict['name'])
    result = up_func(context, data_dict)  
    name_translated = {
        'en' : data_dict.get('name_translated-en', data_dict['name']), 
        'ar': data_dict.get('name_translated-ar', '')
    }
    data_dict["extras"] = [{"key": "author_translated", 
            "value": json.dumps(name_translated, ensure_ascii=False)
            }]
    if tag:
        data_dict['id'] = tag.id
    tag = model.tag.Tag.get(_get_or_bust(result, 'id'))
    extras_save(data_dict["extras"], tag, context)
    result["name_translated"] = name_translated
    return result

@p.toolkit.chained_action                                                                                                                                                    
def vocabulary_create(up_func,context,data_dict):
    if data_dict.get('tags', False):
        tags = data_dict.pop('tags')
        del data_dict['tags']

    name_translated = {
        'en' : data_dict.get('name_translated-en', data_dict['name']), 
        'ar': data_dict.get('name_translated-ar', '')
    }
    data_dict["extras"] = [{"key": "author_translated", 
        "value": json.dumps(name_translated, ensure_ascii=False)
        }]
        
    result = up_func(context, data_dict)  
    model = context['model']
    vocabulary = model.vocabulary.Vocabulary.get(_get_or_bust(result, 'id'))
    extras_save(data_dict["extras"], vocabulary, context)
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
        'vocabulary_create': vocabulary_create,
    }


