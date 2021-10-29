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




class UserValidator(Outpost, model=User):
    def requirements(self):
        return self.fields.id
    ...

class PhoneValidator(Outpost, model=Phone):
    def requirements(self):
        return self.fields.number
    ...

class CreateUserValidator(UserValidator):
    
    # def requirements(self):
    #     return AND(
    #         self.fields.name,
    #         self.fields.phone
    #     )

    def readonly(self):
        return {
            self.fields.hash: True,
            self.fields.id: False
        }

    ...
        

print(CreateUserValidator())