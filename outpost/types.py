from typing import Callable, Dict, Iterable, List
from dataclasses import fields
from typing import Any, Union

from .rules import AND, Rule, Require, NoRequirements
from .utils import ModelField


from .abc import GenericValidatorProvider, TOriginalModel, ABCOutpost, Validator, Combinator

from .exceptions import AbstractError, FieldRequirementException, UnexpectedError, ValidationError, ExcludeValue


class OutpostProvider(GenericValidatorProvider):
    
    def require(self, expression: Union[Rule, ModelField]):
        if issubclass(type(expression), Rule):
            new_rule = expression
        elif issubclass(type(expression), ModelField):
            new_rule = Require(expression)

        if isinstance(self.requirements, NoRequirements):
            self.__requirements__ = new_rule
        elif not isinstance(self.requirements, AND):
            self.__requirements__ = AND(self.requirements, new_rule)
        else:
            self.requirements.append_rules(new_rule)

    def validator(self, field: ModelField, validator: 'Outpost' = None, check_result_type: bool = True):
        if validator is not None:
            self.validators.append(Validator(field=field, validator=validator, check_result_type=check_result_type))
        else:
            def decorator(func):
                self.validators.append(Validator(field=field, method=func, check_result_type=check_result_type))
                return func

            return decorator
    
    def combine(self, *fields: ModelField):
        def decorator(func):
            self.combinators.append(Combinator(fields=fields, method = func))
            return func

        return decorator
        
    @staticmethod
    def __generate_model_proxy__(model: TOriginalModel):
        #idk why Enum metaclass dont likes common dicts. _member_names field is needed for it, and there is nothing i can do
        class MemberDict(dict):
            _member_names = ()

        members = MemberDict()
 
        members.update(dict((field_.name, field_.name) for field_ in fields(model)))
        members._member_names = [key for key in members.keys()]
        # return type(f"{model.__name__}FieldsProxy", (Enum,), members)
        return type(f"{model.__name__}", (ModelField,), members)

    def __init__(self, model: TOriginalModel):
        super().__init__(model)
        self.clear()

    def clear(self):
        self.__readonly__ = list()
        self.__defaults__ = dict()
        self.__validators__ = list()
        self.__combinators__ = list()
        self.__requirements__ = NoRequirements()

    def __str__(self):
        return f'<{self.__class__.__qualname__} object>\n'+\
            f'\treadonly: {[f"{x}" for x in self.readonly]}\n'+\
            f'\tdefaults: {[f"{x[0]}: {x[1]}" for x in self.defaults.items()]}\n'+\
            f'\tvalidators: {[f"{x}" for x in self.validators]}\n'+\
            f'\tcombinators: {[f"{x}" for x in self.combinators]}\n'+\
            f'\trequirements: {self.requirements.text_rule()}'

    @classmethod
    def from_model(class_, model:TOriginalModel) -> GenericValidatorProvider[TOriginalModel]:
        return class_(model)




# class ValidationContext:
#     def __init__(self, model:type, model_proxy: ModelField, type_validator: ABCTypeValidator, requirements: Rule, readonly: dict, validators:dict ) -> None:
#         self.model = model
#         self.fields = model_proxy
#         self.type_validator = type_validator
#         self.requirements = requirements
#         self.readonly = readonly
#         self.supervalidators = validators
#         self.default_dataset = {}
#         self.raw_dataset = None
#         self.enumerated_dataset = None
#         self.filtered_dataset = None
#         self.normalized_dataset = {}

#     def __enter__(self):
#         return self

#     def __exit__(self, *_):
#         ...
    
#     @property
#     def result_dataset(self):
#         return self.normalized_dataset
#         # return dict((key.value, value) for key,value in self.normalized_datset.items())

#     def check_requirements(self, passed_fields: Iterable = None):
#         if passed_fields:
#             filtered_dataset_keys = passed_fields
#         else:
#             filtered_dataset_keys = self.filtered_dataset.keys()
#         try:
#             self.requirements.resolve([key for key in filtered_dataset_keys])
#         except FieldRequirementException as e:
#             raise ValidationError(f'Requirements are not satisfied: {str(e)}')

#     def enumerate_fields(self, dataset:dict = None):
#         self.enumerated_dataset = dict()
#         raw_dataset = dataset or self.raw_dataset
        
#         for field in self.fields:
#             if field in self.default_dataset.keys(): 
#                 self.enumerated_dataset[field] = self.default_dataset[field]
#             elif field.value in self.default_dataset.keys():
#                 self.enumerated_dataset[field] = self.default_dataset[field.value]

#             if field.value in raw_dataset.keys():
#                 self.enumerated_dataset[field] = raw_dataset[field.value]
#             elif field in raw_dataset.keys():
#                 self.enumerated_dataset[field] = raw_dataset[field]

#             # try:
#             #     if not (field in self.enumerated_dataset.keys()):
#             #         self.enumerated_dataset[field] = self.type_validator.get_missing()
#             # except ExcludeValue:
#             #     continue

