#!/usr/bin/env python

import logging
import exifread
import os
import shutil
import sys

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
# create logger
logger = logging.getLogger('moveExifFiles')
logger.setLevel(logging.WARNING)

if len(sys.argv) < 3:
    print("Usage: moveExifFiles.py <directory to process> <destination directory>")
    exit(1)

dirname = sys.argv[1]
destdirname = sys.argv[2]

if not dirname:
    print "source directory cannot be empty!"
    exit(1)

if not destdirname:
    print "destination directory cannot be empty!"
    exit(1)

if not os.path.isdir(dirname):
    print("source directory {} does not exist!".format(dirname))
    exit(1)

if not os.path.isdir(destdirname):
    logger.info ("destination directory {} does not exist, creating it...".format(destdirname))
    print ("Created dir {}".format(destdirname))
    os.makedirs(destdirname)

print("Processing directory (non-recursive): {}".format(dirname))
print("Destination directory: {}".format(destdirname))

def abs_src_path(filename):
    return dirname + os.path.sep + filename

def abs_dest_path(filename):
    return destdirname + os.path.sep + filename

stats = {}

# list all files
files = [f
         for f in os.listdir(dirname)
         if os.path.isfile(abs_src_path(f))]
logger.debug(files)
for f in files:
    #open file, do EXIF stuf
    with open(abs_src_path(f),'rb') as file:
        data=exifread.process_file(file)
        logger.debug(data)
    if not data:
        logger.debug("no EXIF in file {}".format(f))
        continue
    exifDateTimeField = data['EXIF DateTimeOriginal']
    if not exifDateTimeField:
        logger.debug("no EXIF DateTimeOriginal field in the EXIF data")
        continue
    logger.debug(f + " - " + str(exifDateTimeField))
    date = str(exifDateTimeField).replace(":", "-").split()[0]
    logger.debug(date)
    # check if dir with date exists, if not create it
    if not os.path.isdir(abs_dest_path(date)):
        logger.info ("destination directory {} does not exist, creating it...".format(abs_dest_path(date)))
        os.makedirs(abs_dest_path(date))
        print ("Created dir {}".format(abs_dest_path(date)))

    dirStats = stats.get(abs_dest_path(date), {})
    if os.path.isfile(abs_dest_path(date + os.path.sep + f)):
        logger.debug("file {} already exists, will not be moved.".format(abs_dest_path(date + os.path.sep + f)))
        existed = dirStats.get('existed', 0)
        dirStats['existed']=existed + 1
    else:
        shutil.move(abs_src_path(f), abs_dest_path(date + os.path.sep + f))
        logger.debug("file {} moved to {}".format(abs_src_path(f), abs_dest_path(date + os.path.sep + f)))
        moved = dirStats.get('moved', 0)
        dirStats['moved']=moved + 1

    stats[abs_dest_path(date)]=dirStats

if stats:
    print "Summary: \n"
    for cdir, cdirStats in stats.items():
        print "\nDirectory {}".format(cdir)
        for op, count in cdirStats.items():
            print "\t{} files {}".format(count, op)
else:
    print "No changes were done."