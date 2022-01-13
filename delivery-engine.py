from sys import stdin
from dataclasses import dataclass, asdict
from types import NoneType
import time
import json
import unittest

TEST_DATA = [
    "{\"action\": \"send_package\", \"timestamp\": \"2142-08-23T02:40:12-0700\", \"sender_id\": 5, \"recipient_id\": 21, \"package_id\": 18571, \"package_type\": \"marketing\"}",
    "{\"action\": \"send_package\", \"timestamp\": \"2142-08-24T16:20:12-0700\", \"sender_id\": 3, \"recipient_id\": 49, \"package_id\": 1756, \"package_type\": \"personal\"}",
    "{\"action\": \"update_preference\", \"timestamp\": \"2142-08-24T23:40:12Z\", \"recipient_id\": 21, \"personal_package\": false, \"marketing_package\": false}",
    "{\"action\": \"send_package\", \"timestamp\": \"2142-08-28T02:12:12+1230\", \"sender_id\": 8, \"recipient_id\": 21, \"package_id\": 6901, \"package_type\": \"marketing\"}",
    "{\"action\": \"send_package\", \"timestamp\": \"2142-08-24T02:23:12+0100\", \"sender_id\": 42, \"recipient_id\": 21, \"package_id\": 2834, \"package_type\": \"personal\"}",
    "{\"action\": \"send_package\", \"timestamp\": \"2142-09-01T02:45:12+0100\", \"sender_id\": 42, \"recipient_id\": 21, \"package_id\": 2834, \"package_type\": \"personal\"}",
]

ACTIONS = ("send_package", "update_preference")
PACKAGE_TYPES = ("marketing", "personal")

# Dataclasses for validation and re-use data
@dataclass
class Base:
    action: str  # send_package or update_preference
    timestamp: str  # "2142-08-23T02:40:12-0700"
    recipient_id: int

    def validate(self):
        for field_name, field_def in self.__dataclass_fields__.items():
            try:
                actual_type = field_def.type.__origin__
            except AttributeError:
                actual_type = field_def.type

            actual_value = getattr(self, field_name)
            if not isinstance(actual_value, actual_type):
                raise Exception(
                    f"{field_name}: {type(actual_value)} instead of {field_def.type}"
                )

            if field_name == "action":
                action = getattr(self, field_name)
                if action not in ACTIONS:
                    raise Exception(f"{field_name}: <{actual_value}> not in actions")


@dataclass
class SendPackage(Base):
    sender_id: int
    package_id: int
    package_type: str  # marketing or personal

    def validate(self):
        if self.package_type not in PACKAGE_TYPES:
            raise Exception("package type is not valid")
        return super().validate()


@dataclass(init=True, repr=False)
class UpdatePackage(Base):

    AT_LEAST_ONE_REQUIRED_FIELDS = (
        "personal_package",
        "marketing_package",
    )

    personal_package: bool | NoneType = None
    marketing_package: bool | NoneType = None

    def validate(self):
        counter = 0
        for item in self.AT_LEAST_ONE_REQUIRED_FIELDS:
            value = getattr(self, item)
            if value is None:
                counter += 1
            if counter == len(self.AT_LEAST_ONE_REQUIRED_FIELDS):
                raise Exception("At least one field required")
        return super().validate()


@dataclass
class Recipient:
    id: int

    personal_package: bool = True
    marketing_package: bool = True

    PERMISSIONS_FIELDS = ("personal_package", "marketing_package")


