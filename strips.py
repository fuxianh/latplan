#!/usr/bin/env python3

import config
import numpy as np
import numpy.random as random
import latplan
import latplan.model
from latplan.util        import curry
from latplan.util.tuning import grid_search, nn_task
from latplan.util.noise  import gaussian

import keras.backend as K
import tensorflow as tf

import os
import os.path

float_formatter = lambda x: "%.5f" % x
np.set_printoptions(threshold=float('nan'),formatter={'float_kind':float_formatter})

mode     = 'learn_dump'
sae_path = None

# default values
default_parameters = {
    'lr'              : 0.0001, # learning rate
    'batch_size'      : 2000,
    'epoch'           : 1000,   # training epoch. If epoch < full_epoch, it just stops there.
    'max_temperature' : 5.0,
    'min_temperature' : 0.7,
    'M'               : 2,
    'optimizer'       : 'adam',
}

def select(data,num):
    return data[random.randint(0,data.shape[0],num)]

def plot_autoencoding_image(ae,test,train):
    if 'plot' not in mode:
        return
    rz = np.random.randint(0,2,(6,ae.parameters['N']))
    ae.plot_autodecode(rz,ae.local("autodecoding_random.png"),verbose=True)
    ae.plot(test[:6],ae.local("autoencoding_test.png"),verbose=True)
    ae.plot(train[:6],ae.local("autoencoding_train.png"),verbose=True)

def plot_variance_image(ae,test,train):
    if 'plot' not in mode:
        return
    if hasattr(ae,"plot_variance"):
        ae.plot_variance(select(test,6), ae.local("variance_test.png"),  verbose=True)
        ae.plot_variance(select(train,6),ae.local("variance_train.png"), verbose=True)
    
