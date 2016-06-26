#!/usr/bin/env python

import logging
import exifread
import os
import shutil
import hashlib
import sys
import time
import datetime

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
# create logger
logger = logging.getLogger('moveExifFiles')
logger.setLevel(logging.WARNING)


class InputArguments(object):

    # create logger
    logger = logging.getLogger('InputArguments')
    logger.setLevel(logging.WARNING)

    def __init__(self, argv):
        if len(argv) < 3:
            print("Usage: moveExifFiles.py <directory to process> <destination directory>")
            exit(1)

        self.dirname = argv[1]
        self.destdirname = argv[2]

        print("Using source directory (non-recursive): {}".format(self.dirname))
        print("Using destination directory: {}".format(self.destdirname))

        if not self.dirname:
            print "source directory cannot be empty!"
            exit(1)

        if not self.destdirname:
            print "destination directory cannot be empty!"
            exit(1)

        if not os.path.isdir(self.dirname):
            print("source directory {} does not exist!".format(self.dirname))
            exit(1)

        if not os.path.isdir(self.destdirname):
            self.logger.info ("destination directory {} does not exist, creating it...".format(self.destdirname))
            print ("Created dir {}".format(self.destdirname))
            os.makedirs(self.destdirname)
    def abs_src_path(self, filename):
        return self.dirname + os.path.sep + filename

    def abs_dest_path(self, filename):
        return self.destdirname + os.path.sep + filename


class ExifFileReader(object):

    # create logger
    logger = logging.getLogger('ExifFileReader')
    logger.setLevel(logging.WARNING)

    def __init__(self, filename):
        self.filename = filename

    # returned date format YYYY-mm-dd
    def readExifDate(self):
        date = ""
        #open file, do EXIF stuf
        with open(self.filename,'rb') as file:
            data=exifread.process_file(file)
            self.logger.debug(data)
        if data:
            exifDateTimeField = data.get('EXIF DateTimeOriginal', "")
            if exifDateTimeField:
                self.logger.debug(self.filename + " - " + str(exifDateTimeField))
                date = str(exifDateTimeField).replace(":", "-").split()[0]
                self.logger.debug(date)
            else:
                self.logger.debug("no EXIF DateTimeOriginal field in the EXIF data")
        else:
            self.logger.debug("no EXIF in file {}".format(self.filename))

        return date

class Stats(object):
    # create logger
    logger = logging.getLogger('Stats')
    logger.setLevel(logging.WARNING)

    def __init__(self):
        self.stats = {}

    def report(self, key, name):
        dirStats = self.stats.get(key, {})
        curr = dirStats.get(name, 0)
        dirStats[name]=curr + 1
        self.stats[key]=dirStats

    def __repr__(self):
        str = []
        if self.stats:
            str.append("\nSummary: \n")
            for cdir, cdirStats in self.stats.items():
                str.append("\nDirectory {}".format(cdir))
                for op, count in cdirStats.items():
                    str.append("\t{} files {}".format(count, op))
        else:
            str.append("\nNo stats were updated.")

        out_str = ''.join(str)
        return out_str

def create_directories(args, date):
    # get year from date
    year = date.split("-")[0]
    dst_dir_path = args.abs_dest_path(year + os.path.sep + date)
    # check if dir with date exists, if not create it
    if not os.path.isdir(dst_dir_path):
        logger.info ("destination directory {} does not exist, creating it...".format(dst_dir_path))
        os.makedirs(dst_dir_path)
        print ("Created dir {}".format(dst_dir_path))
    return dst_dir_path

def handle_file(args, stats, file):
    logger.debug("Handling file {} ...".format(file))

    src_file_path = args.abs_src_path(file)

    exifReader = ExifFileReader(src_file_path)

    exifDate = exifReader.readExifDate()
    (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)

    # by default, use modified data in format
    date = datetime.fromtimestamp(mtime).isoformat()
    if exifDate:
        # exif date if exists
        date = exifDate

    if date:
        dst_dir_path = create_directories(args, date)
        dst_file_path = dst_dir_path + os.path.sep + file


        if os.path.isfile(dst_file_path):
            # files with the same name exist
            # check their hashes, whether they are the same
            currfileHash = md5(src_file_path)
            newfileHash = md5(dst_file_path)
            if currfileHash == newfileHash:
                logger.debug("file {} already exists, thus it will not be moved.".format(dst_file_path))
                stats.report(dst_dir_path, 'existed')
            else:
                logger.debug("file {} already exists, but the source file {} itself is different, will be moved with different name".format(dst_file_path, src_file_path))
                i = 1
                new_dst_file_name = dst_file_path+'_'+str(i)
                while os.path.isfile(new_dst_file_name):
                    logger.debug("file {} already exists, incrementing 1 to suffix")
                    i = i + 1
                    new_dst_file_name = dst_file_path+'_'+str(i)

                shutil.move(src_file_path, new_dst_file_name)
                stats.report(dst_dir_path, 'renamed')


        else:
            shutil.move(src_file_path, dst_file_path)
            logger.debug("file {} moved to {}".format(src_file_path, dst_file_path))
            stats.report(dst_dir_path, 'moved')


def handle_dir(args, stats, dir):
    logger.debug("Handling dir {} ...".format(dir))
    for root, subdirs, files in os.walk(dir):
        logger.debug(files)
        for f in files:
            handle_file(args, stats, f)

        for subdir in subdirs:
            handle_dir(args, stats, subdir)



def main(argv):

    args = InputArguments(argv)

    stats = Stats()

    handle_dir(args, stats, args.dirname)

    print stats





def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


if __name__ == "__main__":
    main(sys.argv)