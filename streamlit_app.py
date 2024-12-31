import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime as dt

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

def getPaceSeries(t, distance, distances, unit):
    times = [(equivalentRaceTime(distance, d, t) / d * 1000) for d in distances]
    if unit == 0:
        times = [t * 1.609 for t in times]
    return times

allDistances = {
    1500 : '1500m',
    1600 : '1600m',
    1609 : 'Mile',
    3200 : '3200m',
    3218 : '2 Mile',
    5000 : '5k',
    10000 : '10k',
    21097.5 : 'HM',
    16090 : '10 Mile',
    42195 : 'FM'
}

unitMap = {
    0 : 'mi',
    1 : 'km'
}

##### Heading #####
st.title("Compare Race Paces :man-running:")

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
                            default=3)

    unit = col3.pills("Unit for Paces:",
                        options=unitMap.keys(),
                        format_func=lambda u:unitMap[u],
                        selection_mode='single',
                        default=0)
##### End Settings Panel #####

##### Intialize Data #####
distances = {d : allDistances[d] for d in pacesToCalculate}
paces = pd.DataFrame({'Distance' : distances.values()})
##### End Initializing #####

##### Race Times Panel #####
for i in range(0, numRaces):
    
    col1, col2 = st.columns(2)
    d = col1.selectbox("Race Distance",
                     options=allDistances,
                     key=f'd{i}',
                     format_func=lambda d:allDistances[d])
    t = col2.time_input("Race Time:", key=f't{i}', value=None, step=60)
    if t:
        paces[allDistances[d]] = getPaceSeries(convertTimeToSeconds(t), d, distances.keys(), unit)
        paces[allDistances[d]] = pd.to_datetime(paces[allDistances[d]], unit='s')
        # paces[allDistances[d]] = pd.to_datetime(paces[allDistances[d]], unit='s').dt.strftime('%M:%S')
##### End Race Times Panel #####


# st.write(paces)

data = paces.melt(id_vars=paces.columns[0], value_vars=paces.columns[1:], value_name='Pace', var_name='Race')
c = (
    alt.Chart(data)
        .mark_line(point=True)
        .encode(x=alt.X('Distance:N', sort=distances.values()),
            y=alt.Y('Pace:T', timeUnit='minutesseconds'),
            color='Race:N')
)

st.altair_chart(c, use_container_width=True)
