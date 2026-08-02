# Complete Mathematical Equation Report

**Representation mode:** `hybrid_vector`  
**Source image size:** 640 × 480 pixels  
**Equation canvas:** 640 × 480  
**Coordinate system:** `normalized_cartesian`

Exactness: the document contains every line, circle, ellipse, and Bezier segment in the exported vector model. The model itself is an approximation obtained from image processing unless the source already consists of exactly those mathematical primitives.

The equations below are not a shortened GUI preview. Every equation component and every retained coefficient in the exported model is included.

## Line equations

Each detected line is represented parametrically. The parameter interval is included so that the equation draws only the detected segment rather than an infinite line.

### Line 1: x-coordinate

$$
x_{1}(t)=-0.75+\left(1.5\right)t,\qquad 0\le t\le 1
$$

### Line 1: y-coordinate

$$
y_{1}(t)=-0.4375+\left(0\right)t,\qquad 0\le t\le 1
$$

## Circle equations

### Circle 1: x-coordinate

$$
x_{1}(t)=0+\left(0.28125\right)\cos t,\qquad 0\le t<2\pi
$$

### Circle 1: y-coordinate

$$
y_{1}(t)=0.125+\left(-0.28125\right)\sin t,\qquad 0\le t<2\pi
$$

## Piecewise cubic Bezier equations

Every irregular contour is a sequence of cubic Bezier segments. Taken together with the listed parameter domains and fill rule, these equations fully specify the exported vector model.

### Bezier path 1, segment 1: x-coordinate

Closed=True; unfilled contour.

$$
x_{1,1}(t)=(1-t)^3\left(-0.4375\right)+3(1-t)^2t\left(-0.3125\right)+3(1-t)t^2\left(0.3125\right)+t^3\left(0.4375\right),\qquad 0\le t\le 1
$$

### Bezier path 1, segment 1: y-coordinate

$$
y_{1,1}(t)=(1-t)^3\left(-0.1875\right)+3(1-t)^2t\left(0.375\right)+3(1-t)t^2\left(0.375\right)+t^3\left(-0.1875\right),\qquad 0\le t\le 1
$$

### Bezier path 1, segment 2: x-coordinate

$$
x_{1,2}(t)=(1-t)^3\left(0.4375\right)+3(1-t)^2t\left(0.21875\right)+3(1-t)t^2\left(-0.21875\right)+t^3\left(-0.4375\right),\qquad 0\le t\le 1
$$

### Bezier path 1, segment 2: y-coordinate

$$
y_{1,2}(t)=(1-t)^3\left(-0.1875\right)+3(1-t)^2t\left(-0.3125\right)+3(1-t)t^2\left(-0.3125\right)+t^3\left(-0.1875\right),\qquad 0\le t\le 1
$$
