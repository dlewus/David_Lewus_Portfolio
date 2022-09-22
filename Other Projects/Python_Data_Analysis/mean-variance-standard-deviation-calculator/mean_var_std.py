import numpy as np

def calculate(in_array):
    if len(in_array) != 9:
      raise ValueError("List must contain nine numbers.")
    array = np.array(in_array).reshape(3,3)
    mean = [array.mean(axis=0).tolist(), array.mean(axis=1).tolist(), array.mean().astype(float)]
    variance = [array.var(axis=0).tolist(), array.var(axis=1).tolist(), array.var().astype(float)]
    stdev = [array.std(axis=0).tolist(), array.std(axis=1).tolist(), array.std().astype(float)]
    max = [array.max(axis=0).tolist(), array.max(axis=1).tolist(), array.max().astype(float)]
    min = [array.min(axis=0).tolist(), array.min(axis=1).tolist(), array.min().astype(float)]
    sum = [array.sum(axis=0).tolist(), array.sum(axis=1).tolist(), array.sum().astype(float)]
    calculations = {
      'mean':mean,
      'variance':variance,
      'standard variation':stdev,
      'max':max,
      'min':min,
      'sum':sum
    }

    return calculations