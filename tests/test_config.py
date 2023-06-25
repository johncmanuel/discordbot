from src.config_parser import CustomConfigParser


class TestConfig:

    def test_override_config(self):
        config = CustomConfigParser("config.ini")
        assert config.get_bot_value("greeting_on") == "False"
        assert config.get_bot_db_value("twitch_users") == "twitch_users"
        assert bool(config.get_bot_value("greeting_on")) is not False
