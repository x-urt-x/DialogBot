import logging
from logging.handlers import RotatingFileHandler
from enum import IntFlag
import os

class LogZone(IntFlag):
    MAIN = 1 << 0
    YAML = 1 << 1
    DB   = 1 << 2
    NET  = 1 << 3
    DIALOG_HANDLERS = 1 << 4
    USERS = 1 << 5
    MESSAGE_PROCESS = 1 << 6

# Человеческие названия зон
ZONE_NAMES = {
    LogZone.MAIN: "MAIN",
    LogZone.YAML: "YAML",
    LogZone.DB:   "DB",
    LogZone.NET:  "NET",
    LogZone.DIALOG_HANDLERS:  "DIALOG_HANDLERS",
    LogZone.USERS:  "USERS",
    LogZone.MESSAGE_PROCESS: "MESSAGE_PROCESS"
}

class ZoneLogger:

    active_zones = 0

    @staticmethod
    def enable_zone(zone):
        """Включает указанную зону логирования"""
        ZoneLogger.active_zones |= zone

    @staticmethod
    def disable_zone(zone):
        """Выключает указанную зону логирования"""
        ZoneLogger.active_zones &= ~zone

    def __init__(self, log_file='logs/bot.log'):
        self.logger = logging.getLogger("ZoneLogger")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.hasHandlers():
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(logging.Formatter('%(message)s'))

            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setLevel(logging.ERROR)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def _format(self, level: str, zone: LogZone, msg: str) -> str:
        zone_name = self._get_zone_name(zone)
        return f"[{level}] {zone_name}: {msg}"

    def _get_zone_name(self, zone: LogZone) -> str:
        names = [name for z, name in ZONE_NAMES.items() if z & zone]
        return '|'.join(names) if names else f"ZONE({int(zone)})"

    def info(self, zone: LogZone, msg: str, *args, **kwargs):
        if zone & ZoneLogger.active_zones:
            self.logger.info(self._format("INFO", zone, msg), *args, **kwargs)

    def debug(self, zone: LogZone, msg: str, *args, **kwargs):
        if zone & ZoneLogger.active_zones:
            self.logger.debug(self._format("DEBUG", zone, msg), *args, **kwargs)

    def warning(self, zone: LogZone, msg: str, *args, **kwargs):
        if zone & ZoneLogger.active_zones:
            self.logger.warning(self._format("WARNING", zone, msg), *args, **kwargs)

    def error(self, zone: LogZone, msg: str, *args, **kwargs):
        self.logger.error(self._format("ERROR", zone, msg), *args, **kwargs)

    def critical(self, zone: LogZone, msg: str, *args, **kwargs):
        self.logger.critical(self._format("CRITICAL", zone, msg), *args, **kwargs)

logger = ZoneLogger()