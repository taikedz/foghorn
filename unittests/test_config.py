from src.config import Config

class TestConfig:
    def test_config(self):
        with open("etc-config.env", 'w') as fh:
            fh.write("PATH=etc\n")
            fh.write("GLOBAL=world\n")
        with open("home-config.env", 'w') as fh:
            fh.write("PATH=home\n")
            fh.write("SCOPE=home\n")

        conf1 = Config("etc-config.env")
        conf2 = Config("home-config.env").over(conf1)

        assert conf2.get("PATH") == "home"
        assert conf2.get("GLOBAL") == "world"
        assert conf2.get("SCOPE") == "home"

        assert conf2.asDict() == {"PATH": "home", "SCOPE":"home", "GLOBAL": "world"}

        assert conf2.get("GLOBAL", "oops") == "world"
        assert conf2.get("SCOPE", "oops") == "home"
        assert conf2.get("UNKNOWN", "oops") == "oops"