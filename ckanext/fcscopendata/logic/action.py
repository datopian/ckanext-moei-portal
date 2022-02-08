import logging
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.logic as logic

_get_or_bust = logic.get_or_bust

log = logging.getLogger(__name__)

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
    data_dict['display_name'] = data_dict.get('title_translated-en', '') 

    if data_dict['notes_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-en', '')  
                                                                                          
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@p.toolkit.chained_action                                                                                                                                                    
def organization_update(up_func,context,data_dict):
    data_dict['display_name'] = data_dict.get('title_translated-en', '') 

    if data_dict['notes_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-en', '')  
                                                                                                          
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@p.toolkit.chained_action                                                                                                                                                    
def group_create(up_func,context,data_dict): 
    print(data_dict)
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


def get_actions():
    return {
        'package_create': package_create,
        'package_update': package_update,
        'organization_create': organization_create,
        'organization_update': organization_update,
        'group_create': group_create,
        'group_update': group_update
    }


