from sys import stdin
from dataclasses import dataclass, asdict
from types import NoneType
import typing


# base_request has field
# action - "send_package" or "update_package"

# # send_package has structure
# sender_id: signed integer
# recipient_id: signed integer
# package_id: signed integer
# package_type: 'marketing' or 'personal'
# timestamp: str-timestamp like - "2142-08-23T02:40:12-0700"

# # update_package has structure
# recipient_id signed integer

# and at least one of fields
# personal_package: bool
# marketing_package: bool

# Rules
#  ·  Due to difficulty of interstellar communication, requests may be malformed or invalid. These requests should be dropped.

#  ·  Due to difficulty sending packages, a sender may try resending the same
# package multiple times. A send request is uniquely identified by package_id
# that is constant between retries. The recipient should receive the package at
# most one time despite multiple attempts.

# ·  A recipient who has declined to receive a package type should not get that
# package. By default, receipients can receive every package type.


# Other Requirements

# ·  unit tested

# ·  extensible in case we want to deliver different package types

# ·  able to handle a significant amount of packages

ACTIONS = ('send_package', 'update_package')
PACKAGE_TYPES = ('marketing', 'personal')

@dataclass
class Base:
    action: str  # send_package or update_package
    timestamp: str  # "2142-08-23T02:40:12-0700"

    def validate(self):
        for field_name, field_def in self.__dataclass_fields__.items():
            try:
                actual_type = field_def.type.__origin__
            except AttributeError:
                actual_type = field_def.type

            actual_value = getattr(self, field_name)
            if not isinstance(actual_value, actual_type):
                raise Exception(
                    f"{field_name}: '{type(actual_value)}' instead of '{field_def.type}'"
                )
            
            if field_name == 'action':
                action = getattr(self, field_name)
                if action not in ACTIONS:
                    raise Exception('not in actions')

@dataclass
class SendPackage(Base):
    sender_id: int
    recipient_id: int
    package_id: int
    package_type: str  # marketing or personal

    def validate(self):
        if self.package_type not in PACKAGE_TYPES:
            raise Exception('package type is not valid')
        return super().validate()

@dataclass(init=True,repr=False)
class UpdatePackage(Base):
    recipient_id: int

    AT_LEAST_ONE_REQUIRED_FIELDS = (
        'personal_package',
        'marketing_package',
    )

    personal_package : bool | NoneType = None
    marketing_package: bool | NoneType = None

    def validate(self):
        counter = 0
        for item in self.AT_LEAST_ONE_REQUIRED_FIELDS:
            value = getattr(self, item)
            if value is None:
                counter+=1
            if  counter == len(self.AT_LEAST_ONE_REQUIRED_FIELDS):
                raise Exception('At least one field required')
        return super().validate()


base = SendPackage("send_package", "sssr", 12,123,1234,'personal')
base.validate()
data = {'action': 'update_package', 'timestamp': '12321', 'recipient_id': 1}
update = UpdatePackage(**data)
update.validate()
print(asdict(update))




# unit testing
# test 1 
# send_package create incorrect value SendPackage("send_package", "sssr", 12,123,1234,'incorrect_value')
# test 2
# send_package create incorrect type SendPackage("send_package", "sssr", 12, 'incorrect type', 1234, 'personal')
# test 3
# send_package correct - SendPackage("send_package", "sssr", 12,123,1234,'personal')
# Test package_update 4
# data = {'action': 'update_package', 'timestamp': '12321', 'recipient_id': 1, 'personal_package' : True}
# update = UpdatePackage(**data)
# update.validate()
# test validate "at least one field required"
# data = {'action': 'update_package', 'timestamp': '12321', 'recipient_id': 1}
# update = UpdatePackage(**data)
# update.validate()