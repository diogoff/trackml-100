# TrackML 100<sup>th</sup> place

This repository contains the solution that ranked #100 in the private leaderboard of the [TrackML competition on Kaggle](https://www.kaggle.com/c/trackml-particle-identification).

100<sup>th</sup> place?? Why should anyone care? Well, because this solution appeared as an odd one in [post-competition analysis](https://twitter.com/trackmllhc/status/1070339064094736390).

As [David Rousseau](https://www.kaggle.com/c/trackml-particle-identification/discussion/69981#433908) puts it:

> (the odd one out: in the bottom left plot, one can briefly see a dark curve rising high, this is Diogo's submission. It shows that his code finds particularly well particles that do NOT come from the z axis (axis of symmetry) (large r0), while most particles come from there (small r0), and most participants focus on particle with small r0, or even assume they come almost exactly from the z axis. Diogo's score is 0.55480, hardly better than the best public kernel, but his algorithm must be quite interesting)

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/frames/frame_02.png" width="540"></p>

So, let's have a look at the code.

## Main idea

* The training data for this competition contained on the order of 10<sup>4</sup> events (event ids).

* Each event contained on the order of 10<sup>4</sup> particles (particle ids).

* And each particle contained on the order of 10 hits (hit ids).

From the numbers above, we have a total of about (10<sup>4</sup> events) * (10<sup>4</sup> particles per event) = 10<sup>8</sup> particles.

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/images/trackml.png"></p>
<p align="center">(Source: <a href="https://sites.google.com/site/trackmlparticle/">https://sites.google.com/site/trackmlparticle/</a>)</p>

Although there are many particles, the routes that these particles travel through space are constrained by the experimental setup and the laws of physics. For example, since they are immersed in a magnetic field, charged particles will have helical trajectories.

We could try to create a model that reproduces this particular experimental setup. We could even try to learn that model from the training data, and I guess many competitors have worked along these lines.

However, in this competition I tried to use a more general approach. Regardless of the particular experimental setup, I tried to answer the following question:

* *Given a large amount of training particles, is it possible to do track reconstruction from test hits by finding which training particles best fit the test hits?*

Apparently, the answer to this question is _no_, since there are much better approaches out there. In other words, the training set does not seem to be representative of all the tracks that may occur in a test experiment.

However, the problem of finding the training particle that best fits a set of test hits is an interesting computational problem _per se_. I spent my whole time in the competition trying to come up with a feasible computational approach to this problem.

_Disclaimer:_ I never intended to compete based on such naïve approach. This was just something that I would use as a baseline to compare with other algorithms that I would subsequently develop. However, as it often happens in Kaggle, the first idea that comes to mind is the one you will end up with.

## TODO: Explicar aqui o que torna a abordagem computacionalmente possível

## The solution in 3 steps

1. The first step is _particles_: it comprises `qsub_particles.py`, `particles.py` and `merge_particles.py`.

2. The second step is _routes_: it comprises `qsub_routes.py`, `routes.py`.

3. The third step is _tracks_: it comprises `qsub_tracks.py`, `tracks.py` and `merge_tracks.py`.

## The first step: _particles_

The core of this step is `particles.py`. For a given event id (or set of event ids), this script reads and joins the hits file and the truth file for that event id  (`event*-hits.csv` and `event*-truth.csv`).

Random hits are discarded (those with particle id equal to zero).

All particle ids within an event are renumbered sequentially, starting from 1.

A _detector id_ is built by concatenating volume id, layer id and module id for each hit.

The hits for each (training) event are sorted by particle id and, for each particle id, the hits are sorted by absolute value of _z_.

The _x,y,z_ position of each hit is normalized by the distance to the origin.

The end result - in the form of a list of hits with event id, particle id, detector id, position x,y,z and weight - is saved to a CSV file (`event*-particles.csv`).

#### What is `qsub_particles.py`?

`qsub_particles.py` is a script to distribute the execution `particles.py` on a [PBS](https://www.pbspro.org/) cluster.

Basically, it sets up _n_ workers by distributing the event ids in round-robin fashion across these workers.

Each worker runs `particles.py` with the event ids that have been assigned to it.

In case the execution is interrupted or some workers fail, `qsub_particles.py` will check which event ids are missing processing and will again launch _n_ workers to handle those missing events.

#### What is `merge_particles.py`?

Since events are processed independently by _n_ workers, there is a final step to merge all processed events (i.e. the output files `event*-particles.csv`) into a single CSV file (which will be called `particles.csv`).

As a result of this first step, we will have a `particles.csv` file with about 48.0 GB.

## The second step: _routes_

The core of this step is `routes.py`.

It reads the output file from the first step (`particles.csv`) into memory (yes, it reads 48 GB into RAM; I tried using [Dask](https://dask.org/) to avoid this, but at the time of this competition Dask did not support the aggregations that will be computed next).

The x,y,z position of each hit is brought into a new column named _position_.

Now comes the first of several aggregating operations that are central to this approach:

* For each particle id, we create a sequence of _detector ids_ that the particle goes through (see above for the definition of _detector id_).

* For each particle id, we create a sequence of _positions_ that the particle goes through (based on the new _position_ column that we just defined).

* For each particle id, we also keep the sequence of _weights_ that correspond to the particle hits (see the dataset description for a definition of _weight_).

A second aggregating operation is performed on top of the previous one:

* For each sequence of _detector ids_, we group all the particles that have traveled across that sequence of detectors. The particle (hit) positions will be stored in a 2D array where each row represents a different particle. Specifically, each row contains the list of hit positions as the particle goes through that sequence of detectors.

* As before, we keep the _weights_ that correspond to each hit.

We are _not_ going to keep multiple particles for each sequence of detectors. Instead, our goal is to keep only the "mean trajectory" of the particles that have traveled across the same sequence of detectors.

For this purpose:

* We keep the _count_ of particles that have traveled across the same sequence of detectors.

* We keep the mean _position_ of the particle hits at each detector, along the sequence of detectors.

* We keep the mean _weight_ of the particle hits at each detector, along the sequence of detectors.

The results are sorted by _count_ in descending order, so that in the next step we consider first the sequences of detectors (i.e. the _routes_) that have been traveled by the largest number of particles.

#### What is `qsub_routes.py`?

Nothing special. Only the command that runs `routes.py` on a [PBS](https://www.pbspro.org/) cluster.

## The third step: _tracks_

