


#%% Imports



#%% Classes

class Square_Wave_Timer:
    
    '''
    Helper timer which can be used to check toggle states & whether a toggle occurred for periodic timers
    Usage:
        timer.update(current_time_seconds) # Call this to indicate the current 'global' time
        if timer.is_falling(period_sec = 5):
            # do something every 5 seconds
        if timer.is_high(period_sec = 3):
            # do something that lasts 1.5 seconds and repeats every 3 seconds
    '''
    
    def __init__(self):
        self._timers = {}
        self._curr_time_sec = None
    
    def update(self, curr_time_sec):
        self._curr_time_sec = curr_time_sec
        for each_timer in self._timers.values():
            each_timer.update_timer(curr_time_sec)        
        return
    
    def is_high(self, period_sec):
        self._create_missing_timer(period_sec)
        return self._timers[period_sec].is_high()
    
    def is_rising(self, period_sec):
        self._create_missing_timer(period_sec)
        return self._timers[period_sec].is_rising()
    
    def is_falling(self, period_sec):
        self._create_missing_timer(period_sec)
        return self._timers[period_sec].is_falling()
    
    def _create_missing_timer(self, period_sec):
        if period_sec not in self._timers.keys():
            self._timers[period_sec] = self._Single_Square_Wave_Timer(period_sec, self._curr_time_sec)
        return
    
    
    class _Single_Square_Wave_Timer:
        
        ''' Subclass which handles timing of a specific period. Feels hacky to make classes-in-classes... '''
        
        def __init__(self, period_sec, curr_time_sec):
            self._toggle_period_sec = period_sec / 2.0
            self._next_toggle_time = None
            self._toggle_state = False
            self._is_rising = False
            self._is_falling = False
            self.update_timer(curr_time_sec)
        
        def update_timer(self, curr_time_sec):
            
            # Set initial state
            if self._next_toggle_time is None:
                self._set_next_toggle_time(curr_time_sec)
            
            # Toggle each time we pass the next toggle time
            self._is_rising = False
            self._is_falling = False
            changed_this_frame = (curr_time_sec > self._next_toggle_time)
            if changed_this_frame:
                self._toggle_state = not self._toggle_state
                self._is_rising = self._toggle_state
                self._is_falling = not self._is_rising
                self._set_next_toggle_time()
            
            return self._toggle_state
        
        def is_high(self):
            return self._toggle_state
        
        def is_rising(self):
            return self._is_rising
        
        def is_falling(self):
            return self._is_falling
            
        def _set_next_toggle_time(self, curr_time_sec = None):
            
            if curr_time_sec is None:
                curr_time_sec = self._next_toggle_time
            self._next_toggle_time = curr_time_sec + self._toggle_period_sec
            
            return


#%% Functions


#%% Demo

if __name__ == "__main__":
    
    print("", "Example 10 second period timer:", sep = "\n")
    demo_timer_1 = Square_Wave_Timer()
    for time_sec in range(17):
        demo_timer_1.update(time_sec)
        time_str = "{:.0f}s".format(time_sec)
        if demo_timer_1.is_rising(10):
            print("  {} rising".format(time_str))
        if demo_timer_1.is_falling(10):
            print("  {} falling".format(time_str))
        if demo_timer_1.is_high(10):
            print("{} high".format(time_str))
        if not demo_timer_1.is_high(10):
            print("{} low".format(time_str))

    print("", "Example of 2 & 4 second timers simultaneously:", sep = "\n")
    demo_timer_2 = Square_Wave_Timer()
    for time_sec in range(20):
        for small_offset in [-0.01, 0.01]:
            offset_time_sec = time_sec + small_offset
            demo_timer_2.update(offset_time_sec)
            time_str = "{:.2f}s".format(offset_time_sec)
            if demo_timer_2.is_falling(2):
                print("{} 2sec timer is falling".format(time_str))
            if demo_timer_2.is_falling(4):
                print("  {} 4sec timer is falling".format(time_str))
