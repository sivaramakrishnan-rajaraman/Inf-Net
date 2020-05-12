from datetime import datetime
import os
import numpy as np
import torch.optim as optim
from Code.utils.dataloader_MulClsLungInf_UNet import LungDataset
from torchvision import transforms
# from LungData import test_dataloader, train_dataloader  # pls change batch_size
from torch.utils.data import DataLoader
from Code.model_lung_infection.InfNet_UNet import *


def train(epo_num, num_classes, input_channels, batch_size, lr):
    train_dataset = LungDataset(
        imgs_path='./Dataset/TrainingSet/MultiClassInfection-Train/Imgs/',
        pseudo_path='./Dataset/TrainingSet/MultiClassInfection-Train/Prior/',
        label_path='./Dataset/TrainingSet/MultiClassInfection-Train/GT/',
        transform=transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]))
    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    lung_model = UNet(input_channels, num_classes)  # input_channels=3， n_class=3
    print(lung_model)
    lung_model = lung_model.to(device)

    criterion = nn.BCELoss().to(device)
    optimizer = optim.SGD(lung_model.parameters(), lr=lr, momentum=0.7)

    for epo in range(epo_num):

        train_loss = 0
        lung_model.train()

        for index, (img, pseudo, img_mask, _) in enumerate(train_dataloader):

            img = img.to(device)
            pseudo = pseudo.to(device)
            img_mask = img_mask.to(device)

            optimizer.zero_grad()
            output = lung_model(torch.cat((img, pseudo), dim=1))

            output = torch.sigmoid(output)  # output.shape is torch.Size([4, 2, 160, 160])
            loss = criterion(output, img_mask)

            loss.backward()
            iter_loss = loss.item()
            train_loss += iter_loss
            optimizer.step()

            if np.mod(index, 20) == 0:
                print('Epoch: {}/{}, Step: {}/{}, Train loss is {}'.format(epo, epo_num, index, len(train_dataloader), iter_loss))

        os.makedirs('./checkpoints//UNet_Multi-Class-Semi', exist_ok=True)
        if np.mod(epo+1, 10) == 0:
            torch.save(lung_model.state_dict(),
                       './Snapshots/save_weights/Semi-Inf-Net_UNet/unet_model_{}.pkl'.format(epo+1))
            print('saveing checkpoints: unet_model_{}.pkl'.format(epo+1))


if __name__ == "__main__":
    train(epo_num=200,
          num_classes=3,
          input_channels=6,
          batch_size=16,
          lr=1e-2)