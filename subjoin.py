#!/usr/bin/env python

#    SubJoin
#    
#    Copyright 2019 Libère

VERSION = "0.0.2"

# Subtitle Extensions
SUB_EXT = [ 'srt', 'ssa', 'sub' ]

# Video File Extensions
VID_EXT = [ 'mkv', 'webm', 'avi', 'mp4' ]

# Language Codes
ISO_EXT = [ 'en', 'eng', 'de', 'fr', 'jp', 'ch', 'sw', 'hu', 'pt', 'pb', 'spa', 'es' ]

### DUDE, ONLY CHANGE BELOW THIS LINE IF YOU WELL KNOW WHAT YOU ARE DOING ###

import sys
import os
import re
import subprocess
import shutil
from optparse import OptionParser

# Parse Command Line Options
usage = "usage: %prog [options] files"
parser = OptionParser(usage=usage, version="%prog "+VERSION)
parser.add_option("-r", "--remove-backup", dest="remove_backup", help="Remove backup files in the end", action="store_true")
parser.add_option("-f", "--find-missing", dest="find_missing", help="Find files without merged subtitles", action="store_true")
parser.add_option("-d", "--debug", dest="debug", help="show debugging output", action="store_true")
parser.add_option("-n", "--dry-run", dest="dryrun", help="do not actually merge anything", action="store_true")
parser.set_defaults(
	remove_backup = False,
	find_missing = False,
	debug = False,
        dryrun=False
)
(opt, args) = parser.parse_args()

s_ext = '(' + '|'.join(SUB_EXT) + ')'
v_ext = '(' + '|'.join(VID_EXT) + ')'
i_ext = '(' + '|'.join(ISO_EXT) + ')'


def check_for_mkvmerge():
	try:
		output = subprocess.check_output(['mkvmerge', '--version'])
		if not output.startswith('mkvmerge'):
			print "Please install mkvmerge (mkvtoolnix package)!"
			sys.exit(1)
	except OSError:
		print "Please install mkvmerge (mkvtoolnix package)!"
		sys.exit(1)


def merge_file(video_file, subs, lang='en'):
        print
        print "Merging: " + video_file
        for sub in subs:
            print "         " + sub
        print

        if opt.dryrun:
            return False

        # Check extension
        output_file = video_file
        m = re.search('.+\.(?P<ext>mkv|webm)$', video_file)
        if m:
            # Check for existing subtitles
            if has_subtitles(video_file):
                print 'Error: File "' + video_file + '" already contains subtitles.'
                print
                return
        else:
            output_file = video_file.rpartition('.')[0] + '.mkv'

        # Create Backup Folder
        try:
            os.mkdir('backup')
        except OSError:
            pass
        # Move Video File Into Backup Folder
        video_file_bak = 'backup/' + video_file
        os.rename(video_file, video_file_bak)

        command = ['mkvmerge', '--output', output_file, video_file_bak] + subs
	
        if opt.debug:
            print "Running: " + ' '.join(command)

        returncode = subprocess.call(command, shell=False)

        if returncode == 0:
            # Move Subtitle File Into Backup Folder
            for sub in subs:
                os.rename(sub, "backup/" + sub)
            return True
        else:
            print "ERROR: mkvmerge returned with error."
            os.rename(video_file_bak, video_file)
            return False


def find_subtitle_less_files(files):
	vid_reg = re.compile('.+\.(mkv|webm)$')
	
	print "These files are missing subtitles:"

	for f in files:
		if vid_reg.match(f):
			if not has_subtitles(f):
				print " (sub missing) " + f
		else:
  			print " (no sub file) " + f


# only call on mkv or webm files
def has_subtitles(video_file):
	command = ['mkvinfo', video_file]

	if opt.debug:
		print "Running: " + ' '.join(command)

	output = subprocess.check_output(command, shell=False)
	if re.search('Track type: subtitles', output):
		return True

	return False


def find_subs_for_video(files, name):
    subs = []

    for f in files:
        m = re.search(re.escape(name) + '([_.]' + i_ext + ')?\.' + s_ext + '$', f, re.IGNORECASE)
	if m:
            subs.append(f)

    return subs


def merge_files(files):
	# Go Through Found Video Files
	for f in files:
		m = re.search('(?P<name>.+?)\.' + v_ext + '$', f)

		# if we found a video file
		if m:
		    # find matching subtitle files for the current video file
                    subs = find_subs_for_video(files, m.group('name'))

		    merge_result = False

                    if len(subs) > 0:
		        # we found matching subtitle files, so merge them
			merge_result = merge_file(f, subs)

#                        if merge_result and os.path.isfile(sf):
#				print
#				print "ERROR: No Video found for file: " + sf
#				print
                    else:
                        print
                        print "Warning: No Subtitle found for video: %s" % f
                        print

	if opt.remove_backup:
		print "Removing backup files..."
		shutil.rmtree("backup/")


def main():
	check_for_mkvmerge()
	
	files = sorted(args)
	if len(files) < 1:
		print "Please give one or more files as arguments."
		sys.exit(1)

	if opt.find_missing:
		find_subtitle_less_files(files)
	else:
		merge_files(files)

	sys.exit()


if __name__ == "__main__":
	main()
