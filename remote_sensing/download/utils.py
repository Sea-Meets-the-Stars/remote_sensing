""" Utility methods for downloads """

from datetime import datetime, timedelta, timezone

def find_startend_datetime(time_range:tuple=None, 
                           t_end:str=None, 
                           dt_past:dict=None): 

    # Times
    if time_range is None:
        if dt_past is None:
            dt_past = dict(days=1)
        if t_end is None:
            t_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Convert t_start to datetime
        dtend = datetime.strptime(t_end, "%Y-%m-%dT%H:%M:%SZ")
    
        start_datetime = dtend - timedelta(**dt_past)
        start_datetime = start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_datetime = t_end
    else:
        start_datetime, end_datetime = time_range

    # Return
    return start_datetime, end_datetime