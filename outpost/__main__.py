from .types import Outpost
from dataclasses import dataclass
from .utils import validatable
from .rules import Require, AND, OR, NOT

@dataclass
class Phone:
    number: int


@dataclass
class User:
    id: int
    name: str
    hash: str
    phone: Phone




class UserValidator(Outpost, model=User):
    ...

class PhoneValidator(Outpost, model=Phone):
    ...

class SomeHarderValidator(UserValidator):
    
    def requirements(self):
        return OR(
            self.model_fields.id,
            AND(
                self.model_fields.hash,
                self.model_fields.phone,
                NOT(self.model_fields.id)
            )
            
        )
        

# SomeHarderValidator().requirements()
    # def nested_validators(self):
    #     return {
    #         self.model_fields.phone: Phone.validator
    #     }

class SomeElseValidator(UserValidator):
    def nested_validators(self):
        return {
            self.model_fields.id: UserValidator
        }

class SomeHigherValidator(SomeElseValidator):
    def nested_validators(self):
        return {
            self.model_fields.id: UserValidator
        }

SomeHarderValidator().requirements().resolve(('hash', 'phone'))
print(User.__outpost_validators__)