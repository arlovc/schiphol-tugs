#4 tabs

#1 the Map of Schiphol with the Greenzone overlaid (shapely file), with the option to look at all trajectories coming from a specific airline, or handled by a specific handling company, day of the week or during specific hours (slider)
#Here we will display only the location with the maximum difference in time.

#2 stats about the length of the taxiing until tug decoupling. One is the overall average, having barplots with Quantiles. The second container has individuallineplots with 1std(or just average) per airlines and handlers (and gate?), with days (hours) as X-axis. 

#3 totol percentage of tugs pushback outside vs inside the greenzone (per handling agent, per airline) : circular or barplot? Also in time

#4
#sankey : handlers with airlines
#sankey: handlers with gates

#preprocessing

#removing ground handlers from the dataset
#adding time difference, identify maximum
#calculate length until the identified maximum
#adding gate and handlers to the dataframe
#

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
#from streamlit_folium import folium_static
import geopandas as gpd
from shapely import Polygon, Point
from shapely import wkt
import matplotlib.colors as cm
import matplotlib.pyplot as plt
import altair as alt
#import plotly.express as px

#########################################

st.set_page_config (layout="wide")
@st.cache_resource
def read_data():
    
    """reads data, loads green zone, intersects trajectories with Green Zone"""
    
    df = pd.read_csv('transformed_data.csv',index_col=False)
    
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs='epsg:4326')
    airlines = sorted(gdf['airline'].unique().tolist())
    handlers = sorted(gdf['handler'].unique().tolist())
    
    
    return gdf,airlines,handlers

def load_greenzone(fg_everything):
    
    
    map_center = [52.308056, 4.764167]  # Latitude, Longitude of Schiphol Airport
    map_zoom = 13  # Adjust the zoom level as needed
    m = folium.Map(location=map_center, zoom_start=map_zoom)
    
    #load the green_zone
    green_gpd = gpd.read_file('greenzone.geojson')
    green_gpd.crs = 4326
    #extract it
    green_zone = green_gpd['geometry'][0]

    #rebuild (switch lat with lon)
    green_zone_coords =  list(zip(green_zone.boundary.coords.xy[1],green_zone.boundary.coords.xy[0]))
    green_polygon = folium.Polygon(locations=green_zone_coords, color='green', fill=True, fill_color='yellow')
    fg_everything.add_child(green_polygon)
    
    return m,fg_everything

#

@st.cache_resource
def gen_color_gradient(n):
    
    #generate colors
    list_of_colors=list()
    
    for i in range (0,n):
        color = list(np.random.choice(range(256), size=3))
        if color not in list_of_colors:
            color = "#{0:02x}{1:02x}{2:02x}".format(int(color[1]), int(color[1]), int(color[2]))
            list_of_colors.append(color)

        
    return list_of_colors

#

@st.cache_resource
def gen_colors_tab():
    
    colors = [cm.to_hex(plt.cm.tab20(i)) for i in range(20)]
    #choice = np.random.choice(range(20), size=1)
    
    return colors

####################################################################################################################################
##### MAIN ####
st.header('Schiphol Green Zone Monitoring Dashboard')

df,airlines,handlers = read_data()
    
#tabs
tab1, tab2, tab3, tab4 = st.tabs(["Map", "Airline", "Handler","Airport"])


########################### TAB 1 ####################################
with tab1:
    
    st.header('Map')
    ######## Sidebar filters ##############
    
    airline_filter = st.sidebar.multiselect("Airline",airlines)
    hour_filter = st.sidebar.select_slider("Hour", list(range(0,24)),(0,23))
    gate_filter = st.sidebar.multiselect("Gate",list(range(1,61)),list(range(1,10)))
    pier_filter = st.sidebar.multiselect("Pier",['A','B','C','D','E','F'],['A','B','C','D','E','F'])
    handler_filter = st.sidebar.multiselect("Handler", handlers,handlers[0:5])
    full_traj_filter = st.sidebar.radio('Trajectory type',['Full','Decoupling','Heat'],index=0)
    #green_zone_filter = st.sidebar.checkbox("Green Zone")        
    green_zone_filter=True
    
    ######## loading the map ##############
    fg_everything = folium.FeatureGroup(name='Everything')
    m,fg_everything = load_greenzone(fg_everything)
    
    
    ######### Filter data based on user inputs #############
    filtered_data = df.copy()
    airline_mask = df.airline.isin(airline_filter)
    hour_mask = df.hour.isin(hour_filter) #not used
    gate_mask = df.gate.isin(gate_filter)
    pier_mask = df.pier.isin(pier_filter)
    handler_mask = df.handler.isin(handler_filter)
    
    #st.write(airline_mask)
    filter_df = df[airline_mask&gate_mask&pier_mask&handler_mask]
    #st.write(filter_df)
    
    #grouping per airline
    groups = filter_df.groupby('airline')
    
    #get some colors
    colors = gen_colors_tab()

    #####choose display type
    if full_traj_filter=='Full':
            
        for (key, group), color in zip(groups,colors):
            
            for i, row in group.iterrows():

                #add feature groups based on the airline. Add points of a certain color to the group, and add the group to the map. 
                list_of_points = np.dstack(row['geometry'].coords.xy).tolist()[0]

                #add the trajectory per airline
                for points in list_of_points:
                    
                    point = folium.CircleMarker(
                        location=points,
                        radius=1.7,
                        color=color,
                        fill=True,
                        fill_color=None,
                        fill_opacity=0.2,
                    )
                    fg_everything.add_child(point)
            
        out = st_folium(m,
            feature_group_to_add=fg_everything,
            #center=map_center,
            width=1200,
            height=900,)
    
    elif full_traj_filter=='Decoupling':   
    #just show the decoupling location, coloured by airline, size relative to the time it spent there
        
        for (key, group), color in zip(groups,colors):

            for i, row in group.iterrows():
                #st.write(row)
                point = folium.CircleMarker(
                    location=np.dstack(wkt.loads(row['decoup']).coords.xy)[0], #TODO we are doing the reverse operation from the preprocessing.... Make sure to optimize this later
                    radius=1*row['max_time']/500,
                    color=color,
                    fill=True,
                    fill_color=None,
                    fill_opacity=0.2,
                    tooltip = str(round(row['max_time'])) + ' s'
                )
                fg_everything.add_child(point)
        
        out = st_folium(m,feature_group_to_add=fg_everything,width=1200,height=700,)

    else:    
        st.write('Heatmap To be developed')

