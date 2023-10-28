import sys
import asyncio
from tkinter import SCROLL, Grid
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap, QFont, QPalette

from computer_vision import ComputerVision
from overlay import Overlay
from device_control import DeviceControlWidget

class GUI(QMainWindow):
    def __init__(self) -> None:
        super(GUI, self).__init__()
        self.setWindowTitle("Underwatch")
        self.resize(800, 600)
        qApp.setStyleSheet("QWidget{font-size:18px;}")

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        self.layout = QGridLayout()
        centralWidget.setLayout(self.layout)

        self.computer_vision = ComputerVision()
        self.overlay = Overlay(self.computer_vision)
        self.overlay.show()
        self.setup_tabs();
        self.show()

        self.backgroud_thread = Worker(self.background_thread_loop)
        self.backgroud_thread.start()

    def setup_tabs(self):
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs, 0, 0)

        self.underwatch_tab = UnderwatchTab(self, self.computer_vision, self.overlay)
        self.tabs.addTab(self.underwatch_tab, "Settings")

        self.device_control = DeviceControlWidget(self, "Underwatch")
        self.tabs.addTab(self.device_control, "Device Control")

    async def background_thread_loop(self):
        while True:
            await self.computer_vision.update()
            await self.device_control.update(0)
            self.overlay.update()
            await asyncio.sleep(0.01)

class UnderwatchTab(QWidget):
    def __init__(self, parent, computer_vision, overlay) -> None:
        super(UnderwatchTab, self).__init__(parent)
        #self.setStyleSheet("border: 0px solid red;")
        
        outer_layout = QGridLayout()
        scroll_area = QScrollArea(self)
        scroll_widget = QWidget(self)
        inner_layout = QVBoxLayout(self)
        inner_layout.setAlignment(Qt.AlignTop)

        outer_layout.setContentsMargins(0,0,0,0)
        scroll_area.setBackgroundRole(QPalette.Base)
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_widget.setLayout(inner_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

        overlay_layout = QGridLayout()
        overlay_group = QGroupBox("Overlay")
        overlay_group.setLayout(overlay_layout)
        inner_layout.addWidget(overlay_group)
        row = 0

        # Overlay settings
        show_overlay_mode_label = QLabel("Show Overlay:", self)
        overlay_layout.addWidget(show_overlay_mode_label, row,0)
        show_overlay_mode = QComboBox(self)
        overlay_layout.addWidget(show_overlay_mode, row, 1)
        show_overlay_mode.addItem("Never")
        show_overlay_mode.addItem("Always")
        show_overlay_mode.addItem("When Overwatch Is Focused")
        show_overlay_mode.currentIndexChanged.connect(overlay.update_show_overlay_mode)
        show_overlay_mode.setCurrentIndex(2)
        row += 1

        show_detection_regions_label = QLabel("Debug Detection Regions:", self)
        overlay_layout.addWidget(show_detection_regions_label, row,0)
        show_detection_regions_mode = QComboBox(self)
        overlay_layout.addWidget(show_detection_regions_mode, row, 1)
        show_detection_regions_mode.addItem("Never")
        show_detection_regions_mode.addItem("Always")
        show_detection_regions_mode.addItem("When Detection Occurs")
        show_detection_regions_mode.currentIndexChanged.connect(overlay.update_show_regions_mode)
        show_detection_regions_mode.setCurrentIndex(2)
        row += 1

        # Detectables
        detectables_layout = QGridLayout()
        detectables_group = QGroupBox("Detectables")
        detectables_group.setLayout(detectables_layout)
        inner_layout.addWidget(detectables_group)
        for item in computer_vision.detectables.items():
            if (item[0] == "KillcamOrPOTG"):
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
            image.setMinimumWidth(60)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            set_image_to_label(detectable[1]["Template"], image)

            spin_box = QSpinBox(self)
            spin_box.setMinimumHeight(mininum_height)
            spin_box.setValue(detectable[1]["Points"])
            spin_box.setMaximum(999)
            spin_box.setMinimum(-999)
            spin_box.valueChanged.connect(self.update_points)

            combo_box = QComboBox(self)
            combo_box.setMinimumHeight(mininum_height)
            combo_box.setMinimumWidth(180)
            combo_box.addItem("Points Per Second")
            combo_box.addItem("Points (Instant)")
            combo_box.setCurrentIndex(detectable[1]["PointsType"])
            combo_box.currentIndexChanged.connect(self.update_points_type)

            layout.addWidget(image, 0, 0)
            layout.addWidget(label, 0, 1)
            layout.addWidget(spin_box, 0, 2)
            layout.addWidget(combo_box, 0, 3)

            layout.setColumnStretch(1, 1)

        def update_points(self, value):
            self.detectable[1]["Points"] = value;

        def update_points_type(self, value):
            self.detectable[1]["PointsType"] = value;

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