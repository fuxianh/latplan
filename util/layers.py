from keras.layers import *

debug = False
# debug = True

def Print():
    def printer(x):
        print(x)
        return x
    return Lambda(printer)

from functools import reduce
def Sequential (array):
    def apply1(arg,f):
        if debug:
            print("applying {}({})".format(f,arg))
        result = f(arg)
        if debug:
            print(K.int_shape(result))
        return result
    return lambda x: reduce(apply1, array, x)

def ConditionalSequential (array, condition, **kwargs):
    def apply1(arg,f):
        if debug:
            print("applying {}({})".format(f,arg))
        concat = Concatenate(**kwargs)([condition, arg])
        return f(concat)
    return lambda x: reduce(apply1, array, x)

def Residual (layer):
    def res(x):
        return x+layer(x)
    return Lambda(res)

def ResUnit (*layers):
    return Residual(
        Sequential(layers))

def wrap(x,y,**kwargs):
    "wrap arbitrary operation"
    return Lambda(lambda x:y,**kwargs)(x)

def flatten(x):
    if K.ndim(x) >= 3:
        return Flatten()(x)
    else:
        return x

def set_trainable (model, flag):
    if hasattr(model, "layers"):
        for l in model.layers:
            set_trainable(l, flag)
    else:
        model.trainable = flag

