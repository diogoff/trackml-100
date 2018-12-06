#!/usr/bin/python

import glob
import subprocess

files = sorted(glob.glob('data/train_?/event*-hits.csv'))
event_ids_1 = []
for fname in files:
    i0 = fname.find('event') + len('event')
    i1 = fname.find('-hits.csv')
    event_id = int(fname[i0:i1])
    event_ids_1.append(event_id)

files = sorted(glob.glob('out/event*-particles.csv'))
event_ids_2 = []
for fname in files:
    i0 = fname.find('event') + len('event')
    i1 = fname.find('-particles.csv')
    event_id = int(fname[i0:i1])
    event_ids_2.append(event_id)

missing_event_ids = list(set(event_ids_1) - set(event_ids_2))

n = 40
workers = dict()
for (i, event_id) in enumerate(missing_event_ids):
    k = i % n
    if k not in workers:
        workers[k] = []
    workers[k].append(event_id)

for k in sorted(workers.keys()):
    event_ids = ' '.join([str(event_id) for event_id in workers[k]])
    cmd = 'qsub -l nodes=1:ppn=1 -l walltime=24:00:00 -l mem=1GB -N task_%03d -j oe -o out/particles_%03d.out -- trackml/particles.py %s' % (k, k, event_ids)
    print cmd
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate(proc)
    print out.strip(), err.strip()
