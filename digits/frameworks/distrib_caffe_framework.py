### derived by wills
from __future__ import absolute_import


from digits.config import config_value
from . import CaffeFramework
from digits.model.tasks import DistributedTrainTask
from digits.utils import subclass, override, parse_version

@subclass
class DistributedCaffeFramework(CaffeFramework):
    """
    derive from CaffeFramework, use for training in long-distance server
    """
    """
    Defines required methods to interact with the Caffe framework
    This class can be instantiated as many times as there are compatible
    instances of Caffe
    """

    # short descriptive name
    NAME = 'Caffe'

    # identifier of framework class (intended to be the same across
    # all instances of this class)
    CLASS = 'caffe'

    # whether this framework can shuffle data during training
    CAN_SHUFFLE_DATA = False
    SUPPORTS_PYTHON_LAYERS_FILE = True
    SUPPORTS_TIMELINE_TRACING = False

    if config_value('caffe')['flavor'] == 'NVIDIA':
        if parse_version(config_value('caffe')['version']) > parse_version('0.14.0-alpha'):
            SUPPORTED_SOLVER_TYPES = ['SGD', 'NESTEROV', 'ADAGRAD',
                                      'RMSPROP', 'ADADELTA', 'ADAM']
        else:
            SUPPORTED_SOLVER_TYPES = ['SGD', 'NESTEROV', 'ADAGRAD']
    elif config_value('caffe')['flavor'] == 'BVLC':
        SUPPORTED_SOLVER_TYPES = ['SGD', 'NESTEROV', 'ADAGRAD',
                                  'RMSPROP', 'ADADELTA', 'ADAM']
    else:
        raise ValueError('Unknown flavor.  Support NVIDIA and BVLC flavors only.')

    SUPPORTED_DATA_TRANSFORMATION_TYPES = ['MEAN_SUBTRACTION', 'CROPPING']
    SUPPORTED_DATA_AUGMENTATION_TYPES = []

    @override
    def __init__(self):
        super(CaffeFramework, self).__init__()
        self.framework_id = self.CLASS

    @override
    def create_train_task(self, **kwargs):
        """
        create train task
        """
        print 'return DistributedTrainTask'
        return DistributedTrainTask(framework_id=self.framework_id, **kwargs)