########################### TAB 2 ####################################

with tab2:
    st.header('Airlines')
    st.write("")
    #st.write(filter_df.columns.tolist())
    col1, col2, col3 = st.columns([0.35,0.35,0.3],gap='small')
    
        
    airline_df = df[airline_mask]

    average_distance = airline_df.groupby(['airline','day'])['length'].mean()
    std_distance = airline_df.groupby(['airline','day'])['length'].std()
    #st.write(std_distance)

    for airline in airline_filter:
    
        with col1:

                plot_df=pd.DataFrame()
                plot_df['average_distance'] = average_distance[airline].values
                plot_df['average_std1'] = average_distance[airline].values - std_distance[airline].values
                plot_df['average_std2'] = average_distance[airline].values + std_distance[airline].values
                plot_df.reset_index(inplace=True)
    #             st.write('Airline: ', airline)
    #             chart = st.line_chart(data=plot_df,
    #                                   y = ['average_distance','average_std1','average_std2'],
    #                                   color=['#00ff00',"#FF0000","#FF0000"],
    #                                   height=250,  
    #                                   use_container_width=True)

                chart = (
                        alt.Chart(
                            data=plot_df,
                            title='Airline: '+airline,
                        )
                        .mark_line()
                        .encode(
                            x=alt.X("index", axis=alt.Axis(title="Days")),
                            y=alt.Y("average_distance", axis=alt.Axis(title="Average Distance[km]")),
                        )
                )

                st.altair_chart(chart,use_container_width=True)



        with col2:   

#             nr_flights = airline_df.groupby(['airline','day'])['length'].count()

#             plot_df=pd.DataFrame()
#             plot_df['aantal'] = nr_flights[airline].values
#             plot_df.reset_index(inplace=True)

#             chart = (
#                     alt.Chart(
#                         data=plot_df,
#                         title=' ',
#                     )
#                     .mark_line()
#                     .encode(
#                         x=alt.X("index", axis=alt.Axis(title="Days")),
#                         y=alt.Y("aantal", axis=alt.Axis(title="Aantal dagelijkse vluchten")),
#                     )
#             )

#             st.altair_chart(chart,use_container_width=True)
            
            #or instead of flights, we could do something like daily counts of in/out of the greenzone
            #st.write(airline_df.head())
            
            daily_green = airline_df.groupby(['airline','day'])['green'].sum().get(airline)
            daily_green_not = airline_df.groupby(['airline','day'])['green'].count().get(airline) - daily_green
            daily_green = daily_green.reset_index(drop=False)
            daily_green_not = daily_green_not.reset_index(drop=False)
            daily_green_not.name = 'green_not'
            daily_green_not.loc[:,'Waar?'] = ['Buiten']*len(daily_green_not)
            daily_green.loc[:,'Waar?'] = ['Binnen']*len(daily_green_not)
            #daily_green.loc['tekst'] = ['Binnen Green Zone']*len(daily_green)
            daily_green = pd.concat([daily_green,daily_green_not])
            
            
            chart = alt.Chart(
                        data = daily_green,
                        title = 'Dagelijkse bewegingen',
                        ).mark_bar(size=10).encode(
                x='day',
                y='green',
                color='Waar?',
            )
            st.altair_chart(chart,use_container_width=True)
            
        with col3:
            
            airline_group = airline_df[airline_df['airline']==airline]
            green_df = pd.DataFrame(columns = ['Legenda', 'value'])
            green_df.loc[:,'Legenda'] =['Binnen Groene Zone','Buiten Groene Zone'] 
            green_df.loc[:,'value'] =[airline_group.green.sum(), len(airline_group) - airline_group.green.sum()]
            
            #make the chart
            chart = alt.Chart(data = green_df,
                             title = 'Totaal Aantal').mark_arc(innerRadius=45).encode(
                color='Legenda',
                theta='value'
            ).properties(
                height = 350,
                width = 450
            )
            
            st.altair_chart(chart,use_container_width=True)

