"""
UniversalConfig - universal class for managing application configuration.

The class provides a unified interface for working with
configuration from various sources:
- Configuration files (JSON, YAML, INI)
- Command Line arguments
- Logging Settings

Main features:
1. Loading configuration from different file formats
2. Automatic logging system setup
3. Command line argument parsing
4. Unified access to settings from different sources

Usage example:
    >>> config = UniversalConfig("config.yaml")
    >>> value = config.get("verbose")
    >>> db_config = config.get_config("database")
"""

import argparse
import logging
from logging.handlers import RotatingFileHandler
import os.path
import json
import yaml
import custom_error
import configparser


class UniversalConfig:
    """
    Universal configuration manager for Python applications.

    Attributes:
        config_data (dict): Dictionary with loaded configuration data
        parsed_args (dict): Dictionary with parsed command line arguments
        logger (logging.Logger): Configured application logger

    Examples:
        Basic usage:
        >>> config = UniversalConfig("config.json")
        >>> value = config.get("output_path")

        Usage with command line arguments:
        >>> config = UniversalConfig()
        >>> python script.py --verbose --output=result.txt
    """

    def __init__(self, config_path: str = None):
        """
        Initialization UniversalConfig.

        Args:
            config_path (str, optional): Path to configuration file.
                Supported formats: JSON, YAML, INI.
                If None, only default configuration is used.

        Raises:
            FileNotFoundError: If specified file doesn't exist
            custom_error.WrongFileFormat: If file format is not supported

        Examples:
            >>> # Load from JSON file
            >>> config = UniversalConfig("config.json")

            >>> # Load from YAML file
            >>> config = UniversalConfig("config.yaml")

            >>> # Without configuration file
            >>> config = UniversalConfig()
        """
        self.config_data = {}
        self.parsed_args = {}

        if config_path is None:
            pass
        elif os.path.exists(config_path) and os.path.isfile(config_path):
            self.load_config(config_path)
        else:
            raise FileNotFoundError("File not found")

        self.setup_logging()
        self.setup_arg_parser()

    def load_config(self, config_path: str):
        """
        Load configuration from file.

        Supported formats:
        - JSON (.json)
        - YAML (.yaml, .yml)
        - INI (.ini)

        Args:
            config_path (str): Path to configuration file

        Raises:
            custom_error.WrongFileFormat: If file format is not supported
            JSONDecodeError: For JSON parsing errors
            YAMLError: For YAML parsing errors

        Example:
            >>> config = UniversalConfig()
            >>> config.load_config("app_config.yaml")
            >>> print(config.get_config("database"))
        """
        with open(config_path, "r", encoding="utf-8") as config_file:
            if config_path.endswith(".json"):
                self.config_data = json.load(config_file)
            elif config_path.endswith((".yaml", ".yml")):
                self.config_data = yaml.safe_load(config_file)
            elif config_path.endswith(".ini"):
                self.config_data = self._parse_ini_config(config_file)
            else:
                raise custom_error.WrongFileFormat("Wrong format of file")

    def _parse_ini_config(self, config_file) -> dict[str, any]:
        """
        Parse INI file into Python dictionary.

        Implementation features:
        - Supports sections with dots (section.subsection)
        - Automatically converts data types
        - Supports arrays via commas

        Args:
            config_file: INI configuration file object

        Returns:
            dict[str, any]: Dictionary with parsed configuration

        INI file example:
            [database]
            host = localhost
            port = 5432

            [logging.console]
            enabled = true
            level = INFO

            [app.settings]
            features = debug,testing,production
        """
        config = configparser.ConfigParser(interpolation=None)
        config.read_file(config_file)

        result = {}

        for section in config.sections():
            if "." in section:
                main_section, subsection = section.split(".", 1)

                if main_section not in result:
                    result[main_section] = {}

                if subsection not in result:
                    result[main_section][subsection] = {}

                for arg_key, value in config.items(section):
                    result[main_section][subsection][arg_key] = (
                        self._convert_ini_value(value)
                    )
            else:
                result[section] = {}
                for key, value in config.items(section):
                    result[section][key] = self._convert_ini_value(value)

        return result

    def _convert_ini_value(self, value: str):
        """
        Convert INI string value to appropriate Python type.

        Supported conversions:
        - Boolean: "true", "false", "yes", "no", "on", "off", "1", "0"
        - Integer: "123", "-456"
        - Float: "3.14", "-2.5"
        - List: "item1,item2,item3"
        - String: all other cases

        Args:
            value (str): String value from INI file

        Returns:
            any: Converted value of appropriate type

        Examples:
            >>> self._convert_ini_value("true")  # returns: True
            >>> self._convert_ini_value("42")    # returns: 42
            >>> self._convert_ini_value("a,b,c") # returns: ['a', 'b', 'c']
        """
        # boolean
        if value.lower() in ("true", "yes", "on", "1"):
            return True
        elif value.lower() in ("false", "no", "off", "0"):
            return False

        # int and float
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                pass

        # list
        if "," in value:
            return [self._convert_ini_value(item.strip())
                    for item in value.split(",")]

        return value

    def setup_logging(self):
        """
        Set up logging system based on configuration.

        Configuration expected in 'logging' section of config_data:
        {
            "logging": {
                "console": {
                    "enabled": true,
                    "level": "INFO",
                    "format": "%(message)s"
                },
                "file": {
                    "enabled": true,
                    "path": "app.log",
                    "level": "DEBUG",
                    "backup_count": 5,
                    "format": "%(asctime)s - %(message)s"
                }
            }
        }

        Creates:
        - Console handler (enabled by default)
        - File handler with rotation (optional)

        YAML configuration example:
            logging:
              console:
                enabled: true
                level: INFO
              file:
                enabled: true
                path: /var/log/app.log
                level: DEBUG
                backup_count: 3
        """
        logging_config = self.config_data.get("logging", {})

        # Logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # default

        # Default formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler
        console_config = logging_config.get("console", {})
        if console_config.get("enabled", True):
            console_level = getattr(
                logging,
                console_config.get(
                    "level",
                    "INFO"
                )
            )
            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level)

            if "format" in console_config:
                console_formatter = logging.Formatter(
                    console_config["format"]
                )
                console_handler.setFormatter(console_formatter)
            else:
                console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        # File handler
        file_config = logging_config.get("file", {})
        if file_config.get("enabled", False):
            file_level = getattr(
                logging,
                file_config.get(
                    "level",
                    "DEBUG"
                )
            )
            file_path = file_config.get("path", "app.log")
            file_handler = RotatingFileHandler(
                filename=file_path,
                maxBytes=1024*1024,
                backupCount=file_config.get("backup_count", 5)
            )
            file_handler.setLevel(file_level)

            if "format" in file_config:
                file_formatter = logging.Formatter(
                    file_config["format"]
                )
                file_handler.setFormatter(file_formatter)
            else:
                file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

        self.logger = logger

    def setup_arg_parser(self):
        """
        Set up command line argument parser.

        Argument configuration expected in 'arguments' section:
        {
            "arguments": {
                "verbose": {
                    "short": "-v",
                    "long": "--verbose",
                    "type": "boolean",
                    "description": "Enable verbose output",
                    "default": false
                },
                "output": {
                    "short": "-o",
                    "long": "--output",
                    "type": "string",
                    "description": "Output file path",
                    "required": true
                }
            }
        }

        Supported argument types:
        - "boolean": flags (store_true)
        - "integer": integers
        - "float": floating point numbers
        - "string": strings (default)

        Configuration example:
            arguments:
              input_file:
                short: -i
                long: --input
                type: string
                required: true
                description: Input file path
              count:
                short: -c
                long: --count
                type: integer
                default: 1
                choices: [1, 2, 3, 4, 5]
        """
        parser = argparse.ArgumentParser(
            description=self.config_data.get("description", "")
        )

        # Adding arguments
        arguments = self.config_data.get("arguments", {})
        for arg_config in arguments.values():
            flags = []
            if "short" in arg_config:
                flags.append(arg_config["short"])
            if "long" in arg_config:
                flags.append(arg_config["long"])

            kwargs = {
                "help": arg_config.get("description", ""),
                "default": arg_config.get("default"),
                "required": arg_config.get("required", False)
            }

            arg_type = arg_config.get("type", "string")
            if arg_type == "boolean":
                kwargs["action"] = "store_true"
            elif arg_type == "integer":
                kwargs["type"] = int
            elif arg_type == "float":
                kwargs["type"] = float
            else:  # string
                kwargs["type"] = str

            if "choices" in arg_config:
                kwargs["choices"] = arg_config["choices"]

            parser.add_argument(*flags, **kwargs)

        self.parsed_args = vars(parser.parse_args())

    def get(self, key: str, default=None):
        """
        Get command line argument value.

        Args:
            key (str): Argument key (name without prefixes)
            default: Default value if argument not found

        Returns:
            any: Argument value or default

        Example:
            >>> config = UniversalConfig()
            >>> # python script.py --port 8080
            >>> port = config.get("port", 3000)
            >>> print(port)  # 8080
        """
        return self.parsed_args.get(key, default)

    def get_config(self, section: str = None):
        """
        Get configuration section or entire configuration.

        Args:
            section (str, optional): Configuration section name.
                If None, returns entire configuration.

        Returns:
            dict: Configuration dictionary or empty dict if section not found

        Example:
            >>> config = UniversalConfig("app_config.yaml")
            >>> db_config = config.get_config("database")
            >>> app_config = config.get_config("app")
            >>> all_config = config.get_config()
        """
        if section:
            return self.config_data.get(section, {})
        return self.config_data

    def show_help(self):
        """
        Display command line arguments help.

        Uses standard argparse mechanism to show help message.
        Useful for implementing --help command in application.

        Example:
            >>> config = UniversalConfig()
            >>> config.show_help()
            # Displays help for all available arguments
        """
        parser = argparse.ArgumentParser(
            description=self.config_data.get(
                "program", {}
            ).get(
                "description", ""
            )
        )

        parser.print_help()
