# full assembly of the sub-parts to form the complete net

import torch.nn.functional as F
import torch.nn as nn

from .unet_model import UNet
from .unet_parts import *
from .utils import init_weights


class DecoderBlock(nn.Module):    
    def __init__(self, in_channels, out_channels, padding = 1, output_padding = 1):
        super(DecoderBlock, self).__init__()
        self.conv = nn.ConvTranspose2d(in_channels=in_channels, out_channels=out_channels, kernel_size=3, stride=2, padding= padding, output_padding= output_padding)
        self.batchnorm = nn.BatchNorm2d(num_features=out_channels)        
        self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        x = self.conv(x)
        x = self.batchnorm(x)
        x = self.relu(x)
        return x


class DiscBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()        
        self.conv = nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=3, stride=2, padding = 1)
        self.batchnorm = nn.BatchNorm2d(num_features=out_channels)
        self.relu = nn.LeakyReLU(0.2, inplace=True)
        #self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        x = self.conv(x)
        x = self.batchnorm(x)
        x = self.relu(x)
        return x

class Flatten(nn.Module):
    def forward(self, x):
        x = x.view(x.size()[0], -1)
        return x

class GlobalAveragePooling(nn.Module):
    def forward(self, x):        
        return torch.mean(x.view(x.size(0), x.size(1), -1), dim=2)


class CENet(nn.Module):
    def __init__(self):
        super(CENet, self).__init__()
        self.encoder = models.vgg16_bn(pretrained=False).features
        #self.fc = nn.Sequential(nn.Linear(),
        #                        nn.Linear())
        
        self.decoder = nn.Sequential(
                        # The padding size should design for different input size
                        DecoderBlock(512,256, padding=(1,0), output_padding = (1,0)),
                        DecoderBlock(256,128),
                        DecoderBlock(128,64),
                        DecoderBlock(64,32))
        
        self.conv = nn.Conv2d(in_channels=32, out_channels=3, kernel_size=1)
        
    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        x = self.conv(x)        
        return x
    

class Discriminator(nn.Module):
    def __init__(self, n_classes):
        super(Discriminator, self).__init__()
        self.conv1 = DiscBlock(3, 64)
        self.conv2 = DiscBlock(64,128)
        self.conv3 = DiscBlock(128,256)
        self.conv4 = DiscBlock(256,512)    
        
        self.avgpool = nn.AdaptiveAvgPool2d((1,1))
        self.fc = nn.Linear(512, n_classes)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.avgpool(x)
        x = x.view(-1, 512)
        x = self.fc(x)
        return nn.Sigmoid()(x)
        