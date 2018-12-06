#!/usr/bin/python

import os
import sys
import glob
import numpy as np
import pandas as pd

if 'PBS_O_WORKDIR' in os.environ:
    os.chdir(os.environ['PBS_O_WORKDIR'])

event_ids = [int(event_id) for event_id in sys.argv[1:]]

print 'event_ids:', event_ids

for event_id in event_ids:
        
    hits_file = glob.glob('data/train_?/event%09d-hits.csv' % event_id)[0]
    truth_file = glob.glob('data/train_?/event%09d-truth.csv' % event_id)[0]
    
    print 'Reading:', hits_file
    print 'Reading:', truth_file
    
    hits = pd.read_csv(hits_file).set_index('hit_id')
    truth = pd.read_csv(truth_file).set_index('hit_id')
    df = hits.join(truth)

    df = df[df['particle_id'] != 0]
    
    print 'hits:', df.shape[0]
    print 'particles:', df['particle_id'].nunique()
    
    df['event_id'] = event_id
    
    particle_ids = df['particle_id'].unique()
    map_particle_id = dict([(particle_id, i+1) for (i, particle_id) in enumerate(particle_ids)])
    df['particle_id'] = df['particle_id'].map(map_particle_id)
    
    df['detector_id'] = df.apply(lambda x: int('%02d%02d%04d' % (x['volume_id'],
                                                                 x['layer_id'],
                                                                 x['module_id'])), axis=1)

    df['z_abs'] = df['z'].abs()
    df.sort_values(['event_id', 'particle_id', 'z_abs'], inplace=True)

    df['r'] = df.apply(lambda x: np.sqrt(np.sum(np.square([x['x'], x['y'], x['z']]))), axis=1)
    
    df['x'] /= df['r']
    df['y'] /= df['r']
    df['z'] /= df['r']
    
    df = df[['event_id', 'particle_id', 'detector_id', 'x', 'y', 'z', 'weight']]
    
    fname = 'out/event%09d-particles.csv' % event_id
    print 'Writing:', fname
    df.to_csv(fname, float_format='%g', header=True, index=False)
