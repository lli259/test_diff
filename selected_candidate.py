import argparse,os
import numpy as np
from collections import Counter
import pandas as pd

def define_args(arg_parser):

    #arg_parser.add_argument('--num_candidate', nargs='*', default=['4'], help='Gringo input files')
    arg_parser.add_argument('--performance_data', nargs='*', default=['performance'], help='Gringo input files')
    arg_parser.add_argument('--cutoff', nargs='*', default=['200'], help='Gringo input files')
    arg_parser.add_argument('--selected_encodings', nargs='*', default=['selected_encodings'], help='Gringo input files')    
    arg_parser.add_argument('--encodings', nargs='*', default=['encodings'], help='Gringo input files')   


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    define_args(parser)
    args = parser.parse_args()



    t_cutoff=int(args.cutoff[0])
    data_folder=args.performance_data[0]
    enc_out_folder=args.selected_encodings[0]



    enc_folder=args.encodings[0]

    allcandidate=len(os.listdir(enc_folder))

    n_candidate_min=min(3,allcandidate)
    n_candidate_max=min(6,allcandidate)


    if  os.path.exists(enc_out_folder):
        if len(os.listdir(enc_out_folder)) == n_candidate_max-n_candidate_min+1 :
            ans_retrain=input('Encoding candidates were already selected! Need to rerun? y/n')
            if ans_retrain !='y':
                print('Encoding Candidates Generation Passes')
                exit()
            os.system('rm -r '+enc_out_folder+'/*')
        else:
            os.system('rm -r '+enc_out_folder+'/*')
    else:
        #os.system('mkdir '+feature_outfolder)
        pass


    data_f=data_folder+'/'+os.listdir(data_folder)[0]
    df=pd.read_csv(data_f)



    TIME=t_cutoff

    cols=df.columns
    df=df.set_index(cols[0])
    cols=df.columns

    # add wins_index,win_name, win_time column
    wins=[]
    sec_wins=[]
    for i in range(len(df)):
        values=df.iloc[i].values
        values_sorted=sorted(values)
        fillwin=0
        fillsec=0
        for index,value in enumerate(values):
            if (value==values_sorted[0]) and (fillwin==0):
                wins.append(index)
                fillwin=1
            if (value==values_sorted[1]) and (fillsec==0):
                sec_wins.append(index)
                fillsec=1
        
    df['wins']=wins
    win_names=[cols[i] for i in wins]
    df['win_name']=win_names

    df['secwins']=sec_wins
    secwin_names=[cols[i] for i in sec_wins]
    df['secwin_name']=secwin_names

    win_time=[]
    for i in range(len(df)):
        win=df.iloc[i].values[wins[i]]
        win_time.append(win)

    df['win_time']=win_time



    secwin_time=[]
    for i in range(len(df)):
        win=df.iloc[i].values[sec_wins[i]]
        secwin_time.append(win)

    df['secwin_time']=secwin_time


    if not os.path.exists(data_folder+"_output"):
        os.system('mkdir '+data_folder+"_output")

    df.to_csv(data_folder+"_output/allwins.csv")


    ct=Counter(win_names)


    score_dict={}
    for enc in cols:
        score_dict[enc]=0

    print(score_dict)

    #the number of wins
    win_tuple=[]
    for i in ct.items():
        win_tuple.append((i[1],i[0]))
    win_tuple=sorted(win_tuple)

    winsore=1
    win=0
    for i,v in enumerate(win_tuple):
        name=v[1]
        this_win=v[0]
        if this_win != win:
            winsore+=1
            score_dict[name]+=winsore
            win=this_win
        else:
            score_dict[name]+=winsore

    print(win_tuple,score_dict)



    solving_tuple=[]
    avg_rt_tuple=[]
    for i in cols:
        alltime=df[i].values
        solved=[1 if j <TIME else 0 for j in alltime]
        solved_p=sum(solved)/len(alltime)
        avg_t=sum(alltime)/len(alltime)
        solving_tuple.append((solved_p,i))
        avg_rt_tuple.append((avg_t,i))


    solving_tuple=sorted(solving_tuple)


    winsore=0
    solving=0
    for i,v in enumerate(solving_tuple):
        #print(v)
        name=v[1]
        this_solving=v[0]
        if this_solving != solving:
            winsore+=1
            score_dict[name]+=winsore
            solving=this_solving
        else:
            #print(score_dict,name,v)
            score_dict[name]+=winsore
            
    print(solving_tuple,score_dict)

    avg_rt_tuple=sorted(avg_rt_tuple)


    winsore=len(cols)
    avg_t=0
    for i,v in enumerate(avg_rt_tuple):
        name=v[1]
        this_avg_t=v[0]
        if this_avg_t != avg_t:
            winsore-=1
            score_dict[name]+=winsore
            avg_t=this_avg_t
        else:
            score_dict[name]+=winsore

    print(avg_rt_tuple,score_dict)

    rank_tuple=[]
    for k in score_dict.keys():
        v=score_dict[k]
        rank_tuple.append((v,k))

    rank_tuple=sorted(rank_tuple,reverse=True)





    #save to folder

    if not os.path.exists(data_folder+"_selected"):
        os.system('mkdir '+data_folder+"_selected")
    else:
        os.system('rm -r '+data_folder+"_selected/*")      

    #enc_out_folder=enc_folder+'_selected'
    if not os.path.exists(enc_out_folder):
        os.system('mkdir '+enc_out_folder)
    #else:
        #os.system('rm -r '+enc_out_folder+'/*')   

    for index_candidate,n_candidate in enumerate(range(n_candidate_min,n_candidate_max+1)):
        top_col=[]
        for v in rank_tuple[:n_candidate]:
            top_col.append(v[1])

        dfcp=df.copy()
        dfcp=dfcp[top_col]


        if not os.path.exists(data_folder+"_selected/group"+str(index_candidate+1)):
            os.makedirs(data_folder+"_selected/group"+str(index_candidate+1))
            print('mkdir '+data_folder+"_selected/group"+str(index_candidate+1))
        else:
            print('error mkdir '+data_folder+"_selected/group"+str(index_candidate+1))
                
        dfcp.to_csv(data_folder+"_selected/group"+str(index_candidate+1)+"/performance_selected.csv")

        print('performance selection finished.',"group"+str(index_candidate+1),n_candidate,'encodings')

        #select encodings
        if not os.path.exists(enc_out_folder+'/group'+str(index_candidate+1)):
            os.makedirs(enc_out_folder+'/group'+str(index_candidate+1))  
        else:
            os.system('rm '+enc_out_folder+'/group'+str(index_candidate+1)+'/*')
        
        for enc_name in top_col:
            os.system('cp '+enc_folder+'/'+enc_name+'.lp '+enc_out_folder+'/group'+str(index_candidate+1)+'/')
        
        print('encodings candidate generated.',"group"+str(index_candidate+1),n_candidate,'encodings')