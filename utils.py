#!/usr/bin/python

import re

def loadConfig():
    with open("config.ini") as file:
        directories = file.read().splitlines()
    return directories

def loadExceptions():
    with open("exceptions.ini", "r") as file:
        lines = file.read().splitlines()
    exceptions = {}
    for line in lines:
        if len(line) > 1 and line[0] != "#":
            if re.match(r".*;.*", line):
                exception = re.match(r"(.*);(.*)", line)
                if exception:
                    exceptions[exception.group(1)] = exception.group(2)
    return exceptions