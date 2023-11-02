from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from win32gui import GetWindowText, GetForegroundWindow

class Overlay(QWidget):
    def __init__(self, computer_vision) -> None:
        super(Overlay, self).__init__(parent = None)
        self.computer_vision = computer_vision
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

        self.corners = QLabel("", self)
        self.corners.setStyleSheet("border: 1px solid magenta;")
        self.corners.setGeometry(0,0, self.computer_vision.monitor["width"], self.computer_vision.monitor["height"])

        self.points_label = QLabel("Score:", self)
        self.points_label.setStyleSheet("color: rgb(200, 0, 200); font: bold 18px;")
        rect = [1000, 1020, 170, 420]
        computer_vision.scale_to_monitor(rect)
        self.points_label.setGeometry(rect[2], rect[0], rect[3]-rect[2], rect[1]-rect[0])

        self.detection_delay_label = QLabel("Detection Delay:", self)
        self.detection_delay_label.setStyleSheet("color: rgb(200, 0, 200); font: bold 12px;")
        rect = [1020, 1040, 170, 420]
        computer_vision.scale_to_monitor(rect)
        self.detection_delay_label.setGeometry(rect[2], rect[0], rect[3]-rect[2], rect[1]-rect[0])

        self.regions = {}
        for region in computer_vision.regions:
            rect = QLabel("", self)
            top = computer_vision.regions[region]["Rect"][0]
            bottom = computer_vision.regions[region]["Rect"][1]
            left = computer_vision.regions[region]["Rect"][2]
            right = computer_vision.regions[region]["Rect"][3]
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

        self.update()
        
    def update(self):
        show = False
        if (self.show_overlay_mode == 0):
            show = False

        elif (self.show_overlay_mode == 1):
            show = True

        elif (self.show_regions_mode == 2):
            activeWindow = GetWindowText(GetForegroundWindow())
            if (activeWindow == "Overwatch"):
                show = True
            else:
                show = False

        self.set_active(show)
        if (show):
            self.update_regions()

        self.points_label.setText("Score: {0:.0f}".format(self.computer_vision.get_current_score()))
        self.detection_delay_label.setText("Detection Delay: {0:4.0f} MS".format(1000 * self.computer_vision.detection_ping))

    def set_active(self, value):
        if (value is False):
            self.corners.hide()
            self.points_label.hide()
            self.detection_delay_label.hide()
            for region in self.regions:
                self.regions[region]["Rect"].hide()
                self.regions[region]["Label"].setText("")
        else:
            self.corners.show()
            self.points_label.show()
            self.detection_delay_label.show()

    def update_regions(self):
        if (self.show_regions_mode == 0 or self.show_overlay_mode == 0):
            for region in self.regions:
                self.regions[region]["Rect"].hide()
                self.regions[region]["Label"].hide()
                self.regions[region]["Label"].setText("")

        elif (self.show_regions_mode == 1):
            for region in self.regions:
                self.regions[region]["Rect"].show()
                self.regions[region]["Label"].show()
                self.regions[region]["Label"].setText(region)

        elif (self.show_regions_mode == 2):
            for region in self.regions:
                matches = self.computer_vision.regions[region]["Matches"]
                if (matches == []):
                    self.regions[region]["Rect"].hide()
                    self.regions[region]["Label"].hide()
                    self.regions[region]["Label"].setText("")
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

    def update_show_overlay_mode(self, new_mode_index):
        self.show_overlay_mode = new_mode_index

    def update_show_regions_mode(self, new_mode_index):
        self.show_regions_mode = new_mode_index
