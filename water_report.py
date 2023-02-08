from models import WaterUtility, Contaminant, ContaminantReading
import json
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from streamlit_extras.colored_header import colored_header
from annotated_text import annotated_text
from streamlit_lottie import st_lottie

def load_lottiefile(filepath: str):
    with open(filepath, 'r') as f:
        return json.load(f)

def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def img_to_html(img_path):
    img_html = "<a href='https://waterdoctorusa.com'><img src='data:image/png;base64,{}' width='50' class='img-fluid'></a>".format(
      img_to_bytes(img_path)
    )
    return img_html

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)




# -------- SETTINGS --------
vert_space = '<div style="padding: 10px 5px;"></div>'
territories = WaterUtility.get_all()
logo = 'https://lh4.googleusercontent.com/r_DvVzF2wmpBC3ZVQBlofpveBTkLTNPWE8RBFhQvSw571RLyf4e5i8fF6nYsnGY4mNM=w2400'
centered_logo = "<p style='text-align: center; color: grey;'>"+img_to_html('logo/logo.png')+"</p>"
by_wd = 'https://lh5.googleusercontent.com/V-DcILHJebKcQO9vRDkr45ALqKNYwfoutn-LOyS9Hcv1ysjetx3J7ltuQ2Ua3EEs53Q=w2400'
lottie = load_lottiefile('lottie/water_report.json')


# ------- PAGE CONFIG -------
st.set_page_config(
    page_title='Tap Water Data',
    page_icon='logo/logo.png',
    initial_sidebar_state='expanded',
)

# ----------------------------- FUNCTIONS -----------------------------
@st.experimental_memo
def get_contaminants(cont_list, count=1):
    count = count
    pfas = '(Forever Chemicals)'
    for each in cont_list:
        local_css("css/style.css")
        with st.expander(f"**{count}. {each.contaminant}** {pfas if each.contaminant.name in ['PFOS', 'PFOA'] else ''}"):
            #fig = gauge(each)
            #st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=":red[Highest Level Detected]", value=f"{each.max_reading if each.max_reading else each.perc} {each.contaminant.units}", delta=f"{'{:,.2f}'.format(float(each.factor))}x", delta_color='inverse')
            with col2:
                st.metric(label='EPA Health Goal', value=f'{each.mclg} {each.contaminant.units}', help='Level of a contaminant in drinking water below which there is no known or expected health risk')
            with col3:
                na = 'NA'
                empty= ''
                st.metric(label='Minimum Contaminant Level', value=f'{each.mcl if each.mcl else na} {each.contaminant.units if each.mcl else empty}', help='Level of a contaminant that Water Utilities cannot exceed')
            
            st.markdown(vert_space, unsafe_allow_html=True)
            annotated_text(('Source', f'{each.contaminant}','rgba(28, 131, 225, .33)'))
            st.write(f"{each.contaminant.source}")
            
            st.markdown(vert_space, unsafe_allow_html=True)
            annotated_text(('Health Risk', f'{each.contaminant}','rgba(28, 131, 225, .33)'))
            st.write(f"{each.contaminant.risk}")
            
            count += 1
            st.markdown(vert_space, unsafe_allow_html=True)

def gauge(each):
    each.max_reading = each.max_reading if each.max_reading else each.perc
    each.mcl = each.mcl if each.mcl else each.mclg
    max_gauge = [float(each.max_reading), float(each.mcl)]
    fig = go.Figure(go.Indicator(
        domain = {'x': [0, 1], 'y': [0, 1]},
        value = float(each.max_reading),
        mode = "gauge+number",
        title = {'text': f"Contaminant Reading for {each.contaminant.name}"},
        gauge = {'axis': {'range': [None, max(max_gauge)]},
                'steps' : [
                    {'range': [float(each.mclg), float(f'{each.mcl if each.mcl else each.mclg}')], 'color': "lightgray"},
                    {'range': [float(f'{each.mcl if each.mcl else each.mclg}'), max(max_gauge)], 'color': 'lightgray'}
                    ],
                'threshold' : {'line': {'color': "red", 'width': 6}, 'thickness': 0.8, 'value': float(each.mclg)}}))
    return fig

# -------------------------------- APP --------------------------------


