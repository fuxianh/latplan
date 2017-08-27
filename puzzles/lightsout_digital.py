#!/usr/bin/env python3

import numpy as np
from .model.lightsout import generate_configs, generate_random_configs, successors
from .util import wrap
from .util import preprocess

panels = [
    [[0, 0, 0, 0, 0,],
     [0, 0, 1, 0, 0,],
     [0, 1, 1, 1, 0,],
     [0, 0, 1, 0, 0,],
     [0, 0, 0, 0, 0,],],
    [[0, 0, 0, 0, 0,],
     [0, 0, 0, 0, 0,],
     [0, 0, 0, 0, 0,],
     [0, 0, 0, 0, 0,],
     [0, 0, 0, 0, 0,],]]

panels = np.array(panels)

# config representation: on = 1, off = -1 , not zero!!

def setup():
    pass

def generate_cpu(configs):
    import math
    size = int(math.sqrt(len(configs[0])))
    base = panels.shape[1]
    dim = base*size
    def generate(config):
        figure = np.zeros((dim,dim))
        for pos,value in enumerate(config):
            x = pos % size
            y = pos // size
            if value > 0:
                figure[y*base:(y+1)*base,
                       x*base:(x+1)*base] = panels[0]
            else:
                figure[y*base:(y+1)*base,
                       x*base:(x+1)*base] = panels[1]
        return preprocess(figure)
    return np.array([ generate(c) for c in configs ]).reshape((-1,dim,dim))

def generate_gpu(configs, **kwargs):
    import math
    size = int(math.sqrt(len(configs[0])))
    base = panels.shape[1]
    dim = base*size

    from keras.layers import Input, Reshape
    from keras.models import Model
    from keras import backend as K
    import tensorflow as tf
    
    def build():
        P = 2
        configs = Input(shape=(size*size,))
        _configs = 1 - K.round((configs/2)+0.5) # from -1/1 to 1/0
        configs_one_hot = K.one_hot(K.cast(_configs,'int32'), P)
        configs_one_hot = K.reshape(configs_one_hot, [-1,P])
        _panels = K.variable(panels)
        _panels = K.reshape(_panels, [P, base*base])
        states = tf.matmul(configs_one_hot, _panels)
        states = K.reshape(states, [-1, size, size, base, base])
        states = K.permute_dimensions(states, [0, 1, 3, 2, 4])
        states = K.reshape(states, [-1, size*base, size*base])
        return Model(configs, wrap(configs, states))

    return build().predict(np.array(configs),**kwargs)

generate = generate_gpu

def states(size, configs=None):
    if configs is None:
        configs = generate_configs(size)
    return generate(configs)

def transitions_old(size, configs=None, one_per_state=False, **kwargs):
    if configs is None:
        configs = generate_configs(size)
    if one_per_state:
        def pickone(thing):
            index = np.random.randint(0,len(thing))
            return thing[index]
        transitions = np.array([
            generate([c1,pickone(successors(c1))], **kwargs)
            for c1 in configs ])
    else:
        transitions = np.array([ generate([c1,c2])
                                 for c1 in configs for c2 in successors(c1) ])
    return np.einsum('ab...->ba...',transitions)

def transitions(size, configs=None, one_per_state=False, **kwargs):
    if configs is None:
        configs = generate_configs(digit)
    if one_per_state:
        def pickone(thing):
            index = np.random.randint(0,len(thing))
            return thing[index]
        pre = generate(configs, **kwargs)
        suc = generate(np.array([pickone(successors(c1)) for c1 in configs ]), **kwargs)
        return np.array([pre, suc])
    else:
        transitions = np.array([ [c1,c2] for c1 in configs for c2 in successors(c1) ])
        pre = generate(transitions[:,0,:], **kwargs)
        suc = generate(transitions[:,1,:], **kwargs)
        return np.array([pre, suc])

