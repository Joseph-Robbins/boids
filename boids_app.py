from cmath import sqrt
from PyQt5.QtCore import Qt, QPointF, QTimer
from PyQt5.QtWidgets import QGraphicsView, QApplication, QGraphicsScene, QGraphicsPolygonItem, QGraphicsEllipseItem, QWidget, QBoxLayout, QSlider, QLabel, QGridLayout, QGroupBox
from PyQt5.QtGui import QColor, QFont
import numpy as np

from floick import floick

SCENE_WIDTH = 800
SCENE_HEIGHT = 500

NUM_BOIDS = 100
BOID_SENSOR_DISTANCE = 50
BOID_SPEED = 500
BOID_SEPARATION_WEIGHT = 5 #4/8
BOID_ALIGNMENT_WEIGHT = 4  #3/8
BOID_COHESION_WEIGHT = 1   #1/8
TS = int(1/60 * 100)

# This is the rectangular window in which the boids can be seen
class boid_view(QGraphicsView):
    def __init__(self, num_boids):
        super(boid_view, self).__init__()

        self.resize(SCENE_WIDTH + 50, SCENE_HEIGHT + 50)
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, SCENE_WIDTH, SCENE_HEIGHT)
        self.scene.addRect(0, 0, SCENE_WIDTH, SCENE_HEIGHT)
        self.scene.setBackgroundBrush(QColor.fromHsl(200, 199, 30))
        self.setScene(self.scene)

        # Create a flock (floick lol) of boids and add each of them to the scene
        self.floick = floick(num_boids, SCENE_WIDTH, SCENE_HEIGHT)
        for boid in self.floick.boids:
            self.scene.addItem(boid)

    def mousePressEvent(self, event):
        self.update()

    # Each time the tim timer goes off, call the flock's fly method to update boids, and also increase/decrease the number of boids if neccessary
    def update(self):
        if NUM_BOIDS < len(self.floick.boids):
            while NUM_BOIDS < len(self.floick.boids):
                rand = np.random.randint(0, len(self.floick.boids))
                self.scene.removeItem(self.floick.boids[rand])
                self.floick.boids.pop(rand)

        elif NUM_BOIDS > len(self.floick.boids):
            while NUM_BOIDS > len(self.floick.boids):
                self.floick.add_boid(SCENE_WIDTH, SCENE_HEIGHT)
                self.scene.addItem(self.floick.boids[-1])

        self.floick.fly(SCENE_WIDTH, SCENE_HEIGHT, TS, BOID_SENSOR_DISTANCE, BOID_SPEED, BOID_SEPARATION_WEIGHT, BOID_ALIGNMENT_WEIGHT, BOID_COHESION_WEIGHT)

# Define a slider widget with labels to control any single global boid parameter
class boid_control(QWidget):
    def __init__(self, name, min, max, variable):
        super(boid_control, self).__init__()

        self.variable = variable
        self.name = name

        layout = QGridLayout()
        self.setLayout(layout)

        self.lbl_title = QLabel(f"{self.name} - {globals()[self.variable]}", alignment=(Qt.AlignHCenter | Qt.AlignBottom))
        lbl_min = QLabel(str(min))
        lbl_max = QLabel(str(max))
        self.slider = QSlider(orientation=Qt.Horizontal)
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        self.slider.setValue(globals()[self.variable])
        self.slider.valueChanged.connect(self.value_changed)

        layout.addWidget(self.lbl_title, 0, 0, 1, 3)
        layout.addWidget(lbl_min, 1, 0)
        layout.addWidget(self.slider, 1, 2)
        layout.addWidget(lbl_max, 1, 3)

    def value_changed(self):
        globals()[self.variable] = self.slider.value()
        self.lbl_title.setText(f"{self.name} - {self.slider.value()}")

# Define a set of boid_controls to control each of the global boid parameters
class control_panel(QGroupBox):
    def __init__(self):
        super(control_panel, self).__init__()

        self.setTitle(">boids.")
        self.setStyleSheet('QGroupBox {''font: 62px consolas; }')

        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.setLayout(layout)

        title = QLabel("Controls")
        title_font = QFont('Arial', 12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title, alignment=Qt.AlignLeft)

        num_boids = boid_control("Boids", 10, 200, "NUM_BOIDS")
        layout.addWidget(num_boids)
        
        sensor_distance = boid_control("Sensor Radius", 0, 100, "BOID_SENSOR_DISTANCE")
        layout.addWidget(sensor_distance)

        speed = boid_control("Speed", 0, 1000, "BOID_SPEED")
        layout.addWidget(speed)

        separation = boid_control("Separation", 0, 10, "BOID_SEPARATION_WEIGHT")
        layout.addWidget(separation)

        alignment = boid_control("Alignment", 0, 10, "BOID_ALIGNMENT_WEIGHT")
        layout.addWidget(alignment)

        cohesion = boid_control("Cohesion", 0, 10, "BOID_COHESION_WEIGHT")
        layout.addWidget(cohesion)

# Define the main window, in which boid_view and controls live side-by-side
class main_window(QWidget):
    def __init__(self):
        super(main_window, self).__init__()

        layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.setLayout(layout)

        self.boid_view = boid_view(num_boids=NUM_BOIDS)
        layout.addWidget(self.boid_view)

        controls = control_panel()
        layout.addWidget(controls, alignment=Qt.AlignTop)

    def update(self):
        self.boid_view.update()

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    win = main_window()
    win.setWindowTitle("Best Boids Ever")
    win.show()

    # Set up a timer to refresh the boid positions every TS
    tim = QTimer()
    tim.timeout.connect(win.update)
    tim.setInterval(TS)
    tim.start()

    # Start the app
    app.exec()