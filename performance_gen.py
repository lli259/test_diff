import argparse,os
import numpy as np
from collections import Counter
import pandas as pd
import subprocess
from multiprocessing import Process
from multiprocessing import Semaphore

def define_args(arg_parser):

    arg_parser.add_argument('--encodings', nargs='*', default=['encodings'], help='Gringo input files')
    arg_parser.add_argument('--instances', nargs='*', default=['instances'], help='Gringo input files')    
    arg_parser.add_argument('--performance_data', nargs='*', default=['performance'], help='Gringo input files')
    arg_parser.add_argument('--cutoff', nargs='*', default=['200'], help='Gringo input files')


def encoding_name_parser(enc_name):
    return enc_name.split('.')[0].split('_')[0]

def clasp_result_parser(outputs):

    outputs=outputs.split('\n')
    re_time=0
    re_model=0
    for lineout in outputs:
        if 'Time' in lineout[:4]:
            re_time=lineout.split(':')[1].split('s')[0][1:]
        if 'Models' in lineout[:6]:
            re_model=lineout.split(':')[1][1:]
    return re_time,re_model

def getins(infile):

    if not os.path.isfile(infile):
        return []
    ret=[]
    with open(infile,'r') as f:
        lines=f.readlines()
        if len(lines)<2:
            return []
        for l in lines[1:]:
            ret.append(l.split(",")[0])
    return ret

def get_solved_instance(outfile):

    run_inst=getins(outfile)
    if len(run_inst)==0:
        with open(outfile,'w') as f:
            f.write('inst,time,model\n')
    return run_inst


def run_multiprocess(enc_name,encodings_folder,instances_names,instances_folder,out_folder,cutoff_t,process_name,sema):

    #print('process {} running on '.format(process_name))

    #check if enc_result.csv exist, 
    #if exists, get instances
    #if not, create
    outfile=out_folder+'/'+encoding_name_parser(enc_name)+'_result.csv'
    solved_instances=get_solved_instance(outfile)

    #save runtime

    #print('Solving instances using '+enc_name)


    for instance in instances_names:  
        if not instance in solved_instances:         
            
            cmdline='tools/gringo '+encodings_folder+'/'+enc_name +' '+instances_folder+'/'+instance +' | tools/clasp --time-limit=' + str(cutoff_t)
            #print(cmdline)
            print('Solving ', enc_name,instance,'using process ',process_name)
            process_ret = subprocess.getoutput(cmdline)
            #getoutput
            tm,md=clasp_result_parser(process_ret)
            print('Result ',enc_name,instance,tm,md)
            with open (outfile,'a') as f:
                f.write(str(instance)+','+str(tm)+','+str(md)+'\n')   

    sema.release()


def run_instances_for_enc(encodings_folder,instances_names,instances_folder,out_folder,cutoff_t):

    with open(out_folder+'/cutoff.txt','w') as f:
        f.write(str(cutoff_t))


    concurrency = 4
    total_task_num = os.listdir(encodings_folder)
    sema = Semaphore(concurrency)
    all_processes = []
    for i,enc_name in enumerate(total_task_num):
        sema.acquire()
        p = Process(target=run_multiprocess, args=(enc_name,encodings_folder,instances_names,instances_folder,out_folder,cutoff_t,i,sema))
        all_processes.append(p)
        p.start()

    for p in all_processes:
        p.join()
    print('Performance collection Done!')

def combine_result(data_folder1,data_folder2):

    output_file='performance.csv'
    allcsv=os.listdir(data_folder1)
    allcsv=[i for i in allcsv if 'result.csv' in i]
    pd1=pd.read_csv(data_folder1+'/'+allcsv[0])
    cols=pd1.columns.values
    pd1=pd1.set_index(cols[0])
    timecol='time'
    pd1=pd1[[timecol]]
    cols=[ allcsv[0].split('_')[0] ]
    pd1.columns=cols

    for pointer in range(1,len(allcsv)):
        #print(pointer,len(allcsv),data_folder1+'/'+allcsv[pointer])
        pd11=pd.read_csv(data_folder1+'/'+allcsv[pointer])
        cols=pd11.columns.values
        pd11=pd11.set_index(cols[0])
        timecol='time'
        #print('pd1',pd1)
        #print('pd11',pd11)
        pd11=pd11[[timecol]]
        cols=[ allcsv[pointer].split('_')[0] ]
        pd11.columns=cols

        pd1=pd1.join(pd11)
        pd1=pd1.dropna()
    pd1.to_csv(data_folder2+'/'+output_file)


#choose len/10, at least 10 or len, at most 50, to test hardness and set cutoff time
def select_prerun_instance(instances_names):
    np.random.seed(1)
    sample_size=int(len(instances_names)/10)
    if sample_size>50:
        sample_size=50
    else:
        if sample_size<10:
            sample_size=min(len(instances_names),10)
    selected_enc=np.random.choice(instances_names,sample_size,replace=False)

    return selected_enc

