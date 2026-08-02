# Mathematical details

## Coordinates

The internal drawing model uses image coordinates: origin at the upper-left, x increasing right, and y increasing downward.

Exports support:

1. pixel coordinates;
2. normalized Cartesian coordinates in `[0,1]`, with y increasing upward;
3. centered Cartesian coordinates scaled by half of the larger image dimension, preserving aspect ratio.

## Bézier path construction

A contour is simplified, uniformly resampled by arc length, lightly smoothed, and converted from a Catmull–Rom sequence into cubic Bézier segments. For adjacent samples `P_i` and `P_(i+1)`, the controls are

\[
C_1=P_i+\frac{P_{i+1}-P_{i-1}}{6},\qquad
C_2=P_{i+1}-\frac{P_{i+2}-P_i}{6}.
\]

Each segment is then evaluated by

\[
B_i(t)=(1-t)^3P_i+3(1-t)^2tC_1+3(1-t)t^2C_2+t^3P_{i+1}.
\]

## Fourier descriptors

After arc-length resampling, contour points are combined into complex samples `z_n=x_n+i y_n`. The discrete Fourier coefficients are

\[
c_k=\frac{1}{N}\sum_{n=0}^{N-1}z_n e^{-i2\pi kn/N}.
\]

The truncated reconstruction is

\[
\hat z(t)=\sum_{k\in\mathcal K}c_k e^{i2\pi kt}.
\]

The implementation retains low-frequency harmonics around zero because they capture the dominant global shape.

## Orthonormal 2D DCT

For a channel of size `H x W`, the inverse orthonormal DCT-II basis is

\[
I(x,y)=\sum_{v=0}^{H-1}\sum_{u=0}^{W-1} C(v,u)\alpha(v,H)\alpha(u,W)
\cos\left(\frac{\pi(2y+1)v}{2H}\right)
\cos\left(\frac{\pi(2x+1)u}{2W}\right),
\]

where

\[
\alpha(0,N)=\frac{1}{\sqrt N},\qquad
\alpha(k,N)=\sqrt{\frac{2}{N}},\;k>0.
\]

The largest-magnitude coefficients are retained independently for each channel.