def sort_binary(x):
    x = x.round().astype(np.uint64)
    steps = np.arange(start=x.shape[-1]-1, stop=-1, step=-1, dtype=np.uint64)
    two_exp = (2 << steps)//2
    x_int = np.sort(np.dot(x, two_exp))
    # print(x_int)
    xs=[]
    for i in range(((x.shape[-1]-1)//8)+1):
        xs.append(x_int % (2**8))
        x_int = x_int // (2**8)
    xs.reverse()
    # print(xs)
    tmp = np.stack(xs,axis=-1)
    # print(tmp)
    tmp = np.unpackbits(tmp.astype(np.uint8),-1)
    # print(tmp)
    return tmp[...,-x.shape[-1]:]

# tests
# sort_binary(np.array([[[1,0,0,0],[0,1,0,0],],[[0,1,0,0],[1,0,0,0]]]))
# sort_binary(np.array([[[1,0,0,0,0,0,0,0,0],[0,1,0,0,0,0,0,0,0],],
#                       [[0,1,0,0,0,0,0,0,0],[1,0,0,0,0,0,0,0,0]]]))

def count_params(model):
    from keras.utils.layer_utils import count_params
    model._check_trainable_weights_consistency()
    if hasattr(model, '_collected_trainable_weights'):
        trainable_count = count_params(model._collected_trainable_weights)
    else:
        trainable_count = count_params(model.trainable_weights)
    return trainable_count

from keras.callbacks import Callback
class GradientEarlyStopping(Callback):
    def __init__(self, monitor='val_loss',
                 min_grad=-0.0001, epoch=1, verbose=0, smooth=3):
        super(GradientEarlyStopping, self).__init__()
        self.monitor = monitor
        self.verbose = verbose
        self.min_grad = min_grad
        self.history = []
        self.epoch = epoch
        self.stopped_epoch = 0
        assert epoch >= 2
        if epoch > smooth*2:
            self.smooth = smooth
        else:
            print("epoch is too small for smoothing!")
            self.smooth = epoch//2

    def on_train_begin(self, logs=None):
        # Allow instances to be re-used
        self.wait = 0
        self.stopped_epoch = 0

    def gradient(self):
        h = np.array(self.history)
        
        # e.g. when smooth = 3, take the first/last 3 elements, average them over 3,
        # take the difference, then divide them by the epoch(== length of the history)
        return (h[-self.smooth:] - h[:self.smooth]).mean()/self.epoch
        
    def on_epoch_end(self, epoch, logs=None):
        import warnings
        current = logs.get(self.monitor)
        if current is None:
            warnings.warn('Early stopping requires %s available!' %
                          (self.monitor), RuntimeWarning)

        self.history.append(current) # to the last
        if len(self.history) > self.epoch:
            self.history.pop(0) # from the front
            if self.gradient() >= self.min_grad:
                self.model.stop_training = True
                self.stopped_epoch = epoch
                
    def on_train_end(self, logs=None):
        if self.stopped_epoch > 0 and self.verbose > 0:
            print('\nEpoch %05d: early stopping' % (self.stopped_epoch))
            print('history:',self.history)
            print('min_grad:',self.min_grad,"gradient:",self.gradient())
    
def anneal_rate(epoch,min=0.1,max=5.0):
    import math
    return math.log(max/min) / epoch

def take_true(y_cat):
    return wrap(y_cat, y_cat[:,:,0], name="take_true")

class ScheduledVariable:
    """General variable which is changed during the course of training according to some schedule"""
    def __init__(self,name="variable",):
        self.variable = K.variable(self.value(0), name=name)
        
    def value(self,epoch):
        """Should return a scalar value based on the current epoch.
Each subclasses should implement a method for it."""
        pass
    
    def update(self, epoch, logs):
        K.set_value(
            self.variable,
            self.value(epoch))

class GumbelSoftmax(ScheduledVariable):
    count = 0
    
    def __init__(self,N,M,min,max,full_epoch,annealer=anneal_rate,test_gumbel=False,test_softmax=False, alpha=1.):
        self.N = N
        self.M = M
        self.min = min
        self.max = max
        self.anneal_rate = annealer(full_epoch,min,max)
        self.test_gumbel = test_gumbel
        self.test_softmax = test_softmax
        self.alpha = alpha
        super(GumbelSoftmax, self).__init__("temperature")
        
    def call(self,logits):
        u = K.random_uniform(K.shape(logits), 0, 1)
        gumbel = - K.log(-K.log(u + 1e-20) + 1e-20)
        def softmax(x):
            return K.softmax(x / self.min)
        def argmax(x):
            return K.one_hot(K.argmax(x),self.M)
        
        if self.test_gumbel:
            test_logits = logits + gumbel
        else:
            test_logits = logits
        if self.test_softmax:
            one_hot_fn = softmax
        else:
            one_hot_fn = argmax
        return K.in_train_phase(
            K.softmax( ( logits + gumbel ) / self.variable ),
            one_hot_fn(test_logits))
    
    def __call__(self,prev):
        GumbelSoftmax.count += 1
        c = GumbelSoftmax.count-1
        logits = Reshape((self.N,self.M))(prev)

        layer = Lambda(self.call,name="gumbel_{}".format(c))

        q = K.softmax(logits)
        log_q = K.log(q + 1e-20)
        loss = K.mean(q * log_q) * self.alpha

        layer.add_loss(K.in_train_phase(loss, 0.0), logits)

        return layer(logits)

    def value(self,epoch):
        return np.max([self.min,
                       self.max * np.exp(- self.anneal_rate * epoch)])

class BaseSchedule(ScheduledVariable):
    def __init__(self,schedule={0:0}):
        self.schedule = schedule
        super(BaseSchedule, self).__init__()

class StepSchedule(BaseSchedule):
    """
       ______
       |
       |
   ____|

"""
    def value(self,epoch):
        assert epoch >= 0
        pkey = None
        pvalue = None
        for key, value in sorted(self.schedule.items(),reverse=True):
            # from large to small
            key = int(key) # for when restoring from the json file
            if key <= epoch:
                return value
            else:               # epoch < key 
                pkey, pvalue = key, value

        return pvalue

class LinearSchedule(BaseSchedule):
    """
          ______
         /
        /
   ____/

"""
    def value(self,epoch):
        assert epoch >= 0
        pkey = None
        pvalue = None
        for key, value in sorted(self.schedule.items(),reverse=True):
            # from large to small
            key = int(key) # for when restoring from the json file
            if key <= epoch:
                if pkey is None:
                    return value
                else:
                    return \
                        pvalue + \
                        ( epoch - pkey ) * ( value - pvalue ) / ( key - pkey )
            else:               # epoch < key 
                pkey, pvalue = key, value

        return pvalue

# modified version
import progressbar
class DynamicMessage(progressbar.DynamicMessage):
    def __call__(self, progress, data):
        val = data['dynamic_messages'][self.name]
        if val:
            return self.name + ': ' + '{}'.format(val)
        else:
            return self.name + ': ' + 6 * '-'



from keras.constraints import Constraint, maxnorm,nonneg,unitnorm
class UnitNormL1(Constraint):
    def __init__(self, axis=0):
        self.axis = axis

    def __call__(self, p):
        return p / (K.epsilon() + K.sum(p,
                                        axis=self.axis,
                                        keepdims=True))

    def get_config(self):
        return {'name': self.__class__.__name__,
                'axis': self.axis}
    
