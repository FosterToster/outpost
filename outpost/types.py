from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Iterable
from dataclasses import is_dataclass, dataclass, fields
from enum import Enum

from .classproperty import classproperty


from .exceptions import AbstractError


class ABCTypeValidator(ABC):
    def __init__(self, model) -> None:
        self._model = model

    @property
    def model(self):
        return self._model

    @abstractmethod
    def get_fieldlist(self):
        ...


class DataclassTypeValidator(ABCTypeValidator):
    def get_fieldlist(self):
        return tuple(field.name for field in fields(self.model))    

class MemberDict(dict):
    _member_names = ()

class OutpostMeta(type):

    @staticmethod
    def generate_model_proxy(model:type, fields:Iterable):
        members = MemberDict()
        # members.update({'__module__': __name__, '__qualname__': f"{model.__name__}FieldsProxy"})
        members.update(dict((field_, field_) for field_ in fields))
        members._member_names = [key for key in members.keys()]
        return type(f"{model.__name__}FieldsProxy", (Enum,), members)

    def __new__(class_, name_:str, superclasses_:list, dict_:dict, *, model:type = None):
        new_dict = dict()
        new_dict.update(dict_)
        # just create abc classes
        if name_ in ('ABCOutpost', 'Outpost'):
            return super().__new__(class_, name_, superclasses_, new_dict)
        
        # searching for validation model in superclasses
        if model is None:
            for superclass in superclasses_:
                if hasattr(superclass, '__model__'):
                    if getattr(superclass, '__model__') is not None:
                        model = getattr(superclass, '__model__')
                        break
            else:
                raise AbstractError(f'Validator class "{name_}" does not have model to validate.')

        
        # selecting basic type validator
        if is_dataclass(model):
            new_dict['__type_validator__'] = DataclassTypeValidator(model)
        # else:
            # dict_['__type_validator__'] = SQLAlchemyTypeValidator
        
        new_dict['__model__'] = model

        new_dict['__model_proxy__'] = class_.generate_model_proxy(new_dict['__model__'], new_dict['__type_validator__'].get_fieldlist())

        
        result = super().__new__(class_, name_, superclasses_, new_dict)
        # associating validator with model
        if hasattr(model, '__outpost_validators__'):
            model.__outpost_validators__.append(result)
        else:
            model.__outpost_validators__ = list((result,))

        return result


class ABCOutpost(metaclass=OutpostMeta):
    __model__ = None
    __type_validator__ = None
    __model_proxy__ = None

    @classproperty
    def model(class_):
        return class_.__model__

    @classproperty
    def validator(class_):
        return class_.__type_validator__

    @classproperty
    def model_fields(class_):
        a = class_.__model_proxy__
        return a
    
    def nested_validators(self):
        return {}

class Outpost(ABCOutpost):

    

    def defaults(self):
        return self
        ...

    def readonly(self):
        return self
        ...

    @property
    def requirements(self):
        return self
        ...

    def independent(self):
        return self
        ...

    def map(self):
        return ''
