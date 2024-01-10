from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from win32gui import GetWindowText, GetForegroundWindow

from config_handler import config

class Overlay(QWidget):
    def __init__(self, computer_vision) -> None:
        super(Overlay, self).__init__(parent = None)
        self.cv = computer_vision
        
        self.setWindowTitle("overlay")
        flags = 0
        flags |= Qt.WindowType.WindowTransparentForInput 
        flags |= Qt.WindowStaysOnTopHint  
        flags |= Qt.FramelessWindowHint
        flags |= Qt.Tool # Hides the window from the taskbar
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.set_geometry()
        self.update()
    
    def set_geometry(self):
        self.setGeometry(
            self.cv.detection_rect["left"],
            self.cv.detection_rect["top"],
            self.cv.detection_rect["width"],
            self.cv.detection_rect["height"]
        )

        self.corners = QLabel("", self)
        self.corners.setStyleSheet("border: 1px solid magenta;")
        self.corners.setGeometry(
            0,
            0,
            self.cv.detection_rect["width"],
            self.cv.detection_rect["height"]
        )

        self.points_label = QLabel("Score:", self)
        self.points_label.setStyleSheet("color: rgb(200, 0, 200); font: bold 18px;")
        rect = self.cv.scale_rect([1000, 1020, 170, 420])
        self.points_label.setGeometry(
            rect[2],
            rect[0],
            rect[3]-rect[2],
            rect[1]-rect[0]
        )

        self.detection_delay_label = QLabel("Detection Delay:", self)
        self.detection_delay_label.setStyleSheet("color: rgb(200, 0, 200); font: bold 12px;")
        rect = self.cv.scale_rect([1020, 1040, 170, 420])
        self.detection_delay_label.setGeometry(
            rect[2],
            rect[0],
            rect[3]-rect[2],
            rect[1]-rect[0]
        )

        self.regions = {}
        for region in config["regions"]:
            rect = QLabel("", self)
            top = config["regions"][region]["ScaledRect"][0]
            bottom = config["regions"][region]["ScaledRect"][1]
            left = config["regions"][region]["ScaledRect"][2]
            right = config["regions"][region]["ScaledRect"][3]
            rect.setGeometry(left, top, right-left, bottom-top)
            rect.setStyleSheet("color: red; border: 1px solid red;")

            label = QLabel(region, self)
            label.setStyleSheet("color: red; font: bold 14px;")
            if ("Popup" in region):
                label.setGeometry(left - 200, top, 195, bottom - top)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                label.setGeometry(left, top - 100, 200, 100)
                label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

            self.regions[region] = {"Rect": rect, "Label": label}

    def update(self):
        show = False
        if (config["show_overlay_mode"] == 0):
            show = False

        elif (config["show_overlay_mode"] == 1):
            show = True

        elif (config["show_overlay_mode"] == 2):
            activeWindow = GetWindowText(GetForegroundWindow())
            if (activeWindow == "Overwatch"):
                show = True
            else:
                show = False

        self.set_active(show)
        if (show):
            self.update_regions()

        self.points_label.setText("Score: {0:.0f}".format(self.cv.get_current_score()))
        self.detection_delay_label.setText("Detection Delay: {0:4.0f} MS".format(1000 * self.cv.detection_ping))

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
        if (config["show_regions_mode"] == 0 or config["show_overlay_mode"] == 0):
            for region in self.regions:
                self.regions[region]["Rect"].hide()
                self.regions[region]["Label"].hide()
                self.regions[region]["Label"].setText("")

        elif (config["show_regions_mode"] == 1):
            for region in self.regions:
                self.regions[region]["Rect"].show()
                self.regions[region]["Label"].show()
                self.regions[region]["Label"].setText(region)

        elif (config["show_regions_mode"] == 2):
            for region in self.regions:
                matches = config["regions"][region]["Matches"]
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