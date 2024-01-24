from copy import deepcopy
import json
import os

aspect_ratios = {
    0 : {
        "id" : "16:9",
        "sample_w": 1920,
        "sample_h": 1080,
    },
    1: {
        "id" : "21:9",
        "sample_w": 2560,
        "sample_h": 1080,
    },    
}

config = {
    "monitor_number": 1,
    "aspect_ratio_index": 0,
    "show_overlay_mode": 0,
    "show_regions_mode": 0,
    "ignore_spectate": True,
    "ignore_redundant_assists": True,
    "decay": 100,
    "regions": {
        "KillcamOrPOTG": {
            "1920x1080": {
                "x": 1200,
                "y": 110,
                "w": 400,
                "h": 50
            },
            "2560x1080": {
                "x": 1840,
                "y": 110,
                "w": 400,
                "h": 50
            },
        },
        "Popup1": {
            "1920x1080": {
                "x": 750,
                "y": 750,
                "w": 210,
                "h": 30
            },
            "2560x1080": {
                "x": 1070,
                "y": 750,
                "w": 210,
                "h": 30
            },
        },
        "Popup2": {
            "1920x1080": {
                "x": 750,
                "y": 785,
                "w": 210,
                "h": 30
            },
            "2560x1080": {
                "x": 1070,
                "y": 785,
                "w": 210,
                "h": 30
            },
        },
        "Popup3": {
            "1920x1080": {
                "x": 750,
                "y": 820,
                "w": 210,
                "h": 30
            },
            "2560x1080": {
                "x": 1070,
                "y": 820,
                "w": 210,
                "h": 30
            },
        },
        "Give Harmony Orb": {
            "1920x1080": {
                "x": 725,
                "y": 945,
                "w": 50,
                "h": 50
            },
            "2560x1080": {
                "x": 1045,
                "y": 945,
                "w": 50,
                "h": 50
            },
        },
        "Give Discord Orb": {
            "1920x1080": {
                "x": 1145,
                "y": 945,
                "w": 50,
                "h": 50
            },
            "2560x1080": {
                "x": 1465,
                "y": 945,
                "w": 50,
                "h": 50
            },
        },
        "Give Mercy Heal": {
            "1920x1080": {
                "x": 790,
                "y": 655,
                "w": 68,
                "h": 68
            },
            "2560x1080": {
                "x": 1110,
                "y": 655,
                "w": 68,
                "h": 68
            },
        },
        "Give Mercy Boost": {
            "1920x1080": {
                "x": 1062,
                "y": 655,
                "w": 68,
                "h": 68
            },
            "2560x1080": {
                "x": 1382,
                "y": 655,
                "w": 68,
                "h": 68
            },
        },
        "Receive Heal": {
            "MaxMatches": 2,
            "1920x1080": {
                "x": 440,
                "y": 740,
                "w": 210,
                "h": 100
            },
            "2560x1080": {
                "x": 440,
                "y": 740,
                "w": 210,
                "h": 100
            },
        },
        "Receive Status Effect": {
            "MaxMatches": 3,
            "1920x1080": {
                "x": 160,
                "y": 840,
                "w": 140,
                "h": 55
            },
            "2560x1080": {
                "x": 160,
                "y": 840,
                "w": 140,
                "h": 55
            },
        },
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
        print("Loading config file...")
        with open('config.json', 'r') as f:
            load_dict = json.load(f)
            for key in load_dict.keys():
                if key in ["detectables"]:
                    for detectable in load_dict[key].keys():
                        for field in load_dict[key][detectable].keys():
                            config[key][detectable][field] = load_dict[key][detectable][field]
                else:
                    config[key] = load_dict[key]