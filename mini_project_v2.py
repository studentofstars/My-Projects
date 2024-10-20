# -*- coding: utf-8 -*-
"""Mini Project v2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19L9AxfCyKScvGqW-KczRBgjRoYJqHhIg
"""

import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from astropy.constants import G
from astropy import units as u
from astropy.time import Time
import matplotlib.pyplot as plt
from poliastro.plotting.static import StaticOrbitPlotter
from poliastro.bodies import Sun, Earth, Jupiter
from poliastro.twobody import Orbit

# Step 1: Fetch Exoplanet Data from NASA Exoplanet Archive
@st.cache_data
def fetch_exoplanet_data(limit=10000):
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    query = f"""
    SELECT TOP {limit}
        pl_name,
        hostname,
        pl_bmasse,
        pl_orbper,
        pl_orbsmax,
        pl_orbeccen,
        st_mass
    FROM
        ps
    WHERE
        pl_bmasse > 0 AND
        pl_orbper > 0 AND
        pl_orbsmax > 0 AND
        st_mass > 0
    ORDER BY
        pl_orbper ASC
    """
    params = {
        "query": query,
        "format": "json"
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        return df
    else:
        st.error("Error fetching data from NASA Exoplanet Archive.")
        return None

# Step 2: Calculate Radial Velocity Amplitude (K)
def calculate_radial_velocity(planet_mass, star_mass, orbital_period, eccentricity=0):
    planet_mass = planet_mass * u.M_earth  # Planet mass in Earth masses
    star_mass = star_mass * u.M_sun        # Star mass in Solar masses
    orbital_period = orbital_period * u.day # Orbital period in days

    orbital_period = orbital_period.to(u.second)  # Convert orbital period to seconds
    G_const = G.value  # Gravitational constant (m^3 kg^-1 s^-2)

    planet_mass_kg = planet_mass.to(u.kg).value  # Convert planet mass to kg
    star_mass_kg = star_mass.to(u.kg).value      # Convert star mass to kg

    # Calculate radial velocity amplitude (K) in m/s
    K = ((2 * np.pi * G_const) / orbital_period.value)**(1/3) * (planet_mass_kg) / (star_mass_kg**(2/3)) / np.sqrt(1 - eccentricity**2)
    return K  # in m/s


# Step 3: Generate Radial Velocity Curve
def generate_radial_velocity_curve(K, P, time_span):
    time = np.linspace(0, time_span, 1000)  # Time points (days)
    velocity = K * np.sin(2 * np.pi * time / P)  # Radial velocity at each time point
    return time, velocity

# Step 4: Streamlit App Setup
st.title("Exoplanet Detection Simulation")

# Add tabs for different visualizations
tab1, tab2, tab3, tab4 = st.tabs(["Radial Velocity Curves", "Planet Details", "3D Orbits", "Real-Time Data"])
#Sidebar for Tab 1
with st.sidebar:
    st.header("Adjust Filter Parameters")
    st.markdown(" Set your parameters to filter out the curves ")
    dataset_count = st.number_input('Enter the number of datasets to import:', min_value=1, max_value=10000, value=10)

    df = fetch_exoplanet_data(limit=dataset_count)
    if df is not None:
        df = df.dropna(subset=['pl_bmasse', 'pl_orbper', 'pl_orbsmax', 'pl_orbeccen', 'st_mass'])
    # Filter options
    min_mass = st.slider('Select minimum planet mass (Earth Masses)', min_value=float(df['pl_bmasse'].min()), max_value=float(df['pl_bmasse'].max()), value=float(df['pl_bmasse'].min()))
    max_mass = st.slider('Select maximum planet mass (Earth Masses)', min_value=min_mass, max_value=float(df['pl_bmasse'].max()), value=float(df['pl_bmasse'].max()))
    min_period = st.slider('Select minimum orbital period (days)', min_value=float(df['pl_orbper'].min()), max_value=float(df['pl_orbper'].max()), value=float(df['pl_orbper'].min()))
    max_period = st.slider('Select maximum orbital period (days)', min_value=min_period, max_value=float(df['pl_orbper'].max()), value=float(df['pl_orbper'].max()))
    # Slider for eccentricity
    eccentricity = st.slider('Eccentricity', min_value=0.0, max_value=1.0, step=0.01, value=0.0)
    st.write("©Mrutyunjaya Muduli") 

    
with tab1:
    st.header("Radial Velocity Method")

    # Brief explanation of the Radial Velocity Method
    st.markdown("""
    The **Radial Velocity Method** is used to detect exoplanets by observing the wobble of stars due to gravitational pulls from orbiting planets. 
    This method helps determine important parameters such as the mass of the planet, its orbital period, and the distance from the star.
    The data for this graph is fetched directly from the NASA Exoplanet Archive in real time and is processed to generate the plots as shown.
    The radial velocity curves represent the variations in the star's radial velocity caused by the gravitational influence of an orbiting exoplanet.
    """)
   
    if df is not None:
        filtered_df = df[(df['pl_bmasse'] >= min_mass) & (df['pl_bmasse'] <= max_mass) & (df['pl_orbper'] >= min_period) & (df['pl_orbper'] <= max_period)]

        if filtered_df.empty:
            st.write("No planets match your filters!")
        else:
            fig = go.Figure()

            for index, planet in filtered_df.iterrows():
                planet_name = planet['pl_name']
                star_name = planet['hostname']
                planet_mass = planet['pl_bmasse']
                orbital_period = planet['pl_orbper']
                star_mass = planet['st_mass']

                # Calculate radial velocity amplitude
                K = calculate_radial_velocity(planet_mass, star_mass, orbital_period, eccentricity)

                # Generate radial velocity curve
                time_span = orbital_period * 2
                time, velocity = generate_radial_velocity_curve(K, orbital_period, time_span)

                # Add the curve to the Plotly figure
                fig.add_trace(go.Scatter(x=time, y=velocity, mode='lines', name=f'{planet_name} ({star_name})'))

            fig.update_layout(title='Radial Velocity Curves', xaxis_title='Time (days)', yaxis_title='Radial Velocity (m/s)')
            st.plotly_chart(fig)

    st.subheader("Key Formulas Used")

    # Formula for Radial Velocity Amplitude (K)
    st.markdown("""
    The radial velocity amplitude (K) can be calculated using the formula:
    
    $$K = \\frac{2 \\pi G}{P} \\cdot \\frac{M_p}{M_*^{2/3}} \\cdot \\frac{1}{\\sqrt{1 - e^2}}$$
    
    where:
    - \(K\) = Radial velocity amplitude (m/s)
    - \(G\) = Gravitational constant ($$(6.67430 \\cdot 10^{-11} \, m^3 \, kg^{-1} \, s^{-2})$$)
    - \(P\) = Orbital period (in seconds)
    - \(M_p\) = Mass of the planet (in kg)
    - \(M_*\) = Mass of the star (in kg)
    - \(e\) = Eccentricity of the orbit (dimensionless)
    """)

    # Explanation of each parameter
    st.write("### Significance of Parameters:")
    st.write("""
    - **Radial Velocity Amplitude (K)**: Represents the maximum velocity of the star as it wobbles due to the gravitational influence of the planet.
    - **Orbital Period (P)**: The time taken by the planet to complete one orbit around the star.
    - **Mass of the Planet (M_p)**: The mass of the exoplanet, which influences the gravitational pull it exerts on the star.
    - **Mass of the Star (M_*)**: The mass of the host star, which also affects the radial velocity measurements.
    - **Eccentricity (e)**: A measure of how elliptical the orbit is, affecting the shape of the velocity curve.
    """)


with tab2:
    st.header("Planet Details")
    st.markdown("""
    This section displays details about the exoplanets, including:
    - **pl_name**: Name of the exoplanet
    - **hostname**: Host star name
    - **pl_bmasse**: Mass of the planet (in Earth masses)
    - **pl_orbper**: Orbital period (in days)
    - **pl_orbsmax**: Semi-major axis (in AU)
    - **st_mass**: Mass of the host star (in Solar masses)
    """)
    if df is not None:
        st.write("Displaying detailed information about planets:")
        st.dataframe(df[['pl_name', 'hostname', 'pl_bmasse', 'pl_orbper', 'pl_orbsmax', 'st_mass']])

with tab3:
    st.header("3D Visualization of Planetary Orbits")
    st.markdown("""
    The 3D plot now simulates the stellar wobble due to the gravitational pull of orbiting planets. Choose a star from the dataset to visualize the simulation.
    """)
    
    # Let the user select a star
    selected_star = st.selectbox("Select a star to simulate", df['hostname'].unique())
    
    # Get the planet(s) around the selected star
    star_planets = df[df['hostname'] == selected_star]
    
    # Check if there are planets for the selected star
    if star_planets.empty:
        st.write("No planets available for the selected star.")
    else:
        # Setting up simulation for each planet
        fig, ax = plt.subplots()
        plotter = StaticOrbitPlotter(ax)
        
        for _, planet in star_planets.iterrows():
            # Define the orbit of the planet (we use the semi-major axis and orbital period)
            planet_orbit = Orbit.from_classical(Sun, planet['pl_orbsmax'] * u.AU, 0 * u.one, 0 * u.deg, 0 * u.deg, 0 * u.deg, Time.now().tdb)
            
            # Plot planet's orbit
            plotter.plot(planet_orbit, label=planet['pl_name'])
        
        # Display plot
        st.pyplot(fig)
    #st.markdown("""
    #The 3D plot displays the relationship between the semi-major axis, orbital period, and planet mass of the detected exoplanets. 
    #This visualization helps in understanding how different planets interact with their host stars based on their distances and masses.
    #""")
    
    #if df is not None:
        #fig_3d = px.scatter_3d(df, x='pl_orbsmax', y='pl_orbper', z='pl_bmasse', color='pl_name',
                               #labels={'pl_orbsmax': 'Semi-major Axis (AU)', 'pl_orbper': 'Orbital Period (days)', 'pl_bmasse': 'Planet Mass (Earth Masses)'})
        #fig_3d.update_layout(title="Interactive visualization of Planetary Orbits")
        #st.plotly_chart(fig_3d)

with tab4:
    st.header("Real-Time Data Updates")
    st.markdown(""" The **Refresh Data** allows users to fetch the most up-to-date exoplanet data from the NASA Exoplanet Archive. """) 
    if st.button('Refresh Data'):
        df = fetch_exoplanet_data(limit=dataset_count)
        st.write("Data refreshed successfully!")
        st.dataframe(df[['pl_name', 'hostname', 'pl_bmasse', 'pl_orbper', 'pl_orbsmax', 'st_mass']])
    st.subheader (" Radial Velocity Method Explanation Video ")    
    st.video("https://youtu.be/rN7uuqLKv0I?si=L400cu8qcas3dVjU") 
    st.write("©Mrutyunjaya Muduli") 
        