def dump_all_actions(ae,configs,trans_fn,name="all_actions.csv",repeat=1):
    if 'dump' not in mode:
        return
    l = len(configs)
    batch = 5000
    loop = (l // batch) + 1
    try:
        print(ae.local(name))
        with open(ae.local(name), 'wb') as f:
            for i in range(repeat):
                for begin in range(0,loop*batch,batch):
                    end = begin + batch
                    print((begin,end,len(configs)))
                    transitions = trans_fn(configs[begin:end])
                    orig, dest = transitions[0], transitions[1]
                    orig_b = ae.encode(orig,batch_size=1000).round().astype(int)
                    dest_b = ae.encode(dest,batch_size=1000).round().astype(int)
                    actions = np.concatenate((orig_b,dest_b), axis=1)
                    np.savetxt(f,actions,"%d")
    except AttributeError:
        print("this AE does not support dumping")
    except KeyboardInterrupt:
        print("dump stopped")

def dump_actions(ae,transitions,name="actions.csv",repeat=1):
    if 'dump' not in mode:
        return
    try:
        print(ae.local(name))
        with open(ae.local(name), 'wb') as f:
            orig, dest = transitions[0], transitions[1]
            for i in range(repeat):
                orig_b = ae.encode(orig,batch_size=1000).round().astype(int)
                dest_b = ae.encode(dest,batch_size=1000).round().astype(int)
                actions = np.concatenate((orig_b,dest_b), axis=1)
                np.savetxt(f,actions,"%d")
    except AttributeError:
        print("this AE does not support dumping")
    except KeyboardInterrupt:
        print("dump stopped")
    import subprocess
    
def dump_all_states(ae,configs,states_fn,name="all_states.csv",repeat=1):
    if 'dump' not in mode:
        return
    l = len(configs)
    batch = 5000
    loop = (l // batch) + 1
    try:
        print(ae.local(name))
        with open(ae.local(name), 'wb') as f:
            for i in range(repeat):
                for begin in range(0,loop*batch,batch):
                    end = begin + batch
                    print((begin,end,len(configs)))
                    states = states_fn(configs[begin:end])
                    states_b = ae.encode(states,batch_size=1000).round().astype(int)
                    np.savetxt(f,states_b,"%d")
    except AttributeError:
        print("this AE does not support dumping")
    except KeyboardInterrupt:
        print("dump stopped")

def dump_states(ae,states,name="states.csv",repeat=1):
    if 'dump' not in mode:
        return
    try:
        print(ae.local(name))
        with open(ae.local(name), 'wb') as f:
            for i in range(repeat):
                np.savetxt(f,ae.encode(states,batch_size=1000).round().astype(int),"%d")
    except AttributeError:
        print("this AE does not support dumping")
    except KeyboardInterrupt:
        print("dump stopped")
    import subprocess
    

################################################################

# note: lightsout has epoch 200

def run(path,train,test,parameters,train_out=None,test_out=None,):
    if 'learn' in mode:
        if train_out is None:
            train_out = train
        if test_out is None:
            test_out = test
        from latplan.util import curry
        def fn(ae):
            ae.report(train,
                      test_data     = test,
                      train_data_to = train_out,
                      test_data_to  = test_out,)
            # plot_autoencoding_image(ae,test,train)
            
        ae, _, _ = grid_search(curry(nn_task, latplan.model.get(default_parameters["aeclass"]),
                                     path,
                                     train, train_out, test, test_out), # noise data is used for tuning metric
                               default_parameters,
                               parameters,
                               shuffle     = False,
                               report_best = fn,)
        ae.save()
    else:
        ae = latplan.model.get(default_parameters["aeclass"])(path).load()
    return ae

def show_summary(ae,train,test):
    if 'summary' in mode:
        ae.summary()
        ae.report(train, test, train, test)

################################################################

def puzzle(aeclass="ConvolutionalGumbelAE",type='mnist',width=3,height=3,N=36,num_examples=6500):
    for name, value in locals().items():
        default_parameters[name] = value
    
    parameters = {
        'layer'      :[1000],# [400,4000],
        'clayer'     :[16],# [400,4000],
        'dropout'    :[0.4], #[0.1,0.4],
        'noise'      :[0.4],
        'dropout_z'  :[False],
        'activation' :['tanh'],
        'epoch'      :[150],
        'batch_size' :[4000],
        'lr'         :[0.001],
    }
    import importlib
    p = importlib.import_module('latplan.puzzles.puzzle_{}'.format(type))
    p.setup()
    configs = p.generate_configs(width*height)
    configs = np.array([ c for c in configs ])
    assert len(configs) >= num_examples
    print(len(configs))
    random.shuffle(configs)
    transitions = p.transitions(width,height,configs[:num_examples],one_per_state=True)
    states = np.concatenate((transitions[0], transitions[1]), axis=0)
    print(states.shape)
    train = states[:int(len(states)*0.9)]
    test  = states[int(len(states)*0.9):]
    ae = run(os.path.join("samples",sae_path), train, test, parameters)
    show_summary(ae, train, test)
    plot_autoencoding_image(ae,test[:1000],train[:1000])
    plot_variance_image(ae,test[:1000],train[:1000])
    dump_actions(ae,transitions)
    dump_states (ae,states)
    dump_all_actions(ae,configs,        lambda configs: p.transitions(width,height,configs),)
    dump_all_states(ae,configs,        lambda configs: p.states(width,height,configs),)

def hanoi(aeclass="ConvolutionalGumbelAE",disks=7,towers=4,N=36,num_examples=6500):
    for name, value in locals().items():
        default_parameters[name] = value
    parameters = {
        'layer'      :[1000],# [400,4000],
        'clayer'     :[12],# [400,4000],
        'dropout'    :[0.6], #[0.1,0.4],
        'noise'      :[0.4],
        'N'          :[N],  #[25,49],
        'dropout_z'  :[False],
        'activation' : ['tanh'],
        'epoch'      :[1000],
        'batch_size' :[500],
        'optimizer'  :['adam'],
        'lr'         :[0.001],
    }
    print("this setting is tuned for conv")
    import latplan.puzzles.hanoi as p
    configs = p.generate_configs(disks,towers)
    configs = np.array([ c for c in configs ])
    assert len(configs) >= num_examples
    print(len(configs))
    random.shuffle(configs)
    transitions = p.transitions(disks,towers,configs[:num_examples],one_per_state=True)
    states = np.concatenate((transitions[0], transitions[1]), axis=0)
    print(states.shape)
    train = states[:int(len(states)*0.9)]
    test  = states[int(len(states)*0.9):]
    ae = run(os.path.join("samples",sae_path), train, test, parameters)
    print("*** NOTE *** if l_rec is above 0.01, it is most likely not learning the correct model")
    show_summary(ae, train, test)
    plot_autoencoding_image(ae,test[:1000],train[:1000])
    plot_variance_image(ae,test[:1000],train[:1000])
    dump_actions(ae,transitions,repeat=100)
    dump_states (ae,states,repeat=100)
    dump_all_actions(ae,configs,        lambda configs: p.transitions(disks,towers,configs),repeat=100)
    dump_all_states(ae,configs,        lambda configs: p.states(disks,towers,configs),repeat=100)

def lightsout(aeclass="ConvolutionalGumbelAE",type='digital',size=4,N=36,num_examples=6500):
    for name, value in locals().items():
        default_parameters[name] = value
    parameters = {
        'layer'      :[1000],# [400,4000],
        'clayer'     :[16],# [400,4000],
        'dropout'    :[0.4], #[0.1,0.4],
        'noise'      :[0.4],
        'N'          :[N],  #[25,49],
        'dropout_z'  :[False],
        'activation' : ['tanh'],
        'epoch'      :[100],
        'batch_size' :[2000],
        'lr'         :[0.001],
    }
    import importlib
    p = importlib.import_module('latplan.puzzles.lightsout_{}'.format(type))
    configs = p.generate_configs(size)
    configs = np.array([ c for c in configs ])
    assert len(configs) >= num_examples
    print(len(configs))
    random.shuffle(configs)
    transitions = p.transitions(size,configs[:num_examples],one_per_state=True)
    states = np.concatenate((transitions[0], transitions[1]), axis=0)
    print(states.shape)
    train = states[:int(len(states)*0.9)]
    test  = states[int(len(states)*0.9):]
    ae = run(os.path.join("samples",sae_path), train, test, parameters)
    show_summary(ae, train, test)
    plot_autoencoding_image(ae,test[:1000],train[:1000])
    plot_variance_image(ae,test[:1000],train[:1000])
    dump_actions(ae,transitions)
    dump_states (ae,states)
    dump_all_actions(ae,configs,        lambda configs: p.transitions(size,configs),)
    dump_all_states(ae,configs,        lambda configs: p.states(size,configs),)

def main():
    global mode, sae_path
    import sys
    if len(sys.argv) == 1:
        print({ k for k in dir(latplan.model)})
        gs = globals()
        print({ k for k in gs if hasattr(gs[k], '__call__')})
    else:
        print('args:',sys.argv)
        sys.argv.pop(0)
        mode = sys.argv.pop(0)
        sae_path = "_".join(sys.argv)
        task = sys.argv.pop(0)

        def myeval(str):
            try:
                return eval(str)
            except:
                return str
        
        globals()[task](*map(myeval,sys.argv))
    
if __name__ == '__main__':
    main()
