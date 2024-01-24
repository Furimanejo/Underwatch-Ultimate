import sys
import asyncio
from time import sleep

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from computer_vision import ComputerVision
from overlay import Overlay
from device_control import DeviceControlWidget
from config_handler import config, save_to_file, load_from_file, aspect_ratios

class GUI(QMainWindow):
    update_signal = pyqtSignal()

    def __init__(self) -> None:
        super(GUI, self).__init__()
        load_from_file()
        save_to_file()

        self.setWindowTitle("Underwatch Ultimate")
        self.resize(800, 600)
        qApp.setStyleSheet("QWidget{font-size:18px;}")

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        self.layout = QGridLayout()
        centralWidget.setLayout(self.layout)

        self.computer_vision = ComputerVision()
        self.overlay = Overlay(self.computer_vision)
        self.setup_tabs();
        self.show()

        self.update_signal.connect(self.update_graphics)

        self.backgroud_thread = Worker(self.background_thread_loop)
        self.backgroud_thread.start()

    def setup_tabs(self):
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs, 0, 0)

        self.underwatch_tab = SettingsTab(self, self.computer_vision, self.overlay)
        self.tabs.addTab(self.underwatch_tab, "Settings")

        self.device_control = DeviceControlWidget(self, "Underwatch Ultimate")
        self.tabs.addTab(self.device_control, "Device Control")

        self.about_tab = AboutTab(self)
        self.tabs.addTab(self.about_tab, "About")

    def closeEvent(self, event):
        self.backgroud_thread.terminate()
        event.accept()

    async def background_thread_loop(self):
        while True:
            cv_updated = self.computer_vision.update()
            if cv_updated:
                await self.device_control.update(self.computer_vision.get_current_score())
                self.update_signal.emit()
            await asyncio.sleep(1/1000)

    def update_graphics(self):
        if self.computer_vision.resolution_changed:
            self.overlay.close()
            self.overlay = Overlay(self.computer_vision)
            self.computer_vision.resolution_changed = False

        self.underwatch_tab.update()
        self.overlay.update()

