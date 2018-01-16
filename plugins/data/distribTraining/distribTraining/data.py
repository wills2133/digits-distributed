#!/bin/bash

# Copyright (c) 2016-2017, NVIDIA CORPORATION.  All rights reserved.
from __future__ import absolute_import

import cv2
import fnmatch
import math
import os
import random
import re
import shutil

import dicom
import numpy as np

from digits.utils import subclass, override, constants
from digits.utils.constants import COLOR_PALETTE_ATTRIBUTE
from digits.extensions.data.interface import DataIngestionInterface
from .forms import DatasetForm, InferenceForm

import sys

DATASET_TEMPLATE = "templates/dataset_template.html"
INFERENCE_TEMPLATE = "templates/inference_template.html"

#
# Utility functions
#

@subclass
class DataIngestion(DataIngestionInterface):
    """
    A data ingestion extension for cloud training
    """
    def __init__(self, is_inference_db=False, **kwargs):
        super(DataIngestion, self).__init__(**kwargs)


    def process_dataset(job_dir):
        dataset_dir = self.userdata['server_dataset_folder']
        dataset_dir_file = job_dir + '/dataset_dir.txt'

        if not os.path.exists(job_dir):
            print 'job_dir not found!'
            print 'create job_dir!'
            os.mkdir(job_dir)
        f = open(dataset_dir_file, 'w')
        f.write(dataset_dir)
        f.close()

    def get_dataset_addr(self, entry):
        return self.userdata['dataset_server_ip'], self.userdata['dataset_server_port']

    @staticmethod
    @override
    def get_category():
        return "Images"

    @staticmethod
    @override
    def get_id():
        return "CloudTraining"

    @staticmethod
    @override
    def get_dataset_form():
        return DatasetForm()

    @staticmethod
    @override
    def get_dataset_template(form):
        """
        parameters:
        - form: form returned by get_dataset_form(). This may be populated
           with values if the job was cloned
        return:
        - (template, context) tuple
          - template is a Jinja template to use for rendering dataset creation
          options
          - context is a dictionary of context variables to use for rendering
          the form
        """
        extension_dir = os.path.dirname(os.path.abspath(__file__))
        template = open(os.path.join(extension_dir, DATASET_TEMPLATE), "r").read()
        context = {'form': form} #context for template to reference
        return (template, context)

    @staticmethod
    @override
    def get_inference_template(form):
        extension_dir = os.path.dirname(os.path.abspath(__file__))
        template = open(os.path.join(extension_dir, INFERENCE_TEMPLATE), "r").read()
        context = {'form': form}
        return (template, context)

    @staticmethod
    @override
    def get_title():
        return "CloudTraining"

