import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime as dt

def getOptionsFromParams():
    defaults = {}
    if 'num_races' in st.query_params.keys() and st.query_params['num_races'].isnumeric() and 2 <= int(st.query_params['num_races']) <= 5:
        defaults['num_races'] = int(st.query_params['num_races'])
    else:
        defaults['num_races'] = 3

    return defaults

### Distance in meters, time in seconds
def equivalentRaceTime(originalDistance, targetDistance, time):
    return time * pow((targetDistance / originalDistance), 1.06)
    
def convertSecondsToTime(seconds, showHours=True):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int((seconds % 3600) % 60)
    if hours > 0 or showHours:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

def convertTimeToSeconds(ts):
    return (ts.hour * 60 + ts.minute) * 60 + ts.second

def convertTimeStringToSeconds(t):
    if t is None:
        return None
    else:
        parts = t.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return 123


def getAllTimes():
    timeValues = []
    for h in range(0, 9):
        for m in range(0,60):
            for s in range(0,60):
                if h == 0:
                    t = f"{m:02}:{s:02}"
                else:
                    t = f"{h:02}:{m:02}:{s:02}"

                timeValues.append(t)
    return timeValues

def getPaceSeries(t, distance, distances, unit):
    times = [(equivalentRaceTime(distance, d, t) / d * 1000) for d in distances]
    if unit == 0:
        times = [t * 1.609 for t in times]
    return times

def getComparison(paces):
    comparison = paces.copy().iloc[[-1]]
    for c in comparison.columns[1:]:
        comparison[c] = comparison[c].dt.strftime('%H:%M:%S')
        comparison[c] = comparison[c].apply(lambda x: convertTimeStringToSeconds(x))
    # comparison = comparison.to_dict(orient='records')[0]
    comparison['Best'] = comparison.iloc[:,1:].idxmin(axis=1)
    comparison['Worst'] = comparison.iloc[:,1:-1].idxmax(axis=1)
    comparison['Difference'] = (comparison[comparison['Worst'].iloc[0]] - comparison[comparison['Best'].iloc[0]]) / comparison[comparison['Best'].iloc[0]]
    comparison = comparison.to_dict(orient='records')[0]
    comparison['Category'] = 'Normal' if comparison['Difference'] < 0.025 else 'Medium' if comparison['Difference'] < 0.05 else 'Large'

    return comparison

allDistances = {
    1500 : '1500m',
    1600 : '1600m',
    1609 : 'Mile',
    3200 : '3200m',
    3218 : '2 Mile',
    5000 : '5k',
    10000 : '10k',
    21097.5 : 'Half Marathon',
    16090 : '10 Mile',
    42195 : 'Marathon'
}

defaultDistances = {2 : [5, 9],
                    3 : [2, 5, 9],
                    4 : [2, 5, 7, 9],
                    5 : [2, 5, 6, 7, 9]}

unitMap = {
    0 : 'mi',
    1 : 'km'
}

allTimes = getAllTimes()

defaultOptions = getOptionsFromParams()

##### Heading #####
st.title(":woman-running: Compare Race Paces :man-running:")

##### Settings Panel #####
with st.expander(':gear: Modify Settings'):
    col1, col2, col3 = st.columns(3)

    pacesToCalculate = col1.multiselect('Select race paces to calculate:',
                                        options=allDistances.keys(),
                                        key='distances',
                                        default=[1609,5000,10000,21097.5,42195],
                                        format_func=lambda d:allDistances[d])

    numRaces = col2.pills("Number of Race Results:",
                            options=[2,3,4,5],
                            key='numRaces',
                            selection_mode='single',
                            default=defaultOptions['num_races'])

    unit = col3.pills("Unit for Paces:",
                        options=unitMap.keys(),
                        format_func=lambda u:unitMap[u],
                        selection_mode='single',
                        default=0)
##### End Settings Panel #####

##### Intialize Data #####
distances = {d : allDistances[d] for d in pacesToCalculate}
defaults = defaultDistances[numRaces]
paces = pd.DataFrame({'Distance' : distances.values()})
##### End Initializing #####

##### Race Times Panel #####
with st.expander(':stopwatch: Race Times'):
    for i in range(0, numRaces):
        col1, col2 = st.columns(2)
        d = col1.selectbox('Race Distance',
                        options=allDistances,
                        key=f'd{i}',
                        index=defaults[i],
                        format_func=lambda d:allDistances[d])
        t = col2.selectbox('Race Time:',
                     allTimes,
                     key=f't{i}',
                     index=None,
                     placeholder='mm:ss or hh:mm:ss')

        if t:
            paces[allDistances[d]] = getPaceSeries(convertTimeStringToSeconds(t), d, distances.keys(), unit)
            paces[allDistances[d]] = pd.to_datetime(paces[allDistances[d]], unit='s')
##### End Race Times Panel #####


##### Graph Race Paces #####
data = paces.melt(id_vars=paces.columns[0], value_vars=paces.columns[1:], value_name='Pace', var_name='Race')
c = (
    alt.Chart(data)
        .mark_line(point=True)
        .encode(x=alt.X('Distance:N', sort=distances.values()),
            y=alt.Y('Pace:T', timeUnit='minutesseconds'),
            color='Race:N')
)

st.altair_chart(c, use_container_width=True)
##### End Graph #####

##### Start Explanation #####
if len(paces.columns) > 2:
    comparison = getComparison(paces)
    st.write(f"Your best relative race effort is in the {comparison['Best']}.")
    st.write(f"Your worst relative race effort is in the {comparison['Worst']}.")
    st.write(f"The difference is paces is {comparison['Difference']:.1%}. This is a {comparison['Category']} difference.")
##### End Explanation #####