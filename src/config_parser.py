import configparser


class CustomConfigParser:
    """ 
    configparser wrapper. This will always load configuration options from
    config.default.ini, unless overriden with another config file, which must 
    be located at the project's root. 
    """

    def __init__(self, file_path: str) -> None:
        self._config = configparser.ConfigParser()
        self._config_file_path = file_path
        self._config_file = self._config.read(self._config_file_path)

    def write(self, file_path: str):
        """ Writes the config """
        with open(file_path, 'w+') as config_file:
            self._config.write(config_file)

    def _get_value(self, section: str, option: str):
        """ Gets the value of a specified option from a config file """
        try:
            value = self._config.get(section, option)
            return value if value != '' else None
        except (configparser.NoSectionError, configparser.NoOptionError):
            return None

    def _set_value(self, section: str, option: str, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, option, value)

    def get_bot_value(self, option: str):
        """ Retrieves an option from section bot """
        return self._get_value(section="bot", option=option)

    def get_bot_db_value(self, option: str):
        """ Retrieves an option from section bot_db """
        return self._get_value(section="bot_db", option=option)

    def get_sections(self):
        return self._config.sections()

    def get_options(self, section: str):
        return self._config.options(section)
