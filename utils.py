#!/usr/bin/env python3

import re
import configparser


def loadConfig():
    config = configparser.ConfigParser()
    config.read("config/settings.ini")
    return config["DIRECTORIES"]["input"], config["DIRECTORIES"]["outputtvs"], config["DIRECTORIES"]["outputmov"]


def loadExceptions():
    with open("config/exceptions.ini", "r") as file:
        lines = file.read().splitlines()
    exceptions = dict()
    for line in lines:
        if not line.startswith('#'):
            exception = re.match(r"(.*);(.*)", line)
            if exception:
                exceptions[exception.group(1)] = exception.group(2)
    return exceptions
