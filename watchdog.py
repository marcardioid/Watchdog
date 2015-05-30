#!/usr/bin/python

import os
import re
import shutil

# CONFIGURATION START
format_tvs = "%t\\Season %s\\%t - s%se%e"
format_mov = "%t (%y)\\%t (%y)"

dir_src = "D:\\Libraries\\Downloads"
dir_tvs = "D:\\Libraries\\TV Shows"
dir_mov = "D:\\Libraries\\Movies"

extensions = ["mkv", "avi", "mp4"]
min_size = 50 # minimum size in MB

cleanup = True
overwrite = False
verbose = True
# CONFIGURATION END

min_size <<= 20

# Default TV pattern.
pattern_tv = re.compile(r"""(.*?)         # Title
                        [ .]
                        [\s-]*
                        S?(\d{1,2})       # Season
                        [E|X](\d{1,2})    # Episode
                        E?(\d{1,2})?      # Multi-episode
                        [ .a-zA-Z]*
                        (\d{3,4}p)?       # Quality
                    """, re.VERBOSE | re.IGNORECASE)

# Alternative TV pattern. Splitting these to simplify and speed up formatting.
pattern_tv_alt = re.compile(r"""(.*)     # Title
                             [ .]
                             (\d{1})      # Season
                             (\d{2})      # Episode
                             [^\d|^P]
                             [ .a-zA-Z]*
                             (\d{3,4}p)?  # Quality
                         """, re.VERBOSE | re.IGNORECASE)

# Movie pattern.
pattern_movie = re.compile(r"""(.*?)      # Title
                       [ .\[\(]
                       (\d{4})            # Year
                       [\]\)]?
                       [ .a-zA-Z]*
                       (\d{3,4}p)?        # Quality
                    """, re.VERBOSE)

# Load exceptions
f = open("exceptions.ini", "r")
dataFile = re.split("\n", f.read())
f.close()
specialshows = {}
for line in dataFile:
    if line[0] != "#":
        if re.match(r".*;.*", line):
            a = re.match(r"(.*);(.*)", line)
            specialshows[a.group(1)] = a.group(2)

# Clean the source dir. Remove empty folders, small files etc.
def garbagecollect():
    for dir in queue_clean:
        if os.path.exists(dir):
            delete = True
            for root, dirs, files in os.walk(dir):
                for f in files:
                    if f[f.rfind(".")+1:] in extensions and os.path.getsize(os.path.join(root, f)) >= min_size:
                        delete = False
            if delete:
                queue_remove.add(dir)
    for dir in queue_remove:
        try:
            shutil.rmtree(dir)
            print("REMOVED: " + dir)
        except Exception as e:
            print(e)
            print("FAILED TO REMOVE: " + dir)

# Fix titlecasing in new filenames.
def to_titlecase(filename):
    smaller = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'of', 'on', 'or', 'the', 'to', 'v', 'via', 'vs', 'with']
    filename = filename.split(" ")
    result = ""
    result += filename[0][0].upper()
    result += filename[0][1:].lower()
    if len(filename) > 1:
        result += " "
        for word in filename[1:]:
            if word in smaller:
                result += word.lower()
            else:
                result += word[0].upper()
                result += word[1:].lower()
            result += " "
    return result.strip()

# Translate the old filename to the new format.
def formatter(filename_old):
    extension = filename_old[filename_old.rfind(".")+1:]
    if extension not in extensions:
        return (None, None)
    tv = re.findall(pattern_tv, filename_old)
    if tv:
        name = to_titlecase(tv[0][0].replace(".", " "))
        if name in specialshows:
            name = specialshows[name]
        season = tv[0][1].zfill(2)
        episode = tv[0][2].zfill(2)
        if tv[0][3]:
            episode += "e" + tv[0][3].zfill(2)
        quality = tv[0][4] if tv[0][4] else "notHD"
        filename_new = format_tvs.replace("%t", name)
        filename_new = filename_new.replace("%s", season)
        filename_new = filename_new.replace("%e", episode)
        filename_new = filename_new.replace("%q", quality)
        filename_new += "." + extension
        return (filename_new, "TV")
    else:
        tv_alt = re.findall(pattern_tv_alt, filename_old)
        if tv_alt:
            name = to_titlecase(tv_alt[0][0].replace(".", " "))
            if name in specialshows:
                name = specialshows[name]
            season = tv_alt[0][1].zfill(2)
            episode = tv_alt[0][2].zfill(2)
            quality = tv_alt[0][3] if tv_alt[0][3] else "notHD"
            filename_new = format_tvs.replace("%t", name)
            filename_new = filename_new.replace("%s", season)
            filename_new = filename_new.replace("%e", episode)
            filename_new = filename_new.replace("%q", quality)
            filename_new += "." + extension
            return (filename_new, "TV")
        else:
            movie = re.findall(pattern_movie, filename_old)
            if movie:
                name = to_titlecase(movie[0][0].replace(".", " "))
                year = movie[0][1]
                quality = movie[0][2] if movie[0][2] else "notHD"
                filename_new = format_mov.replace("%t", name)
                filename_new = filename_new.replace("%y", year)
                filename_new = filename_new.replace("%q", quality)
                filename_new += "." + extension
                return (filename_new, "MOVIE")
            else:
                print("ERROR: %s" % filename_old)
                return (filename_old, None)

# Move the formatted file.
def relocate(old, new):
    if os.path.exists(new):
        if overwrite:
            os.remove(new)
            shutil.move(old, new)
            print("OVERWROTE: " + str(new))
        else:
            print("ALREADY EXISTS: " + str(new))
    else:
        if not os.path.exists(os.path.dirname(new)):
            os.makedirs(os.path.dirname(new))
        shutil.move(old, new)
        print("MOVED: " +str(new))

queue_clean = set()
queue_remove = set()
def main():
    for root, dirs, files in os.walk(dir_src):
        for filename_old in files:
            try:
                path_old = os.path.join(root, filename_old)
                if os.path.getsize(path_old) >= min_size:
                    (filename_new, type) = formatter(filename_old)
                    if type:
                        if root != dir_src:
                            queue_clean.add(root)
                        if type == "TV":
                            path_new = os.path.join(dir_tvs, filename_new)
                        else:
                            path_new = os.path.join(dir_mov, filename_new)
                        relocate(path_old, path_new)
            except WindowsError as e:
                print(e)
            except Exception as e:
                print("FAILED: " + str(filename_old))
                print(e)
    if cleanup:
        garbagecollect()

if __name__ == "__main__":
    main()