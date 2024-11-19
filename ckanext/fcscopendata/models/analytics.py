import logging
from typing import Optional
import sqlalchemy

import ckan.model.meta as meta
from ckan import model
from datetime import datetime

log = logging.getLogger(__name__)

frontend_stats_table = sqlalchemy.Table(
    "frontend_stats",
    meta.metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),  # New primary key
    sqlalchemy.Column("resource_id", sqlalchemy.String(length=60), nullable=False, primary_key=True),
    sqlalchemy.Column("dataset_id", sqlalchemy.String(length=60), nullable=False),      
    sqlalchemy.Column("count", sqlalchemy.Integer),
    sqlalchemy.Column("language", sqlalchemy.String(length=2), nullable=False),  # AR or EN
    sqlalchemy.Column("dataset_title", sqlalchemy.String(length=60)),
     sqlalchemy.Column(
        "date_created",
        sqlalchemy.DateTime,
        nullable=False,
    ),
)

class Analytics(object):
    def __init__(
        self,
        resource_id,
        dataset_id,
        count,
        language,
        dataset_title,
        date_created=None,
    ) -> None:
        self.resource_id = resource_id
        self.dataset_id = dataset_id
        self.count = count
        self.language = language
        self.dataset_title = dataset_title
        self.date_created = date_created
    
    @classmethod
    def create(cls, analytics_data: 'Analytics'):
        try:
            # Add the new analytics entry
            meta.Session.add(analytics_data)
            meta.Session.commit()
            return analytics_data
        except Exception as e:
            log.error(f"Error creating analytics entry: {e}")
            meta.Session.rollback()
            raise

    @classmethod
    def get(cls, analytics_id: int):
        try:
            return meta.Session.query(Analytics).get(analytics_id)
        except Exception as e:
            log.error(f"Error getting analytics entry with ID '{analytics_id}': {e}")
            raise

    @classmethod
    def delete(cls, analytics_id: int):
        try:
            analytics_data = meta.Session.query(Analytics).get(analytics_id)
            if analytics_data:
                meta.Session.delete(analytics_data)
                meta.Session.commit()
            else:
                log.warning(f"Analytics entry with ID '{analytics_id}' not found for deletion.")
        except Exception as e:
            log.error(f"Error deleting analytics entry with ID '{analytics_id}': {e}")
            meta.Session.rollback()
            raise
    
    @classmethod
    def find_all(cls, pagination: dict, is_count=False, start_date=None, end_date=None):
        try:
            page = pagination.get("page", 1)
            limit = pagination.get("limit", None)
            # Query all data requests with pagination
            query = meta.Session.query(Analytics).order_by(Analytics.date_created.desc())
            if start_date is not None and start_date != '':
                query = query.filter(Analytics.date_created >= start_date)
            if end_date is not None and end_date != '':
                # TODO: certify that exact end_date is proper based on timezone difference. This may cause 'end_date minus 1 day issue on filter'
                query = query.filter(Analytics.date_created <= end_date)
            # Apply pagination
            if limit is not None:
                offset = (page - 1) * limit
                query = query.limit(limit)
            else:
                offset = (page - 1)
            query = query.offset(offset)
            if is_count:
                return query.count()
            return query.all()
        except Exception as e:
            log.error(f"Error finding all data requests: {e}")
            raise

# Map the Analytics class to the analytics_table
meta.mapper(Analytics, frontend_stats_table)