import json
import logging

import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model as model
import ckan.plugins as p
import ckan.plugins.toolkit as tk
from sqlalchemy import or_

ValidationError = tk.ValidationError
_get_or_bust = tk.get_or_bust

log = logging.getLogger(__name__)


def _fix_datasets_groups_intl(context, datasets):
    """
    Add bilingual groups to a list of datasets
    """
    groups_names = [g.get("name")
                    for d in datasets for g in d.get("groups", [])]
    unique_groups_names = list(set(groups_names))
    group_list_action = tk.get_action("group_list")
    group_list_dict = {
        'groups': json.dumps(unique_groups_names),
        'all_fields': True,
        'include_extras': True,
        'include_dataset_count': False,
        'include_users': False,
        'include_groups': False,
        'include_tags': False,
        'include_followers': False
    }
    groups = group_list_action(context, group_list_dict)
    groups_cache = {g.get("id"): g for g in groups}

    for pkg in datasets:
        dataset_groups = pkg.get("groups", [])
        for idx, group in enumerate(dataset_groups):
            group_id = group['id']
            pkg['groups'][idx] = groups_cache[group_id]


def _fix_datasets_downloads_count(context, datasets):
    for pkg in datasets:
        # Get total downloads from db tables.
        try:
            count = tk.get_action(
                'package_stats')(context, {'package_id': pkg['id']})
            pkg["total_downloads"] = count if count != "" and count != '""' else 0
        except Exception as e:
            log.error(
                'package {id} download stats not available'.format(id=pkg['id']))
            log.error(e)
            pkg['total_downloads'] = 0


@p.toolkit.chained_action
@tk.side_effect_free
def package_search(up_func, context, data_dict):
    result = up_func(context, data_dict)

    datasets = result.get("results", [])
    _fix_datasets_groups_intl(context, datasets)
    _fix_datasets_downloads_count(context, datasets)

    # Add bilingual tags in facets result
    tags_facet_items = result.get('search_facets', {}).get(
        'tags', {}).get('items', [])
    new_tags_facet_items = []
    if len(tags_facet_items):
        tags_facet_names = [t.get('name') for t in tags_facet_items]
        tags_q = model.Session.query(model.Tag).filter(
            model.Tag.name.in_(tags_facet_names))
        tags = {t.name: t for t in tags_q.all()}
        for tag_facet in tags_facet_items:
            tag = tags.get(tag_facet.get("name"))
            if tag._extras:
                extras = model_dictize.extras_dict_dictize(
                    tag._extras, context)
                translated = list(filter(lambda d: d['key'] in [
                                  'name_translated'], extras))
                if translated:
                    field_value = json.loads(translated[0].get('value', {}))
                    new_tags_facet_items.append(
                        {**tag_facet, 'name_translated': field_value})
        result['search_facets']['tags']['items'] = new_tags_facet_items
    return result


@p.toolkit.side_effect_free
def frontend_package_search(context, data_dict):
    data_dict['show_drafts'] = False
    return tk.get_action('package_search')({}, data_dict)


@p.toolkit.chained_action
@tk.side_effect_free
def package_show(up_func, context, data_dict):
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

    _fix_datasets_groups_intl(context, [result])

    if result.get('tags', []):
        for idx, tag in enumerate(result.get('tags')):
            result['tags'][idx] =  \
                tk.get_action('tag_show')(context, {'id': tag['id']})

    if result.get('publishing_status', '') == 'draft':
        tk.check_access('package_update', context, {'id': data_dict.get('id')})

    _fix_datasets_downloads_count(context, [result])

    return result


@p.toolkit.chained_action
@tk.side_effect_free
def organization_show(up_func, context, data_dict):
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
def group_list(up_func, context, data_dict):
    groups = data_dict.get('groups', False)
    if groups:
        data_dict['groups'] = json.loads(groups)
    return up_func(context, data_dict)


@p.toolkit.chained_action
@tk.side_effect_free
def organization_list(up_func, context, data_dict):
    organizations = data_dict.get('organizations', False)
    if organizations:
        data_dict['organizations'] = json.loads(organizations)
    return up_func(context, data_dict)


@p.toolkit.chained_action
@tk.side_effect_free
def group_show(up_func, context, data_dict):
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
def tag_show(up_func, context, data_dict):
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    result = up_func(context, data_dict)
    query = model.Session.query(model.tag.Tag).filter(
        or_(model.tag.Tag.id == id, model.tag.Tag.name == id))
    tag = query.first()

    if tag._extras:
        extras = model_dictize.extras_dict_dictize(
            tag._extras, context)
        translated = list(filter(lambda d: d['key'] in [
                          'name_translated'], extras))
        if translated:
            prefix = 'name_translated'
            field_value = json.loads(translated[0].get('value', {}))
            result[prefix] = field_value
    return result


@p.toolkit.chained_action
@tk.side_effect_free
def vocabulary_show(up_func, context, data_dict):
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    result = up_func(context, data_dict)
    query = model.Session.query(model.vocabulary.Vocabulary).filter(
        or_(model.vocabulary.Vocabulary.id == id, model.vocabulary.Vocabulary.name == id))
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
        result['icon_display_url'] = result.get('icon_url') or ''

    if result.get('image_url') and not result.get('image_url').startswith('http'):
        result['image_display_url'] = tk.h.url_for_static(
            'uploads/vocabulary/%s' % result.get('image_url'), qualified=True)
    else:
        result['image_display_url'] = result.get('image_url') or ''

    for idx, tag in enumerate(result['tags']):
        result['tags'][idx] = tk.get_action(
            'tag_show')(context, {'id': tag['id']})

    return result
