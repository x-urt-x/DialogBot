from enum import IntFlag

class Roles(IntFlag):
    GLOBAL = 1 << 4
    USER = 1 << 0
    ADMIN = 1 << 1
    SUPPORT = 1 << 2
    BANNED = 1 << 3