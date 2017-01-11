import numpy as np

def fix_images(images,dims=None):
    if isinstance(images,list) or isinstance(images,tuple):
        expanded = []
        for i in images:
            expanded.extend(fix_image(i,dims))
        return expanded
    if len(images.shape) == 3:
        return images
    if len(images.shape) == 4:
        return np.einsum("bxyc->bcxy",images).reshape((-1,)+images.shape[1:3])
    if len(images.shape) == 2:
        return images.reshape((images.shape[0],)+dims)
    raise BaseException("images.shape={}, dims={}".format(images.shape,dims))

def fix_image(image,dims=None):
    if len(image.shape) == 2:
        return np.expand_dims(image,axis=0)
    if len(image.shape) == 3:
        return np.einsum("xyc->cxy",image).reshape((-1,)+image.shape[0:2])
    if len(image.shape) == 1:
        return image.reshape((1,)+dims)
    raise BaseException("image.shape={}, dims={}".format(image.shape,dims))

import math

def plot_grid(images,w=10,path="plan.png"):
    import matplotlib.pyplot as plt
    l = 0
    images = fix_images(images)
    l = len(images)
    h = int(math.ceil(l/w))
    plt.figure(figsize=(w, h))
    for i,image in enumerate(images):
        ax = plt.subplot(h,w,i+1)
        try:
            plt.imshow(image,interpolation='nearest',cmap='gray',)
        except TypeError:
            TypeError("Invalid dimensions for image data: image={}".format(np.array(image).shape))
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
    plt.savefig(path)

def plot_grid2(images,w=10,path="plan.png"):
    import matplotlib.pyplot as plt
    images = fix_images(images)
    l = images.shape[0]
    h = int(math.ceil(l/w))
    margin = 3
    m_shape = (margin + np.array(images.shape[1:]))
    all_shape = m_shape * np.array((h,w))
    figure = np.ones(all_shape)
    print(images.shape,h,w,m_shape,figure.shape)
    for y in range(h):
        for x in range(w):
            begin = m_shape * np.array((y,x))
            end   = (m_shape * (np.array((y,x))+1)) - margin
            # print(begin,end,y*w+x)
            if y*w+x < len(images):
                figure[begin[0]:end[0],begin[1]:end[1]] = images[y*w+x]
    plt.figure(figsize=all_shape[::-1] * 0.01)
    plt.imshow(figure,interpolation='nearest',cmap='gray',)
    plt.savefig(path)

def plot_ae(ae,data,path):
    xs = data
    zs = ae.encode_binary(xs)
    ys = ae.decode_binary(zs)
    bs = np.round(zs)
    bys = ae.decode_binary(bs)
    import math
    l = int(math.sqrt(ae.N))
    _zs = zs.reshape((-1,l,l))
    _bs = bs.reshape((-1,l,l))
    images = []
    for seq in zip(xs, _zs, ys, _bs, bys):
        images.extend(seq)
    plot_grid(images, path=ae.local(path))
    return xs,zs,ys,bs,bys