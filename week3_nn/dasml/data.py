# coding: utf-8

"""
Helpers for handling the input data.
"""

import os
import shutil

import numpy as np
import six

from dasml import util, specs


def _check_dataset_file(kind, index):
    # validate the kind
    kinds = ("train", "valid", "test", "challenge")
    if kind not in kinds:
        raise ValueError("unknown dataset kind '{}', must be one of {}".format(
            kind, ",".join(kinds)))

    # validate the index
    if not (0 <= index < specs.n_files[kind]):
        raise ValueError("dataset '{}' has no file index {}".format(kind, index))

    return "{}_{}.npz".format(kind, index)


def provide_file(kind, index):
    """
    Returns the absolute file path of a file of an input dataset given by *kind* ("train", "valid",
    "test", or "challenge") and its *index*. When the file is not locally accessible, it is
    downloaded from the public CERNBox directory.
    """
    # get the name of the file
    file_name = _check_dataset_file(kind, index)

    # make sure the user data directory exists
    if not os.path.exists(specs.data_dir):
        os.makedirs(specs.data_dir)

    # when it's already in the user data directy, return the full path
    file_path = os.path.join(specs.data_dir, file_name)
    if os.path.exists(file_path):
        return file_path

    # when the public data dir is accessible via eos, copy the file in the the user data dir
    has_eos = specs.swan_data_dir and os.access(specs.swan_data_dir, os.R_OK)
    if has_eos:
        public_path = os.path.join(specs.swan_data_dir, file_name)
        shutil.copy2(public_path, file_path)
        return file_path

    # otherwise, download it using the public CERNBox url
    quote = six.moves.urllib.parse.quote
    cernbox_path = specs.cernbox_dl_pattern.format(quote("/", safe=""), quote(file_name, safe=""))
    util.download(cernbox_path, file_path)
    return file_path


def load(kind, start_file=0, stop_file=-1):
    """
    Loads a certain *kind* of dataset ("train", "valid", "test", or "challenge") and returns the
    four-vectors of the jet constituents, the true jet four-vector and the truth label in a 3-tuple.
    When *kind* is *challenge*, the two latter elements of the returned tuple are *None*.
    Internally, each dataset consists of multiple files whose arrays are automatically concatenated.
    For faster prototyping and testing, *start_file* (included) and *stop_file* (first file that is
    *not* included) let you define the range of files to load.
    """
    # fix the file range if necessary
    if stop_file < 0:
        stop_file = specs.n_files[kind] - 1

    # get all local file paths via download or public access
    file_paths = [provide_file(kind, i) for i in range(start_file, stop_file)]

    # instead of loading all files, storing their contents and concatenating in the end, which can
    # have a peak memory consumption of twice the inputs, define output arrays with the correct
    # dimensions right away and fill it while iterating through files
    n_events = len(file_paths) * specs.n_events_per_file
    load_truth = kind != "challenge"
    c_vecs = np.zeros((n_events, specs.n_constituents, 4), dtype=np.float32)
    j_vecs = np.zeros((n_events, 4), dtype=np.float32) if load_truth else None
    labels = np.zeros((n_events,), dtype=np.float32) if load_truth else None

    # open files and fill arrays
    for i, file_path in enumerate(file_paths):
        start = i * specs.n_events_per_file
        stop = start + specs.n_events_per_file

        data = np.load(file_path)
        c_vecs[start:stop, ...] = data["constituents"]
        if load_truth:
            j_vecs[start:stop, ...] = data["truth_jet"]
            labels[start:stop, ...] = data["truth_label"]
        data.close()

    return c_vecs, j_vecs, labels
