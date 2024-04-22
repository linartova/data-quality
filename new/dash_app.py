import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import missingno as msno
import pandas as pd

# Sample data
df = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [5, 4, 3, 2, 1],
    'C': [10, 9, 8, 7, 6]
})

# Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div(children=[
    html.H1(children='Dash App with Plotly Graphs'),

    # Missingno graph
    html.Div([
        dcc.Graph(

        ),
        dcc.Graph(
            missing_figure_p
        ),
        dcc.Graph(
            missing_figure_s
        )
    ]),

    # Plotly graphs
    html.Div([
        dcc.Graph(
            id='graph1',
            figure=px.scatter(df, x='A', y='B', title='Scatter Plot')
        ),
        dcc.Graph(
            id='graph2',
            figure=px.bar(df, x='A', y='C', title='Bar Chart')
        ),
        dcc.Graph(
            id='graph3',
            figure=px.line(df, x='A', y='B', title='Line Chart')
        ),
        dcc.Graph(
            id='graph4',
            figure=px.pie(df, names='A', values='C', title='Pie Chart')
        ),
        dcc.Graph(
            id='graph5',
            figure=px.histogram(df, x='B', title='Histogram')
        ),
    ])
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
