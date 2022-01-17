import subprocess



cmdline='tools/gringo.exe encodings/ham5.lp instances/rand_blocked_size10_blk5_s1.csv | tools/clasp.exe >> performance_each_enc_tmp/ham5/rand_blocked_size10_blk5_s4.csv'
print(cmdline)

process = subprocess.getoutput(cmdline)
print(process)



'''


import os
import subprocess

cmdline='tools/gringo.exe encodings/ham5.lp instances/rand_blocked_size10_blk5_s1.csv | tools/clasp.exe > performance_each_enc_tmp/ham5/rand_blocked_size10_blk5_s1.csv'
cmdline='ping 1.1.1.1'
print(cmdline)
#os.system(cmdline)
print(subprocess.check_output(cmdline,shell=True))


'''
