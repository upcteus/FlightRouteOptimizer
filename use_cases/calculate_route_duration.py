def convert_duration_to_minutes(duration):
    if isinstance(duration, str):
        hours = 0
        minutes = 0
        if 'H' in duration:
            hours = int(duration.split('H')[0].replace('PT', ''))
            if 'M' in duration:
                minutes = int(duration.split('H')[1].replace('M', ''))
        elif 'M' in duration:
            minutes = int(duration.replace('PT', '').replace('M', ''))
        return hours * 60 + minutes
    elif isinstance(duration, int):
        return duration
    else:
        return 0
