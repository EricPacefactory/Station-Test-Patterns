

#%% Imports

import argparse
import cv2
import numpy as np

from itertools import cycle

from utils.timers import Square_Wave_Timer
from utils.video_recorder import Video_Recorder
from utils.frame_makers import make_blank_frame, make_noise3ch_frame, make_blurred_noise3ch_frame, make_color_frame, \
                               add_gradient_noise

#%% Parse script args

# Create the parser
ap = argparse.ArgumentParser(description="View/create station test pattern video")

# Add the arguments
default_length = 5
default_output = "cycle_mosaic_1.mp4"
ap.add_argument("-r", "--record", action = "store_true", help = "Enable video recording")
ap.add_argument("-c", "--codec", type = str, help = "Manually set the recorded video codec (e.g. 'avc1', 'XVID', 'MJPG')")
ap.add_argument("-l", "--length_mins", type = float, default = 5, help = "Recorded video length in minutes (default is {})".format(default_length))
ap.add_argument("-o", "--output", type = str, default = "cycle_mosaic_1.mp4", help = "Output save path/name (default is '{}')".format(default_output))

# Execute the parse_args() method
ap_result = ap.parse_args()

# For convenience
ARG_ENABLE_RECORD = ap_result.record
ARG_CODEC = ap_result.codec
ARG_LENGTH_MINS = ap_result.length_mins
ARG_OUTPUT = ap_result.output


#%% Output config

# Hard-coded output formatting
frame_width = 300
video_fps = 30.0


#%% Recording config

# Set up video recording, in case recording is enabled
vwrite = Video_Recorder(ARG_OUTPUT, video_fps, enabled = ARG_ENABLE_RECORD, codec = ARG_CODEC)

# Some user feedback
if ARG_ENABLE_RECORD:
    print("",
          "Recording video (codec: {})".format(vwrite.get_codec()),
          "@ {}".format(vwrite.get_save_path()), sep = "\n")


#%% Config for display areas

# Create blank frame for text drawing
text_width = int(round(frame_width / 4))
text_height = 50
text_wh = (text_width, text_height)
text_blank = make_blank_frame(*text_wh)

# Specify where to place text (relative to text_blank frame)
text_frame_scaling = np.float32((text_width - 1, text_height - 1))
text_xy_norm = (0.1, 0.75)
text_position = tuple(np.int32(np.round(text_frame_scaling * text_xy_norm)))

# All text uses a lot of the same config...
high_contrast_config = {"color": (255,255,255)}
low_contrast_config = {"color": (50,50,50)}
shared_font_config = {
        "fontFace": cv2.FONT_HERSHEY_PLAIN, "fontScale": 2.25, "thickness": 3,\
        "lineType": cv2.LINE_AA, "org": text_position
}

text_1sec_config = {**shared_font_config, **high_contrast_config, "text": "1s"}
text_1sec_low_contrast_config = {**text_1sec_config, **low_contrast_config}

text_5sec_config = {**shared_font_config, **high_contrast_config, "text": "5s"}
text_5sec_low_contrast_config = {**text_5sec_config, **low_contrast_config}

text_15sec_config = {**shared_font_config, **high_contrast_config, "text": "15s"}
text_15sec_low_contrast_config = {**text_15sec_config, **low_contrast_config}

text_60sec_config = {**shared_font_config, **high_contrast_config, "text": "60s"}
text_60sec_low_contrast_config = {**text_60sec_config, **low_contrast_config}

# Continuous noise config
cont_noise_width = frame_width
cont_noise_height = 50
cont_noise_wh = (cont_noise_width, cont_noise_height)
continuous_noise = make_noise3ch_frame(*cont_noise_wh)

# Blinking noise config
blink_noise_width = frame_width
blink_noise_height = 50
blink_noise_wh = (blink_noise_width, blink_noise_height)
blink_noise = make_noise3ch_frame(*blink_noise_wh)

