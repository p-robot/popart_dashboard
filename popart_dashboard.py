#!/usr/bin/env python3
"""
App to plot output data from the PoPART-IBM model

Author: p-robot
"""

import os
from os.path import join
import pandas as pd
import streamlit as st
import altair as alt

plotting_dict = {
    'Incidence': {'name': 'HIV incidence',
                  'var': 'Incidence',
                  'col': '#D55E00'},

    'NewCasesThisYear': {'name': 'New HIV infections',
                         'var': 'NewCasesThisYear',
                         'col': '#D55E00'},

    'Prevalence': {'name': 'HIV prevalence',
                   'var': 'Prevalence',
                   'col': '#D55E00'},

    'PLHIV': {'name': 'Number of people living with HIV', 
              'var': ['NumberPositiveM', 'NumberPositiveF', 'NumberPositive'],
              'codes': ['Men', 'Women', 'Total'],
              'col': ["#D55E00", "#0072B2", "#009E73"]},

    'HIVDeaths': {'name': 'HIV-related deaths', 
              'var': ['NDied_from_HIV', 'NHIV_pos_dead'],
              'codes': ['Deaths from HIV-related causes', 'Deaths of PLHIV'],
              'col': ["#D55E00", "#0072B2"]},
}

output_dir="data/examples"

# List all files in the output directory
all_files = sorted(os.listdir(output_dir))
popart_files = [f for f in all_files if ".csv" in f]

st.title("Output from POPART-IBM")
st.markdown("""PopART-IBM is an individual-based model for simulating HIV epidemics
            in high-prevalence settings, as used in the 
            [HPTN 071 (PopART) trial](https://www.hptn.org/research/studies/hptn-071).
            POPART-IBM source code is available [here](https://github.com/p-robot/POPART-IBM)""")

st.markdown("""All data within this dashboard is synthetic and does not represent real-world individuals.""")


with st.expander("What is HPTN071 (PopART)?", icon = ":material/add:"):
    st.write("""
HPTN071 (PopART) was a cluster randomised trial of 21 high prevalence communities in Zambia and South Africa that took place between 2013 and 2018.  Commonly referred to as the "PopART" trial.  

The trial was looking at the impact of a combination prevention package of different interventions
that included home-based HIV testing.  This home-based testing intervention was delivered by community healthcare workers called 
Community HIV Care Providers, or CHiPs for short.  The trial had three arms: arm A was a combination prevention intervention with universal 
ART), arm B was the combination prevention intervention with ART provided according to local guidelines and arm C was a control
 arm offering standard of care.  The main results of the HPTN071 (PopART) trial were published in 2019 in 
[Hayes et al., (2019)](https://www.nejm.org/doi/full/10.1056/NEJMoa1814556).  
Further details on the trial are published on the trial website: [HPTN 071 (PopART) trial](https://www.hptn.org/research/studies/hptn-071).
""")

with st.expander("What were the results of the HPTN071 (PopART) trial?", icon = ":material/add:"):
    st.write("""Results found the adjusted rate ratio of arm A compared with arm C was 0.93 (a 7% reduction in incidence) and 0.7 for arm B
compared with arm C (30% reduction in incidence).
    """)

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


def add_single_line_chart(data: pd.DataFrame, x: str, y: str, line_color: str) -> alt.Chart:
    """
    Create a line chart with one variable
    """
    output_chart = (alt.Chart(data).mark_line(color=line_color).encode(
                x=alt.X(x, axis=alt.Axis(format='.0f')),
                y = y)
                ).configure_legend(orient='bottom')
    return(output_chart)


def add_multiple_line_chart(data: pd.DataFrame, x: str, y: list, 
                            value_name: str, var_name: str, line_color: list,
                            codes: list) -> alt.Chart:
    """
    Create a line chart with multiple variables
    """
    # Reshape
    df_melt = data[[x]+y].melt(
        x,
        value_name = value_name,
        var_name = var_name)
    
    # Recode if needed
    df_melt[var_name].replace(dict(zip(y, codes)), inplace=True)

    col_var = alt.Color(var_name,
        scale=alt.Scale(
        domain=codes,
        range=line_color))
    
    chart = (alt.Chart(df_melt).mark_line().encode(
        x=alt.X(x, axis=alt.Axis(format='.0f')),
        y = value_name,
        color = col_var)
        ).configure_legend(orient='bottom')
    return(chart)


# Plot HIV indicators and show data in secondary tab
st.header("HIV indicators")
for var in vars_to_plot:
    # Create an expander
    with st.expander(plotting_dict[var]['name'], expanded = True):
        # Create two tabs
        #tab1, tab2 = st.tabs(["Figure", "Data"])
        st.header(plotting_dict[var]['name'])
        # Populate figure tab
        if isinstance(plotting_dict[var]['var'], list):
            chart = add_multiple_line_chart(df_plot,
                                            x = 'Year', 
                                            y = plotting_dict[var]['var'],
                                            value_name = 'Value',
                                            var_name = plotting_dict[var]['name'],
                                            line_color = plotting_dict[var]['col'],
                                            codes = plotting_dict[var]['codes'])
        else:
            chart = add_single_line_chart(data = df_plot, 
                                          x = 'Year', 
                                          y = plotting_dict[var]['var'], 
                                          line_color = plotting_dict[var]['col'])
        st.altair_chart(chart, use_container_width=True)
        # Populate table tab
        # with tab2:
        #     st.header(plotting_dict[var]['name'])
        #     st.dataframe(df_plot[['Year']+ plotting_dict[var]['var']], hide_index=True)

st.header("Community demographics")

# Reshape the data
df_pop = df_plot[['Year', 'TotalPopulation', 'PopulationF', 'PopulationM']].melt(
    'Year', value_name = "Population size", var_name = "Population")

# Recode the data
df_pop.Population.replace(
        {'TotalPopulation': 'Total', 
         'PopulationF': 'Female', 
         'PopulationM': 'Male'}, inplace=True)

with st.expander("Total population size"):
    st.header("Total population size")
    chart = add_multiple_line_chart(data = df_plot,
                                    x = 'Year',
                                    y = ['TotalPopulation', 'PopulationF', 'PopulationM'],
                                    codes = ['Total', 'Male', 'Female'],
                                    var_name = "Population",
                                    value_name = "Population size",
                                    line_color = ["#D55E00", "#0072B2", "#009E73"])
    st.altair_chart(chart, use_container_width=True)

with st.expander("Total deaths"):
    st.header("Total deaths")
    chart = add_single_line_chart(data = df_plot,
                                    x = 'Year',
                                    y = 'N_dead',
                                    line_color = "#D55E00")
    st.altair_chart(chart, use_container_width=True)

