from .types import Outpost
from dataclasses import dataclass
from .rules import AND, OR, NOT, Require

@dataclass
class Phone:
    number: int


@dataclass
class User:
    id: int
    name: str
    hash: str
    phone: Phone


class PhoneValidator(Outpost, model=Phone):
    def requirements(self):
        return self.fields.number
    ...


class UserValidator(Outpost, model=User):
    def requirements(self):
        return self.fields.id

    def validators(self, fieldvalidator):
        
        fieldvalidator(self.fields.phone)(PhoneValidator)

        @fieldvalidator(self.fields.id)
        def idvalidator(value):
            return value



    ...


class CreateUserValidator(UserValidator):
    
    def requirements(self):
        return AND(
            self.fields.name,
            self.fields.phone,
            OR(
                self.fields.id,
                self.fields.phone
            ),
            NOT(self.fields.hash)
        
        )

    def readonly(self):
        return {
            self.fields.hash: True,
            self.fields.id: False
        }

    def validators(self, fieldvalidator):
        @fieldvalidator(self.fields.name)
        def namevalidator(v):
            return v

    ...
        

print(CreateUserValidator())