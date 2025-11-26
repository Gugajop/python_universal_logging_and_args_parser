import argparse
import logging
from logging.handlers import RotatingFileHandler
import os.path
import json
import yaml
import custom_error


class UniversalConfig:
    def __init__(self, config_path: str = None):
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
        """"Загрузка существующей конфигурации из файла"""
        with open(config_path, "r", encoding="utf-8") as config_file:
            if config_path.endswith(".json"):
                self.config_data = json.load(config_file)
            elif config_path.endswith((".yaml", ".yml")):
                self.config_data = yaml.safe_load(config_file)
            else:
                raise custom_error.WrongFileFormat("Wrong format of file")

    def setup_logging(self):
        """Настройка параметров логера"""
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
        """Настройка парсера аргументов"""
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
        """Получение значения аргумента"""
        return self.parsed_args.get(key, default)

    def get_config(self, section: str = None):
        """Получение конфигурации данных"""
        if section:
            return self.config_data.get(section, {})
        return self.config_data

    def show_help(self):
        """Отображение помощи по аргументам"""
        parser = argparse.ArgumentParser(
            description=self.config_data.get(
                "program", {}
            ).get(
                "description", ""
            )
        )

        parser.print_help()
