#!/usr/bin/python

import re

def loadConfig():
    with open("config/config.ini") as file:
        directories = file.read().splitlines()
    return directories

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
