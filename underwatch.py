import sys
import asyncio
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap

from computer_vision import ComputerVision
from overlay import Overlay

class GUI(QMainWindow):
    def __init__(self) -> None:
        super(GUI, self).__init__()
        self.computer_vision = ComputerVision()

        self.setWindowTitle("Underwatch")
        self.move(1920, 0)
        self.resize(800, 600)
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        self.layout = QGridLayout()
        centralWidget.setLayout(self.layout)

        self.setup_tabs();
        self.show()

        self.backgroud_thread = Worker(self.background_thread_loop)
        self.backgroud_thread.start()

    def setup_tabs(self):
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs, 0, 0)

        self.overlayTab = OverlayTab(self, self.computer_vision)
        self.tabs.addTab(self.overlayTab, "Overlay")

        self.detectablesTab = DetectablesTab(self, self.computer_vision)
        self.detectablesTab.setStyleSheet("border: 1px solid red;")
        self.tabs.addTab(self.detectablesTab, "Detectables")
    
    async def background_thread_loop(self):
        while True:
            await self.computer_vision.update()
            self.overlayTab.overlay.update()
            await asyncio.sleep(0.01)

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

class DetectablesTab(QWidget):
    def __init__(self, parent, underwatch) -> None:
        super(DetectablesTab, self).__init__(parent)

        layout = QGridLayout()
        self.setLayout(layout)
        row = 0
        for item in underwatch.detectables:

            label = QLabel(text = item, parent = self)
            label.setStyleSheet("font: bold 14px;")
            layout.addWidget(label, row, 0)
            
            spinbox = QSpinBox(self)
            layout.addWidget(spinbox, row+1, 0)

            slider = QSlider(Qt.Orientation.Horizontal, self)
            layout.addWidget(slider, row+1, 1, 1, 9)

            image = QLabel("", self)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            set_image_to_label(underwatch.detectables[item]["Template"], image)
            layout.addWidget(image, row, 10, 2, 1)

            row += 2

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