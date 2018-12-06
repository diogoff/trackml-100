# TrackML 100<sup>th</sup> place

This repository contains the solution ranked #100 in the private leaderboard of the [TrackML competition on Kaggle](https://www.kaggle.com/c/trackml-particle-identification).

100<sup>th</sup> place?? Why should anyone care? Well, because this solution appeared as an "odd one" in [post-competition analysis](https://twitter.com/trackmllhc/status/1070339064094736390).

As [David Rousseau](https://www.kaggle.com/c/trackml-particle-identification/discussion/69981#433908) (one of the competition organizers) puts it:

> (the odd one out: in the bottom left plot, one can briefly see a dark curve rising high, this is Diogo's submission. It shows that his code finds particularly well particles that do NOT come from the z axis (axis of symmetry) (large r0), while most particles come from there (small r0), and most participants focus on particle with small r0, or even assume they come almost exactly from the z axis. Diogo's score is 0.55480, hardly better than the best public kernel, but his algorithm must be quite interesting)

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/frames/frame_02.png" width="540"></p>

So, let's have a look at the code.

## Main idea

* The training data for this competition contains on the order of 10<sup>4</sup> events (event ids).

* Each event contains on the order of 10<sup>4</sup> particles (particle ids).

* And each particle contains on the order of 10 hits (hit ids).

From the numbers above, we have a total of about (10<sup>4</sup> events) * (10<sup>4</sup> particles per event) = 10<sup>8</sup> particles.

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/images/trackml.png"></p>
<p align="center">(Source: <a href="https://sites.google.com/site/trackmlparticle/">https://sites.google.com/site/trackmlparticle/</a>)</p>

Although there are many particles, the routes that these particles travel through space are constrained by the experimental setup and the laws of physics. For example, since they are immersed in a magnetic field, charged particles will have helical trajectories.

We could try to create a model that takes into account this particular experimental setup. We could even try to learn that model from the training data, and I guess many competitors have worked along these lines.

However, in this competition I tried to use a more general approach. Regardless of the particular experimental setup, I tried to answer the following question:

* *Given a large amount of training particles, is it possible to do track reconstruction from test hits by finding the training particles that best fit the test hits?*

Apparently, the answer to this question is _yes_, but there are way better approaches for track reconstruction. This suggests that the training set does not seem to include all the tracks that may occur in a test experiment.

However, the problem of finding the training particles that best fit a set of test hits is an interesting computational problem by itself. I spent my whole time in the competition trying to come up with a feasible computational approach to this problem.

_Disclaimer:_ I never intended to compete based on such naïve approach. This was just something that I planned to use as a baseline to compare with other approaches that I would subsequently develop. However, as it often happens in Kaggle, the first idea that comes to mind is the one you will end up with.

## How could such approach be computationally feasible?

Searching for the training particles that best fit a set of test hits leads to a combinatorial explosion if the number of training particles and the number of test hits are both large.

First, to find the best test hits for a single training particle involves computing the distances between all test hits and the particle trajectory. This seems straightforward until one realizes that each test event has on the order of 10<sup>5</sup> test hits. If a training particle has on the order of 10 hits, there are on the order of 10<sup>6</sup> three-dimensional distances to compute.

Now consider that there are on the order of 10<sup>8</sup> particles in the training set, as is the case in this competition. Suddenly, there are 10<sup>14</sup> three-dimensional distances to compute.

After computing all these distances, there is still the problem of assigning each test hit to a single particle. If multiple particles compete for the same test hits, we have another combinatorial problem of deciding how to assign test hits to training particles so that we get an overall best fit.

The problem seems unapproachable in this way, unless...

We take into account the discretization of space that is present in this problem through the use of detectors (volume ids, layer ids, module ids).

We assume that when a training particle goes across a detector, we only need to consider the test hits on the same detector, and we can forget about every other test hit in other detectors. This drastically reduces the number of distances to be computed.

If a training particle goes through a sequence of detectors, then the relevant test hits are those that reside on the same sequence of detectors.

We call this sequence of detectors a _route_.

Now, in the figure above, we see that particles are scattered more or less radially (and helically) from the collision point. This means that not every route is possible.

If a particle contains on the order of 10 hits








## The solution in 3 steps

1. The first step is _particles_: it comprises `qsub_particles.py`, `particles.py` and `merge_particles.py`.

2. The second step is _routes_: it comprises `qsub_routes.py`, `routes.py`.

3. The third step is _tracks_: it comprises `qsub_tracks.py`, `tracks.py` and `merge_tracks.py`.

## The first step: _particles_

The core of this step is `particles.py`. For a given event id (or set of event ids), this script reads and joins the hits file and the truth file for that event id  (`event*-hits.csv` and `event*-truth.csv`).

Random hits are discarded (those with particle id equal to zero).

All particle ids within an event are renumbered sequentially, starting from 1.

A _detector id_ is built by concatenating the volume id, layer id and module id for each hit.

The hits for each (training) event are sorted by particle id and, for each particle id, the hits are sorted by absolute value of _z_.

The _x,y,z_ position of each hit is normalized by the distance to the origin.

The end result - in the form of a list of hits with event id, particle id, detector id, position x,y,z and weight - is saved to a CSV file (`event*-particles.csv`).

### What is `qsub_particles.py`?

`qsub_particles.py` is a script to distribute the execution `particles.py` on a [PBS](https://www.pbspro.org/) cluster.

Basically, it sets up _n_ workers by distributing the event ids in round-robin fashion across these workers.

Each worker runs `particles.py` with the event ids that have been assigned to it.

In case the execution is interrupted or some workers fail, `qsub_particles.py` will check which event ids are missing processing and will again launch _n_ workers to handle those missing events.

### What is `merge_particles.py`?

Since events are processed independently by _n_ workers, there is a final step to merge all processed events (i.e. the output files `event*-particles.csv`) into a single CSV file (which will be called `particles.csv`).

As a result of this step, we will have a `particles.csv` file of about 48.0 GB.

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

Now, we are _not_ going to keep multiple particles for each sequence of detectors. Instead, our goal is to keep only the "mean trajectory" of the particles that have traveled across the same sequence of detectors.

For this purpose:

* We keep the _count_ of particles that have traveled across the same sequence of detectors.

* We keep the mean _position_ of the particle hits at each detector, along the sequence of detectors.

* We keep the mean _weight_ of the particle hits at each detector, along the sequence of detectors.

Such "mean trajectory" (defined by the mean position of particle hits at each detector along a sequence of detectors) is called a _route_.

The results are sorted by _count_ in descending order, so that the routes that have been traveled by the largest number of particles are listed first.

As a result of this first step, we will have a `routes.csv` file of about 23.5 GB.

### What is `qsub_routes.py`?

Nothing special. Only the command that runs `routes.py` as a single worker on a [PBS](https://www.pbspro.org/) cluster.

## The third step: _tracks_

The core of this step is `tracks.py`. This script receives a (test) event id and reads the corresponding hits file (`event*-hits.csv`).

* In a similar way to `particles.py`, it builds a _detector id_ by concatenating the volume id, layer id and module id for each hit.

* Also in a similar way to `particles.py`, the x,y,z position of each hit is normalized by the distance to the origin.

* In a similar way to `routes.py`, the x,y,z position of each hit is brought into a new column named _position_.

The (test) hits are grouped by _detector id_. For each detector id, we have a list of hit ids, and another list with their corresponding positions.

`tracks.py` reads `routes.csv` that was created in the previous step. It goes through this file line by line, where each line corresponds to a different route.

The idea is to pick up the (test) hits that are closest to the route being considered. For each detector along the route, we calculate the distance between all test hits at that detector and the (mean) _position_ of the route at the same detector.

The best hits are those that result in the lowest average distance along the route, where this average is calculated by taking into account the (mean) _weight_ associated with each detector along the route.




have the mean position 






* Since routes have been sorted in descending order of particle count, when we get to unique, one-of-a-kind routes that have been traveled by a single particle, we simply discard those routes and stop reading `routes.csv`. (We take these as untrustworthy, possibly random routes that are not worth considering. Anyway, by this point most hits should have been taken up by more trustworthy routes.)

* There is no point in considering routes whose weights are all zero, so we skip these routes as well.

* Also 














### What is `qsub_tracks.py`?

`qsub_tracks.py` is a script to distribute the execution `tracks.py` on a [PBS](https://www.pbspro.org/) cluster.

The (test) events are processed in parallel. Each (test) event id is processed by a separate worker.

In case the execution is interrupted or some workers fail, `qsub_tracks.py` will check which event ids are missing and will launch workers to handle those missing events.

### What is `merge_tracks.py`?

Since events are processed independently, there is a final step to merge all processed events (i.e. the output files `event*-tracks.csv`) into a single CSV file (which will be called `tracks.csv`).

As a result of this step, we will have a `tracks.csv` file of about 206.1 MB. This is the file submitted to the leaderboard.
