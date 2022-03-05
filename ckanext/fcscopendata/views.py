import ckan.model as model
from ckan.common import json, _, g, request
from ckan.logic import get_action
from ckan.views.api import _finish_ok

API_REST_DEFAULT_VERSION = 1

def vocab_tag_autocomplete():
    q = request.args.get(u'incomplete', u'')
    context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}

    limit = request.args.get(u'limit', 10)
    vocab_list = get_action(u'vocabulary_list')(context, {})

    tag_list = []
    if q:
        data_dict = {u'q': q, u'limit': limit}

        for vocab in vocab_list:
            tags = get_action(u'tag_autocomplete')(context, 
                {**data_dict,'vocabulary_id': vocab['id'] })
            for tag_item in tags:
                tag_list.append(tag_item) 
            
    resultSet = {
        u'ResultSet': {
            u'Result': [{u'Name': tag} for tag in tag_list]
        }
    }

    return _finish_ok(resultSet)