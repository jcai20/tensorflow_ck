import tensorflow as tf
tf.enable_eager_execution()
import os
import numpy as np
import random as rd


VGG_MEAN = tf.constant([123.68, 116.779, 103.939], dtype=tf.float32)
MEAN = tf.constant([128, 128, 128], dtype=tf.float32)


class ImageDataGenerator(object):
    """Wrapper class around the new Tensorflows dataset pipeline.

    Requires Tensorflow >= version 1.12rc0
    """

    def __init__(self, root, txt_file, mode, batch_size, num_classes, shuffle=False, buffer_size=10000):
        """Create a new ImageDataGenerator.
        Recieves a path string to a text file, which consists of many lines,
        where each line has first a path string to an image and seperated by
        a space an integer, referring to the class number. Using this data,
        this class will create TensrFlow datasets, that can be used to train
        e.g. a convolutional neural network.

        Args:
            root: Root to the dataset
            txt_file: Path to the text file.
            mode: Either 'training' or 'validation'. Depending on this value,
                different parsing functions will be used.
            batch_size: Number of images per batch.
            num_classes: Number of classes in the dataset.
            shuffle: Wether or not to shuffle the data in the dataset and the
                initial file list.
            buffer_size: Number of images used as buffer for TensorFlows
                shuffling of the dataset.

        Raises:
            ValueError: If an invalid mode is passed.
        """

        self.root = root
        self.txt_file = txt_file
        self.num_classes = num_classes
        # retrieve the data from the text file
        self._read_txt_file()

        self.data_size = len(self.labels)
        print("Dataset contains %d images" % self.data_size)
        # initial shuffling of the file and label lists (together!)
        if shuffle:
            self._shuffle_lists()

        # # convert lists to TF tensor
        self.img_paths = tf.convert_to_tensor(self.img_paths, dtype=tf.string)
        self.labels    = tf.convert_to_tensor(self.labels, dtype=tf.int32)

        dataset = tf.data.Dataset.from_tensor_slices((self.img_paths, self.labels))

        # distinguish between train/infer. when calling the parsing functions
        if mode == 'training':
            dataset = dataset.prefetch(batch_size).map(self._parse_function_train, num_parallel_calls=8)
        elif mode == 'inference':
            dataset = dataset.prefetch(batch_size).map(self._parse_function_inference, num_parallel_calls=8)
        else:
            raise ValueError("Invalid mode '%s'." % mode)

        # shuffle the first `buffer_size` elements of the dataset
        if shuffle:
            dataset = dataset.shuffle(buffer_size=buffer_size)

        # create a new dataset with batches of images
        dataset = dataset.batch(batch_size)

        self.dataset = dataset

    def _read_txt_file(self):
        """Read the content of the text file and store it into lists."""
        self.img_paths = []
        self.labels = []
        with open(self.txt_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                items = line.split(' ')
                self.img_paths.append( os.path.join(self.root, items[0]))
                self.labels.append(int(items[1]))

    def _shuffle_lists(self):
        """Conjoined shuffling of the list of paths and labels."""
        path = self.img_paths
        labels = self.labels
        permutation = np.random.permutation(self.data_size)
        self.img_paths = []
        self.labels = []
        for i in permutation:
            self.img_paths.append(path[i])
            self.labels.append(labels[i])

    def _parse_function_train(self, filename, label):
        """Input parser for samples of the training set."""
        # convert label number into one-hot-encoding
        one_hot = tf.one_hot(label, self.num_classes)

        # load and preprocess the image
        img_string = tf.read_file(filename)
        img_decoded = tf.image.decode_png(img_string, channels=3)       # uint8 dtype
        img = tf.image.resize_images(img_decoded, [256, 256])   # float dtype

        # img_resized = tf.subtract(img_resized, VGG_MEAN)
        img = tf.subtract(img, MEAN)
        img = tf.math.divide(img, MEAN)

        # rotate (0.1 Radian = 5.7 Degree)
        angel = rd.uniform(-0.1, 0.1)
        img = tf.contrib.image.rotate(img, angel)
        # horizontal flip
        img = tf.image.random_flip_left_right(img)
        # random crop
        img = tf.image.random_crop(img, [224, 224, 3])
        # random contrast
        img = tf.image.random_contrast(img, 0.3, 0.7)

        # RGB -> BGR
        # img_bgr = img_resized[:, :, ::-1]
        img_rgb = img

        return img_rgb, one_hot

    def _parse_function_inference(self, filename, label):
        """Input parser for samples of the validation/test set."""
        # convert label number into one-hot-encoding
        one_hot = tf.one_hot(label, self.num_classes)

        # load and preprocess the image
        img_string = tf.read_file(filename)
        img_decoded = tf.image.decode_png(img_string, channels=3)
        img = tf.image.resize_images(img_decoded, [224, 224])

        #img_resized = tf.subtract(img_resized, VGG_MEAN)
        img = tf.subtract(img, MEAN)
        img = tf.math.divide(img, MEAN)

        # RGB -> BGR
        # img_bgr = img_centered[:, :, ::-1]
        img_rgb = img
        return img_rgb, one_hot


if __name__ == '__main__':
    print('This is Data Loader')