#         return self



#     def filter_fields(self, dataset: dict = None):
#         enumerated_dataset = dataset or self.enumerated_dataset
        
#         self.filtered_dataset = dict()

#         for field in self.fields:
#             value = enumerated_dataset.get(field) # getting value from dataset by field enum value
#             if value is None:
#                 continue
#             else:
#                 try:
#                     raise_readonly = self.readonly[field] # getting readonly rule for field
#                 except KeyError:
#                     self.filtered_dataset[field] = value
#                 else:
#                     if raise_readonly:
#                         raise ValidationError(f'Field {field} is read-only')
        
#         return self

#     def defaults(self, default_datset:dict):
#         self.default_dataset = default_datset
#         return self

#     def supervalidate(self, supervalidator, value):
#         if type(supervalidator) == type(ABCOutpost):
#             if issubclass(supervalidator, ABCOutpost):
#                 return supervalidator.validate(value).map()
#             else:
#                 raise AbstractError(f'Supervalidator is not callable or subclass of ABCOutpost')
#         elif callable(supervalidator):
#             return supervalidator(value)
#         else:
#             raise AbstractError(f'Supervalidator is not callable or subclass of ABCOutpost')

#     def validate_field(self, field: ModelField, value:Any):
#         annotation = self.type_validator.get_annotation(field)

#         if self.type_validator._is_instance(value, annotation):
#             return value
#         else:
#             raise ValidationError(f'invalid typecast: type {type(value)} is not satisfying for {annotation}')

#     def normalize_field(self, field:ModelField, value):
#         supervalidator = self.supervalidators.get(field)
#         if supervalidator:
#             return self.validate_field(field, self.supervalidate(supervalidator, value))
#         else:
#             return self.validate_field(field, value)

#     def normalize_dataset(self, dataset:dict = None):

#         if dataset:
#             filtered_datset = dataset
#         else:
#             filtered_datset = self.filtered_dataset

#         if len(filtered_datset) == 0:
#             ValidationError('Filtered dataset is empty. Nothing to validate')

#         for field, value in filtered_datset.items():
#             try:
#                 self.normalized_dataset[field] = self.normalize_field(field, value)
#             except ValidationError as e:
#                 raise ValidationError(f'{field} -> {str(e)}')
#             except UnexpectedError as e:
#                 raise UnexpectedError(f'{field} -> {str(e)}')
#             except Exception as e:
#                 raise UnexpectedError(f'{field}: Unexpected error with value {value}: {str(e)}') from e
            
#         return self
    
#     def validate(self, dataset: dict):
#         self.raw_dataset = dataset
        
#         self.enumerate_fields()
#         self.filter_fields()
#         self.check_requirements()
#         self.normalize_dataset()
        
#         return self
#         ...

#     def dataset(self):
#         return self.result_dataset

#     def map(self) -> Any:
#         result = dict()

#         for field in self.fields:
#             try:
#                 if field in self.result_dataset.keys():
#                     result[field.value] = self.result_dataset[field]
#                 else:
#                     result[field.value] = self.type_validator.get_missing()
#             except ExcludeValue:
#                 continue
#         return self.model(**result)


class Outpost(ABCOutpost):
    ...
    # @classmethod
    # def context(class_) -> ValidationContext:
    #     return ValidationContext(class_.model, class_.fields, \
    #         class_.validator, class_.requirement_rule, \
    #         class_.readonly_fields, class_.supervalidators)\

    # @classmethod
    # def validate(class_, dataset: dict) -> ValidationContext:
    #     return class_.context().validate(dataset=dataset)

    # @classmethod
    # def validation_results(class_, dataset: dict):
    #     return class_.validate(dataset).dataset()

    # @classmethod
    # def map(class_, dataset:dict) -> Any:
    #     return class_.validate(dataset).map()


    # def __new__(class_, *, model:type = None) -> ValidationContext:
    #     if class_ != Outpost:
    #         raise AbstractError(f'{class_.__name__} is for static usage only')

    #     validator = OutpostMeta.choose_validator(model)
    #     return ValidationContext(model, OutpostMeta.generate_model_proxy(model, validator.get_fieldlist()), validator, NoRequirements(), {}, {})


    # def __str__(self) -> str:
    #     return f''' {"Outpost Validator Class":-^55} \n'''\
    #     f''' {self.__class__.__qualname__:-^55} \n'''\
    #     f'''\tmapping model: {self.model}\n'''\
    #     f'''\trequirement rule: {self.requirement_rule.text_rule()}\n'''\
    #     f'''\tread only fields:\n''' + \
    #     '\n'.join(f'\t\t{field}: Raise = {to_raise}' for field, to_raise in self.readonly_fields.items()) + \
    #     f'''\n\tvalidation methods:\n''' + \
    #     '\n'.join(f'\t\t{field}: method = {method.__qualname__}' for field, method in self.supervalidators.items()) + \
    #     f'\n{"END":-^56}'
        
    # ...