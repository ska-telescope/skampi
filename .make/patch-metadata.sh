#!/bin/bash
# ========================================================================
# IMPORTANT: This scrip file is now deprecated. Any call to patch metadata
# should be done with the metadataPatch function on .make-metadata-support
# ========================================================================
# 
# Adds the metadata file to archive
#
# Arguments:
# $1: Archive file
# $2: Metadata file
#
# Supported archive types: zip, egg, whl, gz
#
# Usage:
# patch-metadata.sh <ARCHIVE_FILE> <METADATA_FILE_NAME>
#
# Example Usage:
# # Create manifest file: extract-metadata.sh MANIFEST.skao.int
#
# patch-metadata.sh python-package-0.1.2-py3-none-any.whl MANIFEST.skao.int
#

set -e
set -o pipefail

base=$(pwd)

if [ -z "$1" ]; then
    echo "No archive file specified - aborting!"
    exit 1
else
    THE_ARCHIVE=$(readlink -f $1)
fi

if [ ! -f "${THE_ARCHIVE}" ]; then
    echo "Archive does not exist: ${THE_ARCHIVE} - aborting."
    exit 1
fi

filename=$(basename -- "${THE_ARCHIVE}")
extension="${filename##*.}"
filename="${filename%.*}"
directory=$(dirname -- "${THE_ARCHIVE}")
fullfilename=${directory}"/"${filename}
echo "Archive is: ${THE_ARCHIVE} of type: ${extension}"

if [ -z "$2" ]; then
    echo "No metadata file specified - aborting!"
    exit 1
else
    THE_METADATA=$2
fi

if [ ! -f "${THE_METADATA}" ]; then
    echo "Metadata file does not exist: ${THE_METADATA} - aborting."
    exit 1
fi
echo "MANIFEST is: ${THE_METADATA}"


# layout the metadata directory structure for the file type
tmp_dir=$(mktemp -d -t metadata.XXXXXXXXXX)
case "${extension,,}" in
    "zip") cp ${THE_METADATA} ${tmp_dir}/;;
    "egg") mkdir ${tmp_dir}/EGG-INFO; cp ${THE_METADATA} ${tmp_dir}/EGG-INFO/;;
    "whl") dist_info=$(unzip -l ${THE_ARCHIVE} | grep 'dist-info/WHEEL' | awk '{print $4}' | sed 's/\/WHEEL//'); mkdir ${tmp_dir}/${dist_info}; cp ${THE_METADATA} ${tmp_dir}/${dist_info}/;;
    "tgz");;
    "gz");;
    *) echo "Unrecognised file type - aborting"; exit 1;;
esac

if [ "${extension,,}" == ("gz" || "tgz") ]; then
    gunzip ${THE_ARCHIVE}
    tar -rf ${fullfilename} ${THE_METADATA}
    gzip -f ${fullfilename} > ${THE_ARCHIVE}
else
    cd ${tmp_dir}
    echo working on ${tmp_dir}
    zip -ur ${THE_ARCHIVE} *
fi

rm -rf ${tmp_dir}

exit 0
