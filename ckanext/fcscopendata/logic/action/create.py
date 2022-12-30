import json
import logging
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.uploader as uploader
from datetime import datetime
from sqlalchemy import or_

from ckanext.fcscopendata.lib.util import (
    add_user_as_memeber_on_groups,
    editor_publishing_dataset,
    extras_save
)

_get_or_bust = tk.get_or_bust

log = logging.getLogger(__name__)

@p.toolkit.chained_action
def package_create(up_func, context, data_dict):
    # Get the translated title field value in the original title field so that 
    # core features do not break. eg. solr search with title
    model = context['model']
    data_dict['title'] =  data_dict.get('title_translated-en', '')
    data_dict['notes'] =  data_dict.get('notes_translated-en', '')
    start_period = data_dict.get('start_period', False)
    end_period = data_dict.get('end_period', False)

    if start_period:
        try:
            start_date = datetime.strptime(str(start_period), '%Y-%m').isoformat()
        except:
            try:
                start_date = datetime.strptime(str(start_period), '%Y-%m-%d').isoformat()
            except ValueError as ve:
                log.error('%s for start period', ve)
                raise tk.ValidationError(
                        error_dict =  { 'start_period' : ['Start period needs to be in the format YYYY-MM or YYYY-MM-DD'] },
                        error_summary = ['Start period needs to be in the format YYYY-MM or YYYY-MM-DD']
                    )

    if end_period:
        try:
            end_date = datetime.strptime(str(end_period), '%Y-%m').isoformat()
        except:
            try:
                end_date = datetime.strptime(str(end_period), '%Y-%m-%d').isoformat()
            except ValueError as ve:
                log.error('%s for end period', ve)
                raise tk.ValidationError(
                        error_dict =  { 'end_period' : ['End period needs to be in the format YYYY-MM or YYYY-MM-DD'] },
                        error_summary = ['End period needs to be in the format YYYY-MM or YYYY-MM-DD']
                    )
    if start_period and end_period:
        if start_date > end_date:
            raise tk.ValidationError(
                error_dict =  { 'start_period' : ['Start period need to be lesser than End Period'] },
                error_summary = ['Start period need to be lesser than End Period']
            )

    if data_dict.get('tags', False):
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
        
    result = up_func(context, data_dict)
    return result


@p.toolkit.chained_action   
def resource_create(up_func,context, data_dict):
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
def organization_create(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict.get('notes_translated-en'):                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-en', '')  

    # upload icon  
    upload = uploader.get_uploader('group')
    upload.update_data_dict(data_dict, 'icon_url','icon_upload', 'clear_upload')
    upload.upload(uploader.get_max_image_size())                                                          
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@p.toolkit.chained_action                                                                                                                                                    
def group_create(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-en', '') 

    if data_dict['description_translated-en']:                                                                                                                         
        data_dict['description'] = data_dict.get('description_translated-en', '')  
    
    # upload icon 
    upload = uploader.get_uploader('group')
    upload.update_data_dict(data_dict, 'icon_url','icon_upload', 'clear_upload')
    upload.upload(uploader.get_max_image_size())                                                                 
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
    name_translated = {
        'en' : data_dict.get('name_translated-en', data_dict['name']), 
        'ar': data_dict.get('name_translated-ar', '')
    }

    tag_already_exist = model.Session.query(model.tag.Tag).filter(or_(
        model.tag.Tag.extras.ilike("%{0}%".format(name_translated['en'])),
        model.tag.Tag.extras.ilike("%{0}%".format(name_translated['ar']))
        )
    ).first()

    if tag_already_exist:
        raise tk.ValidationError({
            'message': [
                    u'Tag "{0}" is already belongs to category "{1}".'.format(
                        name_translated['en'], tag_already_exist.vocabulary.name)]
            })
    result = up_func(context, data_dict)  

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
    else:
        tags = False

    name_translated = {
        'en' : data_dict.get('name_translated-en', data_dict['name']), 
        'ar': data_dict.get('name_translated-ar', '')
    }

    description_translated = {
        'en' : data_dict.get('description_translated-en', ''), 
        'ar': data_dict.get('description_translated-ar', '')
    }

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
        
    data_dict["extras"] = [{
        "key": "name_translated", 
        "value": json.dumps(name_translated, ensure_ascii=False)
        },{
        "key": "description_translated", 
        "value": json.dumps(description_translated, ensure_ascii=False)
        },{
        "key": "image_url", 
        "value": data_dict.get('image_url', '')
        },{
        "key": "icon_url", 
        "value": data_dict.get('icon_url', '')
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
                tag_dict = tk.get_action('tag_create')(context,
                {**tag,'vocabulary_id': _get_or_bust(result, 'id')})
                result['tags'].append(tag_dict)
            else:
                raise tk.ValidationError({'message': 'Provied list of tags doesn\'t have valid dictionaries.'})
    return result
