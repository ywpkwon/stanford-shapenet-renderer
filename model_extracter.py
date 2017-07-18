import zipfile
import glob
import os
import csv
from tqdm import tqdm
import shutil

keywords = ['car','auto', 'automobile', 'motorcar', 'suv', 'truck', 'cargo', 'ambulance']
shape_net_dir = '/media/phantom/World/data/ShapeNetCore.v1'
target_dir = '/media/phantom/World/data/shapenet_models'
if not os.path.isdir(target_dir): os.mkdir(target_dir)
files = glob.glob(os.path.join(shape_net_dir, '*.zip'))
for file in tqdm(files):
    name = os.path.splitext(os.path.basename(file))[0]
    csv_file = os.path.join(shape_net_dir, name + '.csv')

    model_ids = []
    with open(csv_file) as cfp:
        reader = csv.DictReader(cfp)
        for row in reader:
            if  any([keyword in row['wnlemmas'] for keyword in keywords]):
                modelid = row['fullId'].replace('3dw.', '')
                model_ids.append(modelid)

    if len(model_ids)==0: continue
    with zipfile.ZipFile(file) as zf:
        for model_id in model_ids:
            if not os.path.isfile(os.path.join(target_dir, model_id, 'model.obj')):
                try:
                    zf.extract(os.path.join(name, model_id, 'model.obj'), path=target_dir)
                    zf.extract(os.path.join(name, model_id, 'model.mtl'), path=target_dir)
                    shutil.move(os.path.join(target_dir,name,model_id), target_dir)
                    os.rmdir(os.path.join(target_dir,name))
                except:
                    print ('zip error: %s, %s' % (name, model_id))
