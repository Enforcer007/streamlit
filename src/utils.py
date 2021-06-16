from glob import iglob
import os


class defaults:
    DATA_FOLDER = "./data/"


def get_all_files(folder_path, only_files=True, skip_files=["pyc"]):
    path = join_paths(folder_path, "**")
    paths = iglob(path, recursive=True)
    if not only_files:
        return paths
    for file_path in paths:
        if is_file(file_path):
            if not file_path.split(".")[-1] in skip_files:
                yield file_path


def join_paths(*args, instr=False):
    path = os.path.join(*args)
    if instr:
        return str(path)
    return path


def is_file(path):
    return os.path.isfile(path)
