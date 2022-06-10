import logging
import ckan.plugins.toolkit as tk
from ckan.common import c
from ckan.authz import users_role_for_group_or_org


log = logging.getLogger(__name__)

def theme_update(pkg, groups, context):
    model = context['model']
    members = model.Session.query(model.Member).\
            filter(model.Member.table_name == 'package').\
            filter(model.Member.table_id == pkg['id']).\
            filter(model.Member.capacity == 'public').\
            filter(model.Member.group_id.notin_(group['id'] for group in groups)).all()

    delete_groups = []
    if members: 
        for member in members:
            model.Session.delete(member)
            model.repo.commit()
            delete_groups.append(member.id)
    return delete_groups

def editor_publishing_dataset(owner_org, context):
    user_capacity = users_role_for_group_or_org(owner_org, context['user'])
    return user_capacity != 'admin'

def add_user_as_memeber_on_groups(groups, context):
    for group_id in groups:
        is_memeber_of_group = users_role_for_group_or_org(group_id, context['user'])
        if not is_memeber_of_group:
            member_dict = {
            'id': group_id,
            'object': c.userobj.id,
            'object_type': 'user',
            'capacity': 'member',
            }
            tk.logic.get_action('member_create')(dict(context, ignore_auth=True),
                                                member_dict)

def extras_save(extra_dicts, model_obj, context):
    model = context['model']
    extras = extra_dicts
    new_extras = {i['key'] for i in extras}
    if extras:
        old_extras = model_obj.extras
        for key in set(old_extras) - new_extras:
            del model_obj.extras[key]
        for x in extras:
            if 'deleted' in x and x['key'] in old_extras:
                del model_obj.extras[x['key']]
                continue
            model_obj.extras[x['key']] = x['value']
    if not context.get('defer_commit'):
        model.repo.commit()

