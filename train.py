import argparse,os


'''
Platform Learning

'''
ALLRUN=['0']
Encoding_rewrite='1'
Performance_gen='2'
Encoding_candidate_gen='3'
Feature_extraction='4'
Feature_selection='5'
Model_building='6'
Schedule_building='7'
Interleaving_building='8'
Evaluation='9'

'''
Platform Prediction
use solve.py
'''




def define_args(arg_parser):
    arg_parser.description = 'ASP Platform'

    arg_parser.add_argument('-p', nargs='*', default=[], help='Platform process number')
    arg_parser.add_argument('--encodings', nargs='*', default=['encodings'], help='Platform input encodings')
    arg_parser.add_argument('--selected_encodings', nargs='*', default=['encodings_selected'], help='Platform selected encodings')
    arg_parser.add_argument('--instances', nargs='*', default=['instances'], help='Gringo input files')
    arg_parser.add_argument('--cutoff', nargs='*', default=['200'], help='Gringo input files')
    arg_parser.add_argument('--rewrite_form', nargs='*', default=['1'], help='Gringo input files')
    arg_parser.add_argument('--performance_data', nargs='*', default=['performance'], help='Gringo input files')
    arg_parser.add_argument('--performance_select', nargs='*', default=['performance_selected'], help='Gringo input files')   
    arg_parser.add_argument('--num_candidate', nargs='*', default=['4'], help='Gringo input files')
    arg_parser.add_argument('--feature_data', nargs='*', default=['features'], help='Gringo input files')
    arg_parser.add_argument('--feature_domain', nargs='*', default=['features_domain'], help='Gringo input files')
    arg_parser.add_argument('--feature_selected', nargs='*', default=['features_selected'], help='Gringo input files')
    arg_parser.add_argument('--ml_models_folder', nargs='*', default=['ml_models'], help='Gringo input files')    
    arg_parser.add_argument('--interleave_folder', nargs='*', default=['interleave'], help='Gringo input files') 
    arg_parser.add_argument('--schedule_folder', nargs='*', default=['schedule'], help='Gringo input files') 
    arg_parser.add_argument('--performance_provided',action='store_true', help='Gringo input files') 
    arg_parser.add_argument('--perform_feat_provided',action='store_true', help='Gringo input files') 

parser = argparse.ArgumentParser()
define_args(parser)
args = parser.parse_args()

#Encoding rewrite

if args.p== ALLRUN or Encoding_rewrite in args.p :
    for enc_file in os.listdir(args.encodings[0]):
        if (not enc_file ==  None) and (not 'aagg.lp'  in enc_file):
            os.system('python aaggrewrite.py '+args.encodings[0]+'/'+enc_file
            +' --aggregate_form ' + args.rewrite_form[0]
            )


#performance data generation
if args.p== ALLRUN or Performance_gen in args.p:
    os.system('python performance_gen.py '
    +' --encodings ' +args.encodings[0]
    +' --instances ' +args.instances[0]
    +' --cutoff ' + args.cutoff[0]
    +' --performance_data ' + args.performance_data[0])

    if not os.path.exists('cutoff/cutoff.txt'):
        print('Cutoff not set. Data collection failed!')
        exit()

#Encoding_candidate generation
if args.p== ALLRUN or Encoding_candidate_gen in args.p or args.performance_provided or args.perform_feat_provided:

    cutoff=args.cutoff[0]

    if os.path.exists('cutoff/cutoff.txt'):
        with open('cutoff/cutoff.txt','r') as f:
            cutoff=f.readline()
            
    os.system('python selected_candidate.py '
    +' --encodings ' +args.encodings[0]
    +' --selected_encodings ' +args.selected_encodings[0]
    +' --cutoff ' + cutoff
    +' --performance_data ' + args.performance_data[0])

#Feature extraction
if args.p== ALLRUN or Feature_extraction in args.p or args.performance_provided:
    instances_folder=args.instances[0]
    encodings_folder=args.encodings[0]
    os.system('python feature_extract.py --instances_folder '+ instances_folder
    +' --encodings_folder ' + encodings_folder
    )

#Feature selection
if args.p== ALLRUN or Feature_selection in args.p or args.performance_provided or args.perform_feat_provided:
    feature_folder=args.feature_data[0]
    performance_folder=args.performance_select[0]
    feature_folder_extra = args.feature_domain[0]
    os.system('python feature_selection.py --feature_folder '+ feature_folder
    +' --feature_folder_extra ' + feature_folder_extra
    +' --performance_folder ' + performance_folder
    )

#Machine Learning Model building
if args.p== ALLRUN or Model_building in args.p or args.performance_provided or args.perform_feat_provided:
    feature_folder=args.feature_selected[0]
    performance_folder=args.performance_select[0]
    #cutoff=args.cutoff[0]
    #cutoff ='200'

    cutoff=args.cutoff[0]

    if os.path.exists('cutoff/cutoff.txt'):
        with open('cutoff/cutoff.txt','r') as f:
            cutoff=f.readline()

    os.system('python model_building.py --feature_folder '+ feature_folder 
    +' --performance_folder ' + performance_folder
    +' --cutoff ' + cutoff
    )

#Schedule building
if args.p== ALLRUN or Schedule_building in args.p or args.performance_provided or args.perform_feat_provided:

    performance_folder=args.performance_select[0]
    
    #cutoff ='200'

    cutoff=args.cutoff[0]

    if os.path.exists('cutoff/cutoff.txt'):
        with open('cutoff/cutoff.txt','r') as f:
            cutoff=f.readline()

    os.system('python schedule_build.py '
    +' --performance_folder ' + performance_folder
    +' --cutoff ' + cutoff
    )

#Interleaving Schedule building
if args.p== ALLRUN or Interleaving_building in args.p or args.performance_provided or args.perform_feat_provided:

    performance_folder=args.performance_select[0]

    #cutoff ='200'
    cutoff=args.cutoff[0]

    if os.path.exists('cutoff/cutoff.txt'):
        with open('cutoff/cutoff.txt','r') as f:
            cutoff=f.readline()

    os.system('python interleave_build.py '
    +' --performance_folder ' + performance_folder
    +' --cutoff ' + cutoff
    )


#Interleaving Schedule building
if args.p== ALLRUN or Evaluation in args.p or args.performance_provided or args.perform_feat_provided:

    performance_folder=args.performance_select[0]

    cutoff=args.cutoff[0]

    if os.path.exists('cutoff/cutoff.txt'):
        with open('cutoff/cutoff.txt','r') as f:
            cutoff=f.readline()

    os.system('python evaluation.py '
    +' --performance_folder ' + performance_folder
    +' --cutoff ' + cutoff
    )
