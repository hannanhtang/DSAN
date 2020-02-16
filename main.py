from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os
import shutil
import numpy as np
from utils.tools import write_result

parser = argparse.ArgumentParser(description='Hyperparameters')
parser.add_argument('--dataset', default='taxi', help='taxi or bike or ctm')
parser.add_argument('--gpu_ids', default='0, 1, 2, 3', help='indexes of gpus to use')
parser.add_argument('--memory_growth', default=True)
parser.add_argument('--index', default=11, help='indexes of model to be trained')
parser.add_argument('--test_name', default="new_arch")
parser.add_argument('--hyp', default=[1])
parser.add_argument('--run_time', default=3)
parser.add_argument('--remove_old_files', default=False)
parser.add_argument('--load_saved_data', default=False)
parser.add_argument('--no_save', default=False)
parser.add_argument('--test_model', default=None)
parser.add_argument('--mixed_precision', default=False)
parser.add_argument('--always_test', default=None)

""" Model hyperparameters """
d_model = 64
parser.add_argument('--num_layers', default=3, help='num of self-attention layers')
parser.add_argument('--d_model', default=d_model, help='model dimension')
parser.add_argument('--dff', default=d_model * 4, help='dimension of feed-forward networks')
parser.add_argument('--num_heads', default=8, help='number of attention heads')
parser.add_argument('--dropout_rate', default=0.1)
parser.add_argument('--cnn_layers', default=1)
parser.add_argument('--cnn_filters', default=d_model)

""" Training settings """
weights_t = np.array([1 for _ in range(12)], dtype=np.float32)[:, np.newaxis]
weights_f = np.array([1 for _ in range(2)], dtype=np.float32)[np.newaxis, :]
weights = weights_t * weights_f
parser.add_argument('--MAX_EPOCH', default=250)
parser.add_argument('--BATCH_SIZE', default=128)
parser.add_argument('--warmup_steps', default=4000)
parser.add_argument('--verbose_train', default=1)
parser.add_argument('--weights', default=weights)
parser.add_argument('--es_patience', default=10)
parser.add_argument('--es_threshold', default=0.01)

""" Data hyperparameters """
parser.add_argument('--n_hist_week', default=1, help='num of previous weeks to consider')
parser.add_argument('--n_hist_day', default=3, help='num of previous days to consider')
parser.add_argument('--n_hist_int', default=1, help='num of time in previous days to consider')
parser.add_argument('--n_curr_int', default=1, help='num of time in today to consider')
parser.add_argument('--n_int_before', default=0, help='num of time before predicted time to consider')
parser.add_argument('--n_pred', default=12, help='future time to predict')
parser.add_argument('--l_half', default=3)
parser.add_argument('--l_half_g', default=None)
parser.add_argument('--pre_shuffle', default=True)
parser.add_argument('--same_padding', default=False)
parser.add_argument('--st_revert', default=False)

args = parser.parse_args()


def write_args(args, m_ind):
    result_output_path = "results/dsan/{}.txt".format(m_ind)
    write_result(result_output_path, str(args))

def remove_oldfiles(model_index):
    try:
        shutil.rmtree('./checkpoints/dsan/{}'.format(model_index), ignore_errors=True)
    except:
        pass
    try:
        os.remove('./results/dsan/{}.txt'.format(model_index))
    except:
        pass
    try:
        shutil.rmtree(os.environ['HOME'] + '/tensorboard/dsan/{}'.format(model_index), ignore_errors=True)
    except:
        pass

if args.mixed_precision:
    os.environ['TF_ENABLE_AUTO_MIXED_PRECISION'] = '1'
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_ids

assert args.dataset in ['taxi', 'bike', 'ctm']
print("Dataset chosen: {}".format(args.dataset))

from train import TrainModel
import tensorflow as tf
import tensorflow.keras.backend as K

gpus = tf.config.experimental.list_physical_devices('GPU')

if gpus and args.memory_growth:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

if not os.path.exists('./results/dsan'):
    os.makedirs('./results/dsan')

if __name__ == "__main__":
    if args.test_name:
        for this_arg in args.hyp:
            for cnt in range(1 if args.test_model else args.run_time):
                model_index = args.dataset + '_{}_{}_{}_{}'.format(
                    'test' if args.test_model else args.index, args.test_name, this_arg, cnt + 1)
                print('Model index: {}'.format(model_index))

                exec("%s = %d" % ('args.{}'.format(args.test_name), this_arg))

                if args.remove_old_files:
                    remove_oldfiles(model_index)

                write_args(args, model_index)

                model_trainer = TrainModel(model_index, args)
                print("\nStrat training DSAN...\n")
                model_trainer.train()

                args.load_saved_data = True
                K.clear_session()

    else:
        for cnt in range(1 if args.test_model else args.run_time):
            model_index = args.dataset + '_{}_{}'.format('test' if args.test_model else args.index, cnt + 1)
            print('Model index: {}'.format(model_index))

            if args.remove_old_files:
                remove_oldfiles(model_index)

            write_args(args, model_index)

            model_trainer = TrainModel(model_index, args)
            print("\nStrat training DSAN...\n")
            model_trainer.train()

            args.load_saved_data = True
            K.clear_session()