class SettingsTab(QWidget):
    def __init__(self, parent, computer_vision, overlay) -> None:
        super(SettingsTab, self).__init__(parent)
        self.computer_vision = computer_vision
        inner_layout = QGridLayout(self)
        inner_layout.setAlignment(Qt.AlignTop)

        scroll_widget = QWidget(self)
        scroll_widget.setLayout(inner_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setBackgroundRole(QPalette.Base)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        outer_layout = QGridLayout()
        outer_layout.setContentsMargins(0,0,0,0)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)

        row = 0
        
        aspect_ratio_label = QLabel("Aspect Ratio:", self)
        inner_layout.addWidget(aspect_ratio_label, row, 0)
        aspect_ratio_combo_box = QComboBox(self)
        inner_layout.addWidget(aspect_ratio_combo_box, row, 1)
        for aspect_ratio in aspect_ratios:
            aspect_ratio_combo_box.addItem(aspect_ratios[aspect_ratio]["id"])
        aspect_ratio_combo_box.currentIndexChanged.connect(lambda value: set_config("aspect_ratio_index", value))
        aspect_ratio_combo_box.setCurrentIndex(config["aspect_ratio_index"])
        row += 1

        show_overlay_mode_label = QLabel("Show Overlay:", self)
        inner_layout.addWidget(show_overlay_mode_label, row,0)
        show_overlay_mode = QComboBox(self)
        inner_layout.addWidget(show_overlay_mode, row, 1)
        show_overlay_mode.addItem("Never")
        show_overlay_mode.addItem("Always")
        show_overlay_mode.addItem("When Overwatch Is Focused")
        show_overlay_mode.currentIndexChanged.connect(lambda value: set_config("show_overlay_mode", value))
        show_overlay_mode.setCurrentIndex(config["show_overlay_mode"])
        row += 1

        show_detection_regions_label = QLabel("Debug Detection Regions:", self)
        inner_layout.addWidget(show_detection_regions_label, row,0)
        show_detection_regions_mode = QComboBox(self)
        inner_layout.addWidget(show_detection_regions_mode, row, 1)
        show_detection_regions_mode.addItem("Never")
        show_detection_regions_mode.addItem("Always")
        show_detection_regions_mode.addItem("When Detection Occurs")
        show_detection_regions_mode.currentIndexChanged.connect(lambda value: set_config("show_regions_mode", value))
        show_detection_regions_mode.setCurrentIndex(config["show_regions_mode"])
        row += 1

        killcam_label = QLabel("Skip Killcam and POTG", self)
        killcam_box = QCheckBox(self)
        killcam_box.setChecked(config["ignore_spectate"])
        killcam_box.stateChanged.connect(lambda value = False : set_config("ignore_spectate", value != 0))
        inner_layout.addWidget(killcam_label, row, 0)
        inner_layout.addWidget(killcam_box, row, 1)
        row += 1

        ignore_redundant_label = QLabel("Ignore Redundant Assits", self)
        ignore_redundant_box = QCheckBox(self)
        ignore_redundant_box.setChecked(config["ignore_redundant_assists"])
        ignore_redundant_box.stateChanged.connect(lambda value : set_config("ignore_redundant_assists", value != 0))
        inner_layout.addWidget(ignore_redundant_label, row, 0)
        inner_layout.addWidget(ignore_redundant_box, row, 1)
        row += 1

        score_label = QLabel("Current Score", self)
        self.score_input_box = QSpinBox(self)
        self.score_input_box.setMaximum(999)
        self.score_input_box.valueChanged.connect(computer_vision.set_score)
        self.score_input_box.setValue(computer_vision.score_over_time)
        inner_layout.addWidget(score_label, row, 0)
        inner_layout.addWidget(self.score_input_box, row, 1)
        row += 1
        
        decay_label = QLabel("Score Decay Per Minute", self)
        decay_input_box = QSpinBox(self)
        decay_input_box.setMaximum(999)
        decay_input_box.setValue(config["decay"])
        decay_input_box.valueChanged.connect(lambda value : set_config("decay", value))
        inner_layout.addWidget(decay_label, row, 0)
        inner_layout.addWidget(decay_input_box, row, 1)
        row += 1

        for i in range(inner_layout.rowCount()):
            inner_layout.setRowMinimumHeight(i, 30)

        # Detectables
        detectables_layout = QGridLayout()
        detectables_group = QGroupBox("Detectables")
        detectables_group.setLayout(detectables_layout)
        inner_layout.addWidget(detectables_group, row, 0, 1, 2)
        for item in config["detectables"].items():
            if item[0] == "KillcamOrPOTG":
                continue
            detectable = SettingsTab.DetectableWidget(self, item)
            detectables_layout.addWidget(detectable)

    class DetectableWidget(QWidget):
        def __init__(self, parent, detectable) -> None:
            super(SettingsTab.DetectableWidget, self).__init__(parent)
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
            spin_box.setMaximum(999)
            spin_box.setMinimum(-999)
            spin_box.setValue(detectable[1]["Points"])
            spin_box.valueChanged.connect(self.update_points)

            combo_box = QComboBox(self)
            combo_box.setMinimumHeight(mininum_height)
            combo_box.setMinimumWidth(200)
            combo_box.addItem("Momentary Points")
            combo_box.addItem("Points Per Second")
            if detectable[1]["Duration"] != 1:
                combo_box.addItem("Points Over Duration")
            combo_box.setCurrentIndex(detectable[1]["Type"])
            combo_box.currentIndexChanged.connect(self.update_points_type)

            layout.addWidget(image, 0, 0)
            layout.addWidget(label, 0, 1)
            layout.addWidget(spin_box, 0, 2)
            layout.addWidget(combo_box, 0, 3)

            layout.setColumnStretch(1, 1)

        def update_points(self, value):
            self.detectable[1]["Points"] = value;
            save_to_file()

        def update_points_type(self, value):
            self.detectable[1]["Type"] = value;
            save_to_file()

    def update(self):
        if self.score_input_box.hasFocus() == False:
            self.score_input_box.blockSignals(True)
            self.score_input_box.setValue(int(self.computer_vision.score_over_time))
            self.score_input_box.blockSignals(False)

class AboutTab(QWidget):
    def __init__(self, parent) -> None:
        super(AboutTab, self).__init__(parent)
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(5, 10, 5, 5)
        
        text = QTextBrowser(self)
        text.setStyleSheet("border: 0px solid black;")
        text.setOpenExternalLinks(True)
        text.setText(
            """
            <p>Made by Furimanejo.
            <p>For more information and instructions check this project's page hosted at <a href="https://github.com/Furimanejo/Underwatch-Ultimate">Github</a>.
            <p>If you need further support you can reach out to me at my <a href="https://discord.com/invite/wz2qvkuEyJ">Discord Server</a>.
            <p>Want to sponsor this project? I accept donations at <a href="https://donate.stripe.com/7sI3eZcExdGrc5WeUU">Stripe</a>.
            """
        )
        layout.addWidget(text, 0, 0)

class Worker(QThread):
    def __init__(self, funtion):
        super(QThread, self).__init__()
        self.function = funtion

    def run(self):
        asyncio.run(self.function())

def set_config(key, value):
    config[key] = value
    save_to_file()

def set_image_to_label(image, label):
    #h, w, ch = 0
    if len(image.shape) == 2:
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

def exception_hook(type, value, tb):
    print("Exception hooked:")
    QCoreApplication.quit()
    import traceback
    txt = ''.join(traceback.format_exception(type, value, tb))
    print(txt)
    input("Press any key to exit...")

sys.excepthook = exception_hook
app = QApplication(sys.argv)
app_window = GUI()
app.exec()

try:
    input("Press any key to exit...")
except:
    pass