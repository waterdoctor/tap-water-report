from models import WaterUtility, ContaminantReading, ZipRequest
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
    img_html = "<a href='https://waterdoctorusa.com/about'><img src='data:image/png;base64,{}' width='50' class='img-fluid'></a>".format(
      img_to_bytes(img_path)
    )
    return img_html

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ------- PAGE CONFIG -------
st.set_page_config(
    page_title='Tap Water Data',
    page_icon='logo/logo.png',
)

# -------- SETTINGS --------
vert_space = '<div style="padding: 10px 5px;"></div>'
territories = WaterUtility.get_all()
logo = 'https://lh4.googleusercontent.com/r_DvVzF2wmpBC3ZVQBlofpveBTkLTNPWE8RBFhQvSw571RLyf4e5i8fF6nYsnGY4mNM=w2400'
centered_logo = "<p style='text-align: center; color: grey;'>"+img_to_html('logo/logo.png')+"</p>"
by_wd = 'https://lh5.googleusercontent.com/V-DcILHJebKcQO9vRDkr45ALqKNYwfoutn-LOyS9Hcv1ysjetx3J7ltuQ2Ua3EEs53Q=w2400'
lottie = load_lottiefile('lottie/water_report.json')
# Removes border on all streamlit forms
css = r'''
        <style>
            [data-testid="stForm"] {border: 0px}
        </style>
    '''
st.markdown(css, unsafe_allow_html=True)




# ----------------------------- FUNCTIONS -----------------------------
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
            annotated_text(('Likely Sources', f'{each.contaminant}','rgba(28, 131, 225, .33)'))
            st.write(f"{each.contaminant.source}")
            
            st.markdown(vert_space, unsafe_allow_html=True)
            annotated_text(('Health Risks', f'{each.contaminant}','rgba(28, 131, 225, .33)'))
            st.write(f"{each.contaminant.risk}")
            
            st.markdown(vert_space, unsafe_allow_html=True)
            annotated_text(('Recommended Filtration Method', f'{each.contaminant}','rgba(28, 131, 225, .33)'))
            filter_list = each.contaminant.get_filter_rec()

            for f in filter_list:
                st.markdown(f'- {f}')
            
            count += 1
            st.markdown(vert_space, unsafe_allow_html=True)


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
    tab1, tab2, tab3 = st.tabs(['Report', 'Water Source', 'FAQs'])
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
        st.info(
            """
            The contaminants listed here is only a handful of contaminants found in your water.
            There's many more that go untested.
            """,
            icon='👀'
        )
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

        # two pie charts of contaminants exceeding health standards and mcl
        
        # Water Supply
        st.header('Where does your water come from?')
        st.write(f'{wutility.supply}')

        # Treatment Process
        st.subheader('How your water is treated.')
        st.write(f'{wutility.treatment}')
    
    with tab3:
        st.info(
            f"""
            All contaminants, public health goals and minimum contaminant level standards in this 
            report was sourced from the [EPA](https://www.epa.gov/ground-water-and-drinking-water/national-primary-drinking-water-regulations) 
            and the latest Consumer Confidence Report ([CCR]({wutility.pdf})) that your
            local water utility is required to publish annually.
            """,
            icon='📝'
        )
        st.header('Frequently Asked Questions')
        with st.expander('**How accurate and reliable are the reported figures?**'):
            st.markdown(
                """
                You can be confident in the reliability of the figures as they were obtained directly from your local water utility.

                However, it's important to note that the contents of your tap water may differ between households, even in close proximity. 
                While the figures presented here provide a solid foundation, for a more comprehensive understanding, it's recommended that you conduct your own testing.
                """
            )
        with st.expander('**What is the difference between a Health Goal vs. Minimum Contaminant Level?**'):
            st.markdown(
                """
                Public health goal (PHG) and minimum contaminant level (MCL) are regulatory standards used in drinking water treatment to ensure that the water is safe to drink. 
                PHGs are non-enforceable health-based targets set by regulatory agencies to provide a level of protection against significant health risks from drinking water contaminants. 
                MCLs, on the other hand, are legally enforceable standards set by the Environmental Protection Agency (EPA) under the Safe Drinking Water Act (SDWA). 
                These standards specify the maximum permissible levels of a chemical contaminant in drinking water that is supplied to the public.

                It's important to note that while MCLs are set to protect public health, they are also established taking into account the cost and feasibility requirements of water utilities. 
                This means that **MCLs may not always be set at the lowest possible level that would provide maximum health protection, but rather at a level that is considered reasonable and achievable given the current state of technology and the resources of water utilities.** 
                """
            )
            st.info(
                """While water utilities focus on MCLs, individuals should pay attention to health standards especially those with severely compromised immune systems, infants, mothers, and the elderly.""",
                icon='🧐'
            )

        with st.expander('**How does the EPA decide which contaminant to regulate?**'):
            st.markdown(
                f"""
                The Environmental Protection Agency (EPA) has rules for more than 90 different contaminants in drinking water to make sure it's safe to drink. 
                The Safe Drinking Water Act (SDWA) lays out a process for the EPA to identify new contaminants that might need regulations. 
                This includes creating a list of contaminants (called the Contaminant Candidate List) and deciding which of these contaminants should have regulations made for them.
                
                The EPA has to make a decision about at least five contaminants from this list every so often (this is called a Regulatory Determination). 
                This decision starts the process of making a new rule (called a National Primary Drinking Water Regulation) for the specific contaminant. 
                The EPA uses the list of contaminants to figure out which ones to study first and gather more information on, so they can make a better decision about whether to regulate it.

                [Learn more](https://www.epa.gov/sdwa/how-epa-regulates-drinking-water-contaminants).
                """
            )
        with st.expander('**What should I do with this information?**'):
            st.markdown(
                """
                The best we can do is to minimize our exposure to contaminants.
                The most impactful way to do this is minimizing exposure from your **daily** drinking water.
                Browse through the contaminants that exceed health standards and get a water filter suited to protect you from that.
                """
            )
            st.success(
                """
                Our personal recommendation is to get a **reverse osmosis** water filtration as that 
                is the most effective and provides protection from more contaminants that other 
                filters cannot.
                """,
            )
        with st.expander('**Where can I find more information about my drinking water and regulations?**'):
            st.markdown(
                f"""
                While there are many resources online, we highly recommend EPA's resources on drinking water, which can be found [here](https://www.epa.gov/ground-water-and-drinking-water).
                """
            )
        st.success(
            """
            Have more questions about your drinking water? Give us an email and we'll be happy to answer them!

            support@waterdoctorusa.com
            """,
            icon='❓'
        )

        

# -------- LANDING PAGE --------
else:
    hero_message = "<p style='text-align: center; font-family: Source Sans Pro, sans-serif; color:Gray;'>Get the most <b>up-to-date</b> information on your home's tap water.</p>"
    st.markdown(hero_message, unsafe_allow_html=True)
    st_lottie(lottie)
    st.caption(
        """
        :blue[Can't find your zipcode?] We're constantly adding more cities to our list.
        """
    )
    with st.expander("Tell us your zipcode and email, and we'll contact you when we add your city's water report!"):

        form = st.form(key='add zipcode', clear_on_submit=True)
        zip = form.text_input('Enter your zipcode')
        email = form.text_input('Your email')

        submit = form.form_submit_button(label='Submit')

        if submit:
            form_request = ZipRequest(zip, email)
            form_request.add_to_db()
            st.success('Your request has been submitted!', icon='🥸')
            st.balloons()
