#!/bin/bash

# Copyright (c) 2016-2017, NVIDIA CORPORATION.  All rights reserved.
from __future__ import absolute_import

import cv2
import fnmatch
import math
import os
from digits.utils import subclass, override, constants
from digits.extensions.data.interface import DataIngestionInterface
from .forms import DatasetForm, InferenceForm

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


    def process_dataset(self, job_dir):
        dataset_dir = self.userdata['server_dataset_folder']
        server_ip = self.userdata['dataset_server_ip']
        server_port = self.userdata['dataset_server_port']
        server_job_info = job_dir + '/server_job_info.txt'

        if not os.path.exists(job_dir):
            print 'job_dir not found!'
            print 'create job_dir!'
            os.mkdir(job_dir)
        f = open(server_job_info, 'w')
        f.write(server_ip+'\n')
        f.write(server_port+'\n')
        f.write(dataset_dir+'\n')
        f.close()

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

