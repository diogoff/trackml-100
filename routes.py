#!/usr/bin/python

import os
import csv
import time
import numpy as np
import pandas as pd

if 'PBS_O_WORKDIR' in os.environ:
    os.chdir(os.environ['PBS_O_WORKDIR'])

fname = 'particles.csv'
t = time.strftime('%H:%M:%S')
print '[%s] Reading:' % t, fname
df = pd.read_csv(fname)

t = time.strftime('%H:%M:%S')
print '[%s] Calculating position...' % t
df['position'] = df[['x', 'y', 'z']].values.tolist()

t = time.strftime('%H:%M:%S')
print '[%s] Grouping by particle_id...' % t
f = {'detector_id': lambda x: tuple(x),
     'position': lambda x: list(x),
     'weight': lambda x: list(x)}
df = df.groupby(['event_id', 'particle_id']).agg(f).reset_index()

t = time.strftime('%H:%M:%S')
print '[%s] Grouping by detector_id...' % t
f = {'position': lambda x: list(x),
     'weight': lambda x: list(x)}
df = df.groupby('detector_id').agg(f).reset_index()

df['count'] = df['position'].map(lambda x: len(x))
df['position'] = df['position'].map(lambda x: np.mean(x, axis=0).tolist())
df['weight'] = df['weight'].map(lambda x: np.mean(x, axis=0).tolist())

df = df[['detector_id', 'count', 'position', 'weight']]

df.sort_values('count', ascending=False, inplace=True)

fname = 'routes.csv'
t = time.strftime('%H:%M:%S')
print '[%s] Writing:' % t, fname
df.to_csv(fname, quoting=csv.QUOTE_ALL, header=False, index=False)
