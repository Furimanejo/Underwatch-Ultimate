from copy import deepcopy
import json
import os

config = {
    "monitor_number": 1,
    "show_overlay_mode": 0,
    "show_regions_mode": 0,
    "ignore_spectate": True,
    "ignore_redundant_assists": True,
    "decay": 100,
    "regions": {
        "KillcamOrPOTG": {"OriginalRect": [110, 160, 1200, 1600], "MaxMatches": 1},

        "Popup1": {"OriginalRect": [750, 780, 750, 960], "MaxMatches": 1},
        "Popup2": {"OriginalRect": [785, 815, 750, 960], "MaxMatches": 1},
        "Popup3": {"OriginalRect": [820, 850, 750, 960], "MaxMatches": 1},

        "Give Harmony Orb": {"OriginalRect": [945, 995, 725, 775], "MaxMatches": 1},
        "Give Discord Orb": {"OriginalRect": [945, 995, 1145, 1195], "MaxMatches": 1},
        "Give Mercy Heal": {"OriginalRect": [655, 723, 790, 858], "MaxMatches": 1},
        "Give Mercy Boost": {"OriginalRect": [655, 723, 1062, 1130], "MaxMatches": 1},

        "Receive Heal": {"OriginalRect": [740, 840, 440, 650], "MaxMatches": 2},

        "Receive Status Effect": {"OriginalRect": [840, 895, 160, 300], "MaxMatches": 3},
    },
    "detectables": {
        "KillcamOrPOTG": {"Filename": "killcam_potg_sobel.png", "Threshold": .75},

        "Elimination": {"Filename": "elimination.png", "Threshold": .8, "Points": 25, "Type": 2, "Duration": 2.5},
        "Assist": {"Filename": "assist.png", "Threshold": .8, "Points": 20, "Type": 2, "Duration": 2.5},
        "Saved": {"Filename": "saved.png", "Threshold": .8, "Points": 30 ,"Type": 2, "Duration": 2.5},
        "Eliminated": {"Filename": "you_were_eliminated.png", "Threshold": .8, "Points": 0 ,"Type": 2, "Duration": 2.5},
    
        "Give Harmony Orb": {"Filename": "apply_harmony.png", "Threshold": .9, "Points": 10, "Type": 0, "Duration": 1},
        "Give Discord Orb": {"Filename": "apply_discord.png", "Threshold": .9, "Points": 20, "Type": 0, "Duration": 1},
        "Give Mercy Heal": {"Filename": "apply_mercy_heal.png", "Threshold": .7, "Points": 10, "Type": 0, "Duration": 1},
        "Give Mercy Boost": {"Filename": "apply_mercy_boost.png", "Threshold": .7, "Points": 20, "Type": 0, "Duration": 1},
    
        "Receive Zen Heal": {"Filename": "receive_zen_heal.png", "Threshold": .8, "Points": 10, "Type": 0, "Duration": 1},
        "Receive Mercy Heal": {"Filename": "receive_mercy_heal.png", "Threshold": .8, "Points": 15, "Type": 0, "Duration": 1},
        "Receive Mercy Boost": {"Filename": "receive_mercy_boost.png", "Threshold": .8, "Points": 25, "Type": 0, "Duration": 1},
        
        "Receive Hack": {"Filename": "receive_hack_icon.png", "Threshold": .8, "Points": 100, "Type": 0, "Duration": 1},
        "Receive Discord Orb": {"Filename": "receive_discord.png", "Threshold": .8, "Points": -20, "Type": 1, "Duration": 1},
        "Receive Anti-Heal": {"Filename": "receive_purple_pot.png", "Threshold": .8, "Points": -50, "Type": 0, "Duration": 1},
        "Receive Heal Boost": {"Filename": "receive_yellow_pot.png", "Threshold": .8, "Points": 20, "Type": 0, "Duration": 1},
        "Receive Immortality": {"Filename": "receive_immortality.png", "Threshold": .8, "Points": 20, "Type": 0, "Duration": 1},
    }
}

def save_to_file():
    save_dict = deepcopy(config)
    del save_dict["regions"]
    for det in save_dict["detectables"].values():
        for field in list(det.keys()):
            if (field not in ["Points", "Type"]):
                del det[field]

    with open('config.json', 'w') as f:
        json.dump(save_dict,  f, indent= 4)

def load_from_file():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            load_dict = json.load(f)
            for key in load_dict.keys():
                if key in ["detectables"]:
                    for detectable in load_dict[key].keys():
                        for field in load_dict[key][detectable].keys():
                            config[key][detectable][field] = load_dict[key][detectable][field]
                else:
                    config[key] = load_dict[key]
                    