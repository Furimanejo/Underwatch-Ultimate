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

        self.prompt_detectables = ["Stuck", "Detected", "Life Gripped", "Hacked", "Hindered", "Reviving", "Pinned", "Sleep", "Stunned", "Trapped", "Revealed"]
        self.filters = {
            "KillcamOrPOTG": self.sobel_operation,
            "Elimination": self.popup_filter,
            "Assist": self.popup_filter,
            "Saved": self.popup_filter,
        }
        for d in self.prompt_detectables:
            self.filters[d] = self.prompt_filter

        self.debug_image = None
        self.detection_rect = {}
        self.resolution_scaling_factor = 1
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
            self.resolution_scaling_factor = scale
            self.detectables_setup()
            return True

    def detectables_setup(self):
        for region in config["regions"]:
            i = config["aspect_ratio_index"]
            resolution = str(aspect_ratios[i]["sample_w"]) + "x" + str(aspect_ratios[i]["sample_h"])
            rect = config["regions"][region].get(resolution)
            if rect == None:
                print("Region \"" + region + "\" not defined for current aspect ratio")
                rect = config["regions"][region].get("1920x1080")

            config["regions"][region]["ScaledRect"] = self.scale_rect(rect)
            config["regions"][region]["Matches"] = []

        for item in config["detectables"]:
            self.load_and_scale_template(config["detectables"][item])
            if item in self.filters:
                config["detectables"][item]["template"] = self.filters[item](config["detectables"][item]["template"])
    
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

        self.update_detections()
        
        if config["ignore_redundant_assists"]:
            config["detectables"]["Assist"]["Count"] = max(0, config["detectables"]["Assist"]["Count"] - config["detectables"]["Elimination"]["Count"])

        frame_delta_points = 0
        for d in config["detectables"]:
            if d == "KillcamOrPOTG":
                continue
            if config["detectables"][d]["type"] == 0:
                self.score_instant += config["detectables"][d]["Count"] * config["detectables"][d]["points"]
            elif config["detectables"][d]["type"] == 1:
                frame_delta_points += config["detectables"][d]["Count"] * config["detectables"][d]["points"] 
            elif config["detectables"][d]["type"] == 2:
                frame_delta_points += config["detectables"][d]["Count"] * config["detectables"][d]["points"] / config["detectables"][d]["duration"]

        self.score_over_time += delta_time * frame_delta_points
        self.score_over_time -= delta_time * config["decay"] / 60
        self.score_over_time = max(0, self.score_over_time)

        t1 = time.time()
        a = .1
        self.detection_ping = (1-a) * self.detection_ping + a * (t1-t0)
        return True

    def update_detections(self):
        upper_regions = ["KillcamOrPOTG", "Prompt"]
        self.grab_frame_cropped_to_regions(upper_regions)

        if config["ignore_spectate"]:
            self.match_detectables_on_region("KillcamOrPOTG", ["KillcamOrPOTG"])
            if config["detectables"]["KillcamOrPOTG"]["Count"] > 0:
                return

        self.match_detectables_on_region("Prompt", self.prompt_detectables)

        lower_regions = [r for r in config["regions"] if r not in upper_regions]
        self.grab_frame_cropped_to_regions(lower_regions)

        # Popups
        popupRegions = ["Popup1", "Popup2", "Popup3"]
        for region in popupRegions:
            self.match_detectables_on_region(region, ["Elimination", "Assist", "Saved", "Died"])

        # Hero Specific
        for item in ["Give Harmony Orb", "Give Discord Orb", "Give Mercy Boost", "Give Mercy Heal"]:
            self.match_detectables_on_region(item, [item])

        # Receive Heals
        healDetectables = ["Receive Zen Heal", "Receive Mercy Boost", "Receive Mercy Heal"]
        self.match_detectables_on_region("Receive Heal", healDetectables)

        # Status
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
    
    def match_detectables_on_region(self, regionKey, detectableKeys):
        for d in detectableKeys:
            if config["detectables"][d].get("points") == 0:
                detectableKeys.remove(d)

        if len(detectableKeys) == 0:
            return

        region_rect = config["regions"][regionKey]["ScaledRect"]
        crop = self.get_cropped_frame_copy(region_rect)

        filtered_crops = {}
        for d in detectableKeys:
            filt = self.filters.get(d)
            if filt is not None and filt not in filtered_crops:
                filtered_crops[filt] = filt(crop.copy())
                

        for d in detectableKeys:
            if d in self.filters:
                selected_crop = filtered_crops[self.filters[d]]
            else:
                selected_crop = crop

            max_matches = config["regions"][regionKey].get("MaxMatches", 1)
            if len(config["regions"][regionKey]["Matches"]) >= max_matches:
                break

            if d in self.prompt_detectables:
                # To save performance and avoid false positives: crop the selected crop to the center, to fit the template's width
                template_w = config["detectables"][d]["template"].shape[1]
                crop_w = selected_crop.shape[1]
                left = int((crop_w - template_w)/2)
                right = left + template_w
                left = max(left - 3, 0)
                right = min(right + 3, crop_w)
                selected_crop = selected_crop[:,left:right,:]

            r_shape = selected_crop.shape
            t_shape = config["detectables"][d]["template"].shape
            if t_shape[0] > r_shape[0] or t_shape[1] > r_shape[1]:
                print("Template {0}({1}) is bigger than region {2}".format(d, t_shape, r_shape))
                return

            match_max_value = self.match_template(selected_crop, config["detectables"][d]["template"])
            
            if match_max_value > config["detectables"][d]["threshold"]:
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
    
    def prompt_filter(self, frame):
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        (h, s, v) = cv.split(hsv)
        mean_v = cv.mean(v)[0]
        t = 200
        if mean_v > t:
            v = s
        v = cv.Canny(v, t, 0)
        v = cv.dilate(v, np.ones((3,3), np.uint8), iterations= 1)
        return cv.merge((v, v, v))

    def get_cropped_frame_copy(self, rect):
        top = rect["y"] - self.frame_offset[0]
        bottom = rect["y"] + rect["h"] - self.frame_offset[0]
        left = rect["x"] - self.frame_offset[1]
        right = rect["x"] + rect["w"] - self.frame_offset[1]
        return self.frame[top:bottom, left:right].copy()

    def scale_rect(self, rect):
        scaled_rect = {
            "x": int (rect["x"] * self.resolution_scaling_factor),
            "y": int (rect["y"] * self.resolution_scaling_factor),
            "w": int (rect["w"] * self.resolution_scaling_factor),
            "h": int (rect["h"] * self.resolution_scaling_factor)
        }
        return scaled_rect
    
    def load_and_scale_template(self, item):
        path = os.path.join(os.path.abspath("."), "templates", item["filename"])
        base_template = cv.imread(path)

        template_scaling = aspect_ratios[config["aspect_ratio_index"]].get("template_scaling", 1)
        height = int(base_template.shape[0] * self.resolution_scaling_factor * template_scaling)
        width =  int(base_template.shape[1] * self.resolution_scaling_factor * template_scaling)
        scaled = cv.resize(base_template.copy(), (width, height))

        item["original_image"] = base_template
        item["template"] = scaled