from sqlalchemy.inspection import inspect
from sqlalchemy import Column
from sqlalchemy.orm import RelationshipProperty
from typing import Iterable, Any

from .utils import ModelField
from .abc import IAnnotationGenerator, IFieldGenerator, TOriginalModel


class AlchemyFieldGenerator(IFieldGenerator):
    def all_fields(self) -> Iterable[str]:
        mapper = inspect(self.model)
        return (*[x.name for x in mapper.columns] ,*[x._dependency_processor.key for x in mapper.relationships])

class AlchemyAnnotationGenerator(IAnnotationGenerator):
    def __init__(self, model: TOriginalModel) -> None:
        super().__init__(model)
        self.mapper = inspect(model)
        self.fields_dict = dict()
        self.fields_dict.update(
            dict((col.name, col) for col in self.mapper.columns )
        )
        self.fields_dict.update(
            dict((rel._dependency_processor.key, rel) for rel in self.mapper.relationships )
        )


    def get_annotation(self, field: ModelField) -> type:

        field = self.fields_dict[field.name]
        
        if isinstance(field, Column):
            print(field.type)
            print(f'column: {field}')
        elif isinstance(field, RelationshipProperty):
            ...
            # print(f'relation: {field}')
        else:
            ...
            # print(f'unknown: {field}')
        return str