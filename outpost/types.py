from abc import ABC, abstractmethod
from typing import Callable, Iterable
from dataclasses import is_dataclass,fields
from enum import Enum

from .rules import AND, Rule, Require, NoRequirements

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


class OutpostMeta(type):

    @staticmethod
    def generate_model_proxy(model:type, fields:Iterable):

        #idk why Enum metaclass dont likes common dicts. _member_names field is needed for it, and there is nothing i can do
        class MemberDict(dict):
            _member_names = ()

        members = MemberDict()
 
        members.update(dict((field_, field_) for field_ in fields))
        members._member_names = [key for key in members.keys()]
        # return type(f"{model.__name__}FieldsProxy", (Enum,), members)
        return type(f"{model.__name__}", (Enum,), members)

    @staticmethod
    def acquire_model_from_superclasses(superclasses_, model:type = None):
        parent_model = None
        
        for superclass in superclasses_:
            if hasattr(superclass, '__model__'):
                if getattr(superclass, '__model__') is not None:
                    # store parent model
                    if parent_model is None:
                        parent_model = getattr(superclass, '__model__')
                    
                    # check that model is in hierarchy
                    if model is None:
                        model = getattr(superclass, '__model__')
                    elif not issubclass(model, getattr(superclass, '__model__')):
                        raise AbstractError(f'Model {model.__name__} is not in {parent_model.__name__} hierarchy.')
                    else:
                        model = getattr(superclass, '__model__')
        
        return model

    @staticmethod
    def inherit_requirements(superclasses_, own_rule: Rule):
        rules = [
            superclass.__requirement_rule__ for superclass in superclasses_ \
                if hasattr(superclass, '__requirement_rule__') and getattr(superclass, '__requirement_rule__') is not None
            ]
        
        if own_rule is not None:
            if isinstance(own_rule, Enum):
                rules.append(Require(own_rule))
            else:
                rules.append(own_rule)
        
        result = AND()

        for rule in rules:
            if isinstance(rule, AND):
                result.append_rules(*rule.rules)
            else:
                result.append_rules(rule)

        if len(result.rules) == 0:
            return None
        if len(result.rules) == 1:
            return result.rules[0]
        else:
            return result    

    @staticmethod
    def inherit_readonly(superclasses_, own_readonly):
        result = dict()
        for superclass in superclasses_:
            result.update(superclass.readonly_fields)

        result.update(own_readonly)
        
        return result

    @staticmethod
    def inherit_nested_validators(superclasses_, own_validators):
        result = dict()
        for superclass in superclasses_:
            result.update(superclass.validation_methods)

        result.update(own_validators)
        
        return result
            

    def __new__(class_, name_:str, superclasses_:list, dict_:dict, *, model:type = None):
        # just create abc classes
        if name_ in ('ABCOutpost', 'Outpost'):
            return super().__new__(class_, name_, superclasses_, dict_)

        new_dict = dict()
        new_dict.update(dict_)
        
        # semantic model inheritance
        model = class_.acquire_model_from_superclasses(superclasses_, model)
        if model is None:
            raise AbstractError(f'Validator class "{name_}" does not have model to validate.')

        
        # selecting basic type validator
        if is_dataclass(model):
            new_dict['__type_validator__'] = DataclassTypeValidator(model)
        # else:
            # dict_['__type_validator__'] = SQLAlchemyTypeValidator
        
        new_dict['__model__'] = model

        new_dict['__model_fields__'] = class_.generate_model_proxy(
            new_dict['__model__'], 
            new_dict['__type_validator__'].get_fieldlist()
        )
        
        result_class = super().__new__(class_, name_, superclasses_, new_dict)
        
        # associating validator with model
        # if hasattr(model, '__outpost_validators__'):
        #     model.__outpost_validators__.append(result_class)
        # else:
        #     model.__outpost_validators__ = list((result_class,))

        result_class.__requirement_rule__ = class_.inherit_requirements(
            superclasses_, 
            getattr(result_class, 'requirements')(result_class)
        )

        try:
            delattr(result_class, 'requirements')
        except AttributeError:
            ...

        result_class.__readonly_fields__ = class_.inherit_readonly(
            superclasses_, 
            getattr(result_class, 'readonly')(result_class)
        )

        try:
            delattr(result_class, 'readonly')
        except AttributeError:
            ...


        own_validators = dict()

        def store_validators(field:Enum):
            def decorator(method):
                own_validators[field] = method
                return method

            return decorator

        getattr(result_class, 'validators')(result_class, store_validators)

        result_class.__validation_methods__ = class_.inherit_nested_validators(superclasses_, own_validators)

        try:
            delattr(result_class, 'validators')
        except AttributeError:
            ...


        return result_class


class ABCOutpost(metaclass=OutpostMeta):
    __model__ = None
    __type_validator__ = None
    __model_fields__ = None
    __requirement_rule__ = None
    __readonly_fields__ = None
    __validation_methods__ = None

    @classproperty
    def model(class_):
        return class_.__model__

    @classproperty
    def validator(class_) -> ABCTypeValidator:
        return class_.__type_validator__

    @classproperty
    def fields(class_) -> Enum:
        return class_.__model_fields__

    @classproperty
    def requirement_rule(class_) -> Rule:
        if class_.__requirement_rule__ is None:
            return NoRequirements()
        else:
            return class_.__requirement_rule__

    @classproperty
    def readonly_fields(class_) -> dict:
        if class_.__readonly_fields__ is None:
            return dict()
        else:
            return class_.__readonly_fields__

    @classproperty
    def validation_methods(class_) -> dict:
        if class_.__validation_methods__ is None:
            return dict()
        else:
            return class_.__validation_methods__
    
    def requirements(self):
        return None

    def readonly(self):
        return {}

    def validators(self, fieldvalidator:Callable):
        return None

class Outpost(ABCOutpost):

    def __str__(self) -> str:
        return f''' {"Outpost Validator Class":-^55} \n'''\
        f''' {self.__class__.__qualname__:-^55} \n'''\
        f'''\tmapping model: {self.model}\n'''\
        f'''\trequirement rule: {self.requirement_rule.text_rule()}\n'''\
        f'''\tread only fields:\n''' + \
        '\n'.join(f'\t\t{field}: Raise = {to_raise}' for field, to_raise in self.readonly_fields.items()) + \
        f'''\n\tvalidation methods:\n''' + \
        '\n'.join(f'\t\t{field}: method = {method.__qualname__}' for field, method in self.validation_methods.items()) + \
        f'\n{"END":-^56}'
        
    ...