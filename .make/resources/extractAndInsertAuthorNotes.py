import os.path
import re
import sys


# Create dict of author notes for each version (as written in the md header) if
# they exist in CHANGELOG.md, e.g:
# {
#   "## [0.4.24]":  "
#                   ### Author Notes\n\nSome notes for version 0.4.24\n
#                   line 2 with more notes
#                   ",
#   "## [0.4.23]":  "
#                   ### Author Notes\n\nSome notes for version 0.4.23\n
#                   line 2 with more notes
#                   "
# }
def get_author_notes():
    if os.path.isfile(changelogFile):
        with open(changelogFile) as changelog:
            readingNotes = False
            authorNotes = ""
            version = ""
            for line in changelog:
                if readingNotes and re.search("^#+ .*", line):
                    allNotes[version] = authorNotes.strip()
                    readingNotes = False
                    authorNotes = ""

                matchVersion = re.search(r"(^## \[(\d+.\d+.\d+)*\].*$)", line)
                if matchVersion:
                    version = matchVersion.group(1).strip()

                matchNotes = re.search("^### Author Notes.*$", line)
                if matchNotes:
                    readingNotes = True
                    authorNotes += line

                elif readingNotes:
                    authorNotes += line

        if authorNotes != "":
            allNotes[version] = authorNotes.strip()

    return allNotes


# Write author notes obtained from get_author_notes() to CHANGELOG.md under the
# correct header
def insert_author_notes(authorNotes):
    if os.path.isfile(changelogFile):
        if os.path.isfile(tempChangelogFile):
            with open(tempChangelogFile, "r") as changelog:
                contents = changelog.readlines()

            with open(tempChangelogFile, "w") as changelog:
                for line in contents:
                    changelog.write(line)
                    if re.search(r"(^## \[(\d+.\d+.\d+)*\].*$)", line):
                        if line.strip().strip("\n") in authorNotes:
                            changelog.writelines(
                                "\n"
                                + authorNotes[line.strip().strip("\n")].strip(
                                    "\n"
                                )
                                + "\n"
                            )


if __name__ == "__main__":
    changelogFile = sys.argv[1]
    tempChangelogFile = sys.argv[2]
    allNotes = {}

    authorNotes = get_author_notes()
    insert_author_notes(authorNotes)
