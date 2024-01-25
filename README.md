An application to controls sex toys based on Overwatch 2 gameplay. Here's a [list](https://iostindex.com/?filter0ButtplugSupport=4) of supported devices.

# Instructions:
- Install and run [Intiface Central](https://intiface.com/central/).
- Download and run [a release of Underwatch Ultimate](https://github.com/Furimanejo/Underwatch-Ultimate/releases).
- One the tab "Device Control" click connect to intiface. Make sure your toys are on and appear on the list of connected devices.
- Play Overwatch, you can test the app on the training range.

# Current Features:
The app mainteins a score and uses that score to control the connected toys accordingly. The score goes up when certain visual elements are detected on the screen and goes down gradually over time according to the "score decay" set.
 - Points Per Seconds/Points Over Duration: When the detecion occurs the selected amount of points are added to the score every second, or every X seconds for elements that present a fixed duration, like elimination popups (X=2.5s).
 - Momentary points: The selected amount of points is added to the score when the detection occurs and removed when the detection ends, not accumulating over time.

## Elements Detected:
- Popup of eliminations, assist, saves, eliminated(self).
- Applying Mercy's healing and boost, Zenyatta's harmony and discord orbs.
- Receiving Mercy's healing and boost, Zenyatta's harmony and discord orbs, Ana's healing buff and debuff, Baptiste's immortality field, and Sombra's Hacked.

# Observations:
- If you want to use the overlay, make sure your game is running in borderless display mode.
- The gameplay detection should work even with custom color schemes, let me know if it doesn't.
- Currently there's support for resolutions of 16:9 and 21:9 aspect ratios.
- For multiple monitors setups: you can change the montitor where the detection occurs by editing the variable "monitor_number" in the generated config file "config.json".

# Support:
Join my [discord server](https://discord.gg/wz2qvkuEyJ) if you have any questions, suggestions or just wanna talk about related stuff.

And if you liked the app and want to support me, you can donate at https://donate.stripe.com/7sI3eZcExdGrc5WeUU
