from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from win32gui import GetWindowText, GetForegroundWindow

class Overlay(QWidget):
    def __init__(self, underwatch) -> None:
        super(Overlay, self).__init__(parent = None)
        self.underwatch = underwatch
        self.show_overlay_mode = 0
        self.show_regions_mode = 0

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

        self.points_label = QLabel("UWU Points:", self)
        self.points_label.setStyleSheet("color: magenta; font: bold 18px;")
        self.points_label.setGeometry(175 , self.underwatch.monitor["height"] - 80,  200, 20)

        self.detection_delay_label = QLabel("Detection Delay:", self)
        self.detection_delay_label.setStyleSheet("color: magenta; font: bold 12px;")
        self.detection_delay_label.setGeometry(175 , self.underwatch.monitor["height"] - 60,  200, 20)

        self.regions = {}

        for region in underwatch.regions:
            rect = QLabel("", self)
            top = underwatch.regions[region]["Rect"][0]
            bottom = underwatch.regions[region]["Rect"][1]
            left = underwatch.regions[region]["Rect"][2]
            right = underwatch.regions[region]["Rect"][3]
            rect.setGeometry(left, top, right-left, bottom-top)
            rect.setStyleSheet("color: red; border: 1px solid red;")

            label = QLabel(region, self)
            label.setStyleSheet("color: red; font: bold 14px;")
            if ("Popup" in region):
                label.setGeometry(left - 200, top, 195, bottom-top)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                label.setGeometry(left, top-20, 200, 20)

            self.regions[region] = {"Rect": rect, "Label": label}
        
    def update(self):
        if (self.show_overlay_mode == 2):
            self.update_show_overlay_mode(self.show_overlay_mode)

        if (self.isVisible == False):
            return

        if (self.show_regions_mode == 2):
            self.update_show_regions_mode(self.show_regions_mode)

        self.points_label.setText("UWU Points: {0:.0f}".format(self.underwatch.score))
        self.detection_delay_label.setText("Detection Delay: {0:4.0f}ms".format(1000 * self.underwatch.detection_delay))

    def update_show_overlay_mode(self, new_mode_index):
        self.show_overlay_mode = new_mode_index

        if (self.show_overlay_mode == 0):
            self.hide()
        
        elif (self.show_overlay_mode == 1):
            self.show()

        elif (self.show_overlay_mode == 2):
            activeWindow = GetWindowText(GetForegroundWindow())
            if (activeWindow == "Overwatch"):
                self.show()
            else:
                self.hide()

    def update_show_regions_mode(self, new_mode_index):
        self.show_regions_mode = new_mode_index
        if (self.show_regions_mode == 0):
            for region in self.regions:
                self.regions[region]["Rect"].hide()
                self.regions[region]["Label"].hide()

        elif (self.show_regions_mode == 1):
            for region in self.regions:
                self.regions[region]["Rect"].show()
                self.regions[region]["Label"].setText(region)
                self.regions[region]["Label"].show()

        elif (self.show_regions_mode == 2):
            for region in self.regions:
                match = self.underwatch.regions[region]["Match"]
                if (match is None):
                    self.regions[region]["Rect"].hide()
                    self.regions[region]["Label"].hide()
                else:
                    self.regions[region]["Rect"].show()
                    self.regions[region]["Label"].setText(match)
                    self.regions[region]["Label"].show()