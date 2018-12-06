#!/usr/bin/python

import subprocess

cmd = 'qsub -l nodes=1:ppn=1 -l walltime=48:00:00 -l mem=500GB -N routes -j oe -o out/routes.out -- trackml/routes.py'

print cmd

proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

out, err = proc.communicate(proc)

print out.strip(), err.strip()
