import click

from ckanext.fcscopendata.modal import (
    tag_extra_table,
    vocabulary_extra_table
)

def get_commands():
    return [fluent]

@click.group()
def fluent():
    pass

@fluent.command()
def initdb():
    """Adds extras fields to ckan tag and vocabulary.
    Usage:
        fluent initdb
        - Creates the necessary tables in the database
    """
    if not tag_extra_table.exists():
        tag_extra_table.create()
        click.secho(u"Tag extras DB tables created", fg=u"green")

    if not vocabulary_extra_table.exists():
        vocabulary_extra_table.create()
        click.secho(u"Vocabulary extras DB tables created", fg=u"green")
    
    click.secho(u"Tag and Vocabulary extra DB tables already created", fg=u"green")
