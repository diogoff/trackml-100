#!/usr/bin/python

import glob
import subprocess

files = sorted(glob.glob('data/test/event*-hits.csv'))
event_ids_1 = []
for fname in files:
    i0 = fname.find('/event') + len('/event')
    i1 = fname.find('-hits.csv')
    event_id = int(fname[i0:i1])
    event_ids_1.append(event_id)

files = sorted(glob.glob('out/event*-tracks.csv'))
event_ids_2 = []
for fname in files:
    i0 = fname.find('event') + len('event')
    i1 = fname.find('-tracks.csv')
    event_id = int(fname[i0:i1])
    event_ids_2.append(event_id)

missing = list(set(event_ids_1) - set(event_ids_2))

for i in missing:
    
    cmd = 'qsub -q ansys -l nodes=1:ppn=1 -l walltime=24:00:00 -l mem=16GB -N task_%03d -j oe -o out/tracks_%03d.out -- trackml/tracks.py %d' % (i, i, i)

    print '%3d:' % i, cmd

    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = proc.communicate(proc)

    print out.strip(), err.strip()
