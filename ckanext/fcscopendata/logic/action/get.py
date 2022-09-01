import json
import logging
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model as model


ValidationError = tk.ValidationError
_get_or_bust = tk.get_or_bust

log = logging.getLogger(__name__)

@p.toolkit.chained_action
@tk.side_effect_free
def package_search(up_func, context, data_dict):
    result = up_func(context, data_dict)
    # Only add bilingual fields if the action is called from API.
    if not context.get('request_from_ui', False):
        context = {'model': model, 'session': model.Session,
                    'user': tk.c.user, 'auth_user_obj': tk.c.userobj}
                    
        for idx, pkg in enumerate(result['results']):
            if pkg.get('groups', []):
                for gidx, group in enumerate(pkg.get('groups', [])):
                    group_dict = tk.get_action('group_show')(context, {'id': group.get('id')})
                    result['results'][idx]['groups'][gidx] = group_dict

            if pkg.get('organization', {}):
                org_dict = tk.get_action('organization_show')(context, {'id': pkg.get('organization', {})['id'] })
                result['results'][idx]['organization'] = org_dict

            if pkg.get('tags', []):
                for index, tag in enumerate(result['results'][idx]['tags']):
                    result['results'][idx]['tags'][index] =  \
                    tk.get_action('tag_show')(context, {'id': tag['id'] })
    return result

@p.toolkit.chained_action   
@tk.side_effect_free
def package_show(up_func,context,data_dict): 
    result = up_func(context, data_dict)
    if result.get('organization'):
        org_id = result.get('organization', {}).get('id')
        org_dict = tk.get_action('organization_show')(context, {
            'id': org_id,
            'include_dataset_count': False,
            'include_datasets': False,
            'include_users': False,
            'include_groups': False,
            'include_tags': False,
            'include_followers': False
            })
        result['organization'] = org_dict
    
    if result.get('groups', []):
        for idx, group in enumerate(result.get('groups')):
            group_dict = tk.get_action('group_show')(context, {
                'id': group['id'],
                'include_dataset_count': False,
                'include_datasets': False,
                'include_users': False,
                'include_groups': False,
                'include_tags': False,
                'include_followers': False
                })
            result.get('groups')[idx] = group_dict

    if result.get('tags', []):
        for idx, tag in enumerate(result.get('tags')):
            result['tags'][idx] =  \
            tk.get_action('tag_show')(context, {'id': tag['id'] })

    if result.get('publishing_status', '') == 'draft':
        tk.check_access('package_update', context, {'id': data_dict.get('id')})

    id = result.get('id')
    try:
        result['total_downloads'] = tk.get_action('package_stats')(context, {'package_id': id})
    except:
        log.error(f'package {id} stats not available')

    # resources = result.get('resources')
    # overall_stat = 0
    # for i, resource in enumerate(resources):
    #     resource_id = resource.get('id')
    #     try:
    #         stats = logic.get_action('resource_stats')(context, {'resource_id': resource_id})
    #         result['resources'][i]['total_downloads'] = stats
    #         overall_stat += int(stats)
    #     except:
    #         log.error(f'resource {resource_id} not found')

    # if "total_downloads" not in result:
    #     result['total_downloads'] = overall_stat

    if "total_downloads" not in result:
        result['total_downloads'] = 0
    return result


@p.toolkit.chained_action   
@tk.side_effect_free
def organization_show(up_func,context,data_dict): 
    result = up_func(context, data_dict)  

    # Return full icon url
    if result.get('logo_url') and not result.get('logo_url').startswith('http'):
        result['logo_display_url'] = tk.h.url_for_static(
                'uploads/group/%s' % result.get('logo_url'),
                qualified=True
            )
    else:
         result['logo_display_url'] = result.get('logo_url') or ''                                                                                                                                                                                                                                                                                                             
    return result


@p.toolkit.chained_action   
@tk.side_effect_free
def group_list(up_func,context,data_dict):
    groups = data_dict.get('groups', False)
    if groups:
        data_dict['groups'] = json.loads(groups)
    return up_func(context, data_dict)  


@p.toolkit.chained_action   
@tk.side_effect_free
def organization_list(up_func,context,data_dict):
    organizations = data_dict.get('organizations', False)
    if organizations:
        data_dict['organizations'] = json.loads(organizations)
    return up_func(context, data_dict)  


@p.toolkit.chained_action   
@tk.side_effect_free
def group_show(up_func,context,data_dict): 
    result = up_func(context, data_dict)  

    # Return full icon url
    if result.get('logo_url') and not result.get('logo_url').startswith('http'):
        result['logo_display_url'] = tk.h.url_for_static(
                'uploads/group/%s' % result.get('logo_url'),
                qualified=True
            )
    else:
         result['logo_display_url'] = result.get('logo_url') or ''                                                                                                                                                                                                                                                                                                                
    return result


@p.toolkit.chained_action         
@tk.side_effect_free
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
@tk.side_effect_free
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

        for field in extras:
            for key in field:
                if field['key'].endswith('_translated'):
                    result[field['key']] = json.loads(field.get('value', {}))
                else:
                    result[field['key']] = field.get('value', '')
        
    # return icon and image full url    
    if result.get('icon_url') and not result.get('icon_url').startswith('http'):
        result['icon_display_url'] = tk.h.url_for_static(
                'uploads/vocabulary/%s' % result.get('icon_url'), qualified=True)
    else:
        result['icon_display_url'] = result.get('icon_url') or  ''


    if result.get('image_url') and not result.get('image_url').startswith('http'):
        result['image_display_url'] = tk.h.url_for_static(
                'uploads/vocabulary/%s' % result.get('image_url'), qualified=True)
    else:
        result['image_display_url'] = result.get('image_url') or  ''



    for idx, tag in enumerate(result['tags']): 
        result['tags'][idx] = tk.get_action('tag_show')(context, {'id': tag['id']})

    return result