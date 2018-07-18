
import keras.backend as K

from keras.objectives import binary_crossentropy as bce
from keras.objectives import mse, mae

def BCE(x, y):
    return bce(K.batch_flatten(x),
               K.batch_flatten(y))
def MSE(x, y):
    return mse(K.batch_flatten(x),
               K.batch_flatten(y))


# Hausdorff distance
# (Piramuthu 1999) The Hausdor Distance Measure for Feature Selection in Learning Applications
# Hausdorff distance is defined by sup_x inf_y d(x,y).

# algorithm: repeat both x and y N times for N objects.
# pros: matrix operation, fast.
# cons: N^2 memory

def _repeat_nxn_matrix(x,y,N):
    y2 = K.expand_dims(y,1)          # [batch, 1, N, features]
    y2 = K.repeat_elements(y2, N, 1) # [batch, N, N, features]
    # results in [[y1,y2,y3...],[y1,y2,y3...],...]
    
    x2 = K.repeat_elements(x, N, 1)  # [batch, N*N, features]
    x2 = K.reshape(x2, K.shape(y2))  # [batch, N, N, features]
    # results in [[x1,x1,x1...],[x2,x2,x2...],...]
    
    return x2, y2

def Hausdorff(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)

    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    sup_x = K.max(K.min(d, axis=2), axis=1) # [batch]
    sup_y = K.max(K.min(d, axis=1), axis=1) # [batch] --- mind the axis
    return K.mean(K.maximum(sup_x, sup_y))

def DirectedHausdorff1(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)

    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    sup_x = K.max(K.min(d, axis=2), axis=1) # [batch]
    return K.mean(sup_x)

def DirectedHausdorff2(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)

    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    sup_y = K.max(K.min(d, axis=1), axis=1) # [batch] --- mind the axis
    return K.mean(sup_y)

# average distance: (Fujita 2013) Metrics based on average distance between sets

def SumMin(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    sum_x = K.sum(K.min(d, axis=2), axis=1) # [batch]
    sum_y = K.sum(K.min(d, axis=1), axis=1) # [batch] --- mind the axis
    return K.mean(K.maximum(sum_x, sum_y))

def DirectedSumMin1(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    sum_x = K.sum(K.min(d, axis=2), axis=1) # [batch]
    return K.mean(sum_x)

def DirectedSumMin2(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    sum_y = K.sum(K.min(d, axis=1), axis=1) # [batch] --- mind the axis
    return K.mean(sum_y)

# new: SumLSE, only for negative log likelihood (BCE)

def SumLSE(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    log_likelihood = -d

    sum_x = -K.sum(K.logsumexp(log_likelihood, axis=2), axis=1) # [batch]
    sum_y = -K.sum(K.logsumexp(log_likelihood, axis=1), axis=1) # [batch]
    return K.mean(K.maximum(sum_x, sum_y))

def DirectedSumLSE1(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    log_likelihood = -d

    sum_x = -K.sum(K.logsumexp(log_likelihood, axis=2), axis=1) # [batch]
    return K.mean(sum_x)

def DirectedSumLSE2(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    log_likelihood = -d

    sum_y = -K.sum(K.logsumexp(log_likelihood, axis=1), axis=1) # [batch]
    return K.mean(sum_y)

def MaxLSE(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sub(distance(x2,y2), axis=-1) # [batch, N, N]

    log_likelihood = -d

    max_x = -K.max(K.logsumexp(log_likelihood, axis=2), axis=1) # [batch]
    max_y = -K.max(K.logsumexp(log_likelihood, axis=1), axis=1) # [batch]
    return K.mean(K.maximum(max_x, max_y))

def DirectedMaxLSE1(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    log_likelihood = -d

    max_x = -K.max(K.logsumexp(log_likelihood, axis=2), axis=1) # [batch]
    return K.mean(max_x)

def DirectedMaxLSE2(distance, x, y, N):
    x2, y2 = _repeat_nxn_matrix(x,y,N)
    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    log_likelihood = -d

    max_y = -K.max(K.logsumexp(log_likelihood, axis=1), axis=1) # [batch]
    return K.mean(max_y)

def LSELSE(distance, x, y, N):
    y2 = K.expand_dims(y,1)          # [batch, 1, N, features]
    y2 = K.repeat_elements(y2, N, 1) # [batch, N, N, features]
    
    x2 = K.repeat_elements(x, N, 1)  # [batch, N*N, features]
    x2 = K.reshape(x2, K.shape(y2))  # [batch, N, N, features]

    d  = K.sum(distance(x2,y2), axis=-1) # [batch, N, N]

    return K.mean(K.logsumexp(d, axis=[1,2]))

def set_BCE(x, y, N, combine=DirectedSumLSE1):
    return combine(K.binary_crossentropy,x,y,N)

def set_MSE(x, y, N, combine=DirectedSumMin1):
    return combine(lambda x,y: K.square(x-y),x,y,N)

