from .data_request import data_request
import logging

log = logging.getLogger(__name__)

def setup():
    """
    Create Data Request table.
    """
    if not data_request.exists():
        data_request.create(checkfirst=True)
        log.info('Table created for Data Requests')
    else:
        log.info('Data Requests table already exists')