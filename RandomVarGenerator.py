import numpy as np
from scipy.stats import erlang


# np.random.seed(42)

class RandomVarGenerator:

    def __init__(self):
        pass

    def uniform(self, min_num, max_num):
        """uniform(min_num,max_num) returns uniform random number between min_num and max_num"""
        rn = float("{:.2f}".format(np.random.uniform(min_num, max_num)))
        return rn

    def exponential(self, mean):
        """uniform(min_num,max_num) returns exponential random number with mean mean """
        rn = float("{:.2f}".format(np.random.exponential(mean)))
        return rn

    def erlang(self, mean, n):
        """erlang(shape , scale) will return the erlang random number with shape=k exponential distribution with each having mean=scale=1/lambda"""
        rn = float("{:.2f}".format(erlang.rvs(a=n, scale=mean)))
        return rn / n


# testing
"""
e = RandomVarGenerator()
for i in range(100):
    print(str(e.exponential(168)))
# print('uniform : ',e.uniform(2,5))
"""
# print('earlang : ', e.erlang(1, 2))
# print('exponential : ',e.exponential(2))