############################ HANDLERS ########################################

with tab3:
    st.header('Handler')
    st.write("")
    col1, col2, col3 = st.columns([0.35,0.35,0.3],gap='small')
    
        
    handler_df = df[handler_mask]

    average_distance = handler_df.groupby(['handler','day'])['length'].mean()
    std_distance = handler_df.groupby(['handler','day'])['length'].std()
    
    for handler in handler_filter:
    
        with col1:

                plot_df=pd.DataFrame()
                plot_df['average_distance'] = average_distance[handler].values
                plot_df['average_std1'] = average_distance[handler].values - std_distance[handler].values
                plot_df['average_std2'] = average_distance[handler].values + std_distance[handler].values
                plot_df.reset_index(inplace=True)
    #             st.write('Airline: ', airline)
    #             chart = st.line_chart(data=plot_df,
    #                                   y = ['average_distance','average_std1','average_std2'],
    #                                   color=['#00ff00',"#FF0000","#FF0000"],
    #                                   height=250,  
    #                                   use_container_width=True)

                chart = (
                        alt.Chart(
                            data=plot_df,
                            title='Handler: '+handler,
                        )
                        .mark_line()
                        .encode(
                            x=alt.X("index", axis=alt.Axis(title="Days")),
                            y=alt.Y("average_distance", axis=alt.Axis(title="Average Distance[km]")),
                        )
                )

                st.altair_chart(chart,use_container_width=True)

        with col2:   

#             nr_flights = handler_df.groupby(['handler','day'])['length'].count()

#             plot_df=pd.DataFrame()
#             plot_df['aantal'] = nr_flights[handler].values
#             plot_df.reset_index(inplace=True)

#             chart = (
#                     alt.Chart(
#                         data=plot_df,
#                         title=' ',
#                     )
#                     .mark_line()
#                     .encode(
#                         x=alt.X("index", axis=alt.Axis(title="Days")),
#                         y=alt.Y("aantal", axis=alt.Axis(title="Aantal dagelijkse vluchten")),
#                     )
#             )

#             st.altair_chart(chart,use_container_width=True)
            
            #or instead of flights, we could do something like daily counts of in/out of the greenzone
            #st.write(airline_df.head())
            
            daily_green = handler_df.groupby(['handler','day'])['green'].sum().get(handler)
            daily_green_not = handler_df.groupby(['handler','day'])['green'].count().get(handler) - daily_green
            daily_green = daily_green.reset_index(drop=False)
            daily_green_not = daily_green_not.reset_index(drop=False)
            daily_green_not.name = 'green_not'
            daily_green_not.loc[:,'Waar?'] = ['Buiten']*len(daily_green_not)
            daily_green.loc[:,'Waar?'] = ['Binnen']*len(daily_green_not)
            #daily_green.loc['tekst'] = ['Binnen Green Zone']*len(daily_green)
            daily_green = pd.concat([daily_green,daily_green_not])
            
            chart = alt.Chart(
                        data = daily_green,
                        title = 'Dagelijkse bewegingen',
                        ).mark_bar(size=10).encode(
                x='day',
                y='green',
                color='Waar?',
            )
            st.altair_chart(chart,use_container_width=True)
            
        with col3:
            
            handler_group = handler_df[handler_df['handler']==handler]
            #st.write(handler_group)
            green_df = pd.DataFrame(columns = ['Legenda', 'value'])
            green_df.loc[:,'Legenda'] =['Binnen Groene Zone','Buiten Groene Zone'] 
            green_df.loc[:,'value'] =[handler_group.green.sum(), len(handler_group) - handler_group.green.sum()]
            
            #make the chart
            chart = alt.Chart(data = green_df,
                             title = 'Totaal Aantal').mark_arc(innerRadius=45).encode(
                color='Legenda',
                theta='value'
            ).properties(
                height = 350,
                width = 450
            )
            
            st.altair_chart(chart,use_container_width=True)
    
    
    
    
with tab4:
    st.header('Airport')



# # Second tab: Airlines
# def show_airlines():
#     st.subheader("Airlines")
    
#     # Group data by airline and calculate average distance per airline
#     airline_avg_distance = df.groupby('airline')['distance'].mean()
    
#     # Bar chart for average distance
#     st.bar_chart(airline_avg_distance)
    
#     # Bar chart for green zone
#     st.bar_chart(df['green_zone'].value_counts())

# # Main Streamlit app
# def main():
#     st.title("Flight Data Analysis App")
    
#     # Create tabs
#     tabs = ["Map", "Airlines"]
#     selected_tab = st.radio("Select a tab:", tabs)
    
#     if selected_tab == "Map":
#         show_map()
#     elif selected_tab == "Airlines":
#         show_airlines()
