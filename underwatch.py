import sys
import asyncio
from tkinter import Grid
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap, QFont

from computer_vision import ComputerVision
from overlay import Overlay

class GUI(QMainWindow):
    def __init__(self) -> None:
        super(GUI, self).__init__()
        self.setWindowTitle("Underwatch")
        self.resize(600, 400)
        #self.move(1920, 0)
        qApp.setStyleSheet("QWidget{font-size:18px;}")


        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        self.layout = QGridLayout()
        centralWidget.setLayout(self.layout)

        self.computer_vision = ComputerVision()
        self.setup_tabs();
        self.show()

        self.backgroud_thread = Worker(self.background_thread_loop)
        self.backgroud_thread.start()

    def setup_tabs(self):
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs, 0, 0)

        self.underwatch_tab = UnderwatchTab(self, self.computer_vision)
        self.underwatch_tab.setStyleSheet("border: 1px solid red;")
        self.tabs.addTab(self.underwatch_tab, "Underwatch")

        self.overlayTab = OverlayTab(self, self.computer_vision)
        self.tabs.addTab(self.overlayTab, "Overlay")

    async def background_thread_loop(self):
        while True:
            await self.computer_vision.update()
            self.overlayTab.overlay.update()
            await asyncio.sleep(0.01)

class UnderwatchTab(QWidget):
    def __init__(self, parent, computer_vision) -> None:
        super(UnderwatchTab, self).__init__(parent)

        detectables_layout = QGridLayout()
        self.setLayout(detectables_layout)
        for item in computer_vision.detectables.items():
            if ("Killcam" in item[0]):
                continue
            detectable = UnderwatchTab.DetectableWidget(self, item)
            detectables_layout.addWidget(detectable)

    class DetectableWidget(QWidget):
        def __init__(self, parent, detectable) -> None:
            super(UnderwatchTab.DetectableWidget, self).__init__(parent)
            self.detectable = detectable

            layout = QGridLayout(self)
            layout.setContentsMargins(0,0,0,0)
            mininum_height = 40

            name  = detectable[0]
            label = QLabel(text = name, parent = self)
            label.setMinimumHeight(mininum_height)

            image = QLabel("", self)
            image.setMinimumHeight(mininum_height)
            image.setMinimumWidth(80)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            set_image_to_label(detectable[1]["Template"], image)

            spin_box = QSpinBox(self)
            spin_box.setMinimumHeight(mininum_height)
            spin_box.setValue(detectable[1]["Points"])
            spin_box.setMaximum(999)
            spin_box.setMinimum(-999)
            #slider = QSlider(Qt.Orientation.Horizontal, self)
            
            combo_box = QComboBox(self)
            combo_box.setMinimumHeight(mininum_height)
            combo_box.setMinimumWidth(180)
            combo_box.addItem("Points per Second")
            combo_box.addItem("Points (instant)")
            combo_box.setCurrentIndex(detectable[1]["PointsType"])

            layout.addWidget(image, 0, 0)
            layout.addWidget(label, 0, 1)
            layout.addWidget(spin_box, 0, 2)
            layout.addWidget(combo_box, 0, 3)

            layout.setColumnStretch(1, 1)


class OverlayTab(QWidget):
    def __init__(self, parent, underwatch) -> None:
        super(OverlayTab, self).__init__(parent)

        self.overlay = Overlay(underwatch)
        self.overlay.show()

        layout = QGridLayout()
        self.setLayout(layout)

        self.show_overlay_mode_label = QLabel("Show Overlay: ")
        layout.addWidget(self.show_overlay_mode_label,0,0)
        self.show_overlay_mode = QComboBox()
        layout.addWidget(self.show_overlay_mode,0,1)
        self.show_overlay_mode.addItem("Never")
        self.show_overlay_mode.addItem("Always")
        self.show_overlay_mode.addItem("When Overwatch Is Focused")
        self.show_overlay_mode.currentIndexChanged.connect(self.overlay.update_show_overlay_mode)
        self.show_overlay_mode.setCurrentIndex(2)

        self.show_detection_regions_label = QLabel("Show Detection Regions: ")
        layout.addWidget(self.show_detection_regions_label,1,0)
        self.show_detection_regions_mode = QComboBox()
        layout.addWidget(self.show_detection_regions_mode,1,1)
        self.show_detection_regions_mode.addItem("Never")
        self.show_detection_regions_mode.addItem("Always")
        self.show_detection_regions_mode.addItem("When Detection Occurs")
        self.show_detection_regions_mode.currentIndexChanged.connect(self.overlay.update_show_regions_mode)
        self.show_detection_regions_mode.setCurrentIndex(2)

class Worker(QThread):
    def __init__(self, funtion):
        super(QThread, self).__init__()
        self.function = funtion

    def run(self):
        asyncio.run(self.function())

def set_image_to_label(image, label):
    #h, w, ch = 0
    if(len(image.shape) == 2):
        h, w = image.shape
        ch = 1
    else:
        h, w, ch = image.shape
    bytes_per_line = ch * w
    convert_to_Qt_format = QImage(image.data, w, h, bytes_per_line, QImage.Format_BGR888)
    width = label.width()
    heigth = label.height()
    qImage = convert_to_Qt_format.scaled(width, heigth, Qt.KeepAspectRatio)
    label.setPixmap(QPixmap(qImage))

app = QApplication(sys.argv)
app_window = GUI()
sys.exit(app.exec())