class MessageServer:
    def __init__(self, *args, **kwargs):
        self._recipients = {}
        self._packages = []
        self._dropped = 0
        self._max_packages_count = kwargs.get("max_packages_count", None)

    @staticmethod
    def _validate_json(input: str) -> dict:
        loaded_json = json.loads(input)
        action_type = loaded_json.get("action", None)
        if action_type is None:
            raise Exception("Not valid action")
        elif action_type == ACTIONS[0]:
            item = SendPackage(**loaded_json)
            item.validate()
            return asdict(item)
        elif action_type == ACTIONS[1]:
            item = UpdatePackage(**loaded_json)
            item.validate()
            return asdict(item)
        else:
            raise Exception("Invalid action")

    def _print_to_std(self, input):
        print(input)

    def _update_preference(self, input: dict) -> bool:
        recipient_id = str(input.get("recipient_id"))

        recipient = {"id": input.get("recipient_id")}
        if input.get("personal_package") is not None:
            recipient["personal_package"] = input.get("personal_package")
        if input.get("marketing_package") is not None:
            recipient["marketing_package"] = input.get("marketing_package")

        if self._recipients.get(recipient_id, None) is None:
            self._recipients[recipient_id] = recipient
        self._recipients[recipient_id].update(recipient)

        if input not in self._packages:
            self._print_to_std(input)
            self._packages.append(input)
            return True

        self._dropped += 1
        return False

    def _process_package(self, input: dict) -> bool:
        recipient_id = str(input.get("recipient_id"))
        if self._recipients.get(recipient_id, None) is None:
            recipient = {
                "id": input.get("recipient_id"),
                "personal_package": True,
                "marketing_package": True,
            }
            self._recipients[str(recipient["id"])] = recipient

        if input not in self._packages:
            recipient = self._recipients[recipient_id]
            if self._is_allowed_package(recipient, input):
                self._print_to_std(input)
                self._packages.append(input)
                return True
        self._dropped += 1
        return False

    def process_input(self, input: str):
        if self._max_packages_count is not None and self._max_packages_count <= 0:
            self._dropped += 1
            return

        try:
            json = self._validate_json(input)
            if json.get("action") == ACTIONS[0]:
                ret = self._process_package(json)
            else:
                ret = self._update_preference(json)
            if ret and self._max_packages_count is not None:
                self._max_packages_count -= 1
        except Exception:
            self._dropped += 1

    def _is_allowed_package(self, recipient: dict, request: dict) -> bool:
        if (
            recipient["marketing_package"] is True
            and request["package_type"] == "marketing"
        ):
            return True
        if (
            recipient["personal_package"] is True
            and request["package_type"] == "personal"
        ):
            return True
        return False

    def results(self):
        return {
            "packages_delivered": len(self._packages),
            "packages_dropped": self._dropped,
        }


def server():
    start = time.time()
    server_instance = MessageServer()

    # for demonstration purpose only, i replace code from 212 line to input  TEST_DATA
    # for line in stdin:
    for item in TEST_DATA:
        server_instance.process_input(item)

    print(server_instance.results())
    print(f"Processing took: {(time.time() - start):.2f} seconds")


# unit testing
class TestingProtocols(unittest.TestCase):
    def test_incorrect_send_package_value(self):
        self.assertRaises(
            Exception,
            SendPackage(
                "send_package", "sssr", 12, 123, 1234, "incorrect_package_type"
            ),
        )

    def test_incorrect_send_package_type(self):
        self.assertRaises(
            Exception,
            SendPackage(
                "send_package", "sssr", 12, "incorrect_item_type", 1234, "personal"
            ),
        )

    def test_send_package_correct_validation(self):
        self.assertEqual(
            {
                "action": "send_package",
                "package_id": 1234,
                "package_type": "personal",
                "recipient_id": 12,
                "sender_id": 123,
                "timestamp": "sssr",
            },
            asdict(SendPackage("send_package", "sssr", 12, 123, 1234, "personal")),
        )

    def test_validate_update_package(self):
        data = {
            "action": "update_preference",
            "timestamp": "12321",
            "recipient_id": 1,
            "personal_package": True,
        }
        update = UpdatePackage(**data)
        update.validate()


# Test package_update 4
# data = {'action': 'update_preference', 'timestamp': '12321', 'recipient_id': 1, 'personal_package' : True}
# update = UpdatePackage(**data)
# update.validate()
# test validate "at least one field required"
# data = {'action': 'update_preference', 'timestamp': '12321', 'recipient_id': 1}
# update = UpdatePackage(**data)
# update.validate()
# unit tests with TEST_DATA


if __name__ == "__main__":

    # unittest.main()
    server()