def make_cutoff():
    if not os.path.exists('cutoff'):
        os.mkdir('cutoff')
    else:   
        os.system('rm cutoff/*')  

def save_cutoff(t_cutoff):
    with open('cutoff/cutoff.txt','w') as f:
        f.write(str(t_cutoff))

def easy_hard_to(t,cutoff):
    if t<cutoff/7:
        return 'easy'
    if t>cutoff-1:
        return 'timeout'
    return 'hard'

#for all encodings on one instances
def hardness_for_instance(l):
    #['hard','easy','timeout']
    hard=easy=timeout=0
    for i in l:
        if i=='hard':
            hard+=1
        if i=='easy':
            easy+=1
        if i=='timeout':
            timeout+=1
    if hard> 0:
        return 'hard'
    if timeout== len(l):
        return 'timeout'
    if easy== len(l):
        return 'easy'
    return 'hard'

#for all instances
def hardness_for_list(l):
    #['hard','easy','timeout']
    hard=easy=timeout=0
    for i in l:
        if i=='hard':
            hard+=1
        if i=='easy':
            easy+=1
        if i=='timeout':
            timeout+=1
    if hard> len(l)*0.3:
        return 'hard'
    if timeout> len(l)*0.3:
        return 'timeout'
    if easy> len(l)*0.3:
        return 'easy'
    return 'hard'

def get_hardness(data_final,t_cutoff):
    in_file=data_final+'/performance.csv'
    df=pd.read_csv(in_file)
    cols=df.columns.values
    df=df.set_index(cols[0])
    cols=df.columns.values
    hardness_each_enc=[]
    for ind in df.index.values:
        df_row=df.loc[ind,:].values
        hardness_this_list=[easy_hard_to(float(elem),t_cutoff) for elem in df_row]
        hardness_this=hardness_for_instance(hardness_this_list)
        #print(hardness_this_list,hardness_this)
        hardness_each_enc.append(hardness_this)
    return hardness_each_enc

def get_cutoff(pre_run_data_final):
    if not os.path.exists(pre_run_data_final+'/cutoff.txt'):
        return '0'
    with open(pre_run_data_final+'/cutoff.txt','r') as f:
        ret=f.readline()
        #print(ret)
        return ret

def delete_and_save(folder):
    copy_folder = initial= folder
    for i in range(1,21):
        copy_folder= initial+ str(i) 
        if not os.path.exists(copy_folder):
            os.mkdir(copy_folder)
            break
    os.system('mv '+folder+'/* '+copy_folder+'/')
    return copy_folder

def cp_old_history(input_folder,output_folder,instances_folder):

    result_files=os.listdir(input_folder)
    allinsts=os.listdir(instances_folder)
    #allinsts=[i.split('.')[0] for i in allinsts]
    for result_file in result_files:
        file_df=pd.read_csv(input_folder+'/'+result_file)
        file_df=file_df.set_index(file_df.columns.values[0])
        allrun=[]
        for index in file_df.index.values:
            if index in allinsts:
                allrun.append(index)
        file_df=file_df.loc[allrun,:] 
        #print(file_df,input_folder)
        file_df.to_csv(output_folder+'/'+result_file)

            

def test_hardness_instances(encodings_folder,instances_folder,selected_ins,pre_run_data_final,pre_run_result_folder,t_cutoff):

    encodings_names=os.listdir(encodings_folder)
    instances_names=selected_ins

    hardness=''

    for pre_run in range(0,3): #timeoff.2timeoff.4timeoff
        print('\nSolving prerun instances...round ',pre_run,':', t_cutoff,'s')

        #compare history and update pre_run_result, not rerun
        if os.listdir(pre_run_result_folder)!=[] or os.listdir(pre_run_data_final)!=[]:

            pre_run_result_folder1=delete_and_save(pre_run_result_folder)
            pre_run_data_final1=delete_and_save(pre_run_data_final)

            if int(t_cutoff)== int(get_cutoff(pre_run_result_folder1)):
                cp_old_history(pre_run_result_folder1,pre_run_result_folder,instances_folder)
                cp_old_history(pre_run_data_final1,pre_run_data_final,instances_folder)

            #print('old file detected')

        
        '''
        if not os.path.exists(pre_run_result_folder+'/cutoff.txt'):
            os.system('rm '+pre_run_result_folder+'/*')
            os.system('rm '+pre_run_data_final+'/*')
        else:
            if int(t_cutoff)!= int(get_cutoff(pre_run_result_folder)):
                os.system('rm '+pre_run_result_folder+'/*')
                os.system('rm '+pre_run_data_final+'/*')
        '''
        #for enc in encodings_names:
        run_instances_for_enc(encodings_folder,instances_names,instances_folder,pre_run_result_folder,t_cutoff)
        
        #combine results
        combine_result(pre_run_result_folder,pre_run_data_final)


        hardness_list=get_hardness(pre_run_data_final,t_cutoff)
        print(hardness_list)
        hardness=hardness_for_list(hardness_list)
        if hardness=='hard':
            save_cutoff(t_cutoff)
            break
        if hardness=='easy':
            break
        if hardness=='timeout':
            t_cutoff=t_cutoff*2

    return hardness,t_cutoff