# Create fast scrolling pattern
fast_scroll_width = frame_width
fast_scroll_height = 15
fast_scroll_x_idx = np.linspace(0, 1, frame_width)#np.arange(fast_scroll_width)
fast_scroll_one_row = 255 * (np.sin(2*np.pi*fast_scroll_x_idx/np.linspace(0.01, 0.05, frame_width)) > 0)
fast_scroll_bar = np.rollaxis(np.tile(fast_scroll_one_row, (3, fast_scroll_height, 1)), 2, 1).T
fast_scroll_bar = np.uint8(fast_scroll_bar)
fast_scroll_noisy = add_gradient_noise(fast_scroll_bar)

# Create medium scrolling pattern
medium_scroll_width = frame_width
medium_scroll_height = 15
medium_scroll_x_idx = np.arange(medium_scroll_width)
medium_scroll_one_row = 255 * (np.sin(2*np.pi*fast_scroll_x_idx/np.linspace(0.02, 0.1, frame_width)) > 0)
medium_scroll_bar = np.rollaxis(np.tile(medium_scroll_one_row, (3, medium_scroll_height, 1)), 2, 1).T
medium_scroll_bar = np.uint8(medium_scroll_bar)
medium_scroll_noisy = add_gradient_noise(medium_scroll_bar)

# Create slow scrolling pattern
slow_scroll_width = frame_width
slow_scroll_height = 15
slow_scroll_x_idx = np.arange(slow_scroll_width)
slow_scroll_one_row = 255 * (np.sin(2*np.pi*fast_scroll_x_idx/np.linspace(0.05, 0.2, frame_width)) > 0)
slow_scroll_bar = np.rollaxis(np.tile(slow_scroll_one_row, (3, slow_scroll_height, 1)), 2, 1).T
slow_scroll_bar = np.uint8(slow_scroll_bar)
slow_scroll_noisy = add_gradient_noise(slow_scroll_bar)

# Create blank starter frame for figure-8 circle pattern
fig8_width = frame_width
fig8_height = 50
fig8_half_height = int(fig8_height / 2)
figure_8_circle_blank = make_blank_frame(fig8_width, fig8_height)

# Define figure-8 helpers
circle_rad = 6
x_freq = 1.0 / 4.0
y_freq = 2 * x_freq
twopi = 2 * np.pi
sin01 = lambda t, freq: (1 + np.sin(twopi * t * freq)) / 2
get_circle_x = lambda t: int(circle_rad + (fig8_width - (2 * circle_rad)) * sin01(t, x_freq))
get_circle_y = lambda t: int(circle_rad + (fig8_height - (2 * circle_rad)) * sin01(t, y_freq))

# Create color cycling pattern
color_width = int(frame_width / 4)
color_height = 50
color_wh = (color_width, color_height)
primary_bgrs = cycle([(0, 0, 255), (0, 255, 0), (255, 0, 0)])
secondary_bgrs = cycle([(0, 255, 255), (255, 0, 255), (255, 255, 0)])
saturation_bgrs = cycle([(125,125,125), (94, 120, 156), (62, 115, 187), (31, 109, 219), (0, 104, 250)])
brightness_bgrs = cycle([[value] * 3 for value in [0, 50, 100, 150, 200, 250]])
primary_frame = make_color_frame(next(primary_bgrs), *color_wh)
secondary_frame = make_color_frame(next(secondary_bgrs), *color_wh)
saturation_frame = make_color_frame(next(saturation_bgrs), *color_wh)
brightness_frame = make_color_frame(next(brightness_bgrs), *color_wh)


#%% Draw frames

# Timer for handling periodic changes to image
timer = Square_Wave_Timer()

