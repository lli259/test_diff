import argparse,os
import numpy as np
import pandas as pd


def define_args(arg_parser):

    arg_parser.add_argument('--performance_folder', nargs='*', default=['performance_selected'], help='Gringo input files')
    arg_parser.add_argument('--cutoff', nargs='*', default=['200'], help='Gringo input files')
    arg_parser.add_argument('--interleave_out', nargs='*', default=['interleave'], help='Gringo input files') 


if __name__ == "__main__":
    print("------------------------------------------------")
    print('\nCollecting results on validation set...')
    parser = argparse.ArgumentParser()
    define_args(parser)
    args = parser.parse_args()

    results=[]
    with open('evaluation/result.csv','r') as f:
        results=f.readlines()
    
    for l in results:
        print(l[:-1])
    
    df=pd.read_csv('evaluation/result.csv')
    df=df.sort_values(by=['solving'])
    df=df[df.solving==df.iloc[-1].solving]
    df=df.sort_values(by=['time'])
    print('\nBest Solution:',df.iloc[0]['method'])
    print('\n......................')
    print('\nAll solutions evaluated on new instances...')
    with open('evaluation/result2.csv','r') as f:
        results=f.readlines()
    for l in results:
        print(l[:-1])
        if 'kNN' in l[:3]:
            print('\n')