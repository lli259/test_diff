import argparse,os
import sys
import math
import pandas as pd
import numpy as np
import random
from collections import Counter
from sklearn import tree
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
import pickle
from sklearn.metrics import mean_squared_error
from sklearn.metrics import accuracy_score
from sklearn.metrics import make_scorer
from collections import Counter
import warnings
warnings.filterwarnings("ignore")

def define_args(arg_parser):

    arg_parser.add_argument('--feature_folder', nargs='*', default=['features_selected'], help='Gringo input files')
    arg_parser.add_argument('--performance_folder', nargs='*', default=['performance_selected'], help='Gringo input files')
    arg_parser.add_argument('--cutoff', nargs='*', default=['200'], help='Gringo input files')
    arg_parser.add_argument('--ml_models_folder', nargs='*', default=['ml_models'], help='Gringo input files') 
    arg_parser.add_argument('--ml_hyper_folder', nargs='*', default=['ml_hyper'], help='Gringo input files') 

def checkMakeFolder(fdname):
    if not os.path.exists(fdname):
        os.makedirs(fdname)

def check_content(fdname):
    if os.listdir(fdname) == []:
        return False
    else:
        return True

def cleanFolder(fdnames):   
    ans=input('Models existed. Need to retrain models? y/n')
    if ans =='y':
        for file_in in fdnames:
            if os.path.exists(file_in):
                os.system('rm -r '+file_in+'/*')

#write to evaluation file2 
#evaluation/result2.csv
def write2eva2(algname,slv,time):
    fname='evaluation/result2.csv'
    with open (fname,'a') as f:
        cont=','.join([algname,str(slv),str(time)])
        f.write(cont+'\n')
#the objective function to minimize, tuning hyperparameters
#relative_score
#max_relative_score
#min_relative_score
#neg_mean_squared_error
def relative_score(y_true, y_pred):
		res=[]
		for i in range(len(y_true)):
			if y_true[i]>y_pred[i]:
				res.append((y_true[i]-y_pred[i])/(y_true[i]))
			else:
				res.append((y_pred[i]-y_true[i])/(y_true[i]))
		return -sum(res)/float(len(res))

def max_relative_score(y_true, y_pred):

		res=[]
		for i in range(len(y_true)):
			if y_true[i]>y_pred[i]:
				res.append((y_true[i]-y_pred[i])/(y_true[i]))
			else:
				res.append((y_pred[i]-y_true[i])/(y_true[i]))
		return -max(res)

#print solved percentage and avg runtime
def printSvdPercAvgTime(p,runtime,maxtime,printresult=True):
	#success
	sucs=[]
	for i in runtime:
		if i<maxtime-1:
			sucs.append(i)
	if len(sucs)!=0:
		if printresult:
			print(p,float(len(sucs))/len(runtime),"/",float(sum(sucs))/len(sucs))
		return float(len(sucs))/len(runtime), float(sum(sucs))/len(sucs)
	else:
		if printresult:
			print(p,float(0),"/",float(0))
		return 0,0

#split 80% trainset into validSet, trainSet with specified binNum and which bin.
#bin=0, binNum=5.
#the last bin for validing, first 4bins for training.
def splitTrainValid(datasetX,bin,binNum):
	bin_size=int(math.ceil(len(datasetX)/binNum))
	if bin==0:
		return np.array(datasetX[bin_size:]),np.array(datasetX[:bin_size])
	elif bin==binNum-1:
		return np.array(datasetX[:(binNum-1)*bin_size]),np.array(datasetX[-bin_size:])
	else:
		return np.append(datasetX[:bin_size*(bin)],datasetX[bin_size*(bin+1):],axis=0),np.array(datasetX[bin_size*(bin):bin_size*(bin+1)])



def drawLine():
    print("------------------------------------------------")

