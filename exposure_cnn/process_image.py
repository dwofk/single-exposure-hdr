import numpy as np
import tensorflow as tf
from PIL import Image
import os
import random
import cv2

# create a prelu image
def prelu(x, alpha, name):
    pos = tf.nn.relu(x, name)
    neg = alpha * (x - abs(x)) * 0.5
    
    return pos + neg

# build the net: structure fully defined within this function
def buildModel(image, isTraining):
    # conv1
    with tf.variable_scope('conv1') as scope:
        kernel = tf.Variable(tf.random_normal([1, 1, 3, 32], stddev=0.05), name='weights')
        conv = tf.nn.conv2d(image, kernel, [1, 1, 1, 1], padding='SAME')
        biases = tf.Variable(tf.zeros([32]), name='biases')
        pre_activation = tf.nn.bias_add(conv, biases)
        #norm1 = tf.contrib.layers.batch_norm(pre_activation, is_training=isTraining)
        #conv1 = tf.nn.relu(norm1, name='conv1')
        #conv1 = tf.nn.relu(pre_activation, name=scope.name)
        alpha = tf.Variable(tf.zeros(pre_activation.get_shape()[-1]), name='alpha');
        #alpha = tf.get_variable('alpha', pre_activation.get_shape()[-1], initializer=tf.constant_initializer(0.0), dtype=tf.float32)
        conv1 = prelu(pre_activation, alpha, name=scope.name)

    with tf.variable_scope('conv2') as scope:
        kernel = tf.Variable(tf.random_normal([1, 1, 32, 3], stddev=0.05), name='weights')
        conv = tf.nn.conv2d(conv1, kernel, [1, 1, 1, 1], padding='SAME')
        biases = tf.Variable(tf.zeros([3]), name='biases')
        pre_activation = tf.nn.bias_add(conv, biases)
        #alpha = tf.Variable(tf.zeros(pre_activation.get_shape()[-1]), name='alpha');
        #conv1 = tf.nn.relu(pre_activation, name=scope.name)
        #norm2 = tf.contrib.layers.batch_norm(pre_activation, is_training=isTraining)
        alpha = tf.get_variable('alpha', pre_activation.get_shape()[-1], initializer=tf.constant_initializer(0.0), dtype=tf.float32)
        conv2 = prelu(pre_activation, alpha, name=scope.name)
        #norm2 = tf.contrib.layers.batch_norm(pre_activation, is_training=isTraining)
        #conv2 = tf.nn.relu(norm2, name='conv2')

##    with tf.variable_scope('conv2') as scope:
##        kernel = tf.Variable(tf.random_normal([1, 1, 32, 5], stddev=0.05), name='weights')
##        #kernel = _variable_with_weight_decay('weights', shape=[1, 1, 32, 5], stddev=0.05, wd=0.0)
##        conv = tf.nn.conv2d(conv1, kernel, [1, 1, 1, 1], padding='SAME')
##        biases = tf.Variable(tf.zeros([5]), name='biases')
##        pre_activation = tf.nn.bias_add(conv, biases)
##        alpha = tf.get_variable('alpha', pre_activation.get_shape()[-1], initializer=tf.constant_initializer(0.0), dtype=tf.float32)
##        conv2 = prelu(pre_activation, alpha, name=scope.name)
##
##    with tf.variable_scope('conv3') as scope:
##        kernel = tf.Variable(tf.random_normal([3, 3, 5, 5], stddev=0.05), name='weights')
##        #kernel = _variable_with_weight_decay('weights', shape=[3, 3, 5, 5], stddev=0.05, wd=0.0)
##        conv = tf.nn.conv2d(conv2, kernel, [1, 1, 1, 1], padding='SAME')
##        biases = tf.Variable(tf.zeros([5]), name='biases')
##        pre_activation = tf.nn.bias_add(conv, biases)
##        alpha = tf.get_variable('alpha', pre_activation.get_shape()[-1], initializer=tf.constant_initializer(0.0), dtype=tf.float32)
##        conv3 = prelu(pre_activation, alpha, name=scope.name)
##
##    with tf.variable_scope('conv4') as scope:
##        kernel = tf.Variable(tf.random_normal([1, 1, 5, 32], stddev=0.05), name='weights')
##        #kernel = _variable_with_weight_decay('weights', shape=[1, 1, 5, 32], stddev=0.05, wd=0.0)
##        conv = tf.nn.conv2d(conv3, kernel, [1, 1, 1, 1], padding='SAME')
##        biases = tf.Variable(tf.zeros([32]), name='biases')
##        pre_activation = tf.nn.bias_add(conv, biases)
##        alpha = tf.get_variable('alpha', pre_activation.get_shape()[-1], initializer=tf.constant_initializer(0.0), dtype=tf.float32)
##        conv4 = prelu(pre_activation, alpha, name=scope.name)
##
##    with tf.variable_scope('conv5') as scope:
##        kernel = tf.Variable(tf.random_normal([3, 3, 32, 3], stddev=0.05), name='weights')
##        #kernel = _variable_with_weight_decay('weights', shape=[9, 9, 32, 3], stddev=0.05, wd=0.0)
##        conv = tf.nn.conv2d(conv4, kernel, [1, 1, 1, 1], padding='SAME')
##        biases = tf.Variable(tf.zeros([3]), name='biases')
##        pre_activation = tf.nn.bias_add(conv, biases)
##        alpha = tf.get_variable('alpha', pre_activation.get_shape()[-1], initializer=tf.constant_initializer(0.0), dtype=tf.float32)
##        conv5 = prelu(pre_activation, alpha, name=scope.name)

