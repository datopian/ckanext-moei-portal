import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.fcscopendata.logic import action
from ckan.lib.plugins import DefaultTranslation

from flask import Blueprint, render_template


def hello_plugin():
    return u'Hello from the fcscopendata Theme extension'


class FcscopendataPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITranslation)


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
        blueprint.add_url_rule('/hello_plugin', '/hello_plugin', hello_plugin)
        return blueprint

    def get_actions(self):
        return action.get_actions()

