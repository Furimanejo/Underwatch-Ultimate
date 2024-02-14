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
    2: {
        "id" : "16:10",
        "sample_w": 1680,
        "sample_h": 1050,
        "template_scaling": 1680/1920
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
                "x": 1520,
                "y": 110,
                "w": 400,
                "h": 50
            },
            "1680x1050":{
                "x": 1080,
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
            "1680x1050": {
                "x": 1680/2-185,
                "y": 656,
                "w": 185,
                "h": 27
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
            "1680x1050": {
                "x": 1680/2-185,
                "y": 656+30,
                "w": 185,
                "h": 27
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
            "1680x1050": {
                "x": 1680/2-185,
                "y": 656+30+30,
                "w": 185,
                "h": 27
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
            "1680x1050": {
                "x": 635,
                "y": 932,
                "w": 45,
                "h": 45
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
            "1680x1050": {
                "x": 1000,
                "y": 932,
                "w": 45,
                "h": 45
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
            "1680x1050": {
                "x": 690,
                "y": 625,
                "w": 60,
                "h": 60
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
            "1680x1050": {
                "x": 930,
                "y": 625,
                "w": 60,
                "h": 60
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
            "1680x1050": {
                "x": 385,
                "y": 750,
                "w": 200,
                "h": 90
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
            "1680x1050": {
                "x": 144,
                "y": 848,
                "w": 120,
                "h": 36
            },
        },
        "Prompt":{
            "1920x1080": {
                "x": (1920-300)/2,
                "y": 228,
                "w": 300,
                "h": 58
            },
            "2560x1080": {
                "x": (2560-300)/2,
                "y": 228,
                "w": 300,
                "h": 58
            },
            "1680x1050": {
                "x": (1680-265)/2,
                "y": 200,
                "w": 265,
                "h": 52
            },
        }
    },
    "detectables": {
        "KillcamOrPOTG": {"filename": "killcam_potg_sobel.png", "threshold": .75},
        # Popup
        "Elimination": {"filename": "elimination.png", "threshold": .8, "points": 25, "type": 2, "duration": 2.5},
        "Assist": {"filename": "assist.png", "threshold": .8, "points": 20, "type": 2, "duration": 2.5},
        "Saved": {"filename": "saved.png", "threshold": .8, "points": 30 ,"type": 2, "duration": 2.5},
        "Died": {"filename": "died.png", "threshold": .8, "points": 0 ,"type": 2, "duration": 2.5},
        # Prompt
        "Detected": {"filename": "prompt_detected.png", "threshold": .5, "points": 100, "type": 0},
        "Life Gripped": {"filename": "prompt_gripped.png", "threshold": .5, "points": 100, "type": 0},
        "Hacked": {"filename": "prompt_hacked.png", "threshold": .5, "points":100, "type": 0},
        "Hindered": {"filename": "prompt_hindered.png", "threshold": .5, "points": 100, "type": 0},
        "Reviving": {"filename": "prompt_reviving.png", "threshold": .5, "points": 100, "type": 0},
        "Pinned": {"filename": "prompt_pinned.png", "threshold": .5, "points": 100, "type": 0},
        "Revealed": {"filename": "prompt_revealed.png", "threshold": .5, "points": 100, "type": 0},
        "Sleep": {"filename": "prompt_sleep.png", "threshold": .5, "points": 100, "type": 0},
        "Stuck": {"filename": "prompt_stuck.png", "threshold": .5, "points": 100, "type": 0},
        "Stunned": {"filename": "prompt_stunned.png", "threshold": .5, "points": 100, "type": 0},
        "Trapped": {"filename": "prompt_trapped.png", "threshold": .5, "points": 100, "type": 0},
        # Status
        "Receive Zen Heal": {"filename": "receive_zen_heal.png", "threshold": .8, "points": 10, "type": 0},
        "Receive Mercy Heal": {"filename": "receive_mercy_heal.png", "threshold": .8, "points": 15, "type": 0},
        "Receive Mercy Boost": {"filename": "receive_mercy_boost.png", "threshold": .8, "points": 25, "type": 0},
        "Receive Hack": {"filename": "receive_hack_icon.png", "threshold": .8, "points": 100, "type": 0},
        "Receive Discord Orb": {"filename": "receive_discord.png", "threshold": .8, "points": -20, "type": 1},
        "Receive Anti-Heal": {"filename": "receive_purple_pot.png", "threshold": .8, "points": -50, "type": 0},
        "Receive Heal Boost": {"filename": "receive_yellow_pot.png", "threshold": .8, "points": 20, "type": 0},
        "Receive Immortality": {"filename": "receive_immortality.png", "threshold": .8, "points": 20, "type": 0},
        # Hero Specific
        "Give Mercy Heal": {"filename": "apply_mercy_heal.png", "threshold": .7, "points": 10, "type": 0},
        "Give Mercy Boost": {"filename": "apply_mercy_boost.png", "threshold": .7, "points": 20, "type": 0},
        "Give Harmony Orb": {"filename": "apply_harmony.png", "threshold": .9, "points": 10, "type": 0},
        "Give Discord Orb": {"filename": "apply_discord.png", "threshold": .9, "points": 20, "type": 0},
    }
}

def save_to_file():
    save_dict = deepcopy(config)
    del save_dict["regions"]
    for det in save_dict["detectables"].values():
        for field in list(det.keys()):
            if (field not in ["points", "type"]):
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