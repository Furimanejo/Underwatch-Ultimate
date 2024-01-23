from math import e
import os
import time
import mss
import numpy as np
import cv2 as cv

from config_handler import config, aspect_ratios

class ComputerVision():
    def __init__(self) -> None:
        self.last_update = 0
        self.min_update_period = 0.1
        self.detection_ping = 0
        self.score_over_time = 0
        self.score_instant = 0

        self.detection_rect = {}
        self.scaling_factor = 1
        self.resolution_changed = False
        self.detect_resolution()
    
    def detect_resolution(self):
        monitor_number = config["monitor_number"]
        
        monitor_rect = {}
        with mss.mss() as sct:
            monitor_rect = sct.monitors[monitor_number]
        
        sample_width = aspect_ratios[config["aspect_ratio_index"]]["sample_w"]
        sample_height = aspect_ratios[config["aspect_ratio_index"]]["sample_h"]
        
        game_rect = monitor_rect
        scale = 1
        monitor_aspect_ratio = monitor_rect["width"] / monitor_rect["height"]
        if monitor_aspect_ratio >= sample_width / sample_height:
            # scale to fit height, like fitting a 16:9 window on a 21:9 screen
            scale = monitor_rect["height"] / sample_height
            desired_width = int(sample_width * scale)
            black_bar_width = int((monitor_rect["width"] - desired_width) / 2)
            game_rect["width"] = desired_width
            game_rect["left"] += black_bar_width
        else:
            # scale to fit width, like fitting a 16:9 window on a 16:10 screen
            scale = monitor_rect["width"] / sample_width
            desired_height = int(sample_height * scale)
            black_bar_height = int((monitor_rect["height"] - desired_height) / 2)
            game_rect["height"] = desired_height
            game_rect["top"] += black_bar_height

        if self.detection_rect == game_rect:
            return False
        else:
            print("Setting detection rect: " + str(game_rect))
            self.detection_rect = game_rect
            self.scaling_factor = scale
            self.detectables_setup()
            return True

    def detectables_setup(self):
        for region in config["regions"]:
            i = config["aspect_ratio_index"]
            resolution = str(aspect_ratios[i]["sample_w"]) + "x" + str(aspect_ratios[i]["sample_h"])
            rect = config["regions"][region].get(resolution)
            if rect == None:
                print(resolution)
                print("Region " + region + " not defined for current aspect ratio")
                rect = config["regions"][region].get("1920x1080")

            config["regions"][region]["ScaledRect"] = self.scale_rect(rect)
            config["regions"][region]["Matches"] = []

        for item in config["detectables"]:
            config["detectables"][item]["Template"] = self.load_and_scale_template(config["detectables"][item]["Filename"])
            if item in ["Elimination", "Assist", "Saved"]:
                config["detectables"][item]["Template"] = self.popup_filter(config["detectables"][item]["Template"])
    
    def set_score(self, value):
        self.score_over_time = value;
        
    def update(self):
        t0 = time.time()
        if t0 - self.last_update < self.min_update_period:
            return False
        delta_time = min(1, t0 - self.last_update)
        self.last_update = t0

        self.resolution_changed = self.detect_resolution()

        self.score_instant = 0
        for r in config["regions"]:
            config["regions"][r]["Matches"] = []
        for d in config["detectables"]:
            config["detectables"][d]["Count"] = 0

        on_killcam = False
        if config["ignore_spectate"]:
            on_killcam = self.update_killcam_or_potg()
        
        if on_killcam == False:
            regions_to_crop = [r for r in config["regions"] if r != "KillcamOrPOTG"]
            self.grab_frame_cropped_to_regions(regions_to_crop)
            self.update_popup_detection()
            self.update_other_detections()
        
        if config["ignore_redundant_assists"]:
            config["detectables"]["Assist"]["Count"] = max(0, config["detectables"]["Assist"]["Count"] - config["detectables"]["Elimination"]["Count"])

        frame_delta_points = 0
        for d in config["detectables"]:
            if d == "KillcamOrPOTG":
                continue
            if config["detectables"][d]["Type"] == 0:
                self.score_instant += config["detectables"][d]["Count"] * config["detectables"][d]["Points"]
            elif config["detectables"][d]["Type"] == 1:
                frame_delta_points += config["detectables"][d]["Count"] * config["detectables"][d]["Points"] 
            elif config["detectables"][d]["Type"] == 2:
                frame_delta_points += config["detectables"][d]["Count"] * config["detectables"][d]["Points"] / config["detectables"][d]["Duration"]

        self.score_over_time += delta_time * frame_delta_points
        self.score_over_time -= delta_time * config["decay"] / 60
        self.score_over_time = max(0, self.score_over_time)

        t1 = time.time()
        a = .1
        self.detection_ping = (1-a) * self.detection_ping + a * (t1-t0)
        return True

    def update_killcam_or_potg(self):
        self.grab_frame_cropped_to_regions(["KillcamOrPOTG"])
        self.match_detectables_on_region("KillcamOrPOTG", ["KillcamOrPOTG"], operation = self.sobel_operation)
        return config["detectables"]["KillcamOrPOTG"]["Count"] > 0

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
        top = self.detection_rect["height"]
        left = self.detection_rect["width"]
        bottom = 0
        right = 0

        # Find rect that encompasses all regions
        for region in regionNames:
            rect = config["regions"][region]["ScaledRect"]
            top = min(top, rect["y"])
            bottom = max(bottom, rect["y"]+rect["h"])
            left = min(left, rect["x"])
            right = max(right, rect["x"]+rect["w"])

        self.frame_offset = (top, left)

        top += self.detection_rect["top"]
        bottom += self.detection_rect["top"]
        left += self.detection_rect["left"]
        right += self.detection_rect["left"]

        with mss.mss() as sct:
            self.frame = np.array(sct.grab((left, top, right, bottom)))[:,:,:3]
    
    def match_detectables_on_region(self, regionKey, detectableKeys, operation = None):
        for d in detectableKeys:
            if config["detectables"][d].get("Points") == 0:
                detectableKeys.remove(d)

        if len(detectableKeys) == 0:
            return

        region_rect = config["regions"][regionKey]["ScaledRect"]
        crop = self.get_cropped_frame_copy(region_rect)
        if operation is not None:
            crop = operation(crop)

        for d in detectableKeys:
            max_matches = config["regions"][regionKey].get("MaxMatches", 1)
            if len(config["regions"][regionKey]["Matches"]) >= max_matches:
                break
            match_max_value = self.match_template(crop,config["detectables"][d]["Template"])
            if match_max_value > config["detectables"][d]["Threshold"]:
                config["detectables"][d]["Count"] += 1
                config["regions"][regionKey]["Matches"].append(d)
            
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
        top = rect["y"] - self.frame_offset[0]
        bottom = rect["y"] + rect["h"] - self.frame_offset[0]
        left = rect["x"] - self.frame_offset[1]
        right = rect["x"] + rect["w"] - self.frame_offset[1]
        return self.frame[top:bottom, left:right].copy()

    def scale_rect(self, rect):
        scaled_rect = {
            "x": int (rect["x"] * self.scaling_factor),
            "y": int (rect["y"] * self.scaling_factor),
            "w": int (rect["w"] * self.scaling_factor),
            "h": int (rect["h"] * self.scaling_factor)
        }
        return scaled_rect
    
    def load_and_scale_template(self, file_name):
        path = os.path.join(os.path.abspath("."), "templates", file_name)
        template = cv.imread(path)
        
        height = int(template.shape[0] * self.scaling_factor)
        width =  int(template.shape[1] * self.scaling_factor)

        return cv.resize(template, (width, height))