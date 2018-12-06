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

<p align="center"><img src="https://raw.githubusercontent.com/diogoff/trackml-100/master/images/trackml.png" width="540"></p>
