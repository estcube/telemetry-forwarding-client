"""Provides a class for configuration parsing and modifying"""

import configparser
import logging
from copy import deepcopy
from rw_lock import ReadWriteLock

CONSTRAINTS = {
    "Mission Control": {
        "relay-enabled": {
            "type": "bool",
            "label": "Relay enabled"
        },
        "mcs-relay-url": {
            "type": "str",
            "label": "MCS relay URL"
        },

        "receiver-callsign": {
            "type": "str",
            "label": "Receiver callsign"
        },
        "norad-id": {
            "type": "int",
            "label": "Norad ID"
        },
        "longitude": {
            "type": "float",
            "label": "Longitude"
        },
        "latitude": {
            "type": "float",
            "label": "Latitude"
        }
    },

    "TNC interface": {
        "tnc-protocol-type": {
            "type": "select",
            "requiresRestart": True,
            "options": ["KISS"],
            "disabledOptions": ["AGW"],
            "label": "TNC protocol type"
        },
        "tnc-connection-type": {
            "type": "select",
            "requiresRestart": True,
            "options": ["TCP/IP"],
            "disabledOptions": ["RS232"],
            "label": "TNC connection type"
        },
        "tnc-ip": {
            "type": "str",
            "requiresRestart": True,
            "label": "TNC IP"
        },
        "tnc-device": {
            "type": "str",
            "requiresRestart": True,
            "label": "TNC device"
        },
        "max-connection-attempts": {
            "type": "int",
            "requiresRestart": True,
            "label": "Max connection attempts",
            "hidden": True
        },
        "connection-retry-time": {
            "type": "int",
            "requiresRestart": True,
            "label": "Connection retry time",
            "hidden": True
        }
    },

    "Client": {
        "database": {
            "type": "str",
            "description": "Path to the database file. Relative to executable file.",
            "requiresRestart": True,
            "label": "Database path",
            "hidden": True
        },
        "static-files-path": {
            "type": "str",
            "description": "Path to the root directory of static frontend files",
            "debug": True,
            "requiresRestart": True,
            "label": "Static files path",
            "hidden": True
        },
        "telemetry-configuration": {
            "type": "str",
            "description": "Path to the file that specified the telemetry data fields.",
            "requiresRestart": True,
            "label": "Telemetry data configuration"
        },
        "frontend-port": {
            "type": "int",
            "description": "Port that the frontend and api are served on.",
            "requiresRestart": True,
            "label": "Frontend port"
        }
    }
}


class Configuration(object):
    """ Class for parsing and modifying the configuration. """

    _log = logging.getLogger(__name__)

    def __init__(self, path: str):
        self.config = configparser.RawConfigParser()
        self.config_path = path
        self.config.read(path)
        self.constraints = {}
        self.sections = self.config.sections()

        self.lock = ReadWriteLock()

    def get_conf(self, section, element):
        """
        Retrieves the configured value at the specified field.

        example: getConf("Mission Control", "relay-enabled")
        """
        with self.lock.read_lock:
            return self.config.get(section, element)

    def get_constraints(self):
        """ Returns all of the constraints for the configuration. """
        return CONSTRAINTS

    def get_all_conf(self):
        """
        Returns the whole configuration as a dictionary, where each section is mapped to its own
        dictionary or fields.
        """
        with self.lock.read_lock:
            conf = {}
            config = self.config
            for each_section in config.sections():
                section = {}
                for (each_key, each_val) in config.items(each_section):
                    section[each_key] = each_val
                conf[each_section] = section

            return conf

    # example: setConf("Mission Control", "relay-enabled", False)
    def set_conf(self, section, element, value):
        """
        Sets the configuration value at the given position to the given value.

        Controls that the value is of a correct type, and for certain values, checks if it is in
        the permitted value list.
        After setting the value, also overwrites the configuration file with the current
        configuration state after the change.
        """
        with self.lock.write_lock:
            if section not in CONSTRAINTS:
                raise ValueError("Section {} does not exist.".format(section))

            section_constraints = CONSTRAINTS[section]
            if element not in section_constraints:
                raise ValueError("Field {} - {} does not exist.".format(section, element))

            constr = section_constraints[element]
            if constr["type"] == "str":
                pass
            elif constr["type"] == "int":
                try:
                    if not isinstance(value, int):
                        value = int(value)
                except Exception as e:
                    raise type(e)(section, element, value, "Integer")
            elif constr["type"] == "float":
                try:
                    if not isinstance(value, float):
                        value = float(value)
                except Exception as e:
                    raise type(e)(section, element, value, "Float")
            elif constr["type"] == "bool":
                if not isinstance(value, bool):
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    else:
                        raise ValueError(section, element, value, "Boolean")
            elif constr["type"] == "select":
                if value not in constr["options"]:
                    raise ValueError("{} - {} only supports values: {}".format(
                        section, element, constr["options"]))

            self.config.set(section, element, value)

            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)

    def get_conf_with_constraints(self):
        """
        Goes through the constraints and the values and returns a dictionary with constraints that have the value appended.
        """
        with self.lock.read_lock:
            constraints = deepcopy(CONSTRAINTS)
            config = self.get_all_conf()

            for i in constraints:
                for j in constraints[i]:
                    val = None
                    if i in config and j in config[i]:
                        val = (config[i][j])
                    constraints[i][j].update({"value": val})

            return constraints
