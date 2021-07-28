# %%
#importing necessary libraries
import numpy as np
import cv2
import glob
import os
import sys
from random import randint
from math import ceil, sqrt
import natsort
import random
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.applications import MobileNetV2

# %%
user = 'aws'

if user == 'siddhi':
    path_videos = 'C:/RoadCrossingAssistant/Data/Videos/'
    path_labels_csv = 'C:/RoadCrossingAssistant/Data/labels_framewise_csv.csv'
    path_labels_list = 'C:/RoadCrossingAssistant/Data/labels_framewise_list.pkl'
    path_frames = 'C:/RoadCrossingAssistant/Data/Frames/'

elif user == 'yagnesh':
    path_videos = '/home/yagnesh/Study/Machine Learning/ML projects/RoadCrossingAssistant_Arrays/videos/'
    path_labels_csv = '/home/yagnesh/Study/Machine Learning/ML projects/RoadCrossingAssistant_Arrays/labels_framewise.csv'
    path_labels_list = '/home/yagnesh/Study/Machine Learning/ML projects/RoadCrossingAssistant_Arrays/labels_framewise.pkl'

elif user == 'aws':
    path_videos = '/home/ubuntu/Data/Videos/'
    path_labels_csv = '/home/ubuntu/Data/labels_framewise_csv.csv'
    path_labels_list = '/home/ubuntu/Data/labels_framewise_list.pkl'
    path_frames = '/home/ubuntu/Data/Frames/'
    checkpoint_path = "/home/ubuntu/checkpoints/training_deploy/cp.ckpt"

# %%
#Perform train-test-validation split(66-22-16)

x = np.arange(1, 105)
np.random.seed(42)
np.random.shuffle(x)
videos_validation = x[:16]
videos_test = x[16: 16+22]
videos_train = x[16+22: ]

print(videos_train, len(videos_train))
print(videos_test, len(videos_test))
print(videos_validation, len(videos_validation))

# %%
filenames_train = []
labels_train = []
filenames_validation = []
labels_validation = []
filenames_test = []
labels_test = []


for vid in videos_train:
    folder = path_frames + "video{}/".format(vid)
    frames = glob.glob(folder + 'frame*.jpg')
    frames = natsort.natsorted(frames)
    filenames_train.extend(frames)
    labels_path = path_frames + "video{}/".format(vid) + "labels{}.npy".format(vid)
    labels_array = np.load(labels_path)
    labels_list = list(labels_array)
    labels_train.extend(labels_list)

filenames_train = np.array(filenames_train)
labels_train = np.array(labels_train)

for vid in videos_test:
    folder = path_frames + "video{}/".format(vid)
    frames = glob.glob(folder + 'frame*.jpg')
    frames = natsort.natsorted(frames)
    filenames_test.extend(frames)
    labels_path = path_frames + "video{}/".format(vid) + "labels{}.npy".format(vid)
    labels_array = np.load(labels_path)
    labels_list = list(labels_array)
    labels_test.extend(labels_list)

filenames_test = np.array(filenames_test)
labels_test = np.array(labels_test)

for vid in videos_validation:
    folder = path_frames + "video{}/".format(vid)
    frames = glob.glob(folder + 'frame*.jpg')
    frames = natsort.natsorted(frames)
    filenames_validation.extend(frames)
    labels_path = path_frames + "video{}/".format(vid) + "labels{}.npy".format(vid)
    labels_array = np.load(labels_path)
    labels_list = list(labels_array)
    labels_validation.extend(labels_list)

filenames_validation = np.array(filenames_validation)
labels_validation = np.array(labels_validation)

print(filenames_train.shape, filenames_validation.shape, filenames_test.shape)
print(labels_train.shape, labels_validation.shape, labels_test.shape)

# %%
# Generators
def parse_function(filename, label):

    image = tf.io.read_file(filename)
    image = tf.image.decode_jpeg(image)
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.image.resize(image, [270, 480], method=tf.image.ResizeMethod.AREA, 
                            preserve_aspect_ratio=True)
    return image, label


def train_preprocess(image, label):

    image = tf.image.random_brightness(image, 0.15)
    image = tf.image.random_contrast(image, 0.8, 1.5)
    image = tf.image.random_saturation(image, 0.6, 3)

    return image, label

dataset_train = tf.data.Dataset.from_tensor_slices((filenames_train,labels_train))
dataset_train = dataset_train.shuffle(len(filenames_train))
dataset_train = dataset_train.map(parse_function, num_parallel_calls=4)
dataset_train = dataset_train.map(train_preprocess, num_parallel_calls=4)
dataset_train = dataset_train.batch(16)
dataset_train = dataset_train.prefetch(1)

