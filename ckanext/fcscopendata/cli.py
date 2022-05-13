import click
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.logic import get_action

from ckanext.fcscopendata.modal import (
    tag_extra_table,
    vocabulary_extra_table
)

def get_commands():
    return [fcsc]

@click.group()
def fcsc():
    pass

@fcsc.command()
def initdb():
    """Adds extras fields to ckan tag and vocabulary.
    Usage:
        fcsc initdb
        - Creates the necessary tables in the database
    """
    if not tag_extra_table.exists():
        tag_extra_table.create()
        click.secho(u"Tag extras DB tables created", fg=u"green")

    if not vocabulary_extra_table.exists():
        vocabulary_extra_table.create()
        click.secho(u"Vocabulary extras DB tables created", fg=u"green")
    
    click.secho(u"Tag and Vocabulary extra DB tables already created", fg=u"green")


@fcsc.command()
def removetags():
    """Remove duplicate tags
    Usage:
        fcsc removetags
    """
    context = {
        'model': model, 
        'session': model.Session, 
        'ignore_auth': True,
        'allow_partial_update': True
    }
    packages = get_action(u"package_list")(context, {})
    admin = get_action('get_site_user')(context, {})
    context['user'] = admin.get("apikey")
    original = {}
    duplicate = {}

    for pkg_name in packages:
        package = get_action("package_show")(context, {'id': pkg_name})
        tags = package.get("tags")

        new_tags = []
        tag_name = []
        if tags:
            for tag in tags:
                name = tag.get('name').lower()
                if (name in original) and (name in tag_name):
                    duplicate[name] = tag

                elif (name in original) and (name not in tag_name):
                    new_tags.append(original[name])
                else:
                    if tag.get('vocabulary_id'):
                        new_tags.append(tag)
                    else:
                        original[name] = tag
                        new_tags.append(tag)
                        tag_name.append(name)

        package['tags'] = new_tags
        package['cli'] = True
        get_action("package_update")(context, package)

    for _, item in duplicate.items():
        get_action("tag_delete")(context, item)

    click.secho(u"Duplicate Tags Removed", fg=u"green")

        
                        
        


