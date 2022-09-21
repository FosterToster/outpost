from typing import *
from abc import ABC, abstractmethod
from dataclasses import MISSING, fields

from .utils import ModelField

class ABCTypeValidator(ABC):
    def __init__(self, model) -> None:
        self._model = model

    @property
    def model(self):
        return self._model

    @abstractmethod
    def _is_instance(self, value, type: type) -> bool:
        ...

    @abstractmethod
    def get_annotation(self, field:ModelField):
        ...



class TypingModuleValidator:

    STR_ALIASES = {
        Union: str(Union),
        Iterable : str(Iterable),
        Optional: str(Optional),
        Callable : str(Callable),
        Any : str(Any),
    }

    def _is_supported_alias(self, annotation : str):
        for str_alias in self.STR_ALIASES.values():
            if annotation.startswith(str_alias):
                return True
        return False

    def _is_typing_alias(self, annotation: str):
        str_aliases = self.STR_ALIASES.values()
        prefixes = [alias[:alias.find('.')] for alias in str_aliases]
        return annotation.startswith(tuple(prefixes))

    def _get_alias_method(self, annotation: str):
        if annotation.startswith(self.STR_ALIASES[Union]) or annotation.startswith(self.STR_ALIASES[Optional]):
            return self._is_union_instance
        elif annotation.startswith(self.STR_ALIASES[Iterable]):
            return self._is_iterable_instance
        elif annotation.startswith(self.STR_ALIASES[Callable]):
            return self._is_callable_instance
        elif annotation.startswith(self.STR_ALIASES[Any]):
            return self._is_any_instance

    def _is_callable_instance(self, value, _type: type):
        return callable(value)

    def _is_instance(self, value : Any, _type : type) -> bool:
        if self._is_typing_alias(str(_type)):
            if not self._is_supported_alias(str(_type)):
                raise Exception(f'Тип {_type} не поддерживается')
            method = self._get_alias_method(str(_type))
            if method is not None:
                return method(value, _type)
            else:
                raise Exception(f'Нет подходящего метода для типа {_type}')
        else: 
            return isinstance(value, _type)
    
    def _is_union_instance(self, value, _type : type):
        for item_annotation in _type.__args__:
            if self._is_instance(value, item_annotation):
                return True
        return False

    def _is_iterable_instance(self, value, _type : type):
        if isinstance(value, Iterable):
            try:
                # _type = _type.__args__[0]
                for actual_type in _type.__args__:
                    for item_value in value:
                        if self._is_instance(item_value, actual_type):
                            return True

                return False
            except IndexError:
                return True
        else:
            return False
    
    def _is_any_instance(self, value, _type : type):
        return True

class DataclassTypeValidator(TypingModuleValidator, ABCTypeValidator):
   
    def get_fieldlist(self):
        return tuple(field.name for field in fields(self.model))    

    def _is_instance(self, value: Any, _type: type) -> bool:
        if value is MISSING:
            return True
        else:
            return super()._is_instance(value, _type)

    def get_annotation(self, field: ModelField):
        for data_field in fields(self.model):
            if data_field.name == field.value:
                return data_field.type
        else:
            return Any

    def get_missing(self):
        return MISSING
