#!/usr/bin/python

import os
import re
import shutil
import utils

# CONFIGURATION START
formatTVS = "%t\\Season %s\\%t - s%se%e"
formatMOV = "%t (%y)\\%t (%y)"

extensions = ["mkv", "avi", "mp4", "mov", "iso"]
minSize = 50 # minimum size in MB
minSize <<= 20

cleanup = True
overwrite = False
verbose = True
debug = False

queueClean = set()
queueRemove = set()
specialShows = dict()
# CONFIGURATION END

# TV pattern.
pattern_tv = re.compile(r"""(.*?)         # Title
                        [ .]
                        [\s-]*
                        S?(\d{1,2})       # Season
                        [E|X](\d{1,2})    # Episode
                        E?(\d{1,2})?      # Multi-episode
                        [ .a-zA-Z]*
                        (\d{3,4}p)?       # Quality
                    """, re.VERBOSE | re.IGNORECASE)

# TV pattern (alternative). Splitting these to simplify and speed up formatting.
pattern_tv_alt = re.compile(r"""(.*)     # Title
                             [ .]
                             (\d{1})      # Season
                             (\d{2})      # Episode
                             [^\d|^P]
                             [ .a-zA-Z]*
                             (\d{3,4}p)?  # Quality
                         """, re.VERBOSE | re.IGNORECASE)

# MOVIE pattern.
pattern_movie = re.compile(r"""(.*?)      # Title
                       [ .\[\(]
                       (\d{4})            # Year
                       [\]\)]?
                       [ .a-zA-Z]*
                       (\d{3,4}p)?        # Quality
                    """, re.VERBOSE)

# Load exceptions
def loadExceptions():
    specialShows.clear()
    specialShows.update(utils.loadExceptions())

def loadConfig():
    directories = utils.loadConfig()
    return (os.path.normpath(directories[0]), os.path.normpath(directories[1]), os.path.normpath(directories[2]))

# Clean the source dir. Remove empty folders, small files etc.
def garbagecollect():
    for dir in queueClean:
        if os.path.exists(dir):
            delete = True
            for root, dirs, files in os.walk(dir):
                for f in files:
                    if (f[f.rfind('.')+1:] in extensions and os.path.getsize(os.path.join(root, f)) >= minSize) or f[f.rfind('.')+1:] == "srt":
                        delete = False
            if delete:
                queueRemove.add(dir)
    for dir in queueRemove:
        try:
            if os.path.exists(dir):
                shutil.rmtree(dir)
                if verbose:
                    print("REMOVED: {}".format(dir))
        except Exception as e:
            if verbose:
                print(e)
                print("FAILED TO REMOVE: {}".format(dir))

# Fix titlecasing in new filenames.
def toTitlecase(filename):
    smaller = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'of', 'on', 'or', 'the', 'to', 'v', 'via', 'vs', 'with']
    words = filename.split(' ')
    result = words[0][0].upper() + words[0][1:].lower()
    if len(words) > 1:
        result += ' '
        for word in words[1:]:
            if len(word) == 0:
                continue
            result += word.lower() if word.lower() in smaller else word[0].upper() + word[1:].lower()
            result += ' '
    return result.strip()

# Fills in the 'blanks' of a given format given a translation dictionary
def rename(format, translations):
    result = format
    for k, v in translations.items():
        result = result.replace(k, v)
    return result

# Translate the old filename to the new format.
def formatter(filename_old):
    extension = filename_old[filename_old.rfind('.')+1:]
    if extension not in extensions and extension != "srt":
        return (None, None)
    tv = re.findall(pattern_tv, filename_old)
    if tv:
        name = toTitlecase(tv[0][0].replace('.', ' '))
        if name in specialShows:
            name = specialShows[name]
        season = tv[0][1].zfill(2)
        episode = tv[0][2].zfill(2)
        if tv[0][3]:
            episode += "e" + tv[0][3].zfill(2)
        quality = tv[0][4] if tv[0][4] else "notHD"
        filename_new = rename(formatTVS, {"%t": name, "%s": season, "%e": episode, "%q": quality})
        filename_new += '.' + extension
        return (filename_new, "TV")
    else:
        tv_alt = re.findall(pattern_tv_alt, filename_old)
        if tv_alt:
            name = toTitlecase(tv_alt[0][0].replace('.', ' '))
            if name in specialShows:
                name = specialShows[name]
            season = tv_alt[0][1].zfill(2)
            episode = tv_alt[0][2].zfill(2)
            quality = tv_alt[0][3] if tv_alt[0][3] else "notHD"
            filename_new = rename(formatTVS, {"%t": name, "%s": season, "%e": episode, "%q": quality})
            filename_new += '.' + extension
            return (filename_new, "TV")
        else:
            movie = re.findall(pattern_movie, filename_old)
            if movie:
                name = toTitlecase(movie[0][0].replace('.', ' '))
                year = movie[0][1]
                quality = movie[0][2] if movie[0][2] else "notHD"
                filename_new = rename(formatMOV, {"%t": name, "%y": year, "%q": quality})
                filename_new += '.' + extension
                return (filename_new, "MOVIE")
            else:
                if verbose:
                    print("ERROR: {}".format(filename_old))
                return (filename_old, None)

# Move the formatted file.
def relocate(old, new):
    if os.path.exists(new):
        if overwrite:
            os.remove(new)
            shutil.move(old, new)
            if verbose:
                print("OVERWROTE: {}".format(new))
        else:
            if verbose:
                print("ALREADY EXISTS: {}".format(new))
    else:
        if not os.path.exists(os.path.dirname(new)):
            os.makedirs(os.path.dirname(new))
        shutil.move(old, new)
        if verbose:
            print("MOVED: {}".format(new))

def main(dir_src, dir_tvs, dir_mov):
    loadExceptions()
    for root, dirs, files in os.walk(dir_src):
        for filename_old in files:
            try:
                path_old = os.path.join(root, filename_old)
                if os.path.getsize(path_old) >= minSize or filename_old[filename_old.rfind('.')+1:] == "srt":
                    (filename_new, type) = formatter(filename_old)
                    if type:
                        if root != dir_src and not debug:
                            queueClean.add(root)
                        if type == "TV":
                            path_new = os.path.join(dir_tvs, filename_new)
                        else:
                            path_new = os.path.join(dir_mov, filename_new)
                        if not debug:
                            relocate(path_old, path_new)
                        else:
                            print("{}\t->\t{}".format(filename_old, filename_new))
            except WindowsError as e:
                if verbose:
                    print(e)
            except Exception as e:
                if verbose:
                    print("FAILED: {}".format(filename_old))
                    print(e)
    if cleanup and not debug:
        garbagecollect()

if __name__ == "__main__":
    dir_src, dir_tvs, dir_mov = loadConfig()
    main(dir_src, dir_tvs, dir_mov)