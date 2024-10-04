import logging
from typing import Optional
import sqlalchemy

import ckan.model.meta as meta
from ckan import model
from datetime import datetime

log = logging.getLogger(__name__)

# TODO: tweak this table so that it reflects a data_request model
# https://docs.sqlalchemy.org/en/20/core/metadata.html
floor_lock = sqlalchemy.Table(
    "data_request",
    meta.metadata,
    sqlalchemy.Column("id", sqlalchemy.types.UnicodeText,
                      primary_key=True),
    sqlalchemy.Column("date", sqlalchemy.types.TIMESTAMP,
                      server_default=sqlalchemy.text("now() + interval '60 seconds'")),
    sqlalchemy.Column("email", sqlalchemy.types.UnicodeText)
)


class FloorLock(object):
    def __init__(self, floor_id: str, expiration, user_name: str) -> None:
        self.floor_id = floor_id
        self.expiration = expiration
        self.user_name = user_name

    @classmethod
    def get(cls, floor_id: str):
        try:
            floor = (
                meta.Session.query(FloorLock)
                .filter(FloorLock.floor_id == floor_id)
                .one()
            )
            return floor
        except Exception as e:
            log.error(e)

    @classmethod
    def create(
        cls,
        floor_id: str,
        expiration,
        user_name: str
    ) -> Optional[dict]:
        try:
            floor = FloorLock(floor_id)
            meta.Session.add(floor)
            meta.Session.commit()

            return floor

        except Exception as e:
            log.error(e)
            meta.Session.rollback()
            raise

    @classmethod
    def delete(cls, floor_id: str) -> None:
        try:
            if floor_id is not None:
                floor = meta.Session.query(FloorLock).filter(
                    FloorLock.floor_id == floor_id
                ).one()
                meta.Session.delete(floor)
                meta.Session.commit()
                return floor
            else:
                floors = meta.Session.query(FloorLock).filter(
                    FloorLock.floor_id == floor_id
                ).all()
                for floor in floors:
                    meta.Session.delete(floor)
                meta.Session.commit()
                return floors

        except Exception as e:
            log.error(e)
            meta.Session.rollback()

    @classmethod
    def delete_expired(cls):
        try:
            floor_locks = meta.Session.query(FloorLock).filter(
                FloorLock.expiration < datetime.now()
            ).all()
            for floor_lock in floor_locks:
                meta.Session.delete(floor_lock)
            meta.Session.commit()
            return floor_locks

        except Exception as e:
            log.error(e)
            meta.Session.rollback()


meta.mapper(FloorLock, floor_lock)
