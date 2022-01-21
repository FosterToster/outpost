from sqlalchemy.inspection import inspect
from typing import Iterable

from .abc import IAnnotationGenerator, IFieldGenerator


class AlchemyFieldGenerator(IFieldGenerator):
    def all_fields(self) -> Iterable[str]:
        mapper = inspect(self.model)
        return (*[x.name for x in mapper.columns] ,*[x._dependency_processor.key for x in mapper.relationships])

class AlchemyAnnotationGenerator(IAnnotationGenerator):
    ...