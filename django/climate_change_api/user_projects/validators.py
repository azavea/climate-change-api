import json

from jsonschema import validate, ValidationError as JSValidationError
from rest_framework.validators import ValidationError as DRFValidationError


with open('user_projects/projectschema.json', 'r') as f:
    schema = json.load(f)


def validate_user_project(data):
    try:
        validate(data, schema)
    except JSValidationError as e:
        raise DRFValidationError(e.message)
