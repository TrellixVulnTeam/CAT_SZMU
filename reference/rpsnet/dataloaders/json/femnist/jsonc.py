import numpy as np
import json
import os
import torch


size=[1,28,28]


x = []
y = []
user = []
for file in os.listdir('./'):
    if '.py' not in file:
        print('file: ',file)
        with open(file) as json_file:
            data = json.load(json_file) # read file and do whatever we need to do.
            print('users: ',data['users'])
            print('num_samples: ',data['num_samples'])
            for key, value in data['user_data'].items():
                print('user: ',key)
                print('length: ',len(value))
                for type, data in value.items():
                    if type == 'x':
                        print('x size: ',torch.from_numpy(np.array(data)).size())
                        x.append(torch.from_numpy(np.array(data)))
                    elif type == 'y':
                        y.append(data)

                user.append(key)

x=torch.cat(x,0).view(-1,size[0],size[1],size[2])
y=torch.LongTensor(np.array([d for f in y for d in f],dtype=int)).view(-1)

print('x: ',x.size())
print('y: ',y.size())
print('user: ',len(user))


sample = {'user': user[0], 'x': x[0], 'y': y[0]}
print('sample: ',sample)