# -------- WATER REPORT --------
st.markdown(centered_logo, unsafe_allow_html=True)
st.markdown(vert_space, unsafe_allow_html=True)

main_title = '<h1 style="text-align:center">Enter your zipcode</h1>'
st.markdown(main_title, unsafe_allow_html=True)
st.markdown(vert_space, unsafe_allow_html=True)
city_state_zip = st.selectbox('Enter your Zipcode', territories, label_visibility='collapsed')

if city_state_zip:
    
    wutility = WaterUtility.get_from_db(city_state_zip)
    st.title(f'Tap Water Report ({wutility.last_updated})')
    colored_header(
        label=f'*{city_state_zip}*',
        description=f'Data was sourced from the most recent Consumer Confidence Report (CCR) published by :blue[{wutility.name}] on {wutility.publish}. [Source]({wutility.pdf})',
        color_name='blue-70'
    )
    tab1, tab2 = st.tabs(['Report', 'More Info'])

    with tab1:
        readings = ContaminantReading.get_from_db(wutility)
        # Get top 5 contaminants
        primary_cont = WaterUtility.get_primary(readings)
        secondary_cont = WaterUtility.get_secondary(readings)
        
        # TODO: Also a clear label whether it's good, okay, or bad. Maybe a 5-star rating based on relative performance? or absolute performance?
        st.subheader('Water Aesthetics')
        col1, col2, col3 = st.columns(3)
        with col1:
            tds = secondary_cont['TDS']
            st.metric(label='TDS', value=tds.max, delta=f'{int(tds.max)-500}', delta_color='inverse', help='Total Dissolved Solids should be below **500** as recommended by EPA')
        with col2:
            hardness = secondary_cont['Hardness']
            st.metric(label='Hardness', value=hardness.max, delta=f'{int(hardness.max)-250}', delta_color='inverse', help='Hardness should be below **250** as recommended by EPA')
        with col3:
            ph = secondary_cont['pH']
            st.metric(label='pH', value=ph.max, help='pH levels should be between **6.5 - 8.5** as recommended by EPA')
        st.markdown(
            '''
            
            '''
        )
        st.caption(':blue[TDS] A measure of how much solid particles (dirt, sand, minerals, bacteria, etc.) are present in the water.')
        st.caption(':blue[Hardness] A measure of how much Magnesium and Calcium are present in the water. The white residue or spots that you see on your glassware is from hard water.')
        
        # TODO: Other secondary contaminants that have aesthetic effects on water
        '---'


        # -------- TOP 5 CONTAMINANTS --------
        st.header('Top 5 Contaminants Found in Your Water')

        get_contaminants(primary_cont[:5])
        
        placeholder = st.empty()
        # -------- SHOW REST OF THE LIST --------
        if placeholder.button('More...'):
            with placeholder.container():
                get_contaminants(primary_cont[5:], 6)
        
        '---'
        st.caption(":blue[Minimum Contaminant Level Goal (MCLG)] A measure set by the EPA based on health effects data, it's the maximum level of a contaminant in drinking water at which no known or anticipated adverse effect on the health of persons would occur, allowing an adequate margin of safety. Note: _MCLG_ and _MRDLG (Minimum Residual Disinfectant Level Goal)_ is used interchangeably in this report.")
        st.caption(":blue[Minimum Contaminant Level (MCL)] The maximum level allowed of a contaminant in water which is delivered to any user of a public water system strictly based on technical feasibility of treatment. Note: _MCL_ and _MRDL (Minimum Residual Disinfectant Level)_ is used interchangeably in this report.")
    
    # -------- ADDITIONAL INFO --------
    with tab2:

        # Water Supply
        st.subheader('Where does your water come from?')
        st.write(f'{wutility.supply}')

        # Treatment Process
        st.subheader('How your water is treated.')
        st.write(f'{wutility.treatment}')

# -------- LANDING PAGE --------
else:
    hero_message = "<p style='text-align: center; font-family: Source Sans Pro, sans-serif; color:Gray;'>The most <b>up-to-date</b> information you can find about your home's tap water.</p>"
    st.markdown(hero_message, unsafe_allow_html=True)
    st_lottie(lottie)
