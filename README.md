# TrackML 100<sup>th</sup> place

This repository contains the solution ranked #100 in the private leaderboard of the [TrackML competition on Kaggle](https://www.kaggle.com/c/trackml-particle-identification).

100<sup>th</sup> place?? Why should anyone care? Because this solution appears to perform well at reconstructing tracks that are far away from the collision axis.

Based on a [post-competition analysis](https://twitter.com/trackmllhc/status/1070339064094736390), David Rousseau (one of the organizers) [wrote](https://www.kaggle.com/c/trackml-particle-identification/discussion/69981#433908):

> (the odd one out: in the bottom left plot, one can briefly see a dark curve rising high, this is Diogo's submission. It shows that his code finds particularly well particles that do NOT come from the z axis (axis of symmetry) (large r0), while most particles come from there (small r0), and most participants focus on particle with small r0, or even assume they come almost exactly from the z axis. Diogo's score is 0.55480, hardly better than the best public kernel, but his algorithm must be quite interesting)

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/frames/frame_02.png" width="540"></p>

So, let's have a look at the solution.

## Introduction

The training set for this competition contains on the order of 10<sup>4</sup> events (event ids). Each event contains on the order of 10<sup>4</sup> particles (particle ids). Therefore, there are a total of about (10<sup>4</sup> events) * (10<sup>4</sup> particles per event) = 10<sup>8</sup> training particles.

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/images/trackml.png" width="540"></p>
<p align="center">(Source: <a href="https://sites.google.com/site/trackmlparticle/">https://sites.google.com/site/trackmlparticle/</a>)</p>

Although there are many particles, the routes that these particles travel through space are constrained by the experimental setup and the laws of physics. For example, since there is a magnetic field, charged particles will have helical trajectories.

We could try to create a model that takes into account this particular experimental setup. We could even try to learn that model from the training data, and I guess many competitors have worked along these lines.

However, in this competition I tried a more general approach. Regardless of the particular experimental setup, I tried to answer the following question:

* *Given a large amount of training particles, is it possible to do track reconstruction from test hits by finding the training particles that best fit the test hits?*

To better explain this idea, consider the following picture:

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/images/particle.png" width="600"></p>

In the picture above, there is a training particle that passes through three detectors. In each of these detectors, there are multiple test hits. Some test hits will be closer to the training particle than others. 

The main idea is to do the following:

* Pick the test hits that are closest to the particle hits on each detector. Calculate the average distance between the particle hits and their closest test hits across detectors.

* Repeat this process for every training particle. Get the closest test hit on each detector that the particle passes through. Calculate the average distance between particle hits and their closest test hits across detectors.

* For each training particle that is considered, there will a candidate track comprising the test hits that are closest to that particle. This candidate track is characterized by a certain average distance. 

* The best candidate tracks are the ones that have the smallest average distances.

In the original dataset for the competition, every particle hit is associated with a certain _weight_. When computing the average distances above, use a weighted average that takes these weights into account.

## Using routes instead of particles

To reduce the computational burden, we group the particles that pass through exactly the same sequence of detectors. These particles are said to have the same _route_.

In the picture below, we consider three detectors and four particles that pass through these (and only these) detectors in exactly the same sequence.

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/images/route.png" width="600"></p>

The route is calculated as the "mean trajectory" of these particles. At each detector, we calculate mean position of the particle hits. The route is defined by the sequence of such positions across detectors.

To identify candidate tracks, we follow the same process as described above, but now using routes instead of the original particles, as illustrated in the following picture:

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/images/track.png" width="600"></p>

This means that only one candidate track will be considered for each unique sequence of detectors. However, different routes may share some detectors, so candidate tracks may compete for test hits on those detectors.

In general, better candidate tracks (i.e. the ones with smaller average distance) are given priority in picking their test hits. Other candidate tracks (with larger average distances) have to pick their test hits from the leftovers.

This could make some candidate tracks even worse, by slightly increasing their average distance. For simplicity, we do not update the average distances for tracks. Decisions are made based on the average distances that were calculated initially.

## The solution in 3 steps

1. The first step is _particles_: it comprises `qsub_particles.py`, `particles.py` and `merge_particles.py`.

2. The second step is _routes_: it comprises `qsub_routes.py`, `routes.py`.

3. The third step is _tracks_: it comprises `qsub_tracks.py`, `tracks.py` and `merge_tracks.py`.

## The first step: _particles_

The core of this step is `particles.py`. For a given event id (or set of event ids), this script reads and joins the hits file and the truth file for that event id  (`event*-hits.csv` and `event*-truth.csv`).

Random hits are discarded (those with particle id equal to zero).

All particle ids within an event are renumbered sequentially, starting from 1.

A _detector id_ is built by concatenating the volume id, layer id and module id for each hit.

The hits for each training event are sorted by particle id and then by absolute value of _z_.

The _x,y,z_ position of each hit is normalized by the distance to the origin. (This will be important when calculating average distances, because distances far away from the origin could be much larger than distances close to the origin.)

The end result - in the form of a list of hits with event id, particle id, detector id, normalized x,y,z and weight - is saved to a CSV file (`event*-particles.csv`).

### What is `qsub_particles.py`?

`qsub_particles.py` is a script to distribute the execution `particles.py` on a [PBS](https://www.pbspro.org/) cluster.

Basically, it sets up _n_ workers by distributing the event ids in round-robin fashion across these workers.

Each worker runs `particles.py` with the event ids that have been assigned to it.

In case the execution is interrupted or some workers fail, `qsub_particles.py` will check which event ids are missing and will again launch _n_ workers to handle those missing events.

### What is `merge_particles.py`?

Since the events are processed independently, there is a final step to merge all processed events (i.e. the output files `event*-particles.csv`) into a single CSV file (which will be called `particles.csv`).

As a result of this step, we will have a `particles.csv` file of about 48.0 GB.

## The second step: _routes_

The core of this step is `routes.py`.

It reads the output file from the first step (`particles.csv`) into memory. (Yes, it reads 48 GB into RAM. I tried using [Dask](https://dask.org/) to avoid this, but at the time of this competition Dask did not support the aggregations that will be computed next.)

The x,y,z positions of each hit are brought together into a new column named _position_.

The hits are grouped by particle id, and the following aggregations are performed:

* For each particle id, we create a sequence of _detector ids_ that the particle goes through (see above for the definition of _detector id_).

* For each particle id, we create a sequence of _positions_ that the particle goes through (based on the new _position_ column that we just defined).

* For each particle id, we also keep the sequence of _weights_ that correspond to the particle hits (see the dataset description for a definition of _weight_).

Now that hits are grouped by particle, we will group particles by sequence of detectors (route):

* For each sequence of _detector ids_, we group all the particles that have traveled through that sequence of detectors. The hit positions are stored in a 2D array where each row represents a different particle and each column represents a different detector.

* The corresponding hit weights are also stored in a 2D array.

Now, we are _not_ going to keep multiple particles for each sequence of detectors. Instead, our goal is to keep only the "mean trajectory" of the particles that have traveled across the same route.

For this purpose:

* We calculate the _count_ of particles that have traveled across each route.

* We calculate the mean _position_ of the particle hits at each detector, along each route.

* We calculate the mean _weight_ of the particle hits at each detector, along each route.

The end result - in the form of a list of routes with detector sequence, particle count, position sequence and weight sequence - is saved to a CSV file (`event*-particles.csv`).

The routes are sorted by _count_ in descending order, so that routes traveled by the largest number of particles will be considered first in the next step.

### What is `qsub_routes.py`?

Nothing special. Just the command that runs `routes.py` as a single worker on a [PBS](https://www.pbspro.org/) cluster.

As a result of this second step, we will have a `routes.csv` file of about 23.5 GB.

## The third step: _tracks_

The core of this step is `tracks.py`. For a given test event, this script reads the corresponding hits file (`event*-hits.csv`).

* In a similar way to `particles.py`, it builds a _detector id_ by concatenating the volume id, layer id and module id for each hit. It also normalizes the x,y,z position of each hit by the distance to the origin.

* In a similar way to `routes.py`, the x,y,z position of each test hit is brought into a new column named _position_.

The test hits are grouped by _detector id_. For each detector id, we have a list of test hit ids, and another list with their corresponding positions.

Subsequently, `tracks.py` reads `routes.csv` that was created in the previous step. It goes through this file line by line, where each line corresponds to a different route.

For each route being considered, we go through the detector sequence in order to pick the test hits that are closest to the route position at each detector.

We then calculate the weighted average distance between route those test hits and the route positions across detectors.

Some computational shortcuts when iterating through routes:

* Since routes have been sorted in descending order of particle count, when we get to routes that have been traveled by a single particle, we simply discard those routes and stop reading `routes.csv`. The rationale for doing this is that these could be random, one-of-a-kind routes that are not worth considering. 

* There is no point in considering routes whose weights are all zero, so we skip these routes as well, in case they appear.

* Also, we consider routes for which there are test hits in _every_ detector along that route. If there are no test hits in some detector along the route, we skip that route.

After iterating through routes, we sort them by average distance. Routes with lower average distance will be listed first, as these seem to be a better fit to the test hits.

Test hits are then assigned to routes on a first-come, first-served basis. Since the best-fitting routes are listed first, these can pick the test hits that best suit them. The remaining routes will have to pick test hits from the leftovers.

Every route corresponds to a new track id. Any test hits that were left unpicked by routes are assigned a track id of zero.

The end result - in the form of a list of test hits with event id, hit id and track id - are saved to a CSV file (`event*-tracks.csv`).

### What is `qsub_tracks.py`?

`qsub_tracks.py` is a script to distribute the execution `tracks.py` on a [PBS](https://www.pbspro.org/) cluster.

The test events are processed independently. Each event id is processed by a separate worker.

In case the execution is interrupted or some workers fail, `qsub_tracks.py` will check which event ids are missing and will launch workers to handle those missing events.

### What is `merge_tracks.py`?

Since the test events are processed independently, there is a final step to merge all processed events (i.e. the output files `event*-tracks.csv`) into a single CSV file (which will be called `tracks.csv`).

As a result of this step, we will have a `tracks.csv` file of about 206.1 MB. This is the file that can be submitted to Kaggle.
