from outpost import Outpost, OutpostModel
from dataclasses import dataclass

# models
@dataclass
class Phone:
    id: int
    number: str


@dataclass
class User:
    id: int
    name: str
    pwd: str
    contact: Phone
    pwd_hash: str


# validators definitions

# basic validator for Phone
class PhoneValidator(Outpost):

    # defining Outpost configuration class
    # used to define validating model and provide configuration methods
    class model(OutpostModel, Phone):
        ...

    # required field definition
    model.requirement = model.guid or model.visit and model.ident

    # supervalidate and normalize some field
    # decorator accepts a model field to validate, optional "validator" (described further) and optional kwarg "check_result_type:bool=True" - set False to avoid type checking for method result. True by default 
    # method "value" arg is an unsave raw value from dataset
    # method result must be a normalized value satisfying with the given annotation (or not :3)
    # method raises ValidationError in case of invalid value for field
    # method can be multiple decorated to be used for several fields
    @model.validator(model.id, check_result_type=False)
    @model.validator(model.number)
    def validate_id(value:Any) -> int:
        try:
            return int(value)
        except ValueError as e:
            raise ValidationError(str(e))


# basic validator for User
class UserValidator(Outpost):
    class model(OutpostModel, User):
        ...

    # simplified model.validator usage. 
    # Just to mark that "contact" field should be validated with PhoneValidator
    model.validator(model.contact, PhoneValidator)


    # validate dependent fields
    # uses to validate values combination
    # decorator accepts any amount of model fields which values will be passed to validation method in same order
    # method will be called when all values alredy been validated and normalized, only if all fields of combination have a values
    # must raise ValidationError if invalid value combination are found
    # return value will be ignored
    @model.combine(model.pwd, model.name, model.pwd_hash)
    def pwd_hash(pwd, name, pwd_hash):
        if pwd_hash != (hash(pwd)+hash(name)):
            raise ValidationError('Wrong username or password')
    

# User validator for "Create" case
class CreateUserValidator(UserValidator):

    # explicid inheritance of model from superclass
    model = UserValidator.model

    # defining a defaul values for fields for this validation case
    # if some field have a default value, requirement rule for this field is always satisfied
    # default values will be validated with external dataset values to prevent unexpected behaviour
    model.defaults({
        model.name: "John Doe"
    })

    # defining read-only fields
    # kwarg to_raise:bool = False: if True, ValidationError will be raised in case of readonly field was passed in the dataset. False by default.
    model.readonly(model.id, model.pwd_hash, to_raise=True)

    # updating requirement rule
    model.requirement(model.name and model.pwd and model.contact)


# usage

# dataset
dataset = {
    'name': 'User 1',
    'pwd': 'fafasges',
    'contact': {
        'id': 1,
        'number': "+79996465214"
    }

}

# case 1: basic validator usage
try:
    # just validate given dataset and map validation result to a model
    a = CreateUserValidator.validate(dataset).map()
except ValidationError as e:
    print('case #1:', e)
else:
    print('case #1:', a)


# case 2: basic rules overriding usage
try:
    # override defaults for defined validation rules, validate given dataset and map it to a model
    a = CreateUserValidator.context().defaults({CreateUserValidator.model.pwd: 'qwerqwer'}).validate(dataset).map()
except ValidationError as e:
    print('case #2:', e)
else:
    print('case #2:', a)

# case 3: advanced validation context usage
try:
    with CreateUserValidator.context() as context:
        # disable or overwrite all requirements in case of something
        if True:
            context.requirements = None

        # appending defaults
        context.defaults({
            **context.default_values,
            CreateUserValidator.model.id: hash(__name__)
        })

        # validating
        context.validate(dataset)

        # getting validated dataset
        a = context.map()

        # updating result model with some complex value
        a.pwd_hash = hash(a.pwd) + hash(a.name)

except ValidationError as e:
    print('case #3:', e)
else:
    print('case #3:', a)