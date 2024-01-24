from PyQt5.QtWidgets import *
from PyQt5.QtCore import * 
from PyQt5.QtGui import QPalette
import time

import buttplug 

class DeviceControlWidget(QWidget):
    # custom signals have to be defined outside __init__ for some reason
    update_devices_signal = pyqtSignal()

    def __init__(self, parent, client_name):
        super(QWidget, self).__init__(parent)
        self.client_name = client_name
        self.devices = {}
        self.setup_new_intiface_client()
        self.connect_requested = False
        self.last_send = 0
        self.min_update_period = 0.1

        layout = QGridLayout(self)

        intiface_group_box = QGroupBox("Intiface Connection")
        intiface_group_box.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        intiface_layout = QGridLayout()
        intiface_group_box.setLayout(intiface_layout)
        layout.addWidget(intiface_group_box)
        address_label = QLabel("Address:", self)
        intiface_layout.addWidget(address_label, 0, 0)
        self.intiface_address = QLineEdit(f"ws://127.0.0.1:12345", self)
        intiface_layout.addWidget(self.intiface_address, 0, 1)
        self.connect_btn = QPushButton("Connect To Intiface", self)
        self.connect_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.connect_btn.clicked.connect(self.set_connect_request)
        intiface_layout.addWidget(self.connect_btn, 0, 2)

        devices_group_box = QGroupBox("Devices")
        scroll_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.devices_layout = QVBoxLayout()
        self.devices_layout.setAlignment(Qt.AlignTop)
        self.update_devices_signal.connect(self.update_device_list)

        scroll_layout.setContentsMargins(0,0,0,0)
        scroll_area.setBackgroundRole(QPalette.Base)
        scroll_area.setFrameShape(QFrame.NoFrame)

        devices_group_box.setLayout(scroll_layout)
        scroll_layout.addWidget(scroll_area)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_widget.setLayout(self.devices_layout)
        layout.addWidget(devices_group_box)

    def setup_new_intiface_client(self):
        self.client = buttplug.Client(self.client_name, buttplug.ProtocolSpec.v3)
        for w in self.devices.values():
            self.devices_layout.removeWidget(w)
        self.devices = {}

    def set_connect_request(self):
        self.connect_requested = True
    
    async def update(self, send_value):
        if self.connect_requested:
            self.connect_requested = False
            try:
                self.connect_btn.setText("disconnecting...")
                if self.is_connected():
                    await self.client.disconnect()
                    self.setup_new_intiface_client()

                self.connect_btn.setText("Connecting...")
                connector = buttplug.WebsocketConnector(self.intiface_address.text(), logger=self.client.logger)
                await self.client.connect(connector)
                self.connect_btn.setText("Connected")
                await self.client.start_scanning()
            except Exception as e:
                self.connect_btn.setText("Connection Failed")
                print(e)
        
        if self.is_connected() == False:
            return

        self.update_devices_signal.emit()

        t = time.time()
        if t - self.last_send < self.min_update_period:
            return
        self.last_send = t
        
        for device in self.devices:
            if device in self.client.devices:
                await self.devices[device].send(send_value)
    
    def is_connected(self):
        return self.client._connector != None and self.client._connector.connected

    def update_device_list(self):
        if self.is_connected():
            for device in self.client.devices:
                if device not in self.devices:
                    print("New device found: " + self.client.devices[device].name)
                    self.devices[device] = self.DeviceWidget(self, self.client.devices[device])
                    self.devices_layout.addWidget(self.devices[device])

        for device in self.devices:
            if device in self.client.devices:
                self.devices[device].set_connected(True)
            else:
                self.devices[device].set_connected(False)

    class DeviceWidget(QGroupBox):
        def __init__(self, parent, device):
            super(DeviceControlWidget.DeviceWidget, self).__init__(device.name, parent = None)
            self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.device = device
            self.connected = True
            layout = QGridLayout()
            self.setLayout(layout)

            self.actuators = []
            self.actuators_layout = QVBoxLayout()
            layout.addLayout(self.actuators_layout, 0, 0)

            for actuator in self.device.actuators:
                widget = self.ActuatorWidget(self, actuator, "Scalar")
                self.actuators.append(widget)
                self.actuators_layout.addWidget(widget)

            for actuator in self.device.rotatory_actuators:
                widget = self.ActuatorWidget(self, actuator, "Rotatory")
                self.actuators.append(widget)
                self.actuators_layout.addWidget(widget)

            for actuator in self.device.linear_actuators:
                widget = self.ActuatorWidget(self, actuator, "Linear")
                self.actuators.append(widget)
                self.actuators_layout.addWidget(widget)
        
        def set_connected(self, value):
            if value == self.connected:
                return
            if value == False:
                print("Device disconnected: " + self.device.name)
            else:
                print("Device reconnected: " + self.device.name)
            self.connected = value

        async def send(self, value):
            if self.connected:
                for actuator in self.actuators:
                    await actuator.send(value)

        class ActuatorWidget(QGroupBox):
            def __init__(self, parent, actuator, actuator_type = "Scalar"):
                name = str(actuator.index) + ": "
                if hasattr(actuator, "type"):
                    name += actuator.type
                else:
                    name += actuator_type
                super(DeviceControlWidget.DeviceWidget.ActuatorWidget, self).__init__(name, parent = None)
                self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
                self.actuator = actuator
                self.actuator_type = actuator_type
                self.linear_value = 0
                self.linear_direction = 1
                self.last_sent_time = 0

                layout = QGridLayout()
                self.setLayout(layout)

                intensity_name = "Intensity (%)"
                max_intensity_value = 100
                if actuator_type == "Linear":
                    intensity_name = "BPM"
                    max_intensity_value = 999

                min_intensity_label = QLabel("Min " + intensity_name + ":")
                self.min_intensity = QSpinBox()
                self.min_intensity.setRange(0, max_intensity_value)
                self.min_intensity.setValue(0)
                self.min_intensity.setSingleStep(10)
                self.min_intensity.wheelEvent = lambda event: None

                max_intensity_label = QLabel("Max " + intensity_name + ":")
                self.max_intensity = QSpinBox()
                self.max_intensity.setRange(0, max_intensity_value)
                self.max_intensity.setValue(100)
                self.max_intensity.setSingleStep(10)
                self.max_intensity.wheelEvent = lambda event: None

                min_score_label = QLabel("At Score:")
                self.min_score = QSpinBox()
                self.min_score.setRange(-32768, 32767)
                self.min_score.setValue(0)
                self.min_score.setSingleStep(10)
                self.min_score.wheelEvent = lambda event: None

                max_score_label = QLabel("At Score:")
                self.max_score = QSpinBox()
                self.max_score.setRange(-32768, 32767)
                self.max_score.setValue(100)
                self.max_score.setSingleStep(10)
                self.max_score.wheelEvent = lambda event: None

                layout.addWidget(max_intensity_label, 0, 0)
                layout.addWidget(self.max_intensity, 0, 1)
                layout.addWidget(max_score_label, 0, 2)
                layout.addWidget(self.max_score, 0, 3)

                layout.addWidget(min_intensity_label, 1, 0)
                layout.addWidget(self.min_intensity, 1, 1)
                layout.addWidget(min_score_label, 1, 2)
                layout.addWidget(self.min_score, 1, 3)

            async def send(self, value):
                try:
                    min_value = self.min_score.value()
                    max_value = self.max_score.value()
                    min_intensity = self.min_intensity.value()
                    max_intensity = self.max_intensity.value()

                    if (min_value == max_value):
                        max_value = min_value + 1

                    inverse_lerp = (value - min_value ) / (max_value - min_value)
                    inverse_lerp = min(1, max(0, inverse_lerp))

                    current_intensity = (1-inverse_lerp) * min_intensity + inverse_lerp * max_intensity

                    t = time.time()
                    delta_time = t - self.last_sent_time
                    delta_time = min(delta_time, 1)
                    self.last_sent_time = t

                    if self.actuator_type == "Scalar":
                        send_value = min(1, max(0, current_intensity/100))
                        await self.actuator.command(send_value)

                    elif self.actuator_type == "Rotatory":
                        send_value = min(1, max(0, current_intensity/100))
                        await self.actuator.command(send_value, True)

                    elif self.actuator_type == "Linear":
                        self.linear_value += self.linear_direction * delta_time * current_intensity / 60

                        if self.linear_value >= 1:
                            self.linear_value = 1
                            self.linear_direction = -1

                        if self.linear_value <= 0:
                            self.linear_value = 0
                            self.linear_direction = 1

                        await self.actuator.command(int(delta_time*1000), self.linear_value)

                    else:
                        print("Send command not defined for actuator of type: " + self.actuator_type)

                except buttplug.ButtplugError as e:
                    print(e.args)