def machine_learning(args,ml_group):
    feature_folder=args.feature_folder[0]+'/'+ml_group
    performance_folder=args.performance_folder[0]+'/'+ml_group
    cutoff=args.cutoff[0]

    ml_outfolder=args.ml_models_folder[0]+'/'+ml_group
    ml_hyperfolder=args.ml_hyper_folder[0]+'/'+ml_group

    checkMakeFolder(ml_hyperfolder)
    checkMakeFolder(ml_outfolder)

    #set according to your cutoff time
    TIME_MAX=int(cutoff)
    #use varing PENALTY policy or 1000s fixed
    VARING_PENALTY=False
    #random seed
    #set PENALTY_TIME, we can set as 200, PAR10, or PARX
    PENALTY_TIME=int(cutoff)

    np.random.seed(123)
    random.seed(123)

    score_functions=[make_scorer(relative_score),make_scorer(max_relative_score),"neg_mean_squared_error"]
    # here choose "neg_mean_squared_error"
    score_f=score_functions[2]


    featureFile=feature_folder+'/'+os.listdir(feature_folder)[0]
    featureValue=pd.read_csv(featureFile)
    featureValue=featureValue.set_index(featureValue.columns[0])
    allCombine=featureValue.copy()

    performanceFile=performance_folder+'/'+os.listdir(performance_folder)[0]
    performanceValue=pd.read_csv(performanceFile)
    performanceValue=performanceValue.set_index(performanceValue.columns[0])
    algorithmNames=performanceValue.columns.values
    performanceValue.columns=["runtime_"+algo for algo in algorithmNames]
    allCombine=allCombine.join(performanceValue)



    #remove duplicated
    allCombine = allCombine[~allCombine.index.duplicated(keep='first')]
    allCombine.sort_index()


    featureList=allCombine.columns.values[:-len(algorithmNames)]
    print("[Feature used]:",featureList)


    #drop "na" rows
    allCombine=allCombine.dropna(axis=0, how='any')

    #drop "?" rows
    for feature in featureList[1:]:
        if allCombine[feature].dtypes=="object":
            # delete from the pd1 rows that contain "?"
            allCombine=allCombine[allCombine[feature].astype("str")!="?"]


    algs=["runtime_"+algo for algo in algorithmNames]
    allRuntime=allCombine[algs]

    print(allRuntime.shape,allRuntime)
    oracle_value=np.amin(allRuntime.values, axis=1)
    oracle_index=np.argmin(allRuntime.values, axis=1)
    Oracle_name=[allRuntime.columns[oracle_index[i]][1]  for i in range(len(oracle_index))]

    allCombine["Oracle_value"]=oracle_value
    allCombine["Oracle_name"]=Oracle_name

    #shuffle
    allCombine=allCombine.iloc[np.random.permutation(len(allCombine))]


    # get leave out data 15% of the full data:
    leaveIndex=random.sample(range(allCombine.shape[0]), int(allCombine.shape[0]*0.15))

    mlIndex=list(range(allCombine.shape[0]))
    for i in leaveIndex:
        if i in mlIndex:
            mlIndex.remove(i)

    leaveSet=allCombine.iloc[leaveIndex]
    mlSet=allCombine.iloc[mlIndex]
    # get testing data 20% of the full data:
    testIndex=random.sample(range(mlSet.shape[0]), int(mlSet.shape[0]*0.2))

    trainIndex=list(range(mlSet.shape[0]))
    for i in testIndex:
        if i in trainIndex:
            trainIndex.remove(i)

    testSet=mlSet.iloc[testIndex]
    trainSetAll=mlSet.iloc[trainIndex]
    trainSetAll.to_csv(ml_outfolder+'/trainSetAll.csv')
    trainSet,validSet=splitTrainValid(trainSetAll,0,5)

    trainSet=pd.DataFrame(trainSet,columns=trainSetAll.columns)
    validSet=pd.DataFrame(validSet,columns=trainSetAll.columns)

 
    print("ALL after preprocess:",mlSet.shape)
    print("trainAll:",trainSetAll.shape)
    print("--trainSet:",trainSet.shape)
    print("--validSet:",validSet.shape)
    print("testSet:",testSet.shape)
    print("leaveSet:",leaveSet.shape)

    trainSet.to_csv(ml_outfolder+"/trainSet.csv")
    validSet.to_csv(ml_outfolder+"/validSet.csv")
    testSet.to_csv(ml_outfolder+"/testSet.csv")
    leaveSet.to_csv(ml_outfolder+"/leaveSet.csv")
    

    #train each model:

    #hyperparameters tuning
    #grid search
    #train and predict, save
    bestDepth={}
    if os.path.isdir(ml_hyperfolder):
        pickleFiles=[pickFile for pickFile in os.listdir(ml_hyperfolder) if pickFile.endswith(".pickle")]
        if 'regression_bestDepth.pickle' in pickleFiles:
            with open(ml_hyperfolder+'/regression_bestDepth.pickle', 'rb') as handle:
                bestDepth = pickle.load(handle)

    trainResult=trainSet.copy()
    validResult=validSet.copy()
    testResult=testSet.copy()
    leaveResult=leaveSet.copy()

    for alg in algorithmNames:
        trainSet_X=trainSet.loc[:,featureList].values
        trainSet_y=trainSet["runtime_"+alg].values
        validSet_X=validSet.loc[:,featureList].values
        validSet_y=validSet["runtime_"+alg].values
        testSet_X=testSet.loc[:,featureList].values
        testSet_y=testSet["runtime_"+alg].values
        leaveSet_X=leaveSet.loc[:,featureList].values
        leaveSet_y=leaveSet["runtime_"+alg].values

        bestDepthDT=0
        bestDepthRF=0
        bestKNeib=0


        pickleFiles=[pickFile for pickFile in os.listdir(ml_hyperfolder) if pickFile.endswith(".pickle")]
        if 'regression_bestDepth.pickle' in pickleFiles:
            with open(ml_hyperfolder+'/regression_bestDepth.pickle', 'rb') as handle:
                bestDepth = pickle.load(handle)
                bestDepthDT,bestDepthRF,bestKNeib=bestDepth.get(alg,(0,0,0))
        if bestKNeib==0 and bestDepthDT==0 and bestDepthRF==0:

            #Load parameter from pickle
            max_depth = range(2, 30, 1)
            dt_scores = []
            for k in max_depth:
                regr_k =tree.DecisionTreeRegressor(max_depth=k)
                loss = -cross_val_score(regr_k, trainSet_X, trainSet_y, cv=10, scoring=score_f)
                dt_scores.append(loss.mean())
            #plt.plot(max_depth, dt_scores,label="DT")
            #plt.xlabel('Value of depth: Algorithm'+alg)
            #plt.ylabel('Cross-Validated MSE')
            bestscoreDT,bestDepthDT=sorted(list(zip(dt_scores,max_depth)))[0]



            max_depth = range(2, 30, 1)
            dt_scores = []
            for k in max_depth:
                regr_k = RandomForestRegressor(max_depth=k)
                loss = -cross_val_score(regr_k, trainSet_X, trainSet_y, cv=10, scoring=score_f)
                dt_scores.append(loss.mean())
            #plt.plot(max_depth, dt_scores,label="RF")
            #plt.xlabel('Value of depth: Algorithm'+alg)
            #plt.ylabel('Cross-Validated MSE')
            bestscoreRF,bestDepthRF=sorted(list(zip(dt_scores,max_depth)))[0]

            max_neigh = range(2, 30, 1)
            kNN_scores = []
            for k in max_neigh:
                kNeigh =KNeighborsRegressor(n_neighbors=k)
                loss = -cross_val_score(kNeigh,trainSet_X, trainSet_y, cv=10, scoring=score_f)
                kNN_scores.append(loss.mean())
            #plt.plot(max_neigh, kNN_scores,label="kNN")
            #plt.xlabel('Value of depth: regression_'+alg)
            #plt.ylabel('Cross-Validated MSE')
            #plt.legend()
            bestscoreRF,bestKNeib=sorted(list(zip(kNN_scores,max_neigh)))[0]

            #plt.savefig("hyperParameters/regression_"+alg)
            #plt.clf()

            bestDepth[alg]=(bestDepthDT,bestDepthRF,bestKNeib)
            with open(ml_hyperfolder+'/regression_bestDepth.pickle', 'wb') as handle:
                pickle.dump(bestDepth, handle)

        #predict on all trainign validation and test set and save result
        dtModel=tree.DecisionTreeRegressor(max_depth=bestDepthDT)
        dtModel= dtModel.fit(trainSet_X, trainSet_y)
        y_=dtModel.predict(trainSet_X)
        trainResult["DT_"+alg+"_pred"]=y_
        y_=dtModel.predict(validSet_X)
        validResult["DT_"+alg+"_pred"]=y_
        y_=dtModel.predict(testSet_X)
        testResult["DT_"+alg+"_pred"]=y_
        y_=dtModel.predict(leaveSet_X)
        leaveResult["DT_"+alg+"_pred"]=y_
        

        ##########
        rfModel=RandomForestRegressor(max_depth=bestDepthRF)
        rfModel= rfModel.fit(trainSet_X, trainSet_y)
        y_=rfModel.predict(trainSet_X)
        trainResult["RF_"+alg+"_pred"]=y_
        y_=rfModel.predict(validSet_X)
        validResult["RF_"+alg+"_pred"]=y_
        y_=rfModel.predict(testSet_X)
        testResult["RF_"+alg+"_pred"]=y_
        y_=rfModel.predict(leaveSet_X)
        leaveResult["RF_"+alg+"_pred"]=y_
        #########
        kNeigh =KNeighborsRegressor(n_neighbors=bestKNeib)
        kNeigh= kNeigh.fit(trainSet_X, trainSet_y)
        y_=kNeigh.predict(trainSet_X)
        trainResult["kNN_"+alg+"_pred"]=y_
        y_=kNeigh.predict(validSet_X)
        validResult["kNN_"+alg+"_pred"]=y_
        y_=kNeigh.predict(testSet_X)
        testResult["kNN_"+alg+"_pred"]=y_
        y_=kNeigh.predict(leaveSet_X)
        leaveResult["kNN_"+alg+"_pred"]=y_
    #analysis
    ##solved percent and runtime of
    ##per algorithm, oracle and ES
    ##
    runtimeIndex=[i for i in trainResult.columns if "runtime" in i]

 

    drawLine()
    print("trainSet")
    print("Indivadual encoding and Oracle performance: ")
    #print per algorithm
    for alg in runtimeIndex:
        printSvdPercAvgTime(alg.split("_")[1],trainResult[alg],TIME_MAX)
    #print oracle
    printSvdPercAvgTime("oracle_portfolio",trainResult.Oracle_value.values,TIME_MAX)
    print("\nEncoding selection performance:")

    testResultSaving=[]
    for mName in "DT,RF,kNN".split(","):

        print(mName)
        encRuntime=[i for i in trainResult.columns if "runtime" in i]
        modelRuntime=[i for i in trainResult.columns if mName in i]
        modelResults=trainResult[encRuntime+modelRuntime].copy()


        #save each instance's predicted runtime of six encoding and the corresponding predicted encoding name
        #(runtime, name)
        #for each instance, sort by runtime, so that we know which is the first predicted one
        modelResultsCopy=modelResults[modelRuntime].copy()
        for i in modelResultsCopy.columns.values:
            modelResultsCopy[i]=[(j,i)for j in modelResultsCopy[i]]
        predictedList=modelResultsCopy.values
        predictedList.sort()

        #the best predicted is the i[0]:(min_runtime, its_name)
        bestpredname=[i[0][1] for i in predictedList]
        bestname=["runtime_"+i.split("_")[1] for i in bestpredname]
        bestruntime=[modelResults[bestname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["1st_ham"]=bestname
        modelResults["1st_time"]=bestruntime
        printSvdPercAvgTime("1st",bestruntime,TIME_MAX)
        

        #the second predicted is the i[1]:(min_runtime, its_name)
        secondpredname=[i[1][1] for i in predictedList]
        secondname=["runtime_"+i.split("_")[1] for i in secondpredname]
        secondruntime=[modelResults[secondname[i]][i]  for i in range(len(modelResults))]
        modelResults["2nd_ham"]=secondname
        modelResults["2nd_time"]=secondruntime
        #printSvdPercAvgTime("2nd",secondruntime)

        '''
        #the third predicted is the i[2]:(min_runtime, its_name)
        thirdpredname=[i[2][1] for i in predictedList]
        thirdname=["runtime_"+i.split("_")[1] for i in thirdpredname]
        thirdruntime=[modelResults[thirdname[i]][i]  for i in range(len(modelResults))]
        modelResults["3rd_ham"]=thirdname
        modelResults["3rd_time"]=thirdruntime
        #printSvdPercAvgTime("3rd",thirdruntime)
        '''
        #modelResults.to_csv(("resultAnalysis/training_result_analysis_"+mName+".csv"))
    print("\n")
    '''    
    drawLine()
    print("validSet")
    print("Indivadual encoding and Oracle performance: ")
    for alg in runtimeIndex:
        printSvdPercAvgTime(alg+"",validResult[alg],TIME_MAX)
    printSvdPercAvgTime("oracle_portfolio",validResult.Oracle_value.values,TIME_MAX)
    print("\nEncoding selection performance:")
    for mName in "DT,RF,kNN".split(","):
        print(mName)
        encRuntime=[i for i in validResult.columns if "runtime" in i]
        modelRuntime=[i for i in validResult.columns if mName in i]
        modelResults=validResult[encRuntime+modelRuntime].copy()

        modelResultsCopy=modelResults[modelRuntime].copy()
        for i in modelResultsCopy.columns.values:
            modelResultsCopy[i]=[(j,i)for j in modelResultsCopy[i]]
        predictedList=modelResultsCopy.values
        predictedList.sort()

        bestpredname=[i[0][1] for i in predictedList]
        bestname=["runtime_"+i.split("_")[1] for i in bestpredname]
        bestruntime=[modelResults[bestname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["1st_ham"]=bestname
        modelResults["1st_time"]=bestruntime

        printSvdPercAvgTime("1st",bestruntime,TIME_MAX)

        secondpredname=[i[1][1] for i in predictedList]
        secondname=["runtime_"+i.split("_")[1] for i in secondpredname]
        secondruntime=[modelResults[secondname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["2nd_ham"]=secondname
        modelResults["2nd_time"]=secondruntime
        #printSvdPercAvgTime("2nd",secondruntime)

        thirdpredname=[i[2][1] for i in predictedList]
        thirdname=["runtime_"+i.split("_")[1] for i in thirdpredname]
        thirdruntime=[modelResults[thirdname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["3rd_ham"]=thirdname
        modelResults["3rd_time"]=thirdruntime
        #printSvdPercAvgTime("3rd",thirdruntime)

        #modelResults.to_csv(("resultAnalysis/validition_result_analysis_"+mName+".csv"))
        '''
    print("\n")
    print("testSet")
    drawLine()
    print("Indivadual encoding and Oracle performance: ")
    for alg in runtimeIndex:
        printSvdPercAvgTime(alg+"",testResult[alg],TIME_MAX)
    printSvdPercAvgTime("oracle_portfolio",testResult.Oracle_value.values,TIME_MAX)
    print("\nEncoding selection performance: ")
    for mName in "DT,RF,kNN".split(","):
        print(mName)
        encRuntime=[i for i in testResult.columns if "runtime" in i]
        modelRuntime=[i for i in testResult.columns if mName in i]
        modelResults=testResult[encRuntime+modelRuntime].copy()

        modelResultsCopy=modelResults[modelRuntime].copy()
        for i in modelResultsCopy.columns.values:
            modelResultsCopy[i]=[(j,i)for j in modelResultsCopy[i]]
        predictedList=modelResultsCopy.values
        predictedList.sort()

        bestpredname=[i[0][1] for i in predictedList]
        bestname=["runtime_"+i.split("_")[1] for i in bestpredname]
        bestruntime=[modelResults[bestname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["1st_ham"]=bestname
        modelResults["1st_time"]=bestruntime
        sv_percent,sv_time=printSvdPercAvgTime("1st",bestruntime,TIME_MAX)
        testResultSaving.append((sv_percent,sv_time,mName))

        secondpredname=[i[1][1] for i in predictedList]
        secondname=["runtime_"+i.split("_")[1] for i in secondpredname]
        secondruntime=[modelResults[secondname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["2nd_ham"]=secondname
        modelResults["2nd_time"]=secondruntime
        #printSvdPercAvgTime("2nd",secondruntime)
        '''
        thirdpredname=[i[2][1] for i in predictedList]
        thirdname=["runtime_"+i.split("_")[1] for i in thirdpredname]
        thirdruntime=[modelResults[thirdname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["3rd_ham"]=thirdname
        modelResults["3rd_time"]=thirdruntime
        #printSvdPercAvgTime("3rd",thirdruntime)
        '''
        #modelResults.to_csv(("resultAnalysis/testing_result_analysis_"+mName+".csv"))

    testResultSaving=sorted(testResultSaving)[-1]
    method=str(testResultSaving[2])
    result_sol=str(testResultSaving[0])
    result_tm=str(testResultSaving[1])
    #print(testResultSaving[-1])
    

    with open('evaluation/result.csv','a') as f:
        f.write(method+'_'+ml_group+','+result_sol+','+result_tm+'\n')

    print('\n')
  
    #print("leaveSet")
    #drawLine()
    #print("Indivadual encoding and Oracle performance: ")
    for alg in runtimeIndex:
        sv_percent,sv_time=printSvdPercAvgTime(alg+"",leaveResult[alg],TIME_MAX,False)
        write2eva2(alg+ml_group,sv_percent,sv_time)
    sv_percent,sv_time=printSvdPercAvgTime("oracle_portfolio",leaveResult.Oracle_value.values,TIME_MAX,False)
    write2eva2("oracle_portfolio"+ml_group,sv_percent,sv_time)
    #print("\nEncoding selection performance: ")
    for mName in "DT,RF,kNN".split(","):
        #print(mName)
        encRuntime=[i for i in leaveResult.columns if "runtime" in i]
        modelRuntime=[i for i in leaveResult.columns if mName in i]
        modelResults=leaveResult[encRuntime+modelRuntime].copy()

        modelResultsCopy=modelResults[modelRuntime].copy()
        for i in modelResultsCopy.columns.values:
            modelResultsCopy[i]=[(j,i)for j in modelResultsCopy[i]]
        predictedList=modelResultsCopy.values
        predictedList.sort()

        bestpredname=[i[0][1] for i in predictedList]
        bestname=["runtime_"+i.split("_")[1] for i in bestpredname]
        bestruntime=[modelResults[bestname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["1st_ham"]=bestname
        modelResults["1st_time"]=bestruntime
        sv_percent,sv_time=printSvdPercAvgTime("1st",bestruntime,TIME_MAX,False)
        write2eva2(mName+ml_group,sv_percent,sv_time)

        secondpredname=[i[1][1] for i in predictedList]
        secondname=["runtime_"+i.split("_")[1] for i in secondpredname]
        secondruntime=[modelResults[secondname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["2nd_ham"]=secondname
        modelResults["2nd_time"]=secondruntime
        #printSvdPercAvgTime("2nd",secondruntime)
        '''
        thirdpredname=[i[2][1] for i in predictedList]
        thirdname=["runtime_"+i.split("_")[1] for i in thirdpredname]
        thirdruntime=[modelResults[thirdname[i]].values[i]  for i in range(len(modelResults))]
        modelResults["3rd_ham"]=thirdname
        modelResults["3rd_time"]=thirdruntime
        #printSvdPercAvgTime("3rd",thirdruntime)
        '''
        #modelResults.to_csv(("resultAnalysis/leaveing_result_analysis_"+mName+".csv"))






if __name__ == "__main__":
    print('\nMachine learning model building...')
    parser = argparse.ArgumentParser()
    define_args(parser)
    args = parser.parse_args()


    ml_outfolder=args.ml_models_folder[0]
    ml_hyperfolder=args.ml_hyper_folder[0]

    checkMakeFolder(ml_hyperfolder)
    checkMakeFolder(ml_outfolder)

    if check_content(ml_hyperfolder) or check_content(ml_hyperfolder):
        cleanFolder([ml_hyperfolder,ml_outfolder])

    #evaluating
    if not os.path.exists('evaluation'):
        os.system('mkdir evaluation')
    os.system('rm evaluation/*')
    with open('evaluation/result.csv','w') as f:
        f.write('method,solving,time\n')    

    with open('evaluation/result2.csv','w') as f:
        f.write('evaluation\n')

    feature_folder=args.feature_folder[0]
    feature_groups=os.listdir(feature_folder)
    for ml_group in feature_groups:
        machine_learning(args,ml_group)
    
