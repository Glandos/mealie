from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealie.core.root_logger import get_logger
from mealie.db.data_access_layer._access_model import AccessModel

C = TypeVar("C", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)
DAL = TypeVar("DAL", bound=AccessModel)
logger = get_logger()


class CrudHttpMixins(Generic[C, R, U], ABC):
    item: R
    session: Session

    @property
    @abstractmethod
    def dal(self) -> DAL:
        ...

    def populate_item(self, id: int) -> R:
        self.item = self.dal.get_one(id)
        return self.item

    def _create_one(self, data: C, exception_msg="generic-create-error") -> R:
        try:
            self.item = self.dal.create(data)
        except Exception as ex:
            logger.exception(ex)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"message": exception_msg, "exception": str(ex)})

        return self.item

    def _update_one(self, data: U, item_id: int = None) -> R:
        if not self.item:
            return

        target_id = item_id or self.item.id
        self.item = self.dal.update(target_id, data)

        return self.item

    def _patch_one(self, data: U, item_id: int) -> None:
        try:
            self.item = self.dal.patch(item_id, data.dict(exclude_unset=True, exclude_defaults=True))
        except IntegrityError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"message": "generic-patch-error"})

    def _delete_one(self, item_id: int = None) -> R:
        target_id = item_id or self.item.id
        logger.info(f"Deleting item with id {target_id}")

        try:
            self.item = self.dal.delete(target_id)
        except Exception as ex:
            logger.exception(ex)
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail={"message": "generic-delete-error", "exception": str(ex)}
            )

        return self.item