#    return conv5
    return conv2

# currently not used: do some simple transformations to get more mileage out of an image
def setFromImage(image):
    return [image, np.flipud(image), np.fliplr(image)]

# specialized to current file structure: images should be within 2 layers of folders
# extract full list of image file names to use
def fileList(filepath):
    filelist = []
    directories = os.listdir(filepath)
    for directory in directories:
        filenames = os.listdir(filepath + directory)
        fullfilenames = [filepath + directory + '\\' + x for x in filenames]
        filelist.extend(fullfilenames)
    random.shuffle(filelist)
    return filelist


# train on all 32x32 image pieces once
# loadModel = bool: True if a loadName is passed in, to load a model from memory, False if initializing new model
# plusExposure = bool: True if higher-exposure labels should be used, False if lower-exposure labels should be used
# saveName is the location to save the new model
def runTrain(x, y, saver, loadModel, plusExposure, learning_rate, momentum, loadName='', saveName=''):
    config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=True)
    #with tf.device("/gpu:0"):
    with tf.device("/cpu:0"):
        trainshape = (32, 32, 1, 3)
        norm = 32*32*1*3
        l = tf.placeholder('float32', shape=trainshape)
        sqdiff = tf.square(tf.subtract(l, y))
        y_sqdiff = sqdiff[:,:,:,0]
        cr_sqdiff = sqdiff[:,:,:,1]*10
        cb_sqdiff = sqdiff[:,:,:,2]*10
        print(sqdiff)
        reduced = tf.reduce_sum(y_sqdiff + cr_sqdiff + cb_sqdiff)/norm
        print(reduced)
        loss = tf.sqrt(reduced) # RMSE
        tf.summary.scalar('loss', loss)
        
        currentDirectory = 'S:\\6344-project\\exposure_cnn\\'

        global_step = tf.Variable(0, trainable=False)
        #optimizer = tf.train.GradientDescentOptimizer(learning_rate)
        #optimizer = tf.train.MomentumOptimizer(learning_rate, momentum, use_nesterov=True)
        optimizer = tf.train.AdagradOptimizer(learning_rate)
        train_op = optimizer.minimize(loss)
        
        #input_filepath = 'phos\\0\\'
        #label_filepath = 'phos\\plus_2\\'
        input_filepath = 'C:\\Users\\vysarge\\Documents\\hdr_dataset\\empapatches\\0\\'
        if (plusExposure):
            label_filepath = 'C:\\Users\\vysarge\\Documents\\hdr_dataset\\empapatches\\plus_4\\'
        else:
            label_filepath = 'C:\\Users\\vysarge\\Documents\\hdr_dataset\\empapatches\\minus_4\\'
        
        inputs = fileList(input_filepath)
        #labels = fileList(label_filepath)
        #inputs = os.listdir(input_filepath)
        #labels = os.listdir(label_filepath)

        #with tf.Graph().as_default():
        
        
        
    with tf.Session(config=config) as sess:
        

        if loadModel:
            init_op = tf.global_variables_initializer()
            sess.run(init_op)
            saver.restore(sess, loadName + '\\' + 'model.ckpt')
            print('Load model from ' + loadName)
        else:
            init_op = tf.global_variables_initializer()
            sess.run(init_op)
            print('Initializing fresh variables')

        step = 0
        feed_dict = {}
        sum_loss = 0
        for input_file in inputs:
            fileparts = input_file.split('\\')
            scene = fileparts[-2]
            file = fileparts[-1] # the last element of this split should be the file name
            label_file = label_filepath + scene + '\\' + file
            if (os.path.exists(label_file)):
                im_in = cv2.imread(input_file)
                im_in = cv2.cvtColor(im_in, cv2.COLOR_RGB2YCR_CB)
                #im_in = cv2.cvtColor(im_in, cv2.COLOR_RGB2HSV)
                h, w, d = np.shape(im_in)
                im_in = np.asarray(im_in).astype('float32')
                im_in = im_in.reshape([h, w, 1, 3]);
                #im_inputs = setFromImage(im_in)

                im_la = cv2.imread(label_file)
                im_la = cv2.cvtColor(im_la, cv2.COLOR_RGB2YCR_CB)
                #im_la = cv2.cvtColor(im_la, cv2.COLOR_RGB2HSV)
                h, w, d = np.shape(im_la)
                im_la = np.asarray(im_la).astype('float32')
                im_la = im_la.reshape([h, w, 1, 3]);
                #im_labels = setFromImage(im_la)
                _, loss_value = sess.run([train_op, loss], feed_dict={x:im_in, l:im_la})
                #print(global_step.eval(session=sess))
                #step = global_step.eval(session=sess)
                sum_loss = sum_loss + loss_value
                if (step % 10000 == 0):
                    avg_loss = sum_loss/10000
                    sum_loss = 0
                    print("Step: {}, Loss: {}, Rate: {}".format(step, avg_loss, learning_rate))
                #global_step = global_step + 1
                step = step + 1
            else:
                print('From {}: {} does not exist'.format(input_file, label_file))

        if not os.path.exists(currentDirectory+saveName):
            os.makedirs(currentDirectory+saveName)
        saver.save(sess, currentDirectory + saveName + '\\' + 'model.ckpt') # save model checkpoint
    #im = Image.open('input.bmp')
    #h, w = im.size
    #im_te = np.asarray(im).astype('float32')
    #im_in =  im_te.reshape([h, w, 1, 3]);

