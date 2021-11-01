from outpost.exceptions import ValidationError
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

# print(Outpost(model=User).validate({'some': 'dataset'}))

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
        return self.fields.hash

    def readonly(self):
        return {
            self.fields.name: False
        }

    def validators(self, fieldvalidator):
        @fieldvalidator(self.fields.name)
        def namevalidator(v):
            return v

    ...
        
try:
    print(CreateUserValidator.validate({'id': '1234', 'hash': "fafsfd", 'name': 'asdf'}))
except ValidationError as e:
    print(e.__class__.__name__, str(e))