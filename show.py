import matplotlib.pyplot as plt
import scipy.misc

name = '/media/phantom/World/data/shapenet_rendering/27f138cd6641ce52b038a1a418d53cbe/27f138cd6641ce52b038a1a418d53cbe_r_000'


# img = scipy.misc.imread(name+'_depth0001.png')
img = scipy.misc.imread(name+'.png')
import pdb; pdb.set_trace()
with open(name+'_coord.txt', 'r') as fp:
    lines = fp.readlines()
    pts = [[float(v) for v in line.split()] for line in lines]

def draw_polygon(points, indices):
    points = [points[i] for i in indices]
    points.append(points[0])
    plt.plot([p[0] for p in points], [p[1] for p in points])

plt.imshow(img)
draw_polygon(pts, [0,1,2,3])
draw_polygon(pts, [4,5,6,7])
draw_polygon(pts, [0,1,5,4])
draw_polygon(pts, [3,2,6,7])
draw_polygon(pts, [0,3,7,4])
draw_polygon(pts, [1,2,6,5])
plt.show()