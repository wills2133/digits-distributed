# Copyright (c) 2016-2017, NVIDIA CORPORATION.  All rights reserved.
from __future__ import absolute_import

import os

from digits import utils
from digits.utils import subclass
from flask.ext.wtf import Form
from wtforms import validators


@subclass
class DatasetForm(Form):
    """
    A form used to create a Sunnybrook dataset
    """

    def validate_folder_path(form, field):
        if not field.data:
            pass
        else:
            # make sure the filesystem path exists
            if not os.path.exists(field.data) or not os.path.isdir(field.data):
                raise validators.ValidationError(
                    'Folder does not exist or is not reachable')
            else:
                return True


    dataset_server_ip = utils.forms.StringField(
        'Dataset server ip',
        validators=[
        ],
        tooltip="Dataset server ip in format 'xxx.xxx.xxx.xxx'."
    )

    dataset_server_port = utils.forms.StringField(
        'Dataset server port',
        validators=[
        ],
        tooltip="Dataset server port in format 'xxxx'."
    )

    server_dataset_folder = utils.forms.StringField(
        u'Server Dataset Folder',
        validators=[
            # validators.DataRequired(),
            # validate_folder_path,
        ],
        tooltip="Specify the path to the dataset folder in training server to upload"
    )

@subclass
class InferenceForm(Form):

    def validate_file_path(form, field):
        if not field.data:
            pass
        else:
            # make sure the filesystem path exists
            if not os.path.exists(field.data) and not os.path.isdir(field.data):
                raise validators.ValidationError(
                    'File does not exist or is not reachable')
            else:
                return True
    """
    A form used to perform inference on a text classification dataset
    """
    test_image_file = utils.forms.StringField(
        u'Image file',
        validators=[
            validate_file_path,
        ],
        tooltip="Provide the (server) path to an image."
    )

    validation_record = utils.forms.SelectField(
        'Record from validation set',
        choices=[
            ('none', '- select record -'),
        ],
        default='none',
        tooltip="Test a record from the validation set."
    )
