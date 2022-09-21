from typing import Iterable, Union
from abc import ABC, abstractmethod

from .exceptions import FieldRequirementException



# class Enum(Enum):
#     ...

# basic rule
class Rule(ABC):
    @abstractmethod
    def resolve(self, passed_fields: Iterable[str]):
        ...

    @abstractmethod
    def text_rule(self):
        ...

    def __or__(self, other):
        if isinstance(self, OR):
            return OR(*self.rules, other)
        else:
            return OR(self, other)

    def __and__(self, other):
        if isinstance(self, AND):
            return AND(*self.rules, other)
        else:
            return AND(self, other)
    ...

class NoRequirements(Rule):
    def resolve(self, _):
        ...

    def text_rule(self):
        return ''


class Require(Rule):
    def __init__(self, field:'ModelField') -> None:
        if not isinstance(field, ModelField):
            raise FieldRequirementException(f'Rule "{field}" is not model field')

        self._field = field

    @property
    def field(self):
        return self._field

    def resolve(self, passed_fields: Iterable[str]):
        if not (self.field in passed_fields):
            raise FieldRequirementException(f"Field {self.text_rule()} required")

    def text_rule(self):
        return str(self.field)


class _RequireMany(Rule):
    
    def __init__(self, *rules:Union['ModelField', Rule]) -> None:
        self._rules = list()
        self.append_rules(*rules)
        

    def append_rules(self, *rules:Union['ModelField', Rule]):
        for rule in rules:
            if isinstance(rule, ModelField):
                self._rules.append(Require(rule))
            elif isinstance(rule, Rule):
                self._rules.append(rule)
            else:
                raise FieldRequirementException(f'Rule {rule} is not Requirement')
        

    @property
    def rules(self) -> Iterable[Rule]:
        return self._rules


class OR(_RequireMany):
    def resolve(self, passed_fields: Iterable[str]):
        for rule in self.rules:
            try:
                rule.resolve(passed_fields)
            except FieldRequirementException as e:
                continue
            else:
                return None
        else:
            raise FieldRequirementException(f'Fields requirement rule: {self.text_rule()}')

    def text_rule(self):
        return '(' + ' OR '.join(rule.text_rule() for rule in self.rules) + ')'

class AND(_RequireMany):
    def resolve(self, passed_fields: Iterable[str]):
        for rule in self.rules:
            try:
                rule.resolve(passed_fields)
            except FieldRequirementException as e:
                raise FieldRequirementException(f'Fields requirement rule: {self.text_rule()}')
            else:
                continue

    def text_rule(self):
        return '(' + ' AND '.join(rule.text_rule() for rule in self.rules) + ')'


class NOT(Rule):
    def __init__(self, rule: Union['ModelField', Rule]) -> None:
        if isinstance(rule, ModelField):
            self._rule = Require(rule)
        elif isinstance(rule, Rule):
            self._rule = rule
        else:
            raise FieldRequirementException(f'Rule {rule} is not Requirement')

    @property
    def rule(self):
        return self._rule

    def resolve(self, passed_fields: Iterable[str]):
        try:
            self.rule.resolve(passed_fields)
        except FieldRequirementException:
            pass
        else:
            raise FieldRequirementException(f"Fields requirement rule: {self.text_rule()}")

    def text_rule(self):
        return f'NOT {self.rule.text_rule()}'
            

from .utils import ModelField

                    
        
    
