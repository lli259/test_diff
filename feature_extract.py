#python2
import argparse,os
import numpy as np
from collections import Counter
import pandas as pd
import subprocess
from multiprocessing import Process
from multiprocessing import Semaphore


def define_args(arg_parser):

    arg_parser.add_argument('--encodings_folder', nargs='*', default=['encodings'], help='Gringo input files')
    arg_parser.add_argument('--instances_folder', nargs='*', default=['instances'], help='Gringo input files')
    arg_parser.add_argument('--feature_data', nargs='*', default=['features'], help='Gringo input files')
    
def encoding_name_parser(enc_name):
    return enc_name.split('/')[1].split('.')[0].split('_')[0]


def run_multiprocess(enc,encodings_folder,instances_folder,features_folder,process_i,sema):

    dynamic_f="Choices,Conflicts/Choices,Avg_Conflict_Levels,Avg_LBD_Levels,Learnt_from_Conflict,"\
        "Learnt_from_Loop,Frac_Learnt_from_Conflict,Frac_Learnt_from_Loop,Literals_in_Conflict_Nogoods,"\
        "Literals_in_Loop_Nogoods,Frac_Literals_in_Conflict_Nogoods,Frac_Literals_in_Loop_Nogoods,Removed_Nogoods,"\
        "Learnt_Binary,Learnt_Ternary,Learnt_Others,Frac_Removed_Nogood,Frac_Learnt_Binary,Frac_Learnt_Ternary,"\
        "Frac_Learnt_Others,Skipped_Levels_while_Backjumping,Avg_Skipped_Levels_while_Backjumping,Longest_Backjumping,"\
        "Running_Avg_Conflictlevel,Running_Avg_LBD"
    dynamic_f=dynamic_f.split(',')
    dynamic_f2=[i+'_1' for i in dynamic_f]
    dynamic_f2=','.join(dynamic_f2)
    
    feature_names="Frac_Neg_Body,Frac_Pos_Body,Frac_Unary_Rules,Frac_Binary_Rules,Frac_Ternary_Rules,Frac_Integrity_Rules,Tight,"\
		"Problem_Variables,Free_Problem_Variables,Assigned_Problem_Variables,Constraints,"\
		"Constraints/Vars,Created_Bodies,Program_Atoms,SCCS,Nodes_in_Positive_BADG,Rules,"\
		"Normal_Rules,Cardinality_Rules,Choice_Rules,Weight_Rules,Frac_Normal_Rules,Frac_Cardinality_Rules,"\
		"Frac_Choice_Rules,Frac_Weight_Rules,Equivalences,Atom-Atom_Equivalences,Body-Body_Equivalences,"\
		"Other_Equivalences,Frac_Atom-Atom_Equivalences,Frac_Body-Body_Equivalences,Frac_Other_Equivalences,"\
		"Binary_Constraints,Ternary_Constraints,Other_Constraints,"\
		"Frac_Binary_Constraints,Frac_Ternary_Constraints,Frac_Other_Constraints,"\
        "Choices,Conflicts/Choices,Avg_Conflict_Levels,Avg_LBD_Levels,Learnt_from_Conflict,"\
        "Learnt_from_Loop,Frac_Learnt_from_Conflict,Frac_Learnt_from_Loop,Literals_in_Conflict_Nogoods,"\
        "Literals_in_Loop_Nogoods,Frac_Literals_in_Conflict_Nogoods,Frac_Literals_in_Loop_Nogoods,Removed_Nogoods,"\
        "Learnt_Binary,Learnt_Ternary,Learnt_Others,Frac_Removed_Nogood,Frac_Learnt_Binary,Frac_Learnt_Ternary,"\
        "Frac_Learnt_Others,Skipped_Levels_while_Backjumping,Avg_Skipped_Levels_while_Backjumping,Longest_Backjumping,"\
        "Running_Avg_Conflictlevel,Running_Avg_LBD,"+dynamic_f2
    

    instances=os.listdir(instances_folder)
    enc=encodings_folder+'/'+enc
    if not os.path.exists(features_folder+"/"+encoding_name_parser(enc)+"_feature.csv"):
        with open(features_folder+"/"+encoding_name_parser(enc)+"_feature.csv","a") as f:
            f.write("instance_id,"+feature_names+"\n")

    run_inst_df=pd.read_csv(features_folder+"/"+encoding_name_parser(enc)+"_feature.csv")
    run_inst=run_inst_df['instance_id'].values

    for ins in instances:
        if not ins in run_inst:
            print('Extracting ',enc,ins,'using process',process_i)
            ins=instances_folder+'/'+ins
            cmd_time="./tools/claspre/gringo "+enc+" "+ins+" | ./tools/claspre/claspre"
            result_time=subprocess.getoutput(cmd_time)
            result_time=result_time.split("\n")

            if len(result_time)<10:
                #fail
                print (ins.split("/")[1])
                print ('Fail')
            else:
                
                f_values=[]
                for i in result_time[2:]:
                    if "[" in i and "]" in i:
                        feat_value_tem=""
                        for ch in i:
                            if ch in "0123456789.":
                                feat_value_tem+=ch
                        f_values.append(feat_value_tem)

                with open(features_folder+"/"+encoding_name_parser(enc)+"_feature.csv","a") as f:
                    f.write(ins.split("/")[1]+","+",".join(f_values)+"\n")

    sema.release()
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    define_args(parser)
    args = parser.parse_args()

    instances_folder=args.instances_folder[0]
    encodings_folder=args.encodings_folder[0]
    features_folder=args.feature_data[0]

    encodings=os.listdir(encodings_folder)
    instances=os.listdir(instances_folder)

    if not os.path.exists(features_folder):
        os.system('mkdir '+features_folder)



    concurrency = 4
    total_task_num = os.listdir(encodings_folder)
    sema = Semaphore(concurrency)
    all_processes = []
    for process_i,enc_name in enumerate(total_task_num):
        sema.acquire()
        p = Process(target=run_multiprocess, args=(enc_name,encodings_folder,instances_folder,features_folder,process_i,sema))
        all_processes.append(p)
        p.start()

    for p in all_processes:
        p.join()
    print('Features collection Done!')


    