# *** Video loop ***
total_frames = int(round(video_fps * ARG_LENGTH_MINS * 60))
for k in range(total_frames):
    
    # Update toggle timers
    curr_time_sec = k / video_fps
    timer.update(curr_time_sec)
    
    # Draw blinking text
    text_1s_high_contrast = make_blank_frame(*text_wh)
    text_1s_low_contrast = make_blank_frame(*text_wh)
    if timer.is_high(1):
        cv2.putText(text_1s_high_contrast, **text_1sec_config)
        cv2.putText(text_1s_low_contrast, **text_1sec_low_contrast_config)
        
    text_5s_high_contrast = make_blank_frame(*text_wh)
    text_5s_low_contrast = make_blank_frame(*text_wh)
    if timer.is_high(5):
        cv2.putText(text_5s_high_contrast, **text_5sec_config)
        cv2.putText(text_5s_low_contrast, **text_5sec_low_contrast_config)
    
    text_15s_high_contrast = make_blank_frame(*text_wh)
    text_15s_low_contrast = make_blank_frame(*text_wh)
    if timer.is_high(15):
        cv2.putText(text_15s_high_contrast, **text_15sec_config)
        cv2.putText(text_15s_low_contrast, **text_15sec_low_contrast_config)
    
    text_60s_high_contrast = make_blank_frame(*text_wh)
    text_60s_low_contrast = make_blank_frame(*text_wh)
    if timer.is_high(60):
        cv2.putText(text_60s_high_contrast, **text_60sec_config)
        cv2.putText(text_60s_low_contrast, **text_60sec_low_contrast_config)
    
    # Draw all text combined in a single row
    high_contrast_text = np.hstack([text_1s_high_contrast, text_5s_high_contrast, text_15s_high_contrast, text_60s_high_contrast])
    low_contrast_text = np.hstack([text_1s_low_contrast, text_5s_low_contrast, text_15s_low_contrast, text_60s_low_contrast])
    
    # Draw figure-8 circle
    figure_8_circle = figure_8_circle_blank.copy()
    circle_xy = (get_circle_x(curr_time_sec), get_circle_y(curr_time_sec))
    cv2.circle(figure_8_circle, circle_xy, circle_rad, (255, 255, 255), -1, cv2.LINE_AA)
    figure_8_circle[fig8_half_height:, :] = add_gradient_noise(figure_8_circle[fig8_half_height:, :])
    
    # Update fast scrolling bar
    fast_scroll_bar = np.roll(fast_scroll_bar, 1, axis = 1)
    fast_scroll_noisy = add_gradient_noise(fast_scroll_bar)
    
    # Update medium scrolling bar
    if timer.is_rising(0.25):
        medium_scroll_bar = np.roll(medium_scroll_bar, 1, axis = 1)
    medium_scroll_noisy = add_gradient_noise(medium_scroll_bar)
    
    # Update slow scrolling bar
    if timer.is_rising(0.5):
        slow_scroll_bar = np.roll(slow_scroll_bar, 1, axis = 1)
    slow_scroll_noisy = add_gradient_noise(slow_scroll_bar)
    
    # Draw color cycling
    if timer.is_falling(4):
        primary_frame = make_color_frame(next(primary_bgrs), *color_wh)
        secondary_frame = make_color_frame(next(secondary_bgrs), *color_wh)        
    if timer.is_rising(2):
        saturation_frame = make_color_frame(next(saturation_bgrs), *color_wh)    
    if timer.is_falling(1):
        brightness_frame = make_color_frame(next(brightness_bgrs), *color_wh)    
    color_frames = (primary_frame, secondary_frame, saturation_frame, brightness_frame)
    noisy_colors = [add_gradient_noise(frame) for frame in color_frames]
    color_frames = np.hstack(noisy_colors)
    
    # Update blink noise 
    if timer.is_falling(8):
        blink_noise = make_noise3ch_frame(*blink_noise_wh)
        
    # Update continuouse noise every frame
    continuous_noise = make_blurred_noise3ch_frame(*cont_noise_wh, 5)
    continuous_noise = cv2.addWeighted(continuous_noise, 1.0, high_contrast_text, 0.1, 0)
    
    # Build final display by stacking rows of images
    display_frame = np.vstack((
            high_contrast_text,
            low_contrast_text,
            figure_8_circle,
            fast_scroll_noisy,
            medium_scroll_noisy,
            slow_scroll_noisy,
            color_frames,
            blink_noise,
            continuous_noise))
    
    # Show frame for reference
    cv2.imshow("Display", display_frame)
    keypress = cv2.waitKey(1)
    if keypress == 27:
        break
    
    # Record if needed
    vwrite.write(display_frame)


# Clean up
vwrite.release()
cv2.destroyAllWindows()