import streamlit as st 
import plotly.express as px 
import pandas as pd

def create_plotly_bar_chart(df,x,y):
    #if len(df.columns) == 2:
    return px.bar(df,x=x,y=y)

def create_plotly_line_chart(df,x,y):
    return px.line(df,x=x,y=y)
    #return st.line_chart(df,x=df.columns[0],y=df.columns[1],color='grey',use_container_width=True)

def create_plotly_pie_chart(df,x,y):
    return px.pie(df,values=x,names=y)


data = {
    'Category': ['A', 'B', 'C', 'D'],
    'Value1': [10, 20, 15, 25],
    'Value2': [15, 25, 20, 30]
}


df = pd.DataFrame(data)

# Get column names for x-axis and y-axis
x_axis_label = st.selectbox("Select X-axis:", df.columns.values.tolist(), index=0)
y_axis_label = st.selectbox("Select Y-axis:", df.columns[1:].values.tolist(), index=0)
tabs = st.tabs(['Bar Chart','Line Chart','Pie Chart'])

with tabs[0]:
            #px.bar(df,x=df.columns[0],y=df.columns[1])
            #st.bar_chart(df,x=df.columns[0],y=df.columns[1])
    fig = create_plotly_bar_chart(df=df,x=x_axis_label,y=y_axis_label)
    st.plotly_chart(fig,use_container_width=True)

# Create bar chart using Plotly Express
#fig = px.bar(df, x=x_axis_label, y=y_axis_label, title=f'Bar Chart ({x_axis_label} vs {y_axis_label})')

# Update axis labels
#fig.update_layout(
#    xaxis_title=x_axis_label,
#    yaxis_title=y_axis_label
#)

# Show the plot using Streamlit
#st.plotly_chart(fig)