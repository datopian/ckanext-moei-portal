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
    site_user = get_action(u"get_site_user")({u"ignore_auth": True}, {})
    context = {u"user": site_user[u"name"]}

    original_tags = {}
    duplicate_tags = {}

    for pkg_name in packages:
        package_dict = get_action("package_show")(context, {'id': pkg_name})
        tags = package_dict.get("tags")
        pkg_tag_dicts = []
        pkg_tag_list = []
        
        if tags:
            for tag in tags:
                name = tag.get('name').lower()
                if (name in original_tags) and (name in pkg_tag_list):
                    duplicate_tags[name] = tag

                elif (name in original_tags) and (name not in pkg_tag_list):
                    pkg_tag_dicts.append(original_tags[name])
                else:
                    if tag.get('vocabulary_id'):
                        pkg_tag_dicts.append(tag)
                    else:
                        original_tags[name] = tag
                        pkg_tag_dicts.append(tag)
                        pkg_tag_list.append(name)
    

        package_dict['tags'] = pkg_tag_dicts
        package_dict['allow_free_tags'] = True
        get_action("package_update")(context, package_dict)

    for _, item in duplicate_tags.items():
        get_action("tag_delete")(context, item)

    click.secho(u"Duplicate Tags Removed", fg=u"green")

        
                        
        


