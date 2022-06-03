
#%% Imports

import os
import cv2
import numpy as np

from itertools import product

from tempfile import TemporaryDirectory


#%%


class Video_Recorder:
    
    '''
    Convenience wrapper around OpenCV VideoWriter. Adds ability to enable/disable writer,
    timelapse recording (i.e. skip frames), auto frame sizing and auto codec/ext settings
    '''
    
    def __init__(self, save_path, recording_fps, timelapse_factor = 1.0, enabled = True):
        
        # Store inputs
        self._input_save_path = os.path.abspath(save_path)
        self.recording_fps = recording_fps
        self.tl_factor = timelapse_factor
        self._enabled = enabled
        
        # Allocate variables for recording
        self._vwriter = None
        self._write_wh = None
        self._save_codec = None
        self._save_ext = None
        self._actual_save_path = None
        
        # Pre-determine whether we're timelapsing for convenience
        self._tl_increment = 1.0 / max(1.0, timelapse_factor)
        self._tl_count = 1.0
        self._tl_enabled = (timelapse_factor - 1.0 > 0.01)
        
        # Timelapse factors less than 1 aren't supported (requires duplicating frames)
        timelapse_below_1 = (timelapse_factor < 0.99999)
        if timelapse_below_1:
            raise ValueError("Cannot set timelapse factor below 1!")
        
        pass
    
    # .................................................................................................................
    
    def is_open(self):
        
        '''
        Check if the video writer is currently open (and therefore actively able to write frames to disk)
        Returns:
            True/False
        '''
        
        if self._vwriter is None:
            return False
        
        return self._vwriter.isOpened()
    
    # .................................................................................................................
    
    def set_codec(self, codec_str):
        
        '''
        Allows for manually setting the desired recording codec. By default, the video writer will try to
        determine an appropriate codec, but this requires writing sample videos to test, it also
        dumps a lot of garbage warnings into the console. Using the function allows for skipping
        the auto-codec detection, assuming a good codec is already known!
        Note 1: An appropriate file extension must be given when setting up the writer (i.e. the save_path),
                not all extensions work with all codecs on all systems
        Note 2: By manually setting the codec, auto-codec detection is disabled, so there is no guarentee
                that the saved file will be valid!
        '''
        
        self._save_codec = codec_str
        
        return
    
    # .................................................................................................................

    def release(self):
        
        '''
        Close the video writer. This is important for getting correctly formatted video files!
        Returns:
            Nothing
        '''
        
        if self._vwriter is not None:
            self._vwriter.release()
            
            # Sanity check. Check if the saved file exists
            saved_file_exists = os.path.exists(self._actual_save_path)
            if not saved_file_exists:
                print("", "WARNING:",
                      "Recorded video file is missing!", sep = "\n")
            
            # Sanity check. Make sure the recorded file isn't empty
            saved_file_is_empty = os.path.getsize(self._actual_save_path) < 500
            if saved_file_is_empty:
                print("", "WARNING:",
                      "Recorded video file is empty, it may be corrupted!",
                      "This can be caused by bad codec/file extension settings",
                      "      Codec used: {}".format(self._save_codec), 
                      "  Extension used: {}".format(self._save_ext), sep = "\n")
        
        return
    
    # .................................................................................................................
    
    def write(self, frame):
        
        '''
        Records frame data as a video (if this writer is enabled).
        Inputs:
            frame: image data to be recorded (must be a consistently sized image!)
        
        Returns:
            True/False (True if the frame was written, False otherwise)
        '''
        
        # For clarity
        frame_was_written = False
        
        # Bail if recording is disabled
        if not self._enabled:
            return frame_was_written
        
        # Handle timelapsing if needed
        if self._tl_enabled:
            
            # Skip frames until we count to/over a full timelapsed cycle
            self._tl_count += self._tl_increment
            if self._tl_count < 1:
                return frame_was_written
            
            # Reset the timelapsed count for future iterations
            self._tl_count -= 1.0
        
        # Write the current frame
        try:
            self._vwriter.write(frame)
            frame_was_written = True
            
        except AttributeError:
            # Attribute error occurs when we haven't setup the vwriter yet (i.e. it is None)
            
            # Figure out the video frame sizing, based on the given frame shape
            frame_height, frame_width = frame.shape[0:2]
            self._write_wh = (frame_width, frame_height)
            
            # Create a video writer & write the frame again (No error handling this time, but hopefully we're ok...)
            self._vwriter = self._create_video_writer()
            self._vwriter.write(frame)
            frame_was_written = True
        
        return frame_was_written
    
    # .................................................................................................................
    
    def _create_video_writer(self):
        
        # Some sanity checks
        if self._write_wh is None:
            raise AttributeError("Recording frame size not set!")
        if self.recording_fps is None:
            raise AttributeError("Recording frame rate not set!")
        
        # Make sure the folder we're saving to actually exists!
        save_folder = os.path.dirname(self._input_save_path)
        os.makedirs(save_folder, exist_ok = True)
        
        # Break up save name, since we may need to modify the extension
        orig_full_name = os.path.basename(self._input_save_path)
        name_only, orig_ext = os.path.splitext(orig_full_name)
        
        # Auto-determine the saving format if needed
        save_codec = self._save_codec
        save_ext = orig_ext.replace(".", "")
        if save_codec is None:
            save_codec, save_ext = find_valid_recording_parameters()
        
        # Re-write the save pathing, in case the extension changed
        save_full_name = "{}.{}".format(name_only, save_ext)
        save_path = os.path.join(save_folder, save_full_name)
        
        # Create OCV video writer, assume frame data is color (even when grayscale, which seems to be less buggy)
        is_color = True
        fourcc = cv2.VideoWriter_fourcc(*save_codec)
        new_vwriter = cv2.VideoWriter(save_path,
                                      fourcc,
                                      self.recording_fps,
                                      self._write_wh,
                                      is_color)
        
        # Store codec/ext and final pathing for reference
        self._save_codec = save_codec
        self._save_ext = save_ext
        self._actual_save_path = save_path
        
        return new_vwriter
    
    # .................................................................................................................
    # .................................................................................................................


