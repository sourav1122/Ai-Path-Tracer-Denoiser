import torch, os, sys, cv2
import torch.nn as nn
from torch.nn import init
import functools
import torch.optim as optim
import matplotlib.pyplot as plt

from torch.utils.data import Dataset, DataLoader
from torch.nn import functional as func
from PIL import Image

import torchvision.transforms as transforms
import numpy as np
import torch
from preprocess import preprocess

def find_max(dir, num_scenes, num_mov, num_noise):
    images = images = sorted(os.listdir(dir))
    m = np.zeros((num_scenes+1,num_mov+1,num_noise+1))
    for file in images:
        splits = file.split('_')
        m[int(splits[0]),int(splits[1]),int(splits[2])] = max(m[int(splits[0])][int(splits[1])][int(splits[2])], int(splits[3][:-4]))
    return m

class AutoEncoderData(Dataset):

    def __init__(self,  images_dir, scenes_dir, gt_dir, size, m, crop=False, crop_size=0):
        super(AutoEncoderData, self).__init__()

        self.scenes_dir = scenes_dir
        self.images_dir = images_dir
        self.gt_dir = gt_dir
        self.images = sorted(os.listdir(images_dir))
        self.inputs = sorted(os.listdir(scenes_dir))
        self.outputs = sorted(os.listdir(gt_dir))
        self.width = size[0]
        self.height = size[1]
        self.m = m
        self.crop = crop
        self.crop_size = crop_size

    def __getitem__(self, index):
        input = np.zeros((7,self.height, self.width,10))
        output = np.zeros((7,self.height, self.width,3))
        image_name = self.images[index]
        splits = image_name.split('_')
        start = index
        if index > int(self.m[int(splits[0]),int(splits[1]),int(splits[2])] - 6):
            start = int(self.m[int(splits[0]),int(splits[1]),int(splits[2])] - 6)
        for i in range(start,start+7):
            input[i-start] = np.load(self.scenes_dir+'/'+self.inputs[i])
            output[i-start]  = np.load(self.gt_dir+'/'+self.outputs[i])
        if self.crop:
            crop_width = np.random.randint(self.width/self.crop_size)*self.crop_size
            crop_height = np.random.randint(self.height/self.crop_size)*self.crop_size
            input = torch.from_numpy(input[:,crop_width:crop_width+self.crop_size,crop_height:crop_height+self.crop_size,:].astype(np.float))
            output = torch.from_numpy(output[:,crop_width:crop_width+self.crop_size,crop_height:crop_height+self.crop_size,:].astype(np.float))
        else:
            input = torch.from_numpy(input.astype(np.float))
            output = torch.from_numpy(output.astype(np.float))

        return {'image':input.permute(0,3,1,2),'output':output.permute(0,3,1,2)}

    def __len__(self):
        return len(self.images)

if __name__ == '__main__':
    device =  torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    root_dir = '../test/'

    m = find_max('../test/RGB',13,1,1)
    preprocess(root_dir,root_dir+'RGB',root_dir+'Depth',root_dir+'Albedos',root_dir+'Normals',root_dir+'GroundTruth',m,512)
    data_num = 1
    dataset = AutoEncoderData('../test/RGB','../test/input','../test/gt',(512,512),m, True, 256)
    data = dataset[data_num]
    input = data['image'].float().to(device)
    label = data['output'].float().to(device)
    for j in range(7):
        fig, ax = plt.subplots(3)
        ax[0].imshow(input[j,:3,:,:].permute(1,2,0).detach().cpu().numpy())
        ax[0].set_title("Input")
        ax[1].imshow(input[j,3:6,:,:].permute(1,2,0).detach().cpu().numpy())
        ax[1].set_title("Normal")
        ax[2].imshow(input[j,6:7,:,:].permute(1,2,0).detach().cpu().numpy()[:,:,0])
        ax[2].set_title("Depth")
        plt.show()
