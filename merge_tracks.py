#!/usr/bin/python

import glob
from tqdm import tqdm

files = sorted(glob.glob('out/event*-tracks.csv'))

fname = 'tracks.csv'
print 'Writing:', fname
fout = open(fname, 'w')

fout.write('event_id,hit_id,track_id\n')

for fname in tqdm(files):
    fin = open(fname, 'r')
    lines = fin.readlines()
    fin.close()
    for line in lines[1:]:
        fout.write(line)

fout.close()
