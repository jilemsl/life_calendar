import pandas as pd
import numpy as np
import calplot
import matplotlib.pyplot as plt

def create_profile() : 
    """
    This function creates a dataset that contains daily information of the user
    Each activity of the dataset is a column and each row is a day. The user choses the variables.
    He can modify them later manually. Every cell is a float score between -10 and 10. 

    """

    name = input("What is your name? ")
    

    x = True

    activities = []

    while x :
        
        activity = input("What activity do you want to track? (Type 'done' when finished) ")
        if activity.lower() == 'done' :
            x = False

        else :
            activities.append(activity)

    columns = []
    for activity in activities :
        columns.append(f'{activity}_score')
        columns.append(f'{activity}_duration')


    df = pd.DataFrame(columns=columns)
    df['date'] = np.nan
    df['daily_score'] = np.nan


    df.to_csv(f'data/{name}_profile.csv')






def update_score(profile) :
    """
    This function updates the dataset with the daily scores of the user.

    """

    
    df = pd.read_csv(rf'data/{profile}_profile.csv')
    
    dict = {}

    dict['date'] = pd.to_datetime('today').strftime('%Y-%m-%d')

    var_list = []

    for variables in df.columns :

        if variables != 'date' and variables != 'daily_score':

            if variables.endswith('_score') :

                var_score = input(f"{variables} today : (0->10, 0->-10 or press enter to skip) ")

                if var_score != '' :

                    dict[variables] = float(var_score)
                    var_list.append(float(var_score))

                else:

                    dict[variables] = np.nan

            if variables.endswith('_duration') :

                var_duration = input(f"{variables} today : (in minutes or press enter to skip) ")

                if var_duration != '' :
                    dict[variables] = float(var_duration)

                else:
                    dict[variables] = np.nan
    
    score = daily_score(var_list)

    dict['daily_score'] = score

    df = pd.concat([df, pd.DataFrame(dict, index=[0])], ignore_index=True)
    df.to_csv(rf'data/{profile}_profile.csv', index=False)

    



def daily_score(var_list, alpha = 0.5) :
    """
    This function calculates a daily score based on the activities and their scores.

    """

    score = 0

    for elt in var_list :
        sign = np.sign(elt)
        score += sign * (abs(elt/10))**alpha / len(var_list)
 
    return max(0, score)



def plot_calendar_heatmap(profile, time_period=None, time_frame='daily'):
    """
    Plots a calendar heatmap of the daily scores from red to green.
    
    Args:
        profile: username string
        time_period: tuple of two pd.Timestamp (start, end), or None for all
        time_frame: 'daily', 'weekly', 'monthly', 'annually'
    """

    """
    Note : currently monthly and annually time frames are not plotting properly

    """

    df = pd.read_csv(rf'data/{profile}_profile.csv', parse_dates=['date'])
    df.set_index('date', inplace=True)
    df['daily_score'] = df['daily_score'].fillna(0)

    # Filter by time period
    if time_period is not None:
        start, end = time_period
        df = df.loc[start:end]

    # Resample by time_frame
    resample_map = {
        'daily':    'D',
        'weekly':   'W',
        'monthly':  'ME',
        'annually': 'YE'
    }
    freq = resample_map.get(time_frame, 'D')
    series = df['daily_score'].resample(freq).mean()

    calplot.calplot(
        series,
        cmap='RdYlGn',
        vmin=0,
        vmax=1,
        fillcolor='lightgrey',  # days with no data
        linewidth=0.5,
        figsize=(20, 10)
    )

    period_str = f"{time_period[0]} → {time_period[1]}" if time_period else "all time"
    plt.title(f"{profile}'s daily scores ({time_frame} | {period_str})", fontsize=20)
    plt.show()