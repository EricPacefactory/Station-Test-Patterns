

#%% Imports

import cv2
import numpy as np


#%% Classes


#%% Functions

def make_blank_frame(width, height):
    return np.zeros((height, width, 3), dtype = np.uint8)

def make_noise3ch_frame(width, height):
    return np.random.randint(0, 255, (height, width, 3), dtype = np.uint8)

def make_blurred_noise3ch_frame(width, height, blurriness = 3):
    blur_kernel = (blurriness, blurriness)
    return cv2.blur(make_noise3ch_frame(width, height), ksize = blur_kernel, borderType = cv2.BORDER_REFLECT)

def make_color_frame(color_bgr, width, height):
    return np.full((height, width, 3), color_bgr, dtype = np.uint8)

def add_gradient_noise(frame):
    
    ''' Adds (blurred) grayscale noise that increases in intensity from left-to-right across the given frame '''
    
    frame_h, frame_w = frame.shape[0:2]
    
    noise_frame = cv2.cvtColor(make_blurred_noise3ch_frame(frame_w, frame_h, 3), cv2.COLOR_BGR2GRAY)
    gradient_1d = np.clip(np.linspace(-0.25, 1.25, frame_w), 0, 1)
    gradient_2d = np.tile(gradient_1d, (frame_h, 1))
    gradient_noise_frame = np.uint8(gradient_2d * noise_frame)
    gradient_noise_frame = cv2.cvtColor(gradient_noise_frame, cv2.COLOR_GRAY2BGR)
    
    return cv2.add(frame, gradient_noise_frame)


#%% Demo

if __name__ == "__main__":
    
    example_wh = (100, 100)
    red_bgr = (0, 0, 255)
    blue_bgr = (255, 0, 0)
    
    example_frames = [
            make_blank_frame(*example_wh),
            make_noise3ch_frame(*example_wh),
            make_blurred_noise3ch_frame(*example_wh),
            make_color_frame(red_bgr, *example_wh),
            add_gradient_noise(make_color_frame(blue_bgr, *example_wh))
    ]
    
    combined_image = np.hstack(example_frames)
    cv2.imshow("Examples", combined_image)
    cv2.waitKey(0);
    cv2.destroyAllWindows()
