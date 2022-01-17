import os,sys
fdname='Potassco/Decision'
files=os.listdir(fdname)
print(files)
cmd='python main.py '+fdname+'/'+files[4]
print(cmd)
os.system(cmd)
exit()
for i in files:
    cmd='python main.py '+fdname+'/'+i
    print(cmd)
    #os.system(cmd)

    