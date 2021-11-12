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

    def validators(self, supervalidator):
        
        supervalidator(self.fields.phone)(PhoneValidator)

        @supervalidator(self.fields.id)
        def idvalidator(value):
            return value



    ...


class CreateUserValidator(UserValidator):
    
    def requirements(self):
        return self.fields.hash

    # def readonly(self):
    #     return {
    #         self.fields.name: False
    #     }

    def validators(self, supervalidator):
        
        @supervalidator(self.fields.name)
        def namevalidator(v):
            return v

    ...
        
try:

    dataset = {
        'id': 1234, 
        'hash': "fafsfd", 
        # 'name': 'asdf'
    }

    print(CreateUserValidator.validate(dataset).dataset())
    print(CreateUserValidator.context().defaults({CreateUserValidator.fields.name: "Federico Felini", CreateUserValidator.fields.phone: {PhoneValidator.fields.number: 12341234123}}).validate(dataset).dataset())

    with CreateUserValidator.context() as context:
        context.defaults({CreateUserValidator.fields.name: "Federico Felini", CreateUserValidator.fields.phone: {PhoneValidator.fields.number: 12341234123}})
        context.validate(dataset)
        print(context.dataset())

except ValidationError as e:
    print(e.__class__.__name__, str(e))