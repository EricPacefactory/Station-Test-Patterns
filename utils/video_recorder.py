
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
    
    def __init__(self, save_path, recording_fps = 30.0, timelapse_factor = 1.0, enabled = True, codec = None):
        
        # Store inputs
        self._input_save_path = os.path.abspath(save_path)
        self.recording_fps = float(recording_fps)
        self.tl_factor = float(timelapse_factor)
        self._enabled = enabled
        self._codec = codec
        
        # Allocate variables for recording
        self._vwriter = None
        self._write_wh = None
        self._actual_ext = None
        self._actual_save_path = None
        
        # Pre-determine whether we're timelapsing for convenience
        self._tl_increment = 1.0 / max(1.0, timelapse_factor)
        self._tl_count = 1.0
        self._tl_enabled = (timelapse_factor - 1.0 > 0.01)
        
        # Timelapse factors less than 1 aren't supported (requires duplicating frames)
        timelapse_below_1 = (timelapse_factor < 0.99999)
        if timelapse_below_1:
            raise ValueError("Cannot set timelapse factor below 1!")
        
        # Set up video encoding settings
        self._figure_out_encoding()
    
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
    
    def get_save_path(self):
        
        ''' Provides 'actual' save path (after accounting for codec/extension compatibility) '''
        
        if not self._enabled or self._actual_save_path is None:
            return "None"
        
        return self._actual_save_path
    
    # .................................................................................................................
    
    def get_codec(self):
        
        ''' Provides codec selected for recording '''
        
        if self._codec is None:
            return "None"
        
        return self._codec
    
    # .................................................................................................................

    def release(self):
        
        '''
        Close the video writer. This is important for getting correctly formatted video files!
        Returns:
            Nothing
        '''
        
        if self._vwriter is not None:
            self._vwriter.release()
            
            # Sanity check, make sure a file was saved & isn't empty
            error_with_saved_file = True
            if os.path.exists(self._actual_save_path):
                SIZE_500_BYTES = 500
                error_with_saved_file = (os.path.getsize(self._actual_save_path) < SIZE_500_BYTES)
            
            # Warning for user if something went wrong
            if error_with_saved_file:
                print("",
                      "WARNING:",
                      "Recorded video file may be corrupted!",
                      "This can be caused by bad codec/file extension settings",
                      "      Codec used: {}".format(self._codec),
                      "  Extension used: {}".format(self._actual_ext), sep = "\n")
        
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
            
            # Create a video writer & write the frame again (No error handling this time, but hopefully we're ok...)
            self._vwriter = self._create_video_writer(frame.shape)
            self._vwriter.write(frame)
            frame_was_written = True
        
        return frame_was_written
    
    # .................................................................................................................
    
    def _figure_out_encoding(self):
        
        ''' Helper function used to determine video valid codec/extension combo & adjust save naming accordingly '''
        
        # Don't bother with config if recording isn't enabled
        if not self._enabled:
            return
        
        # Break up save name, since we may need to modify the extension
        save_folder = os.path.dirname(self._input_save_path)
        orig_full_name = os.path.basename(self._input_save_path)
        name_only, orig_ext = os.path.splitext(orig_full_name)
        
        # Auto-determine the saving format if needed
        actual_ext = orig_ext.replace(".", "")
        if self._codec is None:
            encode_ok, actual_codec, actual_ext = find_valid_recording_parameters(actual_ext)
            if not encode_ok:
                raise IOError("Bad codec/extension! Cannot record video")
        else:
            # Make sure codec is 4 character, since 'fourcc' setting requires characters
            actual_codec = str(self._codec)
            codec_is_4_characters = len(actual_codec) == 4
            if not codec_is_4_characters:
                raise ValueError("Invalid codec! Must be 4 characters, got: {}".format(actual_codec))
        
        # Re-write the save pathing, in case the extension changed
        save_full_name = "{}.{}".format(name_only, actual_ext)
        save_path = os.path.join(save_folder, save_full_name)
        
        # Store codec/ext and final pathing for reference
        self._codec = actual_codec
        self._actual_ext = actual_ext
        self._actual_save_path = save_path
        
        return
    
    # .................................................................................................................
    
    def _create_video_writer(self, frame_shape):
        
        # Some sanity checks
        if frame_shape is None:
            raise AttributeError("Recording frame size not set!")
        if self.recording_fps is None:
            raise AttributeError("Recording frame rate not set!")
        
        # Store sizing info for reference
        write_h, write_w = frame_shape[0:2]
        self._write_wh = (write_w, write_h)
        
        # Make sure the folder we're saving to actually exists!
        save_folder = os.path.dirname(self._actual_save_path)
        os.makedirs(save_folder, exist_ok = True)
        
        # Create OCV video writer, assume frame data is color (even when grayscale, which seems to be less buggy)
        is_color = True
        fourcc = cv2.VideoWriter_fourcc(*self._codec)
        new_vwriter = cv2.VideoWriter(self._actual_save_path,
                                      fourcc,
                                      self.recording_fps,
                                      self._write_wh,
                                      is_color)
        
        return new_vwriter
    
    # .................................................................................................................
    # .................................................................................................................


#%% Functions

def find_valid_recording_parameters(preferred_ext = None):
    
    # Hard-code the list of codec/extensions to test
    codecs_list = ["avc1", "XVID", "MJPG"]
    exts_list = ["mp4", "mkv", "avi"]
    
    # Place user-provided ext at top of exts-list
    valid_user_ext = (preferred_ext is not None) and (preferred_ext != "")
    if valid_user_ext:
        preferred_ext = preferred_ext.replace(".", "")
        if preferred_ext in exts_list:
            exts_list.remove(preferred_ext)
        exts_list.insert(0, preferred_ext)
    
    # Hard-code some recording settings
    is_color = True
    fps = 30.0
    frame_wh = (8, 8)
    num_frames = 5
    
    # Create a dummy frame to record
    dummy_frame = np.random.randint(0, 255, (frame_wh[1], frame_wh[0], 3), dtype = np.uint8)
    
    # Initialize outputs
    good_codec_str = None
    good_ext = None
    
    # Test recording of codec/ext pairs in a temporary folder until we find one that works
    codec_ext_pairs = product(codecs_list, exts_list)
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
    output_ok = (good_codec_str is not None) and (good_ext is not None)
    
    return output_ok, good_codec_str, good_ext


#%% Demo

if __name__ == "__main__":
    pass
