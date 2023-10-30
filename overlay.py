from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from win32gui import GetWindowText, GetForegroundWindow

class Overlay(QWidget):
    def __init__(self, underwatch) -> None:
        super(Overlay, self).__init__(parent = None)
        self.computer_vision = underwatch
        self.show_overlay_mode = 2
        self.show_regions_mode = 2

        self.setWindowTitle("overlay")
        self.resize(self.computer_vision.monitor["width"], self.computer_vision.monitor["height"])

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
        self.label.setGeometry(0,0, self.computer_vision.monitor["width"], self.computer_vision.monitor["height"])

        self.points_label = QLabel("UWU Points:", self)
        self.points_label.setStyleSheet("color: magenta; font: bold 18px;")
        self.points_label.setGeometry(175 , self.computer_vision.monitor["height"] - 80,  200, 20)

        self.detection_delay_label = QLabel("Detection Delay:", self)
        self.detection_delay_label.setStyleSheet("color: magenta; font: bold 12px;")
        self.detection_delay_label.setGeometry(175 , self.computer_vision.monitor["height"] - 60,  200, 20)

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
                label.setGeometry(left, top-100, 200, 100)
                label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

            self.regions[region] = {"Rect": rect, "Label": label}

        self.update_show_overlay_mode(self.show_overlay_mode)
        self.update_show_regions_mode(self.show_regions_mode)
        
    def update(self):
        if (self.show_overlay_mode == 2):
            self.update_show_overlay_mode(self.show_overlay_mode)

        if (self.isVisible == False):
            return

        if (self.show_regions_mode == 2):
            self.update_show_regions_mode(self.show_regions_mode)

        self.points_label.setText("Score: {0:.0f}".format(self.computer_vision.get_current_score()))
        self.detection_delay_label.setText("Detection Delay: {0:4.0f}ms".format(1000 * self.computer_vision.detection_ping))

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
                matches = self.computer_vision.regions[region]["Matches"]
                if (matches == []):
                    self.regions[region]["Rect"].hide()
                    self.regions[region]["Label"].hide()
                else:
                    text = ""
                    count = 0
                    for m in matches:
                        count += 1
                        if (count > 1):
                            text += "\n"
                        text += m

                    self.regions[region]["Label"].setText(text)
                    self.regions[region]["Label"].show()
                    self.regions[region]["Rect"].show()