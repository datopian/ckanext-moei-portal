import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import json
from flask import Blueprint
from ckan.lib.plugins import DefaultTranslation
from ckanext.fcscopendata.models import setup

from ckanext.fcscopendata.views import vocab_tag_autocomplete, GroupManage, reports_index, reports_read, requests_download, reports_delete, reports_delete_confirm, reports_solve
import ckanext.fcscopendata.cli as cli
from ckanext.fcscopendata.lib.helpers import (
     get_package_download_stats, 
     is_dataset_draft, 
     get_dataset_group_list,
)

class FcscopendataPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.ITemplateHelpers)


    # IPackageController
    def before_index(self, pkg_dict):
        # Index vocab tags as tag field also so that
        # it is searchable via default tag query.
        data_dict = json.loads(pkg_dict.get('data_dict', {}))
        if data_dict.get('tags', []):
            tag_list = []
            tags = data_dict.get('tags', [])
            for tag in tags:
                tag_list.append(tag['name'])
            pkg_dict['tags'] = tag_list
        return pkg_dict

    def before_search(self, search_params):
        if toolkit.c.userobj:
            user_is_syadmin = toolkit.c.userobj.sysadmin
        else:
            user_is_syadmin = False

        include_drafts = search_params.get('include_drafts', False)
        if not include_drafts and not user_is_syadmin:
            search_params.update({
                'fq': '!(publishing_status:draft)' + search_params.get('fq', '')
            })
        return search_params

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets',
                             'fcscopendata')
         
        setup()

    # IBlueprint
    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''
        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = u'templates'
        # Add plugin url rules to Blueprint object
        blueprint.add_url_rule(u'/api/2/util/vocab/tag/autocomplete', methods=[u'GET'], 
                                view_func=vocab_tag_autocomplete)
        blueprint.add_url_rule(u'/dataset/groups/<id>', defaults= {u'package_type': u'dataset'},
                                view_func=GroupManage.as_view(str(u'groups')))
        blueprint.add_url_rule(u'/reports', view_func=reports_index, strict_slashes=False)
        blueprint.add_url_rule(u'/reports/data-request', view_func=reports_read, strict_slashes=False)
        blueprint.add_url_rule(u'/reports/data-request/download', view_func=requests_download,strict_slashes=False)
        blueprint.add_url_rule(u'/reports/data-request/delete', view_func=reports_delete, methods=['POST'], strict_slashes=False)
        blueprint.add_url_rule(u'/reports/data-request/solve', view_func=reports_solve, methods=['POST'], strict_slashes=False)
        blueprint.add_url_rule(u'/reports/data-request/confirm', view_func=reports_delete_confirm, methods=['POST'], strict_slashes=False )
        return blueprint

    # IActions
    def get_actions(self):
        import ckanext.fcscopendata.logic.action as action
        return dict((name, function) for name, function
                    in action.__dict__.items()
                    if callable(function))

    # IClick
    def get_commands(self):
        return cli.get_commands()


    #ITemplateHelpers
    def get_helpers(self):
        return {
            'get_package_download_stats': get_package_download_stats,
            'is_dataset_draft': is_dataset_draft,
            'get_dataset_group_list': get_dataset_group_list,
        }
