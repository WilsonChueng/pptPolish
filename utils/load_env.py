import configparser
from utils.get_file_path import get_script_file_path
import os

def get_env_para(model_token_name):
    if os.name == "nt":  # Windows
        return os.getenv(model_token_name)
    elif os.name == "posix":  # Linux & macOS
        return os.environ.get(model_token_name)
    else:
        return None

config = configparser.ConfigParser()
config.read(get_script_file_path("config.ini"), encoding="utf-8")
target_uuid_to_count = {}
for key, item in config.items():
    if key == "envs":
        for k, v in item.items():
            os.environ[k] = v