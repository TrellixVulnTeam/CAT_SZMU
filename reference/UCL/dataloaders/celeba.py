import os,sys
import numpy as np
import torch
import utils
from torchvision import datasets,transforms
from sklearn.utils import shuffle
import json
from torch.utils.data import Dataset
from sklearn.utils import shuffle
from PIL import Image

def get(seed=0,pc_valid=0.10,tasknum = 10,args=0):
    data={}
    taskcla=[]
    size=[3, 218, 178]
    size=[3, 32, 32]

    num_task = 10

    if 'small' in args.note:
        data_type = 'small'
    elif 'full' in args.note:
        data_type = 'full'

    if not os.path.isdir('/home/zixuan/KAN/image/dat/'+data_type+'_binary_celeba/'):
        os.makedirs('/home/zixuan/KAN/image/dat/'+data_type+'_binary_celeba')

        mean=[x/255 for x in [125.3,123.0,113.9]]
        std=[x/255 for x in [63.0,62.1,66.7]]

        # celeba
        dat={}
        train_dataset = CELEBATrain(root_dir='/home/zixuan/KAN/image/dat/celeba/'+data_type+'/iid/train/',img_dir='/home/zixuan/KAN/image/dat/celeba/data/raw/img_align_celeba/',transform=transforms.Compose([transforms.Resize(size=(32,32)),transforms.ToTensor(),transforms.Normalize(mean,std)]))
        dat['train'] = train_dataset

        test_dataset = CELEBATest(root_dir='/home/zixuan/KAN/image/dat/celeba/'+data_type+'/iid/test/',img_dir='/home/zixuan/KAN/image/dat/celeba/data/raw/img_align_celeba/',transform=transforms.Compose([transforms.Resize(size=(32,32)),transforms.ToTensor(),transforms.Normalize(mean,std)]))
        dat['test'] = test_dataset

        users = [x[0] for x in set([user for user,image,target in torch.utils.data.DataLoader(dat['train'],batch_size=1,shuffle=True)])]
        users.sort()
        users = users[:num_task]
        print('users: ',users)
        print('users length: ',len(users))

        # # totally 10 tasks, each tasks 2 classes (whether smiling)
        #
        for task_id,user in enumerate(users):
            data[task_id]={}
            data[task_id]['name'] = 'celeba-'+str(user)
            data[task_id]['ncla'] = 2


        for s in ['train','test']:
            loader=torch.utils.data.DataLoader(dat[s],batch_size=1,shuffle=True)

            for task_id,user in enumerate(users):
                data[task_id][s]={'x': [],'y': []}

            for user,image,target in loader:
                if user[0] not in users: continue # we dont want too may classes
                label=target.numpy()[0]
                data[users.index(user[0])][s]['x'].append(image)
                data[users.index(user[0])][s]['y'].append(label)

        # # "Unify" and save
        for n,user in enumerate(users):
            for s in ['train','test']:
                data[n][s]['x']=torch.stack(data[n][s]['x']).view(-1,size[0],size[1],size[2])
                data[n][s]['y']=torch.LongTensor(np.array(data[n][s]['y'],dtype=int)).view(-1)
                torch.save(data[n][s]['x'], os.path.join(os.path.expanduser('/home/zixuan/KAN/image/dat/'+data_type+'_binary_celeba/'),'data'+str(n)+s+'x.bin'))
                torch.save(data[n][s]['y'], os.path.join(os.path.expanduser('/home/zixuan/KAN/image/dat/'+data_type+'_binary_celeba/'),'data'+str(n)+s+'y.bin'))


    # Load binary files
    data={}
    ids=list(shuffle(np.arange(num_task),random_state=seed))
    print('Task order =',ids)
    for i in range(num_task):
        data[i] = dict.fromkeys(['name','ncla','train','test'])
        for s in ['train','test']:
            data[i][s]={'x':[],'y':[]}
            data[i][s]['x']=torch.load(os.path.join(os.path.expanduser('/home/zixuan/KAN/image/dat/'+data_type+'_binary_celeba/'),'data'+str(ids[i])+s+'x.bin'))
            data[i][s]['y']=torch.load(os.path.join(os.path.expanduser('/home/zixuan/KAN/image/dat/'+data_type+'_binary_celeba/'),'data'+str(ids[i])+s+'y.bin'))
        data[i]['ncla']=len(np.unique(data[i]['train']['y'].numpy()))
        data[i]['name']='celeba-'+str(ids[i])


    # Validation
    for t in data.keys():
        r=np.arange(data[t]['train']['x'].size(0))
        r=np.array(shuffle(r,random_state=seed),dtype=int)
        nvalid=int(pc_valid*len(r))
        ivalid=torch.LongTensor(r[:nvalid])
        itrain=torch.LongTensor(r[nvalid:])
        data[t]['valid']={}
        data[t]['valid']['x']=data[t]['train']['x'][ivalid].clone()
        data[t]['valid']['y']=data[t]['train']['y'][ivalid].clone()
        data[t]['train']['x']=data[t]['train']['x'][itrain].clone()
        data[t]['train']['y']=data[t]['train']['y'][itrain].clone()

    # Others
    n=0
    for t in data.keys():
        taskcla.append((t,data[t]['ncla']))
        n+=data[t]['ncla']
    data['ncla']=n

    return data,taskcla,size




