import json
import logging
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.uploader as uploader

from ckanext.fcscopendata.lib.util import (
    add_user_as_memeber_on_groups,
    theme_update,
    editor_publishing_dataset,
    extras_save
)

ValidationError = tk.ValidationError
_get_or_bust = tk.get_or_bust

log = logging.getLogger(__name__)


@p.toolkit.chained_action
def package_update(up_func, context, data_dict):
    # Get the translated title field value in the original title field so that 
    # core features do not break. eg. solr search with title 
    model = context['model']

    if data_dict.get('title_translated-en', False):
        data_dict['title'] =  data_dict.get('title_translated-en', '')
        
    if data_dict.get('notes_translated-en', False):
        data_dict['notes'] =  data_dict.get('notes_translated-en', '')
    
    if not data_dict.get('allow_free_tags', False):
        tags  = model.Session.query(model.tag.Tag).filter(model.tag.Tag.name.in_(
            tag['name'] for tag in data_dict['tags'])).all()

        tags_dict = model_dictize.tag_list_dictize(tags, context)

        for idx, tag in enumerate(data_dict['tags']):
            data_dict['tags'][idx]['vocabulary_id'] = \
                [t.get('vocabulary_id', None) for t in tags_dict if t['name'] == tag['name']][0]

        # Do not create free tags. 
        data_dict['tag_string'] = ''

    # Always publish dataset as private for editor user
    if editor_publishing_dataset(data_dict.get('owner_org', ''), context):
        data_dict['private'] = True

    # Add selected groups in package
    if data_dict.get('topics'):
        pkg_group = data_dict.get('topics')
        if isinstance(pkg_group, str):
            try:
                pkg_group = eval(pkg_group)
            except:
                pkg_group = [pkg_group]
                
        # Add user as member on each group
        add_user_as_memeber_on_groups(pkg_group, context)

        group = model.Session.query(model.group.Group).filter(model.group.Group.id.in_(pkg_group)).all()
        group_dict = model_dictize.group_list_dictize(group, context, with_package_counts=False)
        data_dict['groups'] = group_dict
    else:
        data_dict['groups'] = []

    # Map resource description from scheming note field
    if data_dict.get('resources', False):
        for resources in data_dict['resources']:
            resources['description'] =  resources.get('notes_translated-en', '')
    result = up_func(context, data_dict)

    # Update package member for groups
    try:
        delete_groups = theme_update(result, data_dict['groups'], context)
        result['groups'] = list(filter(lambda g: g['id'] not in delete_groups, result['groups']))
    except: 
        log.warn('Failed to update deleted groups')

    return result


@p.toolkit.chained_action   
def resource_update(up_func,context, data_dict):
    result = up_func(context, data_dict)
    # update dataset publishing status 
    if data_dict.get('pkg_publishing_status', False):
        tk.get_action('package_patch')(context, {
            'id': data_dict.get('package_id', ''), 
            'publishing_status': data_dict.get('pkg_publishing_status')
            })
        data_dict.pop('pkg_publishing_status', None)
    return result


@p.toolkit.chained_action                                                                                                                                                    
def organization_update(up_func,context,data_dict):
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict['notes_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-en', '') 

    # upload icon  
    upload = uploader.get_uploader('group')
    upload.update_data_dict(data_dict, 'logo_url','logo_upload', 'logo_upload_clear')
    upload.upload(uploader.get_max_image_size())                                                                                                 
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result


@p.toolkit.chained_action                                                                                                                                                    
def group_update(up_func,context,data_dict):
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict['description_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('description_translated-en', '')  
        
    
    # upload icon  
    upload = uploader.get_uploader('group')
    upload.update_data_dict(data_dict, 'logo_url','logo_upload', 'logo_upload_clear')
    upload.upload(uploader.get_max_image_size())  
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                   
    return result


@p.toolkit.chained_action                                                                                                                                                    
def vocabulary_update(up_func,context,data_dict):
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

    name_translated = {
        'en' : data_dict.get('name_translated-en', ''), 
        'ar': data_dict.get('name_translated-ar', '')
    }

    description_translated = {
        'en' : data_dict.get('description_translated-en', ''), 
        'ar': data_dict.get('description_translated-ar', '')
    }

    data_dict["extras"] = [{
        "key": "name_translated", 
        "value": json.dumps(name_translated, ensure_ascii=False)
        },{
        "key": "description_translated", 
        "value": json.dumps(description_translated, ensure_ascii=False)
        }]
        
    
    if data_dict.get('image_upload'):
        upload = uploader.get_uploader('vocabulary')
        upload.update_data_dict(data_dict, 'image_url',
                                'image_upload', 'clear_upload')
        upload.upload(uploader.get_max_image_size())

    if data_dict.get('icon_upload'):
        upload = uploader.get_uploader('vocabulary')
        upload.update_data_dict(data_dict, 'icon_url',
                                'icon_upload', 'clear_upload')
        upload.upload(uploader.get_max_image_size())
    
    data_dict["extras"].extend([
        {
        "key": "image_url", 
        "value": data_dict.get('image_url', '')
        },
        {
        "key": "icon_url", 
        "value": data_dict.get('icon_url', '')
        }])   

    result = up_func(context, data_dict)  
    model = context['model']
    vocabulary = model.vocabulary.Vocabulary.get(_get_or_bust(result, 'id'))
    extras_save(data_dict["extras"], vocabulary, context)
    return result