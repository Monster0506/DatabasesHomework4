import configparser
import os


def load_config(config_path="config.ini"):

    config = configparser.ConfigParser()

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config file '{config_path}' not found. "
            "Please create it with database credentials."
        )

    config.read(config_path)

    if "database" not in config:
        raise ValueError("Config file must contain a [database] section.")

    db_config = config["database"]

    required_keys = ["host", "user", "password", "database"]
    missing_keys = [key for key in required_keys if key not in db_config]

    if missing_keys:
        raise ValueError(
            f"Config file missing required keys: {', '.join(missing_keys)}"
        )

    return {
        "host": db_config["host"],
        "user": db_config["user"],
        "password": db_config["password"],
        "database": db_config["database"],
        "charset": "utf8mb4",
        "cursorclass": None,
    }
