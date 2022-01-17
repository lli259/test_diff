import argparse,os
import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor


def define_args(arg_parser):

    arg_parser.add_argument('--feature_folder', nargs='*', default=['features'], help='Gringo input files')
    arg_parser.add_argument('--feature_outfolder', nargs='*', default=['features_selected'], help='Gringo input files')
    arg_parser.add_argument('--feature_folder_extra', nargs='*', default=['features_domain'], help='Gringo input files')
    arg_parser.add_argument('--performance_folder', nargs='*', default=['performance_selected'], help='Gringo input files')
    


def get_most_meaningful(feature_data,performance_data,number_features):
    alldata=feature_data.join(performance_data)

    cols=alldata.columns.values
    #print(alldata.shape)
    alldata=alldata.dropna()
    #print(alldata.shape)
    X_Train=alldata.loc[:,cols[:-1]]
    Y_Train=alldata.loc[:,cols[-1:]]
    #exit()
    #print(X_Train.shape,Y_Train.shape)
    #X_Train = StandardScaler().fit_transform(X_Train)
    #print(X_Train,Y_Train)
    #print(X_Train.shape,Y_Train.shape)
    Y_Train=Y_Train.values.reshape(X_Train.shape[0],)
    
    trainedforest = RandomForestRegressor(n_estimators=200,max_depth=20).fit(X_Train,Y_Train)

    feat_importances = pd.Series(trainedforest.feature_importances_, index= X_Train.columns)
    select_f=feat_importances.nlargest(number_features).index.values
    return select_f

def get_accuracy(most_meaning_f,feature_data,performance_data):
    alldata=feature_data.join(performance_data)
    alldata=alldata.dropna()
    cols=alldata.columns.values
    X_Train=alldata.loc[:,most_meaning_f]
    Y_Train=alldata.loc[:,cols[-1:]]

    #X_Train = StandardScaler().fit_transform(X_Train)
    Y_Train=Y_Train.values.reshape(X_Train.shape[0],)
    trainedforest = RandomForestRegressor(n_estimators=200,max_depth=20).fit(X_Train,Y_Train)
    predictionforest = trainedforest.predict(X_Train)
    
    return mean_squared_error(Y_Train,predictionforest)

def save_to_folder(args,selected_features,selected_file,performance_folder_group):
    feature_outfolder=args.feature_outfolder[0]+'/'+performance_folder_group
    if not os.path.exists(feature_outfolder):
        os.makedirs(feature_outfolder)

    feature_folder=args.feature_folder[0]

    feature_data=pd.read_csv(feature_folder+'/'+selected_file)
    feature_data=feature_data.set_index(feature_data.columns[0])    

    feature_data_selected=feature_data[selected_features]
    feature_data_selected.columns=[selected_file.split('.')[0]+'_'+i for i in feature_data_selected.columns]
    feature_data_selected.to_csv(feature_outfolder+'/'+'features_select.csv')


def save_to_folder_with_domain(args,selected_features,selected_file,most_meaning_f_dm,performance_folder_group):
    feature_outfolder=args.feature_outfolder[0]+'/'+performance_folder_group

    if not os.path.exists(feature_outfolder):
        os.makedirs(feature_outfolder)

    feature_folder=args.feature_folder[0]
    feature_data=pd.read_csv(feature_folder+'/'+selected_file)
    feature_data=feature_data.set_index(feature_data.columns[0])    
    feature_data_selected=feature_data[selected_features]
    feature_data_selected.columns=[selected_file.split('.')[0]+'_'+i for i in feature_data_selected.columns]

    feature_domain_folder=args.feature_folder_extra[0]
    feature_domain_file=os.listdir(feature_domain_folder)[0]
    feature_domain=pd.read_csv(feature_domain_folder+'/'+feature_domain_file)
    feature_domain=feature_domain.set_index(feature_domain.columns[0])
    feature_domain_selected=feature_domain[most_meaning_f_dm]

    feature_data_selected=feature_data_selected.join(feature_domain_selected)
    feature_data_selected=feature_data_selected.dropna()
    feature_data_selected.to_csv(feature_outfolder+'/'+'features_select.csv')

