import logging

import pytest

from src import config


@pytest.fixture(autouse=True)
def reset_logging_config():
    """
    Fixture to reset the logging configuration before and after each test.
    """
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    yield
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


def test_basic_logging_configuration(caplog, tmp_path, monkeypatch):
    """
    Test the basic logging configuration when a non-existent configuration file is specified.

    Args:
        caplog (pytest.LogCaptureFixture): Fixture to capture log output.
        tmp_path (pathlib.Path): Fixture to provide a temporary directory unique to the test invocation.
        monkeypatch (pytest.MonkeyPatch): Fixture to modify environment variables for the test.
    """
    monkeypatch.setenv("LOG_CONFIG_FILE_PATH", str(tmp_path / "nonexistent.ini"))
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FILE_PATH", str(tmp_path / "automation.log"))

    config.init_logging_config()

    with caplog.at_level(logging.INFO):
        logger = logging.getLogger(__name__)
        logger.info("test_logger.pyで処理を実行")

    assert "test_logger.pyで処理を実行" in caplog.text
    assert (
        "The logging configuration file was not found, using basic configuration."
        in caplog.text
    )


def test_file_logging_configuration(caplog, tmp_path, monkeypatch):
    """
    Test the file logging configuration using a temporary logging configuration file.

    Args:
        caplog (pytest.LogCaptureFixture): Fixture to capture log output.
        tmp_path (pathlib.Path): Fixture to provide a temporary directory unique to the test invocation.
        monkeypatch (pytest.MonkeyPatch): Fixture to modify environment variables for the test.
    """
    # 一時ディレクトリにログ設定ファイルを作成
    config_content = """
[loggers]
keys=root

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=defaultFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=defaultFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=defaultFormatter
args=("%(LOG_FILE_PATH)s", 'a', 'utf-8')

[formatter_defaultFormatter]
class=colorlog.ColoredFormatter
format=%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s%(reset)s
datefmt=%Y-%m-%d %H:%M:%S
"""
    config_file = tmp_path / "logging.ini"
    config_file.write_text(config_content)

    monkeypatch.setenv("LOG_CONFIG_FILE_PATH", str(config_file))
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    log_file_path = tmp_path / "test_automation.log"
    monkeypatch.setenv("LOG_FILE_PATH", str(log_file_path))

    config.init_logging_config()

    with caplog.at_level(logging.INFO):
        logger = logging.getLogger(__name__)
        logger.info("test_logger.pyで処理を実行")

    assert log_file_path.exists()
    file_contents = log_file_path.read_text()
    assert "test_logger.pyで処理を実行" in file_contents
