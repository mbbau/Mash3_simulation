import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go

### Page configuration

st.set_page_config(
    layout='wide'
)

assumptions_raw = pd.read_excel("Mash3_BGS_Talk_v02b.xlsx")

assumptions = (
    assumptions_raw
    .iloc[1:,0:3]
    .head(13)
    .rename(columns=
            {'Unnamed: 0':'ASSUMPTIONS',
             'Unnamed: 1':'YR1',
             'Unnamed: 2': 'YR2'})
    .dropna(subset=['YR1'])
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

def subscription_growth(time_frame, assumptions, retention_subscribers = 0):

    subscribers = pd.DataFrame()

    subscribers['month'] = range(0,time_frame)

    if retention_subscribers == 0:
        subscribers['MoM Retention (Subscribers)'] = subscribers.apply(apply_assumption, axis=1, args=("MoM Retention (Subscribers)",))  
    else:
        subscribers['MoM Retention (Subscribers)'] = retention_subscribers

    subscribers['Traffic -> User Conversion Rate'] = subscribers.apply(apply_assumption, axis=1, args=("Traffic -> User Conversion Rate",))
    subscribers['K-Factor (Users)'] = subscribers.apply(apply_assumption, axis=1, args=("K-Factor (Users)",))
    subscribers['Paid Traffic (Installs / Visitors)'] = subscribers.apply(apply_assumption, axis=1, args=("Cost of Paid Traffic",))
    subscribers['Marketing Spend / Month'] = subscribers.apply(apply_assumption, axis=1, args=("Marketing Spend / Month",))
    subscribers['MoM Retention (Users)'] = subscribers.apply(apply_assumption, axis=1, args=("MoM Retention (Users)",))  
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

    return subscribers

def apply_assumption(row, assumption_name):
    if row['month'] < 13:
        return assumptions.loc[assumptions['ASSUMPTIONS'] == assumption_name, 'YR1'].iloc[0]
    else:
        return assumptions.loc[assumptions['ASSUMPTIONS'] == assumption_name, 'YR2'].iloc[0]

#with cols[1]:
subscribers = subscription_growth(time_frame = 25, assumptions = assumptions)
subscription25 = subscription_growth(time_frame = 25, assumptions = assumptions, retention_subscribers = 0.25)
subscription65 = subscription_growth(time_frame = 25, assumptions = assumptions, retention_subscribers = 0.65)

st.dataframe(subscription25.head())

subscriber_growth_line = px.line(
    subscribers,
    x='month',
    y="(All) Total Current Subscribers",
    title="Evolution of Subscribers over Time",
    labels={
        "(All) Total Current Subscribers": "Total Subscribers",
        "month": "Month"}
)

subscriber_growth_line.update_layout(
    plot_bgcolor='white',  
    paper_bgcolor='white',
    title_font=dict(size=35),
    title={'x':0.5, 'y':0.96, 'xanchor': 'center'},
    height=800,  
    width=1200,
    showlegend=False 
).update_xaxes(
    title_font=dict(size=20),
    tickfont_size=20,
    showgrid=False 
).update_yaxes(
    title_font=dict(size=20),
    tickfont_size=15,
    showgrid=False
).add_annotation(
    text="Change in slope due to increase in<br><b>conversion</b>, <b>retention</b> and <b>ad spend</b>",
    x=12,
    y=491.468,
    arrowhead=1,
    yshift=10,
    xanchor="right",
    showarrow=True,
    font=dict(size=20),
    arrowsize=2,
    align="center",
    ax=-50,  
    ay=-30
)

subscriber_growth_line.add_annotation(
    text="Projected subscriber growth over the first two years based on business model simulations,<br>with product improvements leading to increased retention and conversion rates.",
    xref="paper", yref="paper",
    x=0.5, y=0.96,  
    showarrow=False,
    font=dict(size=20, color="grey"),
    xanchor='center', yanchor='bottom',
)

#fig.update_layout(template='plotly_white') 

# Agrega la línea para el límite inferior de la incertidumbre
subscriber_growth_line.add_trace(go.Scatter(
    x=subscription25['month'],
    y=subscription25['(All) Total Current Subscribers'],
    mode='lines',
    line=dict(width=0),
    showlegend=False
))

# Agrega la línea para el límite superior de la incertidumbre
subscriber_growth_line.add_trace(go.Scatter(
    x=subscription65['month'],
    y=subscription65['(All) Total Current Subscribers'],
    mode='lines',
    fill='tonexty',  # Esto rellena el área entre la línea superior y la línea inferior
    fillcolor='rgba(173, 216, 230, 0.5)',  # Un color azul claro con transparencia
    line=dict(width=0),
    showlegend=False
))

subscriber_growth_line.add_annotation(
    text="The area represent all the posible growth<br>"
         "based on the different retentions present<br>"
         "in the industry: <b>25 %</b> to <b>65 %</b> based on research.",
    x=18,
    y=2500,
    arrowhead=1,
    yshift=10,
    xanchor="right",
    showarrow=True,
    font=dict(size=20),
    arrowsize=2,
    align="center",
    ax=-50,  
    ay=-30
)

st.plotly_chart(
    subscriber_growth_line
    )

