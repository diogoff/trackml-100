#!/usr/bin/python

import glob
from tqdm import tqdm

files = sorted(glob.glob('out/event*-particles.csv'))

fname = 'particles.csv'
print 'Writing:', fname
fout = open(fname, 'w')

for fname in tqdm(files):
    fin = open(fname, 'r')
    lines = fin.readlines()
    fin.close()
    if fname == files[0]:
        fout.write(lines[0])
    for line in lines[1:]:
        fout.write(line)

fout.close()
