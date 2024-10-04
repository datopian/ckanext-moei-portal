from .azure_user_id import azure_users_ids
from .analytic_job_models import analytic_job_models
from .panel import panel
from .floor_lock import floor_lock
from .materialized_panel_statistics import _setup_panel_statistics
import logging

log = logging.getLogger(__name__)

# TODO: make it create the DataRequest table on setup
def setup():
    """
    Create Azure Users IDs in the database.
    """
    if not azure_users_ids.exists():
        azure_users_ids.create(checkfirst=True)
        log.info('Table created for Azure Users IDs')
    else:
        log.info('Azure Users IDs table already exists')

    """
    Create Analytic Job Models table in the database.
    """
    if not analytic_job_models.exists():
        analytic_job_models.create(checkfirst=True)
        log.info('Table created for the Analytic Job Models')
    else:
        log.info('Analytic Job Models table already exists')

    """
    Create panel table in the database
    """
    if not panel.exists():
        panel.create(checkfirst=True)
        log.info("Table created for panels")
    else:
        log.info("Panels table already exists")

    """
    Create floor lock table in the database
    """
    if not floor_lock.exists():
        floor_lock.create(checkfirst=True)
        log.info("Table created for panel locks")
    else:
        log.info("Panels lock table already exists")

    """
    Create panel statistics materialized view
    """
    _setup_panel_statistics()

    """
    Update activity table
    """
    from ckan.model import meta
    session = meta.Session
    try:
        session.execute("""ALTER TABLE "activity"
    ADD COLUMN permission_labels TEXT[];""")
        session.commit()
        log.info("Created activity column")
    except:
        log.info("Activity column already exists")
        session.rollback()
