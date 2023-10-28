import asyncio, os, time

import dxcam
import mss

import numpy as np
import cv2 as cv

class ComputerVision():
    def __init__(self) -> None:
        self.last_update = 0
        self.min_update_period = 0.1
        self.score = 0
        self.decay = 4
        self.detection_delay = 0
        self.computer_vision_setup()
        self.detectables_setup()
    
    def computer_vision_setup(self):
        self.monitor = mss.mss().monitors[1]
        print("Monitor detected: {0}".format(self.monitor))
        self.debug_frame = None

    def detectables_setup(self):
        self.regions = {}
        self.regions["KillcamOrPOTG"] = {"Rect": [110, 160, 1200, 1400]}
        popup_left = 780
        popup_right = 960
        self.regions["Popup1"] = {"Rect": [750, 780, popup_left, popup_right]}
        self.regions["Popup2"] = {"Rect": [785, 815, popup_left, popup_right]}
        self.regions["Popup3"] = {"Rect": [820, 850, popup_left, popup_right]}
        self.regions["ApplyHarmony"] = {"Rect": [945, 995, 725, 775]}
        self.regions["ApplyDiscord"] = {"Rect": [945, 995, 1145, 1195]}
        self.regions["ApplyMercyHeal"] = {"Rect": [655, 723, 790, 858]}
        self.regions["ApplyMercyBoost"] = {"Rect": [655, 723, 1062, 1130]}
        self.regions["ReceiveMercyOrZen"] = {"Rect": [740, 840, 440, 650]}

        for region in self.regions:
            self.scale_to_monitor(self.regions[region]["Rect"])
            self.regions[region]["Match"] = None

        self.detectables = {}
        self.detectables["Elimination"] = {"Filename": "elimination.png", "Threshold": .8, "Points": 25, "PointsType": 0}
        self.detectables["Assist"] = {"Filename": "assist.png", "Threshold": .8, "Points": 20,"PointsType": 0}
        self.detectables["Saved"] = {"Filename": "saved.png", "Threshold": .8, "Points": 30,"PointsType": 0}
        self.detectables["ApplyHarmony"] = {"Filename": "apply_harmony.png", "Threshold": .9, "Points": 15, "PointsType": 1}
        self.detectables["ApplyDiscord"] = {"Filename": "apply_discord.png", "Threshold": .9, "Points": 15, "PointsType": 1}
        self.detectables["ApplyMercyBoost"] = {"Filename": "apply_mercy_boost.png", "Threshold": .7, "Points": 20, "PointsType": 1}
        self.detectables["ApplyMercyHeal"] = {"Filename": "apply_mercy_heal.png", "Threshold": .7, "Points": 30, "PointsType": 1}
        self.detectables["ReceiveZenHeal"] = {"Filename": "receive_zen_heal.png", "Threshold": .8, "Points": 10, "PointsType": 1}
        self.detectables["ReceiveMercyHeal"] = {"Filename": "receive_mercy_heal.png", "Threshold": .8, "Points": 10, "PointsType": 1}
        self.detectables["ReceiveMercyBoost"] = {"Filename": "receive_mercy_boost.png", "Threshold": .8, "Points": 25, "PointsType": 1}
        self.detectables["KillcamOrPOTG"] = {"Filename": "killcam_potg_sobel.png", "Threshold": .95}

        for item in self.detectables:
            
            self.detectables[item]["Template"] = self.load_and_scale_template(self.detectables[item]["Filename"])
            if item in ["Elimination", "Assist", "Saved"]:
                self.detectables[item]["Template"] = self.popup_filter(self.detectables[item]["Template"])

    async def update(self):
        t0 = time.time()
        if (t0 - self.last_update < self.min_update_period):
            return
        delta_time = min(1, t0 - self.last_update)
        self.last_update = t0

        for r in self.regions:
            self.regions[r]["Match"] = None
        for d in self.detectables:
            self.detectables[d]["Count"] = 0

        self.grab_frame_cropped_to_regions(["KillcamOrPOTG"])
        on_killcam = self.update_killcam_or_potg()
        
        if (on_killcam == False):
            regions_to_crop = [r for r in self.regions if r != "KillcamOrPOTG"]
            self.grab_frame_cropped_to_regions(regions_to_crop)
            self.update_popup_detection()
            self.update_other_detections()
        
        elims = self.detectables["Elimination"]["Count"] * self.detectables["Elimination"]["Points"]
        assists = self.detectables["Assist"]["Count"] * self.detectables["Assist"]["Points"]
        saved = self.detectables["Saved"]["Count"] * self.detectables["Saved"]["Points"]
        
        total = (max(elims, assists) + saved) / 2.5

        if (total > 0):
            self.score += delta_time * total
        else:
            self.score -= delta_time * self.decay

        self.score = max(0, self.score)

        t1 = time.time()
        a = .05
        self.detection_delay = (1-a)*self.detection_delay + a*(t1-t0)

    def update_killcam_or_potg(self):
        match = self.match_detectables_on_region("KillcamOrPOTG", ["KillcamOrPOTG"], operation = self.sobel_operation)
        return match is not None

    def update_popup_detection(self):
        popupRegions = ["Popup1", "Popup2", "Popup3"]
        popupsToDetect = ["Elimination", "Assist", "Saved"]
        
        for region in popupRegions:
            self.match_detectables_on_region(region, popupsToDetect, operation = self.popup_filter)

    def update_other_detections(self):
        for item in ["ApplyHarmony", "ApplyDiscord", "ApplyMercyBoost", "ApplyMercyHeal"]:
            self.match_detectables_on_region(item, [item])

        zen_match = self.match_detectables_on_region("ReceiveMercyOrZen", ["ReceiveZenHeal"])
        mercy_match = self.match_detectables_on_region("ReceiveMercyOrZen", ["ReceiveMercyBoost", "ReceiveMercyHeal"])
        if (mercy_match is None):
            self.regions["ReceiveMercyOrZen"]["Match"] = zen_match
        elif (zen_match is not None):
            self.regions["ReceiveMercyOrZen"]["Match"] += "+ZenHeal"

    def grab_frame_cropped_to_regions(self, regionNames):
        top = self.monitor["height"]
        left = self.monitor["width"]
        bottom = 0
        right = 0

        # Find rect that encompasses all regions
        for region in regionNames:
            rect = self.regions[region]["Rect"]
            top = min(top, rect[0])
            bottom = max(bottom, rect[1])
            left = min(left, rect[2])
            right = max(right, rect[3])

        self.frame_offset = (top, left)
        with mss.mss() as sct:
            self.frame = np.array(sct.grab((left, top, right, bottom)))[:,:,:3]
    
    def match_detectables_on_region(self, regionKey, detectableKeys, operation = None):
        crop = self.get_cropped_frame_copy(self.regions[regionKey]["Rect"])
        if (operation is not None):
            crop = operation(crop)

        match = None
        for d in detectableKeys:
            match_max_value = self.match_template(crop, self.detectables[d]["Template"])
            if match_max_value > self.detectables[d]["Threshold"]:
                match = d
                self.detectables[match]["Count"] += 1
                break
        
        self.regions[regionKey]["Match"] = match
        return match
    
    def match_template(self, frame, template):
        result = cv.matchTemplate(frame, template, cv.TM_CCOEFF_NORMED)
        minVal, maxVal, minLoc, maxLoc = cv.minMaxLoc(result)
        return maxVal

    def popup_filter(self, frame):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        right = gray.shape[1]
        left = max(0, right - 50)
        mean = cv.mean(gray[:,left:right])
        
        sat = 50
        value = 130
        mask = cv.inRange(gray, int(mean[0] - sat), int( 0.5*mean[0] + value))
        frame[(mask==0)] = [255, 255, 255]
        frame[(mask==255)] = [0, 0, 0]
        return frame

    def sobel_operation(self, frame):
        return cv.Sobel(frame, ddepth= cv.CV_8U, dx = 0, dy = 1, ksize = 3)

    def get_cropped_frame_copy(self, rect):
        top = rect[0] - self.frame_offset[0]
        bottom = rect[1] - self.frame_offset[0]
        left = rect[2] - self.frame_offset[1]
        right = rect[3] - self.frame_offset[1]
        return self.frame[top:bottom, left:right].copy()

    def scale_to_monitor(self, rect):
        rect[0] = int (rect[0] * self.monitor["height"] / 1080)
        rect[1] = int (rect[1] * self.monitor["height"] / 1080)
        rect[2] = int (rect[2] * self.monitor["width"] / 1920)
        rect[3] = int (rect[3] * self.monitor["width"] / 1920)
    
    def load_and_scale_template(self, file_name):
        path = os.path.join(os.path.abspath("."), "templates", file_name)
        template = cv.imread(path)
        height = int(template.shape[0] * self.monitor["height"] / 1080)
        width =  int(template.shape[1] * self.monitor["width"] / 1920)
        return cv.resize(template, (width, height))
