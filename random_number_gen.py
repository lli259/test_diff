import pandas as pd
import numpy as np

for ec in range(0,4):
    r=np.random.rand(100,60)*200
    df=pd.DataFrame(r,index=[ 'inst' + str(i) for i in range(0,100)], columns=[ 'f' + str(i) for i in range(0,60)])
    df.to_csv('ec_'+str(ec)+'_features.csv')



