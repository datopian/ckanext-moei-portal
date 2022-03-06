import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.model as model

from ckanext.fcscopendata.logic import action
import ckanext.fcscopendata.cli as cli
from ckanext.fcscopendata.views import vocab_tag_autocomplete

from ckan.lib.plugins import DefaultTranslation

from flask import Blueprint, render_template
from ckan.common import c

def hello_plugin():
    return u'Hello from the fcscopendata Theme extension'


class FcscopendataPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IClick)


    # IPackageController
    def after_search(self, search_results, search_params):

        # Update group and organization dict with translated fields.
        for idx, results in enumerate(search_results['results']):
            context = {'model': model, 'session': model.Session,
                       'user': c.user, 'auth_user_obj': c.userobj}
            if results.get('groups', []):
                for gidx, group in enumerate(results.get('groups', [])):
                    group_dict = logic.get_action('group_show')(context, {'id': group.get('id')})
                    search_results['results'][idx]['groups'][gidx].update(
                        {'title_translated' : group_dict.get('title_translated', {'ar': '', 'en': ''})})
                    search_results['results'][idx]['groups'][gidx].update(
                        {'description_translated' : group_dict.get('description_translated', {'ar': '', 'en': ''})})

            if results.get('organization', {}):
                org_dict = logic.get_action('organization_show')(context, {'id': results.get('organization', {})['id'] })
                search_results['results'][idx]['organization'].update(
                    {'title_translated' : org_dict.get('title_translated', {'ar': '', 'en': ''})})
                search_results['results'][idx]['organization'].update(
                    {'notes_translated' : org_dict.get('notes_translated', {'ar': '', 'en': ''})})

            if results.get('tags', []):
                for inindex, tag in enumerate(search_results['results'][idx]['tags']):
                    search_results['results'][idx]['tags'][inindex] =  \
                    logic.get_action('tag_show')(context, {'id': tag['id'] })
                    
        return search_results


    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets',
                             'fcscopendata')

    # IBlueprint
    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''
        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = u'templates'
        # Add plugin url rules to Blueprint object
        blueprint.add_url_rule(u'/api/2/util/vocab/tag/autocomplete', methods=[u'GET'], 
                                view_func=vocab_tag_autocomplete)
        return blueprint

    def get_actions(self):
        return action.get_actions()

    # IClick
    def get_commands(self):
        return cli.get_commands()
