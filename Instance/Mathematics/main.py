import matplotlib.pyplot as plt 
import numpy as np
from math import log 

s = np.array(range(1000))
y = log(s) 

plt.plot(s,y)

plt.show()