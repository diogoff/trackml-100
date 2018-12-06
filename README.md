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

Apparently, the answer to this question is no, since this approach was ranked #100 in the competition. However, the problem of finding the training particle that best fits a set of test hits is an interesting computation problem _per se_.

I spent my whole time in the competition trying to come up with a feasible computational approach to this problem.

_Disclaimer:_ I never intended to compete based on such naïve approach. This was just something that I would use as an initial baseline to compare with the performance of other algorithms that I would subsequently develop. However, as it often happens in Kaggle competitions, the first idea that comes to mind is the one you will end up with.