def select_f(args,performance_folder_group):
    print('Feature Evaluation: Group',performance_folder_group)
    #clasp features
    feature_folder=args.feature_folder[0]
    performance_folder=args.performance_folder[0]

    feature_all_enc=os.listdir(feature_folder)

    performance_file_name=os.listdir(performance_folder+'/'+performance_folder_group)[0]

    performance_data=pd.read_csv(performance_folder+'/'+performance_folder_group+'/'+performance_file_name)
    performance_data=performance_data.set_index(performance_data.columns[0])
    all_enc_names=performance_data.columns.values
    performance_data=performance_data[performance_data.columns[0]]


    allscore=[]
    for f_each_enc in feature_all_enc:
        enc_name=f_each_enc.split('_')[0]
        if enc_name in all_enc_names:
            feature_data=pd.read_csv(feature_folder+'/'+f_each_enc)
            feature_data=feature_data.set_index(feature_data.columns[0])
            feature_selected_num_min=feature_selected_num_max=0

            all_diff_features=[]
            if len(feature_data.columns)<20:
                feature_selected_num_min=int(len(feature_data.columns)*0.7)
                feature_selected_num_max=int(len(feature_data.columns)*0.9)
            else:
                feature_selected_num_min=int(len(feature_data.columns)*0.4)
                feature_selected_num_max=int(len(feature_data.columns)*0.7)            
            for diff_f_num in range(feature_selected_num_min,feature_selected_num_max+1):
                #print('Feature Evaluation: ',diff_f_num)
                most_meaning_f=get_most_meaningful(feature_data,performance_data,diff_f_num)
                score=get_accuracy(most_meaning_f,feature_data,performance_data)
                all_diff_features.append((score,most_meaning_f,f_each_enc))
            #print(all_diff_features)
            all_diff_features=sorted(all_diff_features)
            best_score=all_diff_features[0]
            allscore.append(best_score)

    allscore=sorted(allscore)
    selected_features=allscore[0][1]
    print(selected_features,allscore)
    selected_file=allscore[0][2]

    #domain features
    feature_domain_folder=args.feature_folder_extra[0]
    feature_domain_file=[]
    if os.path.exists(feature_domain_folder):
        feature_domain_file=os.listdir(feature_domain_folder)
    if feature_domain_file ==[]:
        save_to_folder(args,selected_features,selected_file,performance_folder_group)
    else:
        feature_domain=pd.read_csv(feature_domain_folder+'/'+feature_domain_file[0])
        feature_domain=feature_domain.set_index(feature_domain.columns[0])
        feature_domain=feature_domain.dropna()
        #print('domain feature selection...',feature_domain.shape)

        all_diff_features=[]
        if len(feature_domain.columns)<20:
            feature_selected_num_min=int(len(feature_domain.columns)*0.7)
            feature_selected_num_max=int(len(feature_domain.columns)*0.9)
        else:
            feature_selected_num_min=int(len(feature_domain.columns)*0.4)
            feature_selected_num_max=int(len(feature_domain.columns)*0.7)            
        for diff_f_num in range(feature_selected_num_min,feature_selected_num_max+1):
            #print('Domain Feature Evaluation: ',diff_f_num)
            most_meaning_f_dm=get_most_meaningful(feature_domain,performance_data,diff_f_num)
            score=get_accuracy(most_meaning_f_dm,feature_domain,performance_data)
            all_diff_features.append((score,most_meaning_f_dm))
            
        #print(all_diff_features)
        all_diff_features=sorted(all_diff_features)
        best_score=all_diff_features[0]
        print(best_score,all_diff_features)       
        most_meaning_f_dm=best_score[1]
        save_to_folder_with_domain(args,selected_features,selected_file,most_meaning_f_dm,performance_folder_group)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    define_args(parser)
    args = parser.parse_args()

    performance_folder=args.performance_folder[0]
    performance_folder_groups=os.listdir(performance_folder)


    feature_outfolder=args.feature_outfolder[0]
    if  os.path.exists(feature_outfolder):
        if len(os.listdir(feature_outfolder)) ==len(performance_folder_groups) :
            ans_retrain=input('Features were already selected! Need to rerun? y/n')
            if ans_retrain !='y':
                print('Feature Selection Passes')
                exit()
            os.system('rm -r '+feature_outfolder+'/*')
        else:
            os.system('rm -r '+feature_outfolder+'/*')
    else:
        os.system('mkdir '+feature_outfolder)

    for performance_folder_group in performance_folder_groups:
        select_f(args,performance_folder_group)

    
    






