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
    A data ingestion extension for the Sunnybrook dataset
    """
    """
    this is the initialization routine used to create an instance of the class. 
    During initialization this is provided with two parameters. 
    The first parameter is named is_inference_db and indicates whether this instance is going to be used during inference. 
    The second parameter is a dictionary that contains all the form fields 
    that were specified by the user either during dataset creation or when specifying data options for inference.
    """
    def __init__(self, is_inference_db=False, **kwargs):
        super(DataIngestion, self).__init__(**kwargs)

    """
    this instance method is the core of the data plug-in: 
    it reads data associated with one of the identifiers returned in itemize_entries 
    and converts the data into a 3-dimensional Numpy array. 
    This function also returns a label, which may be either a scalar or another 3-dimensional Numpy array. 
    Note how the process of reading an image in a DICOM file is relatively straightforward: 
    f = dicom.read_file(full_path)img = f.pixel_array.astype(np.int)
    """

    def process_dataset(job_dir):
        dataset_dir = self.userdata['voc_folder']
        dataset_dir_file = job_dir + '/dataset_dir.txt'
        if os.path.exists(dataset_dir_file):
                f = open(dataset_dir_file, 'w')
                f.write(dataset_dir)
                f.close()
    @override
    def encode_entry(self, entry):
        feature = []
        label = []
        dataset_dir = self.userdata['voc_folder']
        job_dir = entry
        dataset_dir_file = job_dir + '/dataset_dir.txt'
        # print 'dataset_dir', entry
        
        if os.path.exists(dataset_dir_file):
            f = open(dataset_dir_file, 'w')
            f.write(dataset_dir)
            f.close()
        # find_path = False 
        # for p in sys.path:
            
            # plug_in_path = p + '/digitsSSD/scripts'
            # if os.path.exists(plug_in_path):
                # # print ( 'bash ' + plug_in_path + '/create_list.sh ' + self.userdata['voc_folder'] + ' ' +  entry) )
                # os.system( 'bash ' + plug_in_path + '/create_list.sh ' + self.userdata['voc_folder'] + ' ' +  entry )
                # # print ( 'bash ' + plug_in_path + '/create_data.sh ' + self.userdata['voc_folder'] + ' ' +  entry )

                # os.system( 'bash ' + plug_in_path + '/create_data.sh ' + self.userdata['voc_folder'] + ' ' +  entry )
                # shutil.copy( (plug_in_path + '/labelmap_voc.prototxt'), entry)
        #         find_path = True
        #         break;
         
        # if not find_path:
        #     print 'no match plugin path found'
            
        return feature, label

    @staticmethod
    @override
    def get_category():
        return "Images"

    @staticmethod
    @override
    def get_id():
        return "distribDataset"


    """
    this is a static method that returns a form (a child of flask.ext.wtf.Form) 
    which contains all the fields required to create a dataset. 
    For example a form may include text fields to allow users 
    to specify file names or various dataset options.
    """
    @staticmethod
    @override
    def get_dataset_form():
        return DatasetForm()



    """
    this is a static method that returns a Jinja template 
    for the form to display in the DIGITS web user interface; 
    this method also returns a dictionary of context variables 
    that should include all the variables that are referenced in the Jinja template. 
    For example, the Sunnybrook plug-in gives form as context 
    because the Jinja template references this variable to render the form into the web user interface.
    """
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


    """
    this is similar to get_dataset_form but this is used 
    when showing data ingestion options during inference. 
    Note that this method may return None to indicate 
    that your data plug-in cannot be operated during inference. 
    In this case, it is expected that the regular image inference option 
    in DIGITS will work for the model you are training.
    """
    @override
    def get_inference_form(self):
        # n_val_entries = self.userdata['n_val_entries']
        # form = InferenceForm()
        # for idx, ctr in enumerate(self.userdata['contours'][:n_val_entries]):
        #     form.validation_record.choices.append((str(idx), ctr.case))
        return form

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
        return "distribDataset"


    """
    this instance method parses form fields in order to generate a list of data sample identifiers. 
    For example, if your data plug-in needs to encode all the files in a directory 
    then the itemized entries could be a list of all the filenames.
    """
    @override
    def itemize_entries(self, stage):
        return self.userdata['voc_folder']