def train(modelName, epochs):
    assert(epochs>0, 'Must train for at least one epoch!')
    config = tf.ConfigProto(allow_soft_placement=True, log_device_placement=True)
    with tf.device("/gpu:0"):
        trainshape = (32, 32, 1, 3)
        norm = 32*32*1*3
        x = tf.placeholder('float32', shape=trainshape)
        y = buildModel(x, True)
        print(y)
        
        saver = tf.train.Saver()
        learning_rate = 0.000003
        momentum = 0.5
        runTrain(x, y, saver, False, True, learning_rate, momentum, loadName='', saveName=modelName+'0')
        for i in range(epochs-1):
            loadName = modelName+'{}'.format(i)
            saveName = modelName+'{}'.format(i+1)
            learning_rate = learning_rate / 2
            runTrain(x, y, saver, True, True, learning_rate, momentum, loadName=loadName, saveName=saveName)


# process a single image of any size using the provided net saved at modelName
def processImage(x, y, modelName, imageName, outputName):
    #im = Image.open(imageName)
    #im = im.convert('YCbCr')
    im = cv2.imread(imageName)
    h, w, d = np.shape(im)
    im = cv2.resize(im, (int(w/2), int(h/2)), interpolation=cv2.INTER_AREA)
    im = cv2.cvtColor(im, cv2.COLOR_RGB2YCR_CB)
    #im = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
    
    print(np.shape(im))
    h, w, d = np.shape(im)
    im_te = np.asarray(im).astype('float32')
    im_in =  im_te.reshape([h, w, 1, 3]);

    
    with tf.Session(config=tf.ConfigProto(log_device_placement=True)) as sess:
        saver = tf.train.Saver()
        init_op = tf.global_variables_initializer()
        sess.run(init_op)
        saver.restore(sess, modelName)
        print('Load model from ' + modelName)
        
        im_out = y.eval(session=sess,feed_dict={x:im_in})
        im_out = im_out.reshape([h, w, 3]).clip(0, 255).astype('uint8')
    im_o = cv2.cvtColor(im_out, cv2.COLOR_YCR_CB2RGB)
    #im_o = cv2.cvtColor(im_out, cv2.COLOR_HSV2RGB)
    cv2.imwrite(outputName, im_o)


modelPath = 'model\\'
modelName = modelPath + 'model'
# Begin a new model
#runTrain(False, 0.000003, saveName=modelName)
train(modelName, 9)
'''
for i in range(5):
    loadModel = modelPath + modelName
    modelPath = 'model{}\\'.format(i)
    if not os.path.exists(modelPath):
        os.makedirs(modelPath)
    runTrain(True, loadName=loadModel, saveName=modelPath+modelName)
'''
# Update an existing model
#runTrain(True, 0.0000005, loadName=modelName, saveName=modelName)
#runTrain(True, 0.0000001, loadName=modelName, saveName=modelName)
#runTrain(True, 0.00000003, loadName=modelName, saveName=modelName)

# Run an image through the net
#processImage(modelName, 'input.jpg', 'output.jpg')
#processImage(modelName, 'input2.jpg', 'output2.jpg')
#scene = 15
#exposure = 0
#phos_path = 'C:\\Users\\vysarge\\Documents\\hdr_dataset\\Phos2_3MP\\Phos2_scene{}\\'.format(scene)

#test_name = 'Phos2_uni_sc{}_{}.png'.format(scene, exposure)
#processImage(modelName, phos_path + test_name)