#if performance exist and instances=instances and encodings=encodings, exit
def already_collected(p_folder,all_encodings,all_instances):
    if not os.path.exists(p_folder+'/performance.csv'):
        print('Data file exits')
        return False
    else:
        df_check=pd.read_csv(p_folder+'/performance.csv')
        df_check=df_check.set_index(df_check.columns.values[0])

        all_encodings=len(all_encodings)
        all_encodings_pd=len(list(df_check.columns.values))
        if all_encodings != all_encodings_pd:
            print('encodings not match')
            return False      

        all_instances=set(all_instances)
        all_instances_pd=set(list(df_check.index.values))
        #print(all_instances)
        #print(all_instances_pd)
        if len(all_instances.difference(all_instances_pd))!=0:
            print('instances not match')
            return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    define_args(parser)
    args = parser.parse_args()

    

    encodings_folder=args.encodings[0]
    instances_folder=args.instances[0]
    t_cutoff=int(args.cutoff[0])
    data_final=args.performance_data[0]
    output_result_folder=data_final+'_each_enc'

    
    if not os.path.exists(data_final):
        os.mkdir(data_final)    

    if not os.path.exists(output_result_folder):
        os.mkdir(output_result_folder)

    encodings_names=os.listdir(encodings_folder)
    instances_names=os.listdir(instances_folder)

    if already_collected(data_final,encodings_names,instances_names):
        print('Performance data exists. Performance data collection passes')
        exit()
    
    make_cutoff()

    #choose len/10, at least 10 or len, at most 100, to test hardness and set cutoff time
    selected_ins=select_prerun_instance(instances_names)
    pre_run_data_final=data_final+'_prerun'
    pre_run_result_folder=pre_run_data_final+'_each_enc'
    if not os.path.exists(pre_run_data_final):
        os.mkdir(pre_run_data_final) 
    if not os.path.exists(pre_run_result_folder):
        os.mkdir(pre_run_result_folder)     
    #adjust cutoff time twice according to prerun results
    hardness,t_cutoff=test_hardness_instances(encodings_folder,instances_folder,selected_ins,pre_run_data_final,pre_run_result_folder,t_cutoff)

    if hardness=='timeout':
        print('\nExit! Instances are too hard to solve in ',t_cutoff,'s')
        exit()
    if hardness=='easy':
        print('\nExit! Instances are too easy to solve in ',t_cutoff,'s')
        exit()
    
    #append pre_run to existing final results
    # if existing final results
    if int(t_cutoff)== int(get_cutoff(output_result_folder)):
        #combine
        #print('combine')
        for enc_name in encodings_names:
            if os.path.exists(output_result_folder+'/'+encoding_name_parser(enc_name)+'_result.csv'):
                df1=pd.read_csv(output_result_folder+'/'+encoding_name_parser(enc_name)+'_result.csv')
                df2=pd.read_csv(pre_run_result_folder+'/'+encoding_name_parser(enc_name)+'_result.csv')
                df1=df1.set_index(df1.columns.values[0])
                df2=df2.set_index(df2.columns.values[0])
                df1=pd.concat([df1, df2], axis= 0)
                df1 = df1[~df1.index.duplicated(keep='last')]
                df1.to_csv(output_result_folder+'/'+encoding_name_parser(enc_name)+'_result.csv')

        if os.path.exists(data_final+'/performance.csv'):
            df1=pd.read_csv(data_final+'/performance.csv')
            df2=pd.read_csv(pre_run_data_final+'/performance.csv')
            df1=df1.set_index(df1.columns.values[0])
            df2=df2.set_index(df2.columns.values[0])
            df1=pd.concat([df1, df2], axis= 0)
            df1 = df1[~df1.index.duplicated(keep='last')]
            df1.to_csv(data_final+'/performance.csv')
    else:
        #if not existing final results
        if os.listdir(output_result_folder)!=[] or os.listdir(data_final)!=[]:
            delete_and_save(output_result_folder)
            delete_and_save(data_final)
        #print('--------1',pre_run_data_final)
        for enc_name in encodings_names:
            df2=pd.read_csv(pre_run_result_folder+'/'+encoding_name_parser(enc_name)+'_result.csv')
            df2.to_csv(output_result_folder+'/'+encoding_name_parser(enc_name)+'_result.csv',index=False) 
        #print('--------2',pre_run_data_final)
        df2=pd.read_csv(pre_run_data_final+'/performance.csv')           
        df2.to_csv(data_final+'/performance.csv',index=False)

    print('\nSolving remaining instances...',t_cutoff,'s')
    #run all instances
    #for enc in encodings_names:
    run_instances_for_enc(encodings_folder,instances_names,instances_folder,output_result_folder,t_cutoff)
    #combine results
    combine_result(output_result_folder,data_final)

    

