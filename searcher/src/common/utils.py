import logging
import logging.config
from pathlib import Path
from typing import Optional
import configparser as cfp
from typing import Callable, Any, Iterable

DEFAULT_LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "minimal": {"format": "[%(levelname)s]: %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True,
        },
        "httpx": {
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


LOGGER_CONFIG = None


def setup_default_logger():
    logging.config.dictConfig(DEFAULT_LOGGER_CONFIG)


class ConfigNotFoundException(Exception):
    pass


def setup_logger(config: Optional[dict]):
    try:
        if config is None:
            logging.warning("Config for logger not found. Initializing with default")
            raise ConfigNotFoundException()
        config = DEFAULT_LOGGER_CONFIG
        logging.config.dictConfig(config)
    except ConfigNotFoundException:
        pass
    except Exception as ex:
        logging.config.dictConfig(DEFAULT_LOGGER_CONFIG)
        logging.warning(f"Error applying logger config: {str(ex)}")
        raise
    else:
        logging.info("Applied logger config successfully")


def to_bool(s: str):
    s = s.strip().lower()
    if s == "true":
        return True
    if s == "false":
        return False
    raise ValueError(f"Not a bool: {s}")


def auto_cast(value: Any, casters: Optional[Iterable[Callable[[str], Any]]] = None):
    if casters is None:
        casters = (int, float, to_bool)

    # Рекурсия для словаря
    if isinstance(value, dict):
        return {k: auto_cast(v, casters) for k, v in value.items()}

    # Рекурсия для коллекций
    if isinstance(value, list):
        return [auto_cast(v, casters) for v in value]

    if isinstance(value, tuple):
        return tuple(auto_cast(v, casters) for v in value)

    if isinstance(value, set):
        return {auto_cast(v, casters) for v in value}

    # Обработка строки
    if isinstance(value, str):
        value = value.strip()
        for caster in casters:
            try:
                return caster(value)
            except (ValueError, TypeError):
                continue
        return value

    return value


def parse_config(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Config not found in path: {path}")

    parser = cfp.ConfigParser(allow_no_value=True)
    with path.open("r") as f:
        parser.read_file(f)

    result: dict = {}
    for section in parser.sections():
        parts = section.split(".")
        target = result
        # пробежка по промежуточным уровням, создаём вложенные dict'ы
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target.setdefault(part, {})
            target = target[part]
        last = parts[-1]
        items = dict(parser.items(section))
        # если уже есть dict — сливаем, иначе присваиваем
        if last in target and isinstance(target[last], dict):
            target[last].update(items)
        else:
            target[last] = items

    return auto_cast(result)