#%% Functions

def find_valid_recording_parameters():
    
    # Hard-code the list of codec/extensions to test
    codecs_list = ["avc1", "XVID", "MJPG"]
    exts_list = ["mp4", "mkv", "avi"]
    codec_ext_pairs = product(codecs_list, exts_list)
    
    # Hard-code some recording settings
    is_color = True
    fps = 30.0
    frame_wh = (8, 8)
    num_frames = 5
    
    # Create a dummy frame to record
    dummy_frame = np.random.randint(0, 255, (frame_wh[1], frame_wh[0], 3), dtype = np.uint8)
    
    # Create a temporary directory to dump test recording, so they get deleted when we're done
    good_codec_str = None
    good_ext = None
    with TemporaryDirectory() as temp_dir_path:
        
        # Loop through each codec/extension until we successfully create a file
        for each_codec_str, each_ext in codec_ext_pairs:
            
            # Build save pathing
            save_name = "{}.{}".format(each_codec_str, each_ext)
            save_path = os.path.join(temp_dir_path, save_name)
            
            # Create video writer & write dummy frames
            fourcc_int = cv2.VideoWriter_fourcc(*each_codec_str)
            vwriter = cv2.VideoWriter(save_path, fourcc_int, fps, frame_wh, is_color)
            for _ in range(num_frames):
                vwriter.write(dummy_frame)
            vwriter.release()
            
            # Make sure something was saved at least (existance doesn't guarentee validity though)
            file_exists = (os.path.exists(save_path))
            if not file_exists:
                continue
            
            # Bad codec/ext combinations create empty files
            nonzero_file_size = os.path.getsize(save_path) > 500
            if nonzero_file_size:
                good_codec_str = each_codec_str
                good_ext = each_ext
                break
    
    # Last check to make sure we got something useful
    no_good_data = (good_codec_str is None) or (good_ext is None)
    if no_good_data:
        raise IOError("No good codec/ext combination could be found for video recording!")
    
    return good_codec_str, good_ext


#%% Demo

if __name__ == "__main__":
    pass
