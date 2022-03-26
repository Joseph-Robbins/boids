from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsEllipseItem
import numpy as np
from cmath import sqrt

# Defines a vector class with useful operators to calculate boid physics
class vector():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def mag(self): # Return this vector's magnitude
        return sqrt(self.x**2 + self.y**2)

    def sub(self, other): # Subtract each element of the given vector from this vector
        return vector(self.x - other.x, self.y - other.y)

    def add(self, other): # Add each element of the vectors together
        return vector(self.x + other.x, self.y + other.y)

    def mult(self, mult): # This is element-wise, not vector multiplication
        return vector(self.x * mult, self.y * mult)

    def div(self, other): # This is element-wise, not vector division
        return vector(self.x / other, self.y / other)

    def norm(self): # Return the normalised vector
        vec = [self.x, self.y]
        vec = vec / np.linalg.norm(vec)
        return vector(vec[0], vec[1])

# Defines the behaviour of individual boids
class Boid(QGraphicsEllipseItem):
    def __init__(self, SCENE_WIDTH, SCENE_HEIGHT):
        # super().__init__(QPolygonF([QPoint(0, 0), QPoint(20, 10), QPoint(14, 0), QPoint(20, -10)])) # Old polygon shape
        super().__init__(0, 0, 10, 10)

        # Initialise the vectors which we will be working on to move the boids
        self.position = vector(np.random.randint(0, SCENE_WIDTH), np.random.randint(0, SCENE_HEIGHT))
        self.velocity = vector(np.random.randint(-100, 100), np.random.randint(-100, 100))
        self.accel = vector(np.random.randint(-10, 10), np.random.randint(-10, 10))

        # Set the boid's initial parameters for being shown in the QGraphicsScene
        self.setPos(self.position.x, self.position.y)
        self.setRotation(45)
        self.setBrush(QColor.fromHsv(200, 255, np.random.randint(100, 255)))

    # Steer to avoid colliding with your neighbors
    def separation(self, neighbours, sensor_range, speed_mult):
        separation_distance = sensor_range / 2
        desired_vector = vector(0, 0)
        count = 0

        # For every neighbour, check if it is too close
        for boid in neighbours:
            distance = sqrt((boid.pos().x() - self.pos().x())**2 + (boid.pos().y() - self.pos().y())**2).real # Euclidean distance

            if (distance > 0) & (distance < separation_distance): # If the distance to boid is within the separation threshold, we need to move away from it
                diff = self.position.sub(boid.position) # Find difference between my position and boids position
                diff = diff.norm()
                diff = diff.div(distance)
                desired_vector = desired_vector.add(diff) # Find the desired velocity vector
                count += 1

        # If the boid has flockmates which it needs to separate from
        if count > 0:
            desired_vector = desired_vector.norm()
            desired_vector = desired_vector.mult(speed_mult)

            return desired_vector.sub(self.velocity) # Use Reynold's steering formula to find the required steering force to get to 
                                                     # our desired velocity (steering force = desired velocity - current velocity)

        return desired_vector

    # Steer in the same direction as your neighbors
    def alignment(self, neighbours, speed_mult):
        sum = vector(0, 0)
        desired_velocity = vector(0, 0)

        for boid in neighbours:
            sum.add(boid.velocity)

        if (sum.x != 0) | (sum.y != 0):
            desired_velocity = sum.norm()
            desired_velocity = desired_velocity.mult(speed_mult)

            return desired_velocity.sub(self.velocity) # Use Reynold's steering formula to find the required steering force

        return sum

    # Steer towards the center of mass of your neighbors (stay with the group)
    def cohesion(self, neighbours, speed_mult):
        sum = vector(0, 0)
        desired_velocity = vector(0, 0)
        average = vector(0, 0)

        # Sum the position of all the neighbours
        for boid in neighbours:
            sum = sum.add(boid.position)

        if len(neighbours) > 0:
            average = sum.div(len(neighbours)) # Find the neighbours' average position
            # print(f"average: x = {average.x}, y = {average.y}")

            # Calculate a velocity vector to move towards that average position
            desired_velocity = average.sub(self.position)
            desired_velocity = desired_velocity.norm()
            desired_velocity = desired_velocity.mult(speed_mult)

            return desired_velocity.sub(self.velocity) # Use Reynold's steering formula to find the required steering force
        
        return average
        
    # Find all the neighbouring boids within range, given a list of all the boids
    def find_neighbours(self, boids, range):
        # boids = copy(boids)
        neighbours = []
        for boid in boids:
            if boid == self:
                pass
            else:
                distance = sqrt((boid.pos().x() - self.pos().x())**2 + (boid.pos().y() - self.pos().y())**2).real
                if distance < range:
                    neighbours.append(boid)
        
        return neighbours

    # Find and set the boid's new position in the QGraphicsScene
    def update(self, scene_width, scene_height, ts):
        # Update velocity using acceleration
        self.velocity.x = self.velocity.x + (self.accel.x * ts)
        self.velocity.y = self.velocity.y + (self.accel.y * ts)

        # Update position
        self.position.x = self.pos().x() + (self.velocity.x * ts)
        self.position.y = self.pos().y() + (self.velocity.y * ts)

        # alpha = np.degrees(np.arctan2(self.accel.x, self.accel.y))
        # alpha = 180 - np.degrees(np.arctan2(self.velocity.y, self.velocity.x))
        # self.setRotation(alpha)
        # self.setBrush(Qt.green)

        # Reset acceleration
        self.accel.x = 0
        self.accel.y = 0
        
        # If boids go off the screen, make them teleport to the other side of the screen
        if self.position.x > scene_width:
            self.position.x = 0
        elif self.position.x < 0:
            self.position.x = scene_width

        if self.position.y > scene_height:
            self.position.y = 0
        elif self.position.y < 0:
            self.position.y = scene_height

        # Call QGraphicsPolygonItem's setPos method to move the polygon in the QGraphicScene
        self.setPos(QPointF(self.position.x, self.position.y))

# Defines the behaviour of the flock of boids
class floick():
    def __init__(self, num_boids, scene_width, scene_height):
        # Create a list of boids in random positions
        self.boids = []
        for i in range(num_boids):
            self.add_boid(scene_width, scene_height)

    def add_boid(self, scene_width, scene_height):
        self.boids.append(Boid(scene_width, scene_height))

    def fly(self, scene_width, scene_height, ts, sensor_range, speed_mult, sep_weight, align_weight, cohesion_weight):
        for boid in self.boids:
            # Make a list of all of the boids within BOID_SENSOR_RANGE of the current boid
            neighbours = boid.find_neighbours(self.boids, sensor_range)

            # Calculate the boid's acceleration using the 3 flocking rules
            separation = boid.separation(neighbours, sensor_range, speed_mult)
            alignment = boid.alignment(neighbours, speed_mult)
            cohesion = boid.cohesion(neighbours, speed_mult)

            # Apply weights to each of the 3 rules
            separation = separation.mult(sep_weight/10)
            alignment = alignment.mult(align_weight/10)
            cohesion = cohesion.mult(cohesion_weight/10)

            # Set the boid's acceleration to the sum of the accelerations produced by each rule
            boid.accel = boid.accel.add(separation)
            boid.accel = boid.accel.add(alignment)
            boid.accel = boid.accel.add(cohesion)

            # Move the boid on the screen
            boid.update(scene_width, scene_height, ts)
