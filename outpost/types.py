from abc import ABC, abstractmethod
from typing import Callable, Iterable
from dataclasses import dataclass, is_dataclass,fields
from enum import EnumMeta, Enum
from typing import Any, Union

from .type_validators import DataclassTypeValidator, ABCTypeValidator

from .utils import ModelField
from .rules import AND, Rule, Require, NoRequirements

from .classproperty import classproperty


from .exceptions import AbstractError, FieldRequirementException, UnexpectedError, ValidationError


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
        return type(f"{model.__name__}", (ModelField,), members)

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
            if isinstance(own_rule, ModelField):
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
    def inherit_supervalidators(superclasses_, own_validators):
        result = dict()
        for superclass in superclasses_:
            result.update(superclass.supervalidators)

        result.update(own_validators)
        
        return result

    @staticmethod
    def choose_validator(model:type):
        if is_dataclass(model):
            return DataclassTypeValidator(model)
        else:
            return None # for future
            
    def __new__(class_, name_:str, superclasses_:list, dict_:dict, *, model:type = None):
        # just create abc classes
        if name_ in ('ABCOutpost', 'Outpost'):
            return super().__new__(class_, name_, superclasses_, dict_)

        new_dict = dict()
        new_dict.update(dict_)
        
        # semantic model inheritance
        
        # selecting basic type validator
        # if is_dataclass(model):
            #  = DataclassTypeValidator(model)
       
        
        result_class = super().__new__(class_, name_, superclasses_, new_dict)

        result_class.__type_validator__ = class_.choose_validator(model)

        result_class.__model__ = class_.acquire_model_from_superclasses(superclasses_, model)
        if result_class.__model__ is None:
            raise AbstractError(f'Validator class "{name_}" does not have model to validate.')
        
        if result_class.__model_fields__ is None:
            result_class.__model_fields__ = class_.generate_model_proxy(
                result_class.__model__, 
                result_class.__type_validator__.get_fieldlist()
            )
        
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

        def store_supervalidators(field:ModelField):
            def decorator(method):
                own_validators[field] = method
                return method

            return decorator

        getattr(result_class, 'validators')(result_class, store_supervalidators)

        result_class.__supervalidators__ = class_.inherit_supervalidators(superclasses_, own_validators)

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
    __supervalidators__ = None

    @classproperty
    def model(class_):
        if class_.__model__ is None:
            raise AbstractError(f'Model is not defined')
        
        return class_.__model__

    @classproperty
    def validator(class_) -> ABCTypeValidator:
        if class_.__type_validator__ is None:
            return OutpostMeta.choose_validator(class_.model)

        return class_.__type_validator__

    @classproperty
    def fields(class_) -> ModelField:
        if class_.__model_fields__ is None:
            return OutpostMeta.generate_model_proxy(class_.model, class_.validator.get_fieldlist())

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
    def supervalidators(class_) -> dict:
        if class_.__supervalidators__ is None:
            return dict()
        else:
            return class_.__supervalidators__
    
    def requirements(self):
        return None

    def readonly(self):
        return {}

    def validators(self, supervalidator: Callable[[ModelField], Callable[[Any], Any]]):
        return None

