#!/usr/bin/python

import os
import sys
import time
import numpy as np
import pandas as pd

if 'PBS_O_WORKDIR' in os.environ:
    os.chdir(os.environ['PBS_O_WORKDIR'])

if len(sys.argv) < 2:
    print 'Missing event id.'
    exit()

event_id = int(sys.argv[1])

def pp(*strings):
    t = time.strftime('%H:%M:%S')
    print '%s [%3d]' % (t, event_id),
    for s in strings:
        print s,
    print
    sys.stdout.flush()

fname = 'data/test/event%09d-hits.csv' % event_id
pp('Reading:', fname)
df = pd.read_csv(fname)

pp('Processing hits')

df['event_id'] = event_id

df['detector_id'] = df.apply(lambda x: int('%02d%02d%04d' % (x['volume_id'],
                                                             x['layer_id'],
                                                             x['module_id'])), axis=1)

df['r'] = df.apply(lambda x: np.sqrt(np.sum(np.square([x['x'], x['y'], x['z']]))), axis=1)

df['x'] /= df['r']
df['y'] /= df['r']
df['z'] /= df['r']

df['position'] = df[['x', 'y', 'z']].values.tolist()

pp('Grouping hits')
f = {'hit_id': lambda x: list(x), 'position': lambda x: list(x)}
hits = df.groupby('detector_id').agg(f)
hit_ids = hits['hit_id'].to_dict()
hit_positions = hits['position'].to_dict()

fname = 'routes.csv'
pp('Reading:', fname)
routes = open(fname, 'r')

pp('Finding best hits')
best_hits = dict()
best_dist = dict()
for line in routes:
    parts = line.split('"')
    route_id = eval(parts[1])
    route_count = int(parts[3])
    if route_count <= 1:
        break
    route_positions = eval(parts[5])
    route_weights = eval(parts[7])
    if np.count_nonzero(route_weights) == 0:
        continue
    if all([detector_id in hit_ids for detector_id in route_id]):
        best_hits[route_id] = []
        best_dist[route_id] = []
        for (detector_id, route_position) in zip(route_id, route_positions):
            a = np.array(hit_positions[detector_id])
            b = route_position
            dist = np.sqrt(np.sum(np.square(a-b), axis=-1))
            i = np.argmin(dist)
            best_hits[route_id].append(hit_ids[detector_id][i])
            best_dist[route_id].append(dist[i])
        best_dist[route_id] = np.average(best_dist[route_id], weights=route_weights)

pp('Sorting routes')
route_ids = sorted(best_dist, key=best_dist.get)

pp('Finding tracks')
new_track_id = 0
track_ids = dict()
for route_id in route_ids:
    new_track_id += 1
    for hit_id in best_hits[route_id]:
        if hit_id not in track_ids:
            track_ids[hit_id] = new_track_id

pp('Writing track ids')

df['track_id'] = df['hit_id'].map(track_ids).fillna(0.).astype(int)

df = df[['event_id', 'hit_id', 'track_id']]

fname = 'out/event%09d-tracks.csv' % event_id
pp('Writing:', fname)
df.to_csv(fname, header=True, index=False)
