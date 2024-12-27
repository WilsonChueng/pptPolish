import os
import sys


def get_data_file_path(path):
    current_path = os.path.dirname(os.path.abspath(__file__))
    data_path = current_path.split("scripts")[0] + "data"
    return os.path.join(data_path, path)


def get_script_file_path(path):
    data_path = get_script_root_path()
    return os.path.join(data_path, path)


def get_script_root_path():
    current_path = os.path.dirname(os.path.abspath(__file__))
    return current_path.split("utils")[0]
