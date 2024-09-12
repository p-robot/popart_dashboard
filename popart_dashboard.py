"""
App to plot output data from the PoPART-IBM model

Author: p-robot


TO DO
- put on github
- [x] plot additional variables
- [x] expand/collapse figures
- [x] use tabs (for figure or data)
- [x] add some top-line metrics to the outputs (country, community)
- add observed data
- deploy online
- run model online and populate this in real-time
- workflow for running with multiple output files (parquet files?)
- default plotting routines for all file types and all columns
- add PC time periods (How?)
- add routines for showing calibration output
- fix commas in the thousands spot (Stackoverflow?)
"""

import streamlit as st
import pandas as pd
from os.path import join
import os

plotting_dict = {
    'Incidence': {'name': 'HIV incidence',
                  'var': ['Incidence'],
                  'col': '#D55E00'},
    'NewCasesThisYear': {'name': 'New HIV infections',
                         'var': ['NewCasesThisYear'],
                         'col': '#D55E00'},
    'Prevalence': {'name': 'HIV prevalence',
                   'var': ['Prevalence'],
                   'col': '#D55E00'},
    'PLHIV': {'name': 'Number of people living with HIV', 
              'var': ['NumberPositiveM', 'NumberPositiveF', 'NumberPositive'],
              'col': ["#D55E00", "#0072B2", "#009E73"]},
    'HIVDeaths': {'name': 'HIV-related deaths', 
              'var': ['NDied_from_HIV', 'NHIV_pos_dead'],
              'col': ["#D55E00", "#0072B2"]},
}

output_dir="/Users/willprobert/Projects/POPART-IBM_p-robot/examples/PARAMS_COMMUNITY5/Output"

# List all files in the output directory
all_files = sorted(os.listdir(output_dir))
popart_files = [f for f in all_files if ".csv" in f]

st.title("Output from POPART-IBM")
st.markdown("""PopART-IBM is an individual-based model for simulating HIV epidemics
            in high-prevalence settings, as used in the 
            [HPTN 071 (PopART) trial](https://www.hptn.org/research/studies/hptn-071).
            POPART-IBM source code is available [here](https://github.com/p-robot/POPART-IBM)""")

st.divider()

# File selection
option = st.selectbox("Filename", 
                      popart_files,
                      placeholder="PopART-IBM output file ..." )

#st.subheader("Simulation details")
c1, c2, c3 = st.columns(3)
c1.metric("Country", "Zambia")
c2.metric("Community", "5")
c3.metric("Trial arm", "A")

year_range = st.sidebar.slider("Period to show", 1970, 2030, (1990, 2030))

# Variables to display
vars_to_plot = st.sidebar.multiselect("Variables", 
    plotting_dict.keys(),
    default = ['Incidence', 'NewCasesThisYear', 'PLHIV'])

outside_patch_on = st.sidebar.toggle("Overlay surrounding area")
observed_on = st.sidebar.toggle("Overlay observed data")
# Not supported - base line charts do not have vertical lines
#pc_ribbon_on = st.sidebar.toggle("PC time periods")

st.divider()

# Read data
df = pd.read_csv(join(output_dir, option))

# Read the outside patch
df_outside = pd.read_csv(join(output_dir, 
    "Annual_outputs_CL04_Za_C_V1.2_patch1_Rand10_Run1_PCseed0_0_CF.csv"))

# import altair as alt
# st.header("HIV incidence with Altair chart")
# chart = (alt.Chart(df_plot).mark_line(color="blue").encode(
#     x=alt.X('Year', axis=alt.Axis(format=',.0f')),
#     y='Incidence'
# ))
# st.altair_chart(chart, use_container_width=True)

df_plot = df[(df.Year>=year_range[0]) & (df.Year<=year_range[1])]

if outside_patch_on:
    df_outside = df_outside[(df_outside.Year>=year_range[0]) & (df_outside.Year<=year_range[1])]

st.subheader("HIV indicators in 2030 (trial community)")
c4, c5, c6 = st.columns(3)
inc_inside = round(df_plot.Incidence.max()*100, 2)
plhiv_inside = df_plot.NumberPositive.max().astype(int)
pop_inside = df_plot.TotalPopulation.max().astype(int)
c4.metric("Incidence (%)", inc_inside)
c5.metric("PLHIV", plhiv_inside)
c6.metric("Pop. size", pop_inside)

if outside_patch_on:
    st.subheader("HIV indicators in 2030 (surrounding area)")
    c4, c5, c6 = st.columns(3)
    inc_outside = round(df_outside.Incidence.max()*100, 2)
    plhiv_outside = df_outside.NumberPositive.max().astype(int)
    pop_outside = df_outside.TotalPopulation.max().astype(int)

    c4.metric("Incidence (%)", inc_outside, delta = round(inc_outside - inc_inside, 2))
    c5.metric("PLHIV", plhiv_outside, delta = int(plhiv_outside - plhiv_inside))
    c6.metric("Pop. size", pop_outside, delta = int(pop_outside - pop_inside))

# Plot HIV indicators and show data in secondary tab
st.header("HIV indicators")
for var in vars_to_plot:
    with st.expander(plotting_dict[var]['name'], expanded = True):
        tab1, tab2 = st.tabs(["Figure", "Data"])
        tab1.header(plotting_dict[var]['name'])
        tab1.line_chart(data = df_plot,
            x = 'Year',
            y = plotting_dict[var]['var'],
            color = plotting_dict[var]['col'])
        with tab2:
            st.header(plotting_dict[var]['name'])
            st.dataframe(df_plot[['Year']+ plotting_dict[var]['var']], 
                         hide_index=True)

st.header("Community demographics")
with st.expander("Total population size"):
    st.header("Total population size")
    st.line_chart(data = df_plot,
        x = 'Year',
        y = ['TotalPopulation', 'PopulationF', 'PopulationM'],
        color = ["#D55E00", "#0072B2", "#009E73"])

with st.expander("Total deaths"):
    st.header("Total deaths")
    st.line_chart(data = df_plot,
        x = 'Year',
        y = 'N_dead',
        color = ["#D55E00"])
