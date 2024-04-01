import pandas as pd
import plotly.express as px
import streamlit as st

### Page configuration

st.set_page_config(
    layout='wide'
)

assumptions_raw = pd.read_excel("Mash3_BGS_Talk_v01.xlsx")

assumptions = (
    assumptions_raw
    .iloc[1:,0:3]
    .head(10)
    .rename(columns=
            {'Unnamed: 0':'ASSUMPTIONS',
             'Unnamed: 1':'YR1',
             'Unnamed: 2': 'YR2'})
    )

st.title('Subscribers Growth Simulations')

st.markdown("### A sample Simulation of the work done by Blaine Graboyes.")

cols = st.columns((0.4,0.7))

with cols[0]:
    assumptions = st.data_editor(
        assumptions, 
        use_container_width= True,
        hide_index=True
        )


subscribers = pd.DataFrame()
total_months = 25

def apply_assumption(row, assumption_name):
    if row['month'] < 13:
        return assumptions.loc[assumptions['ASSUMPTIONS'] == assumption_name, 'YR1'].iloc[0]
    else:
        return assumptions.loc[assumptions['ASSUMPTIONS'] == assumption_name, 'YR2'].iloc[0]
    
subscribers['month'] = [month for month in range(0,total_months)]

subscribers['Traffic -> User Conversion Rate'] = subscribers.apply(apply_assumption, axis=1, args=("Traffic -> User Conversion Rate",))
subscribers['K-Factor (Users)'] = subscribers.apply(apply_assumption, axis=1, args=("K-Factor (Users)",))
subscribers['Paid Traffic (Installs / Visitors)'] = subscribers.apply(apply_assumption, axis=1, args=("Cost of Paid Traffic",))
subscribers['Marketing Spend / Month'] = subscribers.apply(apply_assumption, axis=1, args=("Marketing Spend / Month",))
subscribers['MoM Retention (Users)'] = subscribers.apply(apply_assumption, axis=1, args=("MoM Retention (Users)",))  
subscribers['MoM Retention (Subscribers)'] = subscribers.apply(apply_assumption, axis=1, args=("MoM Retention (Subscribers)",))  
subscribers['K-Factor (Subscribers)'] = subscribers.apply(apply_assumption, axis=1, args=("K-Factor (Subscribers)",))
subscribers['User -> Subscriber Conversion Rate'] = subscribers.apply(apply_assumption, axis=1, args=("User -> Subscriber Conversion Rate",))

for i in subscribers['month']:

    # ----------- Organic / Social Visitors --------------
    if i == 0:
        subscribers['Organic / Social Visitors'] = assumptions.loc[assumptions['ASSUMPTIONS'] == "Starting Organic / Social Visitors", 'YR1'].iloc[0]
    elif i < 13:
        subscribers.at[i, 'Organic / Social Visitors'] = subscribers.at[i-1, 'Organic / Social Visitors'] + assumptions.loc[assumptions['ASSUMPTIONS'] == "Additive Social / Organic per Month", 'YR1'].iloc[0]
    else:
        subscribers.at[i, 'Organic / Social Visitors'] = subscribers.at[i-1, 'Organic / Social Visitors'] + assumptions.loc[assumptions['ASSUMPTIONS'] == "Additive Social / Organic per Month", 'YR2'].iloc[0]
    
    subscribers['Cost / New User'] = subscribers['Paid Traffic (Installs / Visitors)'] / subscribers['Traffic -> User Conversion Rate']
    subscribers['New Acquired Users (Paid)'] = subscribers['Marketing Spend / Month'] / subscribers['Cost / New User']

    # ----------- Viral Acquired Visitors 
    if  i == 0:
        subscribers["Viral Acquired Visitors"] = 0
    else:
        subscribers.at[i,"Viral Acquired Visitors"] =  subscribers.at[i-1, '(All Channels) New Users'] * subscribers.at[i-1,'K-Factor (Users)'] + subscribers.at[i-1, '(All) Total Current Subscribers'] * subscribers.at[i-1,'K-Factor (Subscribers)']

    # ----------- New Organic + Viral Visitors
        
    subscribers['New Organic + Viral Visitors'] = (subscribers["Viral Acquired Visitors"] + subscribers['Organic / Social Visitors']) * subscribers['Traffic -> User Conversion Rate']

    subscribers['(All Channels) New Users'] = subscribers['New Acquired Users (Paid)'] + subscribers['New Organic + Viral Visitors']

    if  i == 0:
        subscribers["(All Channels) Retained Users"] = 0
    else:
        subscribers.at[i,"(All Channels) Retained Users"] =  subscribers.at[i-1, "(All Channels) (New + Retained) Users"] * subscribers.at[i-1,'MoM Retention (Users)'] - subscribers.at[i-1, "(New) Subscribers"] 

    if  i == 0:
        subscribers["(All Channels) (New + Retained) Users"] = subscribers['(All Channels) New Users'] + subscribers["(All Channels) Retained Users"]
    else:    
       subscribers.at[i,"(All Channels) (New + Retained) Users"] = subscribers.at[i,'(All Channels) New Users'] + subscribers.at[i,"(All Channels) Retained Users"] - subscribers.at[i-1, "(New) Subscribers"]

    subscribers['(New) Subscribers'] = subscribers['User -> Subscriber Conversion Rate'] * subscribers["(All Channels) (New + Retained) Users"]

    if  i == 0:
        subscribers["(Retained) Subscribers"] = 0
    else:
        subscribers.at[i,"(Retained) Subscribers"] =  subscribers.at[i-1, "(New) Subscribers"] * subscribers.at[i-1,'MoM Retention (Subscribers)']

    subscribers["(All) Total Current Subscribers"] = subscribers["(Retained) Subscribers"] + subscribers['(New) Subscribers']

    subscribers['(All Channels) Cumulative New Users'] = subscribers['(All Channels) New Users'].cumsum()



with cols[1]:
    subscriber_growth_line = px.line(subscribers,
        x = 'month',
        y = "(All) Total Current Subscribers")
    st.plotly_chart(
        subscriber_growth_line
        )