def validate_states(states,verbose=True,**kwargs):
    base = panels.shape[1]
    size = states.shape[1]//base
    dim  = states.shape[1]
    def build():
        from keras.layers import Input
        from keras.models import Model
        from keras import backend as K
        import tensorflow as tf
        states = Input(shape=(dim,dim))
        s = states
        s = K.reshape(s,[-1,size,base,size,base])
        s = K.permute_dimensions(s, [0,1,3,2,4])
        s = K.reshape(s,[-1,size,size,1,base,base])
        s = K.tile   (s,[1, 1, 1, 2, 1, 1,]) # number of panels : 2

        allpanels = K.variable(panels)
        allpanels = K.reshape(allpanels, [1,1,1,2,base,base])
        allpanels = K.tile(allpanels, [K.shape(s)[0], size,size, 1, 1, 1])

        error = K.binary_crossentropy(s, allpanels)
        error = K.mean(error, axis=(4,5))
        
        matches = 1 - K.clip(K.sign(error - 0.01),0,1)

        num_matches = K.sum(matches, axis=3)
        panels_ok = K.all(K.equal(num_matches, 1), (1,2))
        panels_ng = K.any(K.not_equal(num_matches, 1), (1,2))
        panels_nomatch   = K.any(K.equal(num_matches, 0), (1,2))
        panels_ambiguous = K.any(K.greater(num_matches, 1), (1,2))

        validity = panels_ok
        
        if verbose:
            return Model(states,
                         [ wrap(states, x) for x in [panels_ng,
                                                     panels_nomatch,
                                                     panels_ambiguous,
                                                     validity]])
        else:
            return Model(states, wrap(states, validity))
        
    model = build()
    #     model.summary()
    if verbose:
        panels_ng, panels_nomatch, panels_ambiguous, validity = model.predict(states, **kwargs)
        print(np.count_nonzero(panels_ng),       "images have some panels which match 0 or >2 panels, out of which")
        print(np.count_nonzero(panels_nomatch),  "images have some panels which are unlike any panels")
        print(np.count_nonzero(panels_ambiguous),"images have some panels which match >2 panels")
        print(np.count_nonzero(validity),        "images have panels (all of them) which match exactly 1 panel each")
        return validity
    else:
        validity = model.predict(states, **kwargs)
        return validity


def to_configs(states, verbose=True, **kwargs):
    base = panels.shape[1]
    size = states.shape[1]//base
    dim  = states.shape[1]

    from keras.layers import Input, Reshape
    from keras.models import Model
    from keras import backend as K
    import tensorflow as tf
    
    def build():
        states = Input(shape=(dim,dim))
        s = states
        s = K.reshape(s,[-1,size,base,size,base])
        s = K.permute_dimensions(s, [0,1,3,2,4])
        s = K.reshape(s,[-1,size,size,1,base,base])
        s = K.tile   (s,[1, 1, 1, 2, 1, 1,]) # number of panels : 2
        
        allpanels = K.variable(panels)
        allpanels = K.reshape(allpanels, [1,1,1,2,base,base])
        allpanels = K.tile(allpanels, [K.shape(s)[0], size,size, 1, 1, 1])
        
        error = K.binary_crossentropy(s, allpanels)
        error = K.mean(error, axis=(4,5))

        matches = 1 - K.clip(K.sign(error - 0.01),0,1)
        # a, h, w, panel
        matches = K.reshape(matches, [K.shape(s)[0], size * size, -1])
        # a, pos, panel
        config = matches * K.arange(2,dtype='float')
        config = K.sum(config, axis=-1)
        # this is 0,1 configs; for compatibility, we need -1 and 1
        config = - (config - 0.5)*2
        return Model(states, wrap(states, K.round(config)))
    
    model = build()
    return model.predict(states, **kwargs)


def validate_transitions(transitions, check_states=True, **kwargs):
    pre = np.array(transitions[0])
    suc = np.array(transitions[1])

    if check_states:
        pre_validation = validate_states(pre, verbose=False, **kwargs)
        suc_validation = validate_states(suc, verbose=False, **kwargs)

    pre_configs = to_configs(pre, verbose=False, **kwargs)
    suc_configs = to_configs(suc, verbose=False, **kwargs)
    
    results = []
    if check_states:
        for pre_c, suc_c, pre_validation, suc_validation in zip(pre_configs, suc_configs, pre_validation, suc_validation):

            if pre_validation and suc_validation:
                succs = successors(pre_c)
                results.append(np.any(np.all(np.equal(succs, suc_c), axis=1)))
            else:
                results.append(False)
    else:
        for pre_c, suc_c in zip(pre_configs, suc_configs):
            succs = successors(pre_c)
            results.append(np.any(np.all(np.equal(succs, suc_c), axis=1)))
    return results
