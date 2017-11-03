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


DATASET_TEMPLATE = "templates/dataset_template.html"
INFERENCE_TEMPLATE = "templates/inference_template.html"

# This is the subset of SAX series to use for Left Ventricle segmentation
# in the challenge training dataset
SAX_SERIES = {

    "SC-HF-I-1": "0004",
    "SC-HF-I-2": "0106",
    "SC-HF-I-4": "0116",
    "SC-HF-I-40": "0134",
    "SC-HF-NI-3": "0379",
    "SC-HF-NI-4": "0501",
    "SC-HF-NI-34": "0446",
    "SC-HF-NI-36": "0474",
    "SC-HYP-1": "0550",
    "SC-HYP-3": "0650",
    "SC-HYP-38": "0734",
    "SC-HYP-40": "0755",
    "SC-N-2": "0898",
    "SC-N-3": "0915",
    "SC-N-40": "0944",
}

#
# Utility functions
#

"""
def shrink_case(case):
    toks = case.split("-")

    def shrink_if_number(x):
        try:
            cvt = int(x)
            return str(cvt)
        except ValueError:
            return x
    return "-".join([shrink_if_number(t) for t in toks])


class Contour(object):

    def __init__(self, ctr_path):
        self.ctr_path = ctr_path
        match = re.search(r"/([^/]*)/contours-manual/IRCCI-expert/IM-0001-(\d{4})-icontour-manual.txt", ctr_path)
        self.case = shrink_case(match.group(1))
        self.img_no = int(match.group(2))

    def __str__(self):
        return "<Contour for case %s, image %d>" % (self.case, self.img_no)

    __repr__ = __str__


def get_all_contours(contour_path):
    # walk the directory structure for all the contour files
    contours = [
        os.path.join(dirpath, f)
        for dirpath, dirnames, files in os.walk(contour_path)
        for f in fnmatch.filter(files, 'IM-0001-*-icontour-manual.txt')
    ]
    extracted = map(Contour, contours)
    return extracted


def load_contour(contour, img_path):
    filename = "IM-%s-%04d.dcm" % (SAX_SERIES[contour.case], contour.img_no)
    full_path = os.path.join(img_path, contour.case, filename)
    img = load_image(full_path)
    ctrs = np.loadtxt(contour.ctr_path, delimiter=" ").astype(np.int)
    label = np.zeros_like(img, dtype="uint8")
    cv2.fillPoly(label, [ctrs], 1)
    return img, label


def load_image(full_path):
    f = dicom.read_file(full_path)
    return f.pixel_array.astype(np.int)
"""

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

        self.userdata['is_inference_db'] = is_inference_db

        self.userdata['class_labels'] = ['background', 'left ventricle']

        # get list of contours
        # if 'contours' not in self.userdata:
        #     contours = get_all_contours(self.voc_folder)
        #     random.shuffle(contours)
        #     self.userdata['contours'] = contours
        # else:
        #     contours = self.userdata['contours']

        # get number of validation entries
        # pct_val = int(self.folder_pct_val2)
        # self.userdata['n_val_entries'] = int(math.floor(len(contours) * pct_val / 100))

        # label palette (0->black (background), 1->white (foreground), others->black)
        # palette = [0, 0, 0,  255, 255, 255] + [0] * (254 * 3)
        # self.userdata[COLOR_PALETTE_ATTRIBUTE] = palette



    """
    this instance method is the core of the data plug-in: 
    it reads data associated with one of the identifiers returned in itemize_entries 
    and converts the data into a 3-dimensional Numpy array. 
    This function also returns a label, which may be either a scalar or another 3-dimensional Numpy array. 
    Note how the process of reading an image in a DICOM file is relatively straightforward: 
    f = dicom.read_file(full_path)img = f.pixel_array.astype(np.int)
    """
    @override
    def encode_entry(self, entry):
        # if isinstance(entry, basestring): #entry: path
        #     img = load_image(entry)
        #     label = np.array([0])
        # else:
        #     img, label = load_contour(entry, self.image_folder)
        #     label = label[np.newaxis, ...]

        # if self.userdata['channel_conversion'] == 'L':
        #     feature = img[np.newaxis, ...]
        # elif self.userdata['channel_conversion'] == 'RGB':
        #     feature = np.empty(shape=(3, img.shape[0], img.shape[1]), dtype=img.dtype)
        #     # just copy the same data over the three color channels
        #     feature[0] = img
        #     feature[1] = img
        #     feature[2] = img
        feature = []
        label = []
        print 'dataset_dir', entry
        # print 'bash /home/wills/.local/lib/python2.7/site-packages/digitsDataPluginSunnybrook/create_list.sh %s %s' % (voc_path, dataset_dir)
        os.system( 'bash /usr/local/lib/python2.7/site-packages/digitsSSD/scripts/create_list.sh %s %s' % (self.userdata['voc_folder'], entry) )

        # print 'bash /home/wills/.local/lib/python2.7/site-packages/digitsDataPluginSunnybrook/create_data.sh %s %s' % (voc_path, dataset_dir)
        os.system( 'bash //usr/local/lib/python2.7/site-packages/digitsSSD/scripts/create_data.sh %s %s' % (self.userdata['voc_folder'], entry) )
        shutil.copy('/home/wills/.local/lib/python2.7/site-packages/digitsSSD/scripts/labelmap_voc.prototxt', entry)
        return feature, label

    @staticmethod
    @override
    def get_category():
        return "Images"

    @staticmethod
    @override
    def get_id():
        return "ssd_pascal"


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
        return "ssd_pascal"


    """
    this instance method parses form fields in order to generate a list of data sample identifiers. 
    For example, if your data plug-in needs to encode all the files in a directory 
    then the itemized entries could be a list of all the filenames.
    """
    @override
    def itemize_entries(self, stage):
        # ctrs = self.userdata['contours']
        # n_val_entries = self.userdata['n_val_entries']

        entries = []
        # if not self.userdata['is_inference_db']:
            # if stage == constants.TRAIN_DB:
            #     entries = ctrs[n_val_entries:]
            # elif stage == constants.VAL_DB:
            #     entries = ctrs[:n_val_entries]
        # elif stage == constants.TEST_DB:
            # if self.userdata['validation_record'] != 'none':
            #     if self.userdata['test_image_file']:
            #         raise ValueError("Specify either an image or a record "
            #                          "from the validation set.")
            #     # test record from validation set
            #     entries = [ctrs[int(self.validation_record)]]
            # else:
                # test image file
                # entries = [self.userdata['test_image_file']]


        # os.system('bash /home/wills/.local/lib/python2.7/site-packages/digitsDataPluginSunnybrook/create_list.sh %s' % self.userdata['voc_folder'])

        return self.userdata['voc_folder']
