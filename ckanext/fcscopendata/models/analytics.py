import logging
from typing import Optional
import sqlalchemy

import ckan.model.meta as meta
from ckan import model
from datetime import datetime

log = logging.getLogger(__name__)

analytics_table = sqlalchemy.Table(
    "frontend_stats",
    meta.metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),  # New primary key
    sqlalchemy.Column("resource_id", sqlalchemy.String(length=60), nullable=False),
    sqlalchemy.Column("resource_created", sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column("resource_updated", sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column("dataset_rating", sqlalchemy.Float, nullable=True),
    sqlalchemy.Column("dataset_title", sqlalchemy.String(length=255), nullable=False),
    sqlalchemy.Column("resource_title", sqlalchemy.String(length=255), nullable=False),
    sqlalchemy.Column("language", sqlalchemy.String(length=2), nullable=False),
)

class Analytics(object):
    def __init__(
        self,
        resource_id: str,
        resource_created: datetime,
        resource_updated: datetime,
        dataset_rating: float,
        dataset_title: str,
        resource_title: str,
        language: str,
    ) -> None:
        self.resource_id = resource_id
        self.resource_created = resource_created
        self.resource_updated = resource_updated
        self.dataset_rating = dataset_rating
        self.dataset_title = dataset_title
        self.resource_title = resource_title
        self.language = language

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
    def find_all(cls, pagination: dict):
        try:
            page = int(pagination.get("page", 1))
            limit = int(pagination.get("limit", 20))
            offset = (page - 1) * limit
            
            # Query all analytics entries with pagination
            query = meta.Session.query(Analytics).order_by(Analytics.resource_created.desc())
            
            # Apply pagination
            analytics_entries = query.offset(offset).limit(limit).all()
            
            return analytics_entries
        except Exception as e:
            log.error(f"Error finding all analytics entries: {e}")
            raise

# Map the Analytics class to the analytics_table
meta.mapper(Analytics, analytics_table)