dataset_test = tf.data.Dataset.from_tensor_slices((filenames_test,labels_test))
dataset_test = dataset_test.shuffle(len(filenames_test))
dataset_test = dataset_test.map(parse_function, num_parallel_calls=4)
dataset_test = dataset_test.batch(16)
dataset_test = dataset_test.prefetch(1)

dataset_val = tf.data.Dataset.from_tensor_slices((filenames_validation,labels_validation))
dataset_val = dataset_val.shuffle(len(filenames_validation))
dataset_val = dataset_val.map(parse_function, num_parallel_calls=4)
dataset_val = dataset_val.batch(16)
dataset_val = dataset_val.prefetch(1)

# %%

tf.keras.backend.set_image_data_format('channels_last')

#change this function as per the model architecture
def create_model():

    inputs = tf.keras.layers.Input([270, 480, 3])
    #x = tf.keras.layers.BatchNormalization()(inputs)

    x = tf.keras.layers.Conv2D(32, (3,3), padding='same', activation=None, dilation_rate = (3,3),
    use_bias=False)(inputs)
    #x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Conv2D(32, (3,3), padding='same', activation=None, dilation_rate = (3,3),
    use_bias=False)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.MaxPool2D(pool_size=(2,2))(x)

    x = tf.keras.layers.Conv2D(64, (3,3), padding='same', activation=None, dilation_rate = (2,2),
    use_bias=False)(x)
    #x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Conv2D(64, (3,3), padding='same', activation=None, dilation_rate = (2,2),
    use_bias=False)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.MaxPool2D(pool_size=(2,2))(x)

    x = tf.keras.layers.Conv2D(64, (3,3), padding='same', activation=None, dilation_rate = (2,2),
    use_bias=False)(x)
    #x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Conv2D(128 , (3,3), padding='same', activation=None, dilation_rate = (2,2),
    use_bias=False)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.MaxPool2D(pool_size=(2,2))(x)

    x = tf.keras.layers.Conv2D(128, (3,3), padding='same', activation=None, use_bias=False)(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)

    x = tf.keras.layers.Dense(64, activation=None, kernel_regularizer=tf.keras.regularizers.l2(1e-3))(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    x = tf.keras.layers.Dense(32, activation=None, kernel_regularizer=tf.keras.regularizers.l2(1e-3))(x)
    x = tf.keras.layers.ReLU(6.)(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
    model = tf.keras.Model(inputs, outputs)


    return model

model = create_model()
model.summary()

model.compile(
        loss=tf.keras.losses.BinaryCrossentropy(),
        optimizer=tf.keras.optimizers.Adam(lr=0.001/5),
        metrics=[tf.keras.metrics.RecallAtPrecision(precision=0.9, name='recallAtPrecision'), 
        tf.keras.metrics.BinaryAccuracy(threshold=0.6, name='binaryAccuracy')])

model.load_weights("/home/ubuntu/checkpoints/approach_3.3/cp.ckpt")
print("loaded weights")

# %%
print("Evaluate on test data")
results = model.evaluate(dataset_test)
print("test loss, test acc:", results)

print("Evaluate on train data")
results = model.evaluate(dataset_train)
print("train loss, trai acc:", results)

print("Evaluate on validation data")
results = model.evaluate(dataset_val)
print("val loss, val acc:", results)


#%%

img = cv2.imread("/home/ubuntu/Data/Frames/video33/frame60.jpg")
#img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# img = cv2.resize(img, (480,270))
# print(img.shape)

# test_input = np.array([img])
# print(test_input.shape)

# print(model.predict(test_input))

frame_input = tf.image.convert_image_dtype(img, tf.float32)
frame_input = tf.image.resize(frame_input, [270, 480], method=tf.image.ResizeMethod.AREA, preserve_aspect_ratio=True)
frame_input = np.expand_dims(frame_input, axis = 0)
print("input shape: ",frame_input.shape)
print("op: ", model.predict(frame_input))

# %%

model.save('/home/ubuntu/savedmodels/approach_3_3')
print("saved model")
loaded = tf.keras.models.load_model('/home/ubuntu/savedmodels/approach_3_3')
print("op: ",loaded.predict(frame_input))

#%%
# from tensorflow.python.compiler.tensorrt import trt_convert as trt
# converter = trt.TrtGraphConverterV2(input_saved_model_dir="/home/ubuntu/savedmodels/training_temp")
# converter.convert()
# converter.save("/home/ubuntu/tensorrt_models/training_temp")

# model = tf.saved_model.load("/home/ubuntu/tensorrt_models/training_temp")
# func = model.signatures['serving_default']

#%%
# x = tf.convert_to_tensor(test_input, dtype=tf.float32)
# print(func(x))