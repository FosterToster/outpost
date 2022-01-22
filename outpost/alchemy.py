from datetime import date, datetime, time
from sqlalchemy.inspection import inspect
from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import String, Integer, Boolean, Float, Enum, DateTime, Date, Time
from sqlalchemy.orm import RelationshipProperty
from typing import Iterable, Any, Optional, Union, _GenericAlias
from collections import OrderedDict

from .utils import ModelField
from .abc import IAnnotationGenerator, IFieldGenerator, TOriginalModel


class AlchemyFieldGenerator(IFieldGenerator):
    def all_fields(self) -> Iterable[str]:
        mapper = inspect(self.model)
        return (*[x.name for x in mapper.columns] ,*[x._dependency_processor.key for x in mapper.relationships])


class AlchemyAnnotationGenerator(IAnnotationGenerator):
    
    __type_aliases__ = OrderedDict([
        (Enum, '_enums_argument'),
        (String, str),
        (Integer, int),
        (Boolean, bool),
        (Float, float),
        (DateTime, datetime),
        (Date, date),
        (Time, time),
    ])


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
        self.__type_aliases__ = OrderedDict(**self.__type_aliases__)

    @property
    def type_aliases(self) -> OrderedDict:
        return self.__type_aliases__

    @classmethod
    def append_typealias(class_, type_:type, typing_alias: type):
        class_.__type_aliases__[type_] = typing_alias

    @staticmethod
    def resolve_supscription(obj: Any, field: str):
        attrs = field.split('.', maxsplit=1)
        subobj = getattr(obj, attrs[0])
        if len(attrs) > 1:
            return AlchemyAnnotationGenerator.resolve_supscription(subobj, attrs[1])
        else:
            return subobj

    @staticmethod
    def resolve_iter(alias: Any):
        if hasattr(alias, '__iter__'):
            if len(alias) > 1:
                return _GenericAlias(Union, tuple(alias))
            else:
                return alias[0]
        else:
            return alias

    def find_column_alias(self, field: Column):
        for type_, alias in self.__type_aliases__.items():
            if isinstance(field.type, type_):
                if type(alias) == str:
                    alias = self.resolve_iter(self.resolve_supscription(field.type, alias))
                    
                if (not field.nullable) or field.primary_key:
                    return alias
                else:
                    return Optional[alias]
        else:
            return Any

    def get_annotation(self, field: ModelField) -> type:

        field = self.fields_dict[field.name]
        
        if isinstance(field, Column):
            return self.find_column_alias(field)
        elif isinstance(field, RelationshipProperty):
            type_ = field.entity._identity_class
            if field.uselist:
                return Iterable[type_]
            else:
                return type_
        else:
            return Any
        return str