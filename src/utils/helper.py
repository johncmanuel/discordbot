import json
import os
import shutil
from inspect import currentframe
from pathlib import Path

from mutagen.mp3 import MP3

# from config import PROJ_CACHE_PATH
from log import Logger


class Helper():
    """ Collection of helper functions """

    @staticmethod
    def combine_strings(strings: list, name: str) -> str:
        """ 
        Combines a list of strings into one string and adds a name
        on top of it. Useful for combining names that are
        spaced out in *args.
        """
        return name + " " + " ".join(strings)

    @staticmethod
    def path_contains_valid_file(path: str) -> bool:
        """ Checks if the path to a file is, indeed, a file. """
        some_path = Path(path)
        return some_path.is_file()

    @staticmethod
    def get_file_extension(path: str) -> str:
        """ 
        Gets file extension of a path to a file. Returns None if
        there is no valid file extension. 
        """
        some_path = Path(path)
        file_ext = some_path.suffix
        return file_ext if file_ext != '' else None

    @staticmethod
    def get_file_name(path: str) -> str:
        """ 
        Gets the filename of a path to a file, 
        removing any directories within it. 
        """
        some_path = Path(path)
        return some_path.name

    @staticmethod
    def strip_file_ext(path: str) -> str:
        """ 
        Removes the file extension from a 
        path to a file. 
        """
        some_path = Path(path)
        return some_path.stem

    @staticmethod
    def get_name(path: str) -> str:
        """ Gets the name of path without directories and file extension """
        some_path = Path(path)
        some_path = Helper.get_file_name(some_path)
        some_path = Helper.strip_file_ext(some_path)
        return some_path

    # @staticmethod
    # def get_directories_of_path(path: str) -> list:
    #     some_path = Path(path)
    #     directories = some_path.parents
    #     directories = [str(directory) for directory in directories]
    #     return directories

    @staticmethod
    def remove_directory_contents(directory: str) -> None:
        """ Cleans the contents of a directory """
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                Logger.CRITICAL(f"Failed to delete {file_path}. Reason: {e}")

    @staticmethod
    def get_func_name() -> str:
        """
        Gets the name of the function being called. 
        This is primarily needed for logging and naming purposes.

        Ex.:
        def test(name):
            print("hi", name)

        def main():
            caller_name = get_func_name()
            test(caller_name)

        main()

        main() will print: hi main
        """
        return currentframe().f_back.f_code.co_name

    @staticmethod
    def mkdir(path: str):
        """ Makes a directory at a path. """
        Path(path).mkdir(exist_ok=True)

    @staticmethod
    def mksubdir(directory_path: str, subdirectory_name: str):
        path = Path(directory_path)
        subdirectory_path = path / subdirectory_name
        subdirectory_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_length_of_audio_src(src):
        """ Gets the length of an audio clip """
        return MP3(src).info.length


class JSONHelper():

    @staticmethod
    def cache_response(data, file_path) -> None:
        """ Cache any kind of data into a json """
        with open(file_path, 'w+', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_json_as_dict(path: str) -> dict:
        """ Retrieves JSON file and returns it as a dictionary. """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