class ValidationContext:
    def __init__(self, model:type, model_proxy: ModelField, type_validator: ABCTypeValidator, requirements: Rule, readonly: dict, validators:dict ) -> None:
        self.model = model
        self.fields = model_proxy
        self.type_validator = type_validator
        self.requirements = requirements
        self.readonly = readonly
        self.supervalidators = validators
        self.default_dataset = {}
        self.raw_dataset = None
        self.enumerated_dataset = None
        self.filtered_dataset = None
        self.normalized_datset = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        ...
    
    @property
    def result_dataset(self):
        return dict((key.value, value) for key,value in self.normalized_datset.items())

    def check_requirements(self, passed_fields: Iterable = None):
        if passed_fields:
            filtered_dataset_keys = passed_fields
        else:
            filtered_dataset_keys = self.filtered_dataset.keys()
        try:
            self.requirements.resolve([key for key in filtered_dataset_keys])
        except FieldRequirementException as e:
            raise ValidationError(f'Requirements are not satisfied: {str(e)}')

    def enumerate_fields(self, dataset:dict = None):
        self.enumerated_dataset = dict()
        raw_dataset = dataset or self.raw_dataset
        
        for field in self.fields:
            self.enumerated_dataset[field] = self.default_dataset.get(field) or self.default_dataset.get(field.value)
            self.enumerated_dataset[field] = raw_dataset.get(field.value) or raw_dataset.get(field) or self.enumerated_dataset[field]

        return self



    def filter_fields(self, dataset: dict = None):
        enumerated_dataset = dataset or self.enumerated_dataset
        
        self.filtered_dataset = dict()

        for field in self.fields:
            value = enumerated_dataset.get(field) # getting value from dataset by field enum value
            if value is None:
                continue
            else:
                try:
                    raise_readonly = self.readonly[field] # getting readonly rule for field
                except KeyError:
                    self.filtered_dataset[field] = value
                else:
                    if raise_readonly:
                        raise ValidationError(f'Field {field} is read-only')
        
        return self

    def defaults(self, default_datset:dict):
        self.default_dataset = default_datset
        return self

    def supervalidate(self, supervalidator, value):
        if type(supervalidator) == type(ABCOutpost):
            if issubclass(supervalidator, ABCOutpost):
                return supervalidator.validate(value).map()
            else:
                raise AbstractError(f'Supervalidator is not callable or subclass of ABCOutpost')
        elif callable(supervalidator):
            return supervalidator(value)
        else:
            raise AbstractError(f'Supervalidator is not callable or subclass of ABCOutpost')

    def validate_field(self, field: ModelField, value:Any):
        annotation = self.type_validator.get_annotation(field)

        if self.type_validator._is_instance(value, annotation):
            return value
        else:
            raise ValidationError(f'invalid typecast: type {type(value)} is not satisfying for {annotation}')

    def normalize_field(self, field:ModelField, value):
        supervalidator = self.supervalidators.get(field)
        if supervalidator:
            return self.validate_field(field, self.supervalidate(supervalidator, value))
        else:
            return self.validate_field(field, value)

    def normalize_dataset(self, dataset:dict = None):

        if dataset:
            filtered_datset = dataset
        else:
            filtered_datset = self.filtered_dataset

        if len(filtered_datset) == 0:
            ValidationError('Filtered dataset is empty. Nothing to validate')

        for field, value in filtered_datset.items():
            try:
                self.normalized_datset[field] = self.normalize_field(field, value)
            except ValidationError as e:
                raise ValidationError(f'{field} -> {str(e)}')
            except UnexpectedError as e:
                raise UnexpectedError(f'{field} -> {str(e)}')
            except Exception as e:
                raise UnexpectedError(f'{field}: Unexpected error with value {value}: {str(e)}') from e
            
        return self
    
    def validate(self, dataset: dict):
        self.raw_dataset = dataset
        
        self.enumerate_fields()
        self.filter_fields()
        self.check_requirements()
        self.normalize_dataset()
        
        return self
        ...

    def dataset(self):
        return self.result_dataset

    def map(self) -> Any:
        return self.model(**self.dataset())


class Outpost(ABCOutpost):

    @classmethod
    def context(class_) -> ValidationContext:
        return ValidationContext(class_.model, class_.fields, \
            class_.validator, class_.requirement_rule, \
            class_.readonly_fields, class_.supervalidators)\

    @classmethod
    def validate(class_, dataset: dict) -> ValidationContext:
        return class_.context().validate(dataset=dataset)

    @classmethod
    def validation_results(class_, dataset: dict):
        return class_.validate(dataset).dataset()

    @classmethod
    def map(class_, dataset:dict) -> Any:
        return class_.validate(dataset).map()


    def __new__(class_, *, model:type = None) -> ValidationContext:
        if class_ != Outpost:
            raise AbstractError(f'{class_.__name__} is for static usage only')

        validator = OutpostMeta.choose_validator(model)
        return ValidationContext(model, OutpostMeta.generate_model_proxy(model, validator.get_fieldlist()), validator, NoRequirements(), {}, {})


    def __str__(self) -> str:
        return f''' {"Outpost Validator Class":-^55} \n'''\
        f''' {self.__class__.__qualname__:-^55} \n'''\
        f'''\tmapping model: {self.model}\n'''\
        f'''\trequirement rule: {self.requirement_rule.text_rule()}\n'''\
        f'''\tread only fields:\n''' + \
        '\n'.join(f'\t\t{field}: Raise = {to_raise}' for field, to_raise in self.readonly_fields.items()) + \
        f'''\n\tvalidation methods:\n''' + \
        '\n'.join(f'\t\t{field}: method = {method.__qualname__}' for field, method in self.supervalidators.items()) + \
        f'\n{"END":-^56}'
        
    ...