########################################################################################################################



# customize dataset class

class CELEBATrain(Dataset):
    """Federated EMNIST dataset."""

    def __init__(self, root_dir,img_dir, transform=None):
        self.transform = transform
        self.size=[218, 178, 3]

        self.x = []
        self.y = []
        self.user = []
        for file in os.listdir(root_dir):
            with open(root_dir+file) as json_file:
                data = json.load(json_file) # read file and do whatever we need to do.
                for key, value in data['user_data'].items():
                    for type, data in value.items():
                        if type == 'x':
                            for img in data:
                                img_name = img_dir + img
                                im = Image.open(img_name)
                                np_im = np.array(im)
                                self.x.append(torch.from_numpy(np_im))
                        elif type == 'y':
                            self.y.append(data)

                    for _ in range(len(data)):
                        self.user.append(key)

        self.x=torch.cat(self.x,0).view(-1,self.size[0],self.size[1],self.size[2])
        self.y=torch.LongTensor(np.array([d for f in self.y for d in f],dtype=int)).view(-1).numpy()

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):

        user = self.user[idx]
        x = self.x[idx]
        y = self.y[idx]

        x = x.data.numpy()
        x = Image.fromarray(x)
        # x = Image.fromarray((x * 255).astype(np.uint8))

        if self.transform:
            x = self.transform(x)
        return user,x,y






class CELEBATest(Dataset):
    """Federated EMNIST dataset."""

    def __init__(self, root_dir,img_dir, transform=None):
        self.transform = transform
        self.size=[218, 178, 3]

        self.x = []
        self.y = []
        self.user = []
        for file in os.listdir(root_dir):
            with open(root_dir+file) as json_file:
                data = json.load(json_file) # read file and do whatever we need to do.
                for key, value in data['user_data'].items():
                    for type, data in value.items():
                        if type == 'x':
                            for img in data:
                                img_name = img_dir + img
                                im = Image.open(img_name)
                                np_im = np.array(im)
                                self.x.append(torch.from_numpy(np_im))
                        elif type == 'y':
                            self.y.append(data)

                    for _ in range(len(data)):
                        self.user.append(key)

        self.x=torch.cat(self.x,0).view(-1,self.size[0],self.size[1],self.size[2])
        self.y=torch.LongTensor(np.array([d for f in self.y for d in f],dtype=int)).view(-1).numpy()

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):

        user = self.user[idx]
        x = self.x[idx]
        y = self.y[idx]

        x = x.data.numpy()
        x = Image.fromarray(x)
        # x = Image.fromarray((x * 255).astype(np.uint8))

        if self.transform:
            x = self.transform(x)
        return user,x,y