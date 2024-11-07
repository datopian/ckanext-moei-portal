import logging
from typing import Optional
import sqlalchemy

import ckan.model.meta as meta
from ckan import model
from datetime import datetime

log = logging.getLogger(__name__)

data_request = sqlalchemy.Table(
    "data_request",
    meta.metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column(
        "date_created",
        sqlalchemy.DateTime,
        nullable=False,
    ),
    sqlalchemy.Column("email", sqlalchemy.String(length=255), nullable=True),
    sqlalchemy.Column("name", sqlalchemy.String(length=255), nullable=True),
    sqlalchemy.Column("topic", sqlalchemy.String(length=255), nullable=False),
    sqlalchemy.Column("phone_number", sqlalchemy.String(length=255), nullable=True),
    sqlalchemy.Column(
        "message_content", sqlalchemy.Text, nullable=False
    ),
    sqlalchemy.Column("solved", sqlalchemy.Boolean, nullable=False, default=False)
)

class DataRequest(object):
    def __init__(
        self,
        email,
        topic,
        phone_number,
        message_content,
        name,
        date_created=None,
        solved=False,
    ) -> None:
        self.email = email
        self.date_created = date_created or datetime.now()
        self.topic = topic
        self.phone_number = phone_number
        self.message_content = message_content
        self.name = name
        self.solved = solved 

    @classmethod
    def create(cls, data_request):
        try:
            meta.Session.add(data_request)
            meta.Session.commit()
            return data_request
        except Exception as e:
            log.error(f"Error creating data request: {e}")
            meta.Session.rollback()
            raise

    @classmethod
    def get(cls, request_id):
        try:
            return meta.Session.query(DataRequest).get(request_id)
        except Exception as e:
            log.error(f"Error getting data request with ID '{request_id}': {e}")
            raise

    @classmethod
    def delete(cls, request_id):
        try:
            data_request = meta.Session.query(DataRequest).get(request_id)
            if data_request:
                meta.Session.delete(data_request)
                meta.Session.commit()
            else:
                log.warning(f"Data request with ID '{request_id}' not found for deletion.")
        except Exception as e:
            log.error(f"Error deleting data request with ID '{request_id}': {e}")
            meta.Session.rollback()
            raise
        
    @classmethod
    def solve(cls, request_id):
        try:
            data_request = meta.Session.query(DataRequest).get(request_id)
            if data_request:
                data_request.solved = True
                meta.Session.commit()
            else:
                log.warning(f"Data request with ID '{request_id}' not found to mark as solved.")
        except Exception as e:
            log.error(f"Error marking data request with ID '{request_id}' as solved: {e}")
            meta.Session.rollback()
            raise
    
    @classmethod
    def find_all(cls, pagination: dict, is_count=False, start_date=None, end_date=None, solved=None):
        try:
            page = pagination.get("page", 1)
            limit = pagination.get("limit", None)
            # Query all data requests with pagination
            query = meta.Session.query(DataRequest).order_by(DataRequest.date_created.desc())
            if start_date is not None and start_date != '':
                query = query.filter(DataRequest.date_created >= start_date)
            if end_date is not None and end_date != '':
                # TODO: certify that exact end_date is proper based on timezone difference. This may cause 'end_date minus 1 day issue on filter'
                query = query.filter(DataRequest.date_created <= end_date)
            if solved == False:
                query = query.filter(DataRequest.solved == False)
            if solved == True:
                query = query.filter(DataRequest.solved == True)
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
    

meta.mapper(DataRequest, data_request)
