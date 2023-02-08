#-*- coding:utf-8 -*-
import random
import torch
from torchvision import transforms
import torchvision.transforms.functional as TF
import cv2
from PIL import Image, ImageOps
import numpy as np

class MultiViewDataInjector():
    def __init__(self, transform_list):
        self.transform_list = transform_list

    def __call__(self, sample):
        sample = transforms.ToPILImage()(sample)
        output = [transform(sample).unsqueeze(0) for transform in self.transform_list]
        output_cat = torch.cat(output, dim=0)
        return output_cat

class RotationTransform:
    """Rotate by one of the given angles."""

    def __init__(self, angles):
        self.angles = angles

    def __call__(self, x):
        angle = random.choice(self.angles)
        if angle > 0.:
            return TF.rotate(x, angle)
        else:
            return x

class GaussianBlur():
    def __init__(self, kernel_size, sigma_min=0.1, sigma_max=2.0):
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        self.kernel_size = kernel_size

    def __call__(self, img):
        sigma = np.random.uniform(self.sigma_min, self.sigma_max)
        img = cv2.GaussianBlur(np.array(img), (self.kernel_size, self.kernel_size), sigma)
        return Image.fromarray(img.astype(np.uint8))

class Solarize():
    def __init__(self, threshold=128):
        self.threshold = threshold

    def __call__(self, sample):
        return ImageOps.solarize(sample, self.threshold)

def get_transform(stage, resize_size, gb_prob=1.0, solarize_prob=0.):
    t_list = []
    color_jitter = transforms.ColorJitter(0.8, 0.8, 0.8, 0.2)
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
    if stage in ('train', 'val'):
        t_list = [
            RotationTransform(angles=[0, 90, 180, 270]),
            transforms.RandomVerticalFlip(),
            transforms.RandomHorizontalFlip(),
            transforms.RandomResizedCrop(resize_size, scale=(0.2, 1.0)),
            transforms.RandomApply([color_jitter], p=0.8),
            transforms.RandomGrayscale(p=0.2),
            transforms.RandomApply([GaussianBlur(kernel_size=23)], p=gb_prob),
            transforms.RandomApply([Solarize()], p=solarize_prob),
            transforms.ToTensor(),
            normalize]
    elif stage == 'ft':
        t_list = [
            transforms.RandomResizedCrop(resize_size),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            normalize]
    elif stage == 'test':
        t_list = [
            transforms.Resize(256),
            transforms.CenterCrop(resize_size),
            transforms.ToTensor(),
            normalize]
    transform = transforms.Compose(t_list)
    return transform