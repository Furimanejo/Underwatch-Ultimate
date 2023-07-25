from doctest import debug
from sys import flags
from turtle import width
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class Overlay(QWidget):
    def __init__(self, underwatch) -> None:
        super(Overlay, self).__init__(parent = None)
        self.underwatch = underwatch

        self.setWindowTitle("overlay")
        self.resize(self.underwatch.monitor["width"], self.underwatch.monitor["height"])

        flags = 0
        flags |= Qt.WindowType.WindowTransparentForInput 
        flags |= Qt.WindowStaysOnTopHint  
        flags |= Qt.FramelessWindowHint
        flags |= Qt.Tool # Hides the window from the taskbar
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Corners
        self.label = QLabel("", self)
        self.label.setStyleSheet("border: 1px solid magenta;")
        self.label.setGeometry(0,0, self.underwatch.monitor["width"], self.underwatch.monitor["height"])

        for region in underwatch.regions:
            top = underwatch.regions[region]["Rect"][0]
            bottom = underwatch.regions[region]["Rect"][1]
            left = underwatch.regions[region]["Rect"][2]
            right = underwatch.regions[region]["Rect"][3]
            label = QLabel(region, self)
            label.setGeometry(left, top, right-left, bottom-top)
            label.setStyleSheet("color: red; font: bold 14px; border: 1px solid red;")
            underwatch.regions[region]["Label"] = label
        
        def update(self):
            pass

    def toggle_on_off(self):
        if(self.isVisible()):
            self.hide()
        else:
            self.show()
