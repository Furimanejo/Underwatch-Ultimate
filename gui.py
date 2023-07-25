import sys, asyncio
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap

from overlay import *
from underwatch import Underwatch

class FrontEnd(QMainWindow):
    def __init__(self) -> None:
        super(FrontEnd, self).__init__()
        self.underwatch = Underwatch()

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

        self.debug_tab = DebugTab(self, self.underwatch)
        self.tabs.addTab(self.debug_tab, "Debug")

        self.overlayTab = OverlayTab(self, self.underwatch)
        self.tabs.addTab(self.overlayTab, "Overlay")

        self.detectablesTab = DetectablesTab(self, self.underwatch)
        self.detectablesTab.setStyleSheet("border: 1px solid red;")
        self.tabs.addTab(self.detectablesTab, "Detectables")
    
    async def background_thread_loop(self):
        while True:
            await self.underwatch.update()
            await self.debug_tab.update()
            await asyncio.sleep(0.01)

class DebugTab(QWidget):
    def __init__(self, parent, underwatch) -> None:
        super(DebugTab, self).__init__(parent)
        self.underwatch = underwatch

        layout = QGridLayout()
        self.setLayout(layout)

        self.image_label = QLabel("", self)
        layout.addWidget(self.image_label, 0 , 0, 10, 10)

        self.saturation = QSpinBox(self)
        self.saturation.setMaximum(255)
        self.saturation.setValue(self.underwatch.sat)
        self.saturation.valueChanged.connect(self.update_values)
        layout.addWidget(self.saturation, 0 , 0)
        self.value = QSpinBox(self)
        self.value.setMaximum(255)
        self.value.setValue(self.underwatch.value)
        self.value.valueChanged.connect(self.update_values)
        layout.addWidget(self.value, 1 , 0)

    def update_values(self):
        self.underwatch.sat = self.saturation.value()
        self.underwatch.value = self.value.value()

    async def update(self):
        if(self.underwatch.debug_frame is not None):
            set_image_to_label(self.underwatch.debug_frame, self.image_label)

class OverlayTab(QWidget):
    def __init__(self, parent, underwatch) -> None:
        super(OverlayTab, self).__init__(parent)
        self.overlay = Overlay(underwatch)
        self.overlay.show()

        self.toggle_overlay_btn = QPushButton("Toggle Overlay", self)
        self.toggle_overlay_btn.clicked.connect(self.overlay.toggle_on_off)

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
app_window = FrontEnd()
sys.exit(app.exec())