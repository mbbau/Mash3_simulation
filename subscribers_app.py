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


subscribers = subscription_growth(time_frame = 25, assumptions = assumptions)
subscription25 = subscription_growth(time_frame = 25, assumptions = assumptions, retention_subscribers = 0.25)
subscription65 = subscription_growth(time_frame = 25, assumptions = assumptions, retention_subscribers = 0.65)

st.title("Sample result from simulations")
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
    title_font=dict(size=25),
    title={'x':0.5, 'y':0.96, 'xanchor': 'center'},
    height=400,  
    width=700,
    showlegend=False 
).update_xaxes(
    title_font=dict(size=12),
    tickfont_size=12,
    showgrid=False 
).update_yaxes(
    title_font=dict(size=12),
    tickfont_size=12,
    showgrid=False
).add_annotation(
    text="Change in slope due to changes in<br><b>conversion</b>, <b>retention</b> and <b>ad spend</b>",
    x=12,
    y=subscribers.loc[12, "(All) Total Current Subscribers"],
    arrowhead=1,
    yshift=10,
    xanchor="right",
    showarrow=True,
    font=dict(size=12),
    arrowsize=2,
    align="center",
    ax=-50,  
    ay=-30
)

subscriber_growth_line.add_annotation(
    text="Projected subscriber growth over the first two years based on business model simulations,<br>with product improvements leading to increased retention and conversion rates.",
    xref="paper", yref="paper",
    x=0.5, y=0.98,  
    showarrow=False,
    font=dict(size=12, color="grey"),
    xanchor='center', yanchor='bottom',
)


subscriber_growth_line.add_trace(go.Scatter(
    x=subscription25['month'],
    y=subscription25['(All) Total Current Subscribers'],
    mode='lines',
    line=dict(width=0),
    showlegend=False
))


subscriber_growth_line.add_trace(go.Scatter(
    x=subscription65['month'],
    y=subscription65['(All) Total Current Subscribers'],
    mode='lines',
    fill='tonexty',  
    fillcolor='rgba(173, 216, 230, 0.5)',  
    line=dict(width=0),
    showlegend=False
))

subscriber_growth_line.add_annotation(
    text="The area represent all the posible growth<br>"
         "based on the different retentions present<br>"
         "in the industry: <b>25 %</b> to <b>65 %</b> based on research.",
    x=18,
    y=subscribers.loc[18, "(All) Total Current Subscribers"],
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

evolution_of_subscribers = st.columns(2)

with evolution_of_subscribers[0]:
    st.markdown("# Static Version")
    st.image('evolution of subscribers.png')

with evolution_of_subscribers[1]:
    st.markdown("# Dynamic Version")
    st.plotly_chart(
        subscriber_growth_line,
        use_container_width=True
        )

marketing_vs_growth = px.scatter(
    subscribers,
    x='Marketing Spend / Month', 
    y='(New) Subscribers', 
    trendline='ols',  
    title='Marketing Spend vs. Subscriber Growth'
)
marketing_vs_growth.update_layout(
    plot_bgcolor='white',  
    paper_bgcolor='white',
    title_font=dict(size=35),
    title={'x':0.5, 'y':0.96, 'xanchor': 'center'},
    height=600,  
    width=1000,
    showlegend=False 
)

marketing_vs_growth.add_annotation(
    text="Expected subscriber growth based on proyected marketing spend year over year.",
    xref="paper", yref="paper",
    x=0.5, y=1.02,  
    showarrow=False,
    font=dict(size=20, color="grey"),
    xanchor='center', yanchor='bottom',
)

marketing_vs_growth.add_annotation(
    text="While the exact relationship between <b>marketing spend</b> and<br>"
         "its influence on subscriber growth is not fully known,<br>"
         "marketing spend is expected to be one of the main factors<br>"
         "affecting the <b>volume of users</b>.",
    x=22000,
    y=1500,
    arrowhead=1,
    yshift=10,
    xanchor="right",
    showarrow=False,
    font=dict(size=20),
    arrowsize=2,
    align="center",
    ax=-50,  
    ay=-30
)

marketing_vs_growth.update_layout(
    xaxis_title='Marketing Spend per Month',
    yaxis_title='Total Subscribers',
    title_font=dict(size=24),
    xaxis_tickfont_size=16,
    yaxis_tickfont_size=16
)


marketing_growth = st.columns(2)

with marketing_growth[0]:
    st.markdown("# Static Version")
    st.image('Marketing Spend vs subscribers growth.png')

with marketing_growth[1]:
    st.markdown("# Dynamic Version")
    st.plotly_chart(
        marketing_vs_growth,
        use_container_width=True
        )




channels_for_new_users = px.bar(
    subscribers.rename(columns={
        'Organic / Social Visitors': 'Organic / Social Users',
        'Viral Acquired Visitors' : 'Viral Acquired Users',
        'New Acquired Users (Paid)': 'New Acquired Subscribers'
        }),
    x='month', 
    y=['Organic / Social Users','Viral Acquired Users','New Acquired Subscribers'],
    title='Sources of New Users'
).update_layout(
    plot_bgcolor='white',  
    paper_bgcolor='white',
    title_font=dict(size=35),
    title={'x':0.5, 'y':0.96, 'xanchor': 'center'},
    height=600,  
    width=1000,
    showlegend=True,
    xaxis_title='Month',
    yaxis_title='Total New Users',
    xaxis_tickfont_size=16,
    yaxis_tickfont_size=16,
    legend=dict(
    yanchor="top",
    y=0.98,
    xanchor="left",
    x=0.01),
    legend_title_text='Channel'
).add_shape(
    name="first stage",
    showlegend=False,
    type="rect",
    xref="paper",
    line=dict(dash="dash"),
    x0=0.0,
    x1=0.12,
    y0=0,
    y1=5000,
).add_annotation(
    text =  "Initially, the majority of traffic<br>"
            "would likely come from<br>"
            "paid marketing which the<br>"
            "business controls.",
    x = 3.5,
    y = 6500,
    showarrow=False,
    font=dict(size=18),
    yshift=35
).add_annotation(
    text =  "As the platform evolves, we'd expect<br>"
            "customers to shift to organic / social traffic<br>"
            "based on the effect of viral growth",
    x = 15,
    y = 25000,
    showarrow=False,
    font=dict(size=18),
    yshift=35
).add_annotation(
    text="Expected traffic of new users coming from marketing spend, virality, and organic visitors.",
    xref="paper", yref="paper",
    x=0.5, y=1.01,  
    showarrow=False,
    font=dict(size=20, color="grey"),
    xanchor='center', yanchor='bottom',
)

new_users_evolution = st.columns(2)

with new_users_evolution[0]:
    st.markdown("# Static Version")
    st.image('Sources of new users.png')

with new_users_evolution[1]:
    st.markdown("# Dynamic Version")
    st.plotly_chart(
        channels_for_new_users,
        use_container_width=True
        )


total_visitors = subscribers['New Acquired Users (Paid)'].sum() + (subscribers['Organic / Social Visitors'].sum() * 0.25) + (subscribers['Viral Acquired Visitors'].sum() * 0.25)
marketing_contribution = subscribers['New Acquired Users (Paid)'].sum() / total_visitors
organic_contribution = (subscribers['Organic / Social Visitors'].sum() * 0.25) / total_visitors
viral_contribution = (subscribers['Viral Acquired Visitors'].sum() * 0.25) / total_visitors

nodos_x = [1, 2, 3]
nodos_y = [3, 3, 3]
nodos_texto = ["New Acquired Users (Paid)", "Organic / Social Visitors", "Viral Acquired Visitors"]

nodo_new_users_x = [2]
nodo_new_users_y = [1]
nodo_new_users_text = ["New Users"]

conexiones_x = [nodos_x[0], nodo_new_users_x[0], None,  
                nodos_x[1], nodo_new_users_x[0], None,  
                nodos_x[2], nodo_new_users_x[0], None]  
conexiones_y = [nodos_y[0], nodo_new_users_y[0], None,  
                nodos_y[1], nodo_new_users_y[0], None,
                nodos_y[2], nodo_new_users_y[0], None]

customer_journey = go.Figure()


factor_escala_ancho = 30

porcentajes_flujo = [marketing_contribution, organic_contribution, viral_contribution]  


for i, pct in enumerate(porcentajes_flujo):
    customer_journey.add_trace(go.Scatter(x=[nodos_x[i], nodo_new_users_x[0]], y=[nodos_y[i], nodo_new_users_y[0]], mode='lines',
                                          line=dict(color='royalblue', width=pct * factor_escala_ancho), name='Conexiones'))

customer_journey.add_trace(
    go.Scatter(x=nodos_x, y=nodos_y, mode='markers+text', 
                           text=nodos_texto, textposition='top center', 
                           marker=dict(size=25, color='LightSkyBlue'), name='Nodos',textfont=dict(size=16))
) 

customer_journey.add_trace(go.Scatter(x=[2, 1.5], y=[1, -1], mode='lines', line=dict(color='tomato', width=2), name='Conexiones'))

customer_journey.add_trace(go.Scatter(x=[2, 2.5], y=[1, -1], mode='lines', line=dict(color='springgreen', width=2), name='Conexiones'))
customer_journey.add_trace(go.Scatter(x=[2.5, 2], y=[-1, -3], mode='lines', line=dict(color='tomato', width=2), name='Conexiones'))
customer_journey.add_trace(go.Scatter(x=[2.5, 3], y=[-1, -3], mode='lines', line=dict(color='springgreen', width=2), name='Conexiones'))

customer_journey.update_layout(title="Expected Customer Journey",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    showlegend=False,    plot_bgcolor='white',  
                    paper_bgcolor='white',
                    title_font=dict(size=35),
                    height=1000,  
                    width=1200,)

customer_journey.update_layout(title={'x':0.5, 'y':0.97, 'xanchor': 'center'})

customer_journey.add_trace(go.Scatter(x=nodo_new_users_x, y=nodo_new_users_y, mode='markers+text', 
                         text=nodo_new_users_text, textposition='middle right',
                         marker=dict(size=25, color='Green'), name='Nodos',textfont=dict(size=16)))

new_nodes_x = [1.5,2.5]
new_nodes_y = [-1, -1]
nodo_nodes_text = ["Churned Users", "New Subscribers"]

customer_journey.add_trace(go.Scatter(x=new_nodes_x, y=new_nodes_y, mode='markers+text', 
                         text=nodo_nodes_text, textposition='middle left',
                         marker=dict(size=25, color=['Red', 'green']), name='Nodos',textfont=dict(size=16)))

final_nodes_x = [2,3]
final_nodes_y = [-3, -3]
final_nodes_text = ["Churned Subscribers", "Retained Subscribers"]

customer_journey.add_trace(go.Scatter(x=final_nodes_x, y=final_nodes_y, mode='markers+text', 
                         text=final_nodes_text, textposition='middle left',
                         marker=dict(size=25, color=['Red', 'green']), name='Nodos',textfont=dict(size=16)))

customer_journey.add_annotation(
    text="Expected Customer Journey Based on Research of the Current State of the E-Learning Industry.",
    xref="paper", yref="paper",
    x=0.5, y=1.01,  
    showarrow=False,
    font=dict(size=20, color="grey"),
    xanchor='center', yanchor='bottom',
)

customer_journey.add_annotation(
    text="According to industry statistics<br><b>Retention Rates</b> can<br>be between <b>25%</b> to <b>60%</b>.",
    xref="paper", yref="paper",
    x=0.85, y=0.40,  
    showarrow=False,
    font=dict(size=20),
    xanchor='center', yanchor='bottom',
)

customer_journey.add_annotation(
    text="<b>Virality</b> will come<br>from users and subscribers<br><b>attracting</b> new users.",
    xref="paper", yref="paper",
    x=0.85, y=0.70,  
    showarrow=False,
    font=dict(size=20),
    xanchor='center', yanchor='bottom',
)

customer_journey.add_annotation(
    text="<b>Acquired Users</b> will come<br>from our<br><b>marketing spend</b>.",
    xref="paper", yref="paper",
    x=0.15, y=0.70,  
    showarrow=False,
    font=dict(size=20),
    xanchor='center', yanchor='bottom',
)

customer_journey.add_annotation(
    text=f"contribution:<br>{round(marketing_contribution*100, 1)}%",
    xref="paper", yref="paper",
    x=0.22, y=0.88,  
    showarrow=False,
    font=dict(size=20),
    xanchor='center', yanchor='bottom',
    bordercolor="#c7c7c7"
)

customer_journey.add_annotation(
    text=f"contribution:<br>{round(organic_contribution*100, 1)}%",
    xref="paper", yref="paper",
    x=0.58, y=0.84,  
    showarrow=False,
    font=dict(size=20),
    xanchor='center', yanchor='bottom',
    bordercolor="#c7c7c7"
)

customer_journey.add_annotation(
    text=f"contribution:<br>{round(viral_contribution*100, 1)}%",
    xref="paper", yref="paper",
    x=0.78, y=0.88,  
    showarrow=False,
    font=dict(size=20),
    xanchor='center', yanchor='bottom',
    bordercolor="#c7c7c7"
)


expected_customer_journey = st.columns(2)

with expected_customer_journey[0]:
    st.markdown("# Static Version")
    st.image('Expected customer Journey.png')

with expected_customer_journey[1]:
    st.markdown("# Dynamic Version")
    st.plotly_chart(
        customer_journey,
        use_container_width=True
        )

