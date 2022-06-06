# Station Test Patterns

Scripts for creating example videos to help test out station data capture & analysis (for use with SCV2 realtime system).

## Usage

Install the library requirements using:

```bash
pip install -r requirements.txt
```

Then run the example generator using:

```bash
python create_cycle_mosaic_1.py -r
```

The `-r` flag is optional and signals that the result should be recorded (i.e. a video file will be generated), leaving this flag out will allow you to view the video without actually recording it.

Other flags exist: run the script with the `-h` flag to view the other options.



## Examples

Below are screenshots from the output generated videos, along with brief explanations of what is included in the pattern (currently only 1 pattern, but more should be added eventually!).

#### Cycle Mosaic 1

<img title="" src="file:///home/wrk/Desktop/video_activity/station_example_video_creator/screenshots/cycle_mosaic_1.jpg" alt="example image" data-align="center">

Example of *cycle mosaic 1*, which is geared towards blinking/cycling types of station patterns. It includes text patterns (1s, 5s, 15s, 60s) which blink with a period corresponding to the text (for example the 1s text toggles on/off every 0.5 seconds so that the *total* period is 1 second). There are also noisy black and white patterns as well as color cycling patterns.



## TODOs

- Add idle-like patterns

- Add more motion-based patterns

- Add flickering effects to patterns
