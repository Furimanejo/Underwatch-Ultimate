import os
import time
import mss
import numpy as np
import cv2 as cv

class ComputerVision():
    def __init__(self) -> None:
        self.decay_per_minute = 100
        self.ignore_spectate = True;
        self.ignore_redundant_assists = True;

        self.score_over_time = 0
        self.score_instant = 0

        self.min_update_period = 0.1
        self.last_update = 0
        self.detection_ping = 0
        self.computer_vision_setup()
        self.detectables_setup()
    
    def computer_vision_setup(self):
        self.monitor = mss.mss().monitors[1]
        print("Monitor detected: {0}".format(self.monitor))
        self.debug_frame = None

    def detectables_setup(self):
        self.regions = {}
        self.regions["KillcamOrPOTG"] = {"Rect": [110, 160, 1200, 1600], "MaxMatches": 1}
        popup_left = 750
        popup_right = 960
        self.regions["Popup1"] = {"Rect": [750, 780, popup_left, popup_right], "MaxMatches": 1}
        self.regions["Popup2"] = {"Rect": [785, 815, popup_left, popup_right], "MaxMatches": 1}
        self.regions["Popup3"] = {"Rect": [820, 850, popup_left, popup_right], "MaxMatches": 1}
        self.regions["Give Harmony Orb"] = {"Rect": [945, 995, 725, 775], "MaxMatches": 1}
        self.regions["Give Discord Orb"] = {"Rect": [945, 995, 1145, 1195], "MaxMatches": 1}
        self.regions["Give Mercy Heal"] = {"Rect": [655, 723, 790, 858], "MaxMatches": 1}
        self.regions["Give Mercy Boost"] = {"Rect": [655, 723, 1062, 1130], "MaxMatches": 1}
        self.regions["Receive Heal"] = {"Rect": [740, 840, 440, 650], "MaxMatches": 2}
        self.regions["Receive Status Effect"] = {"Rect": [840, 895, 160, 300], "MaxMatches": 3}

        for region in self.regions:
            self.scale_to_monitor(self.regions[region]["Rect"])
            self.regions[region]["Matches"] = []

        self.detectables = {}
        self.detectables["KillcamOrPOTG"] = {"Filename": "killcam_potg_sobel.png", "Threshold": .75}

        self.detectables["Elimination"] = {"Filename": "elimination.png", "Threshold": .8, "Points": 25, "Type": 2, "Duration": 2.5}
        self.detectables["Assist"] = {"Filename": "assist.png", "Threshold": .8, "Points": 20, "Type": 2, "Duration": 2.5}
        self.detectables["Saved"] = {"Filename": "saved.png", "Threshold": .8, "Points": 30 ,"Type": 2, "Duration": 2.5}
        self.detectables["Eliminated"] = {"Filename": "you_were_eliminated.png", "Threshold": .8, "Points": 0 ,"Type": 2, "Duration": 2.5}

        self.detectables["Give Harmony Orb"] = {"Filename": "apply_harmony.png", "Threshold": .9, "Points": 10, "Type": 0, "Duration": 1}
        self.detectables["Give Discord Orb"] = {"Filename": "apply_discord.png", "Threshold": .9, "Points": 20, "Type": 0, "Duration": 1}

        self.detectables["Give Mercy Heal"] = {"Filename": "apply_mercy_heal.png", "Threshold": .7, "Points": 10, "Type": 0, "Duration": 1}
        self.detectables["Give Mercy Boost"] = {"Filename": "apply_mercy_boost.png", "Threshold": .7, "Points": 20, "Type": 0, "Duration": 1}

        self.detectables["Receive Zen Heal"] = {"Filename": "receive_zen_heal.png", "Threshold": .8, "Points": 10, "Type": 0, "Duration": 1}
        self.detectables["Receive Mercy Heal"] = {"Filename": "receive_mercy_heal.png", "Threshold": .8, "Points": 15, "Type": 0, "Duration": 1}
        self.detectables["Receive Mercy Boost"] = {"Filename": "receive_mercy_boost.png", "Threshold": .8, "Points": 25, "Type": 0, "Duration": 1}

        self.detectables["Receive Hack"] = {"Filename": "receive_hack_icon.png", "Threshold": .8, "Points": 100, "Type": 0, "Duration": 1}
        self.detectables["Receive Discord Orb"] = {"Filename": "receive_discord.png", "Threshold": .8, "Points": -20, "Type": 1, "Duration": 1}
        self.detectables["Receive Anti-Heal"] = {"Filename": "receive_purple_pot.png", "Threshold": .8, "Points": -50, "Type": 0, "Duration": 1}
        self.detectables["Receive Heal Boost"] = {"Filename": "receive_yellow_pot.png", "Threshold": .8, "Points": 20, "Type": 0, "Duration": 1}
        self.detectables["Receive Immortality"] = {"Filename": "receive_immortality.png", "Threshold": .8, "Points": 20, "Type": 0, "Duration": 1}

        for item in self.detectables:
            self.detectables[item]["Template"] = self.load_and_scale_template(self.detectables[item]["Filename"])
            if item in ["Elimination", "Assist", "Saved"]:
                self.detectables[item]["Template"] = self.popup_filter(self.detectables[item]["Template"])
    
    def set_ignore_spectate(self, value):
        self.ignore_spectate = value

    def set_ignore_redundant_assists(self, value):
        self.ignore_redundant_assists = value

    def set_score(self, value):
        self.score_over_time = value;

    def set_decay(self, value):
        self.decay_per_minute = value

    def update(self):
        t0 = time.time()
        if (t0 - self.last_update < self.min_update_period):
            return
        delta_time = min(1, t0 - self.last_update)
        self.last_update = t0

        self.score_instant = 0
        for r in self.regions:
            self.regions[r]["Matches"] = []
        for d in self.detectables:
            self.detectables[d]["Count"] = 0

        on_killcam = False
        if (self.ignore_spectate):
            on_killcam = self.update_killcam_or_potg()
        
        if (on_killcam == False):
            regions_to_crop = [r for r in self.regions if r != "KillcamOrPOTG"]
            self.grab_frame_cropped_to_regions(regions_to_crop)
            self.update_popup_detection()
            self.update_other_detections()
        
        if (self.ignore_redundant_assists):
            self.detectables["Assist"]["Count"] = max(0, self.detectables["Assist"]["Count"] - self.detectables["Elimination"]["Count"])

        frame_delta_points = 0
        for d in self.detectables:
            if (d == "KillcamOrPOTG"):
                continue
            if (self.detectables[d]["Type"] == 0):
                self.score_instant += self.detectables[d]["Count"] * self.detectables[d]["Points"]
            elif (self.detectables[d]["Type"] == 1):
                frame_delta_points += self.detectables[d]["Count"] * self.detectables[d]["Points"] 
            elif (self.detectables[d]["Type"] == 2):
                frame_delta_points += self.detectables[d]["Count"] * self.detectables[d]["Points"] / self.detectables[d]["Duration"]

        self.score_over_time += delta_time * frame_delta_points
        self.score_over_time -= delta_time * self.decay_per_minute / 60
        self.score_over_time = max(0, self.score_over_time)

        t1 = time.time()
        a = .1
        self.detection_ping = (1-a) * self.detection_ping + a * (t1-t0)

    def update_killcam_or_potg(self):
        self.grab_frame_cropped_to_regions(["KillcamOrPOTG"])
        self.match_detectables_on_region("KillcamOrPOTG", ["KillcamOrPOTG"], operation = self.sobel_operation)
        return self.detectables["KillcamOrPOTG"]["Count"] > 0

    def update_popup_detection(self):
        popupRegions = ["Popup1", "Popup2", "Popup3"]
        popupsToDetect = ["Elimination", "Assist", "Saved", ]
        
        for region in popupRegions:
            self.match_detectables_on_region(region, popupsToDetect, operation = self.popup_filter)
        for region in popupRegions:
            self.match_detectables_on_region(region, ["Eliminated"])

    def update_other_detections(self):
        for item in ["Give Harmony Orb", "Give Discord Orb", "Give Mercy Boost", "Give Mercy Heal"]:
            self.match_detectables_on_region(item, [item])
        
        healDetectables = ["Receive Zen Heal", "Receive Mercy Boost", "Receive Mercy Heal"]
        self.match_detectables_on_region("Receive Heal", healDetectables)

        statusDetectables = ["Receive Hack", "Receive Discord Orb", "Receive Anti-Heal", "Receive Heal Boost", "Receive Immortality"]
        self.match_detectables_on_region("Receive Status Effect", statusDetectables)

    def get_current_score(self):
        return self.score_over_time + self.score_instant

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
        for d in detectableKeys:
            if (self.detectables[d].get("Points") == 0):
                detectableKeys.remove(d)

        if (len(detectableKeys) == 0):
            return

        crop = self.get_cropped_frame_copy(self.regions[regionKey]["Rect"])
        if (operation is not None):
            crop = operation(crop)

        for d in detectableKeys:
            if (len(self.regions[regionKey]["Matches"]) >= self.regions[regionKey]["MaxMatches"]):
                break
            match_max_value = self.match_template(crop, self.detectables[d]["Template"])
            if match_max_value > self.detectables[d]["Threshold"]:
                self.detectables[d]["Count"] += 1
                self.regions[regionKey]["Matches"].append(d)
            
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
