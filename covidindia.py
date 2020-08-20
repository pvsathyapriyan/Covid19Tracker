
#imports
from flask import Flask
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import plotly.express as px
import json

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#--------------------------------------------------------------------------------------------

#Intergrating Dash in Flask

server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/dash/',
    external_stylesheets=external_stylesheets
)


@server.route("/dash")
def my_dash_app():
	app.title = "Covid India Tracker"
	return app.index()

#--------------------------------------------------------------------------------------------


#Loading data and cleaning

#Loading statewise data in firstdataframe
with open('data/states_india.geojson') as f:
    geojson = json.load(f)

#Mapping geojson properties and statenames in csv
state_id_map = {}
for feature in geojson["features"]: 
    state_id_map[feature["properties"]["st_nm"]] = feature["properties"]["state_code"]
    feature["id"] = feature["properties"]["state_code"]


df = pd.read_csv("data/statewisedata.csv")
df["id"] = df["state"].apply(lambda x: state_id_map[x])

#Making a list of states for creating a Dropdown
state_list = list(df['state'])
state_list.append('All states')


#Loading daywise data in seconddataframe
df2 = pd.read_csv('data/covdata.csv', index_col=0, parse_dates=True)
df2.index = pd.to_datetime(df2["date"])

#Adding additional month column to help filtering by months
df2['month']=df2['date'].str.split('-').str[1]
month_list = list(df2['month'])
month_list.append("All months")


#--------------------------------------------------------------------------------------------

#State-wise India map

fig = px.choropleth_mapbox(df,
	    locations="id",
	    geojson = geojson,
	    color="totalcases",
	    hover_name="state",
	    hover_data=["totalcases","deaths","cured"],
	    mapbox_style="carto-positron",
	    center={'lat':24,'lon':78},
	    zoom = 3,
	    template='plotly_dark')

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

#--------------------------------------------------------------------------------------------

#Html and Dash Components

app.layout = html.Div(
    	html.Div([

	        html.Div([
	            html.H1(children='Covid-19 India')
        	], className = "row"),


        	html.Div([

				html.Div([
					html.Div(id="name1",children =[
						html.P("")
	           	], className = 'three columns' ),
	            	
	            ], className = 'three columns'),
				
	            html.Div(id="Total_Cases_count",children =[
	            	html.P("Total Cases")
	           	], className = 'three columns' ),

	           	html.Div(id="Total_Deaths_count",children =[
	           		html.P("Total Deaths")
	           	], className = 'three columns' ),

	           	html.Div(id="Total_Cured_count",children =[
	           		html.P("Cured")
	           	], className = 'three columns')

        	], className = "row"),

			html.Div([

				html.Div([

					dcc.Dropdown(
	                id="select-state",
	                options=[{"label": i, "value": i} for i in state_list],
	                placeholder = "All states",
	                value="All states"
	            	)

	            ], className = 'three columns'),
				
	            html.Div(id="Total_Cases",children =[
	           	], className = 'three columns' ),

	           	html.Div(id="Total_Deaths",children =[
	           	], className = 'three columns' ),

	           	html.Div(id="Total_Cured",children =[
	           	], className = 'three columns')


        	], className = "row"),
	        

        	html.Div([

        		html.Div([
	                dcc.Graph(
	                    id='states-graph',
	        			figure=fig
	                )
	            ], className = "eight columns"),

	            html.Div([
	            	dash_table.DataTable(
					    id='table',
					    columns=[{"name": i, "id": i} for i in df.columns],
					    data=df.to_dict('records'),
					    style_table={
				            'height': 450,
				            'overflowY': 'auto'
        				}
        			)
	     		], className = "four columns")

	        ], className = "row"),


        	html.Div([
	        	html.Div([

			            dcc.Dropdown(
		                id="select-month",
		                options=[{"label": i, "value": i} for i in list(sorted(set(month_list)))],
		                placeholder = "All months",
		                value="All months"
		            	)

		            ], className = 'three columns'),
	        ], className = 'row'),


	        html.Div([

        		html.Div([
	                dcc.Graph(
				        id='new_cases_month'
    				)
	            ], className = "six columns"),

	            html.Div([
	            	dcc.Graph(
				        id='new_deaths_month'
    				)
	     		], className = "six columns")

	        ], className = "row")

        ])
       )

#--------------------------------------------------------------------------------------------------------

#Callbacks

#Function for displaying Count of cases, deaths and cured by fetching state value from dropdown
@app.callback(
    [dash.dependencies.Output('Total_Cases', 'children'),
    dash.dependencies.Output('Total_Deaths', 'children'),
    dash.dependencies.Output('Total_Cured', 'children')],
    [dash.dependencies.Input('select-state', 'value')])
def display_values(value):

	if value == 'All states' or value is None:
		total_cases = sum(df['totalcases'])
		total_deaths = sum(df['deaths'])
		total_cured = sum(df['cured'])
	else:
		total_cases = df['totalcases'][df.state==value]
		total_deaths = df['deaths'][df.state==value]
		total_cured = df['cured'][df.state==value]

	return total_cases,total_deaths,total_cured


#Function for displaying two graphs by fetching month value from dropdown
@app.callback(
	[dash.dependencies.Output('new_cases_month', 'figure'),
    dash.dependencies.Output('new_deaths_month', 'figure')],
    [dash.dependencies.Input('select-month', 'value')])
def monthwise_graph(value):

	#manipulating dataframe if None / All months is selected in dropdown
	if value == 'All months' or value is None:

		new_cases_by_month = []
		new_deaths_by_month = []
		month_list_copy = month_list.copy()
		month_list_copy.remove('All months')

		for i in month_list_copy:
			new_cases_by_month.append(sum(df2.loc[(df2.month == i),'new_cases']))
			new_deaths_by_month.append(sum(df2.loc[(df2.month == i),'new_deaths']))

		fig1 = px.bar(df2, x= month_list_copy, y=new_cases_by_month, barmode="group",
					labels={
		                     "x": "Month",
		                     "y": "Number of cases"
		            }, title = "Month vs Number of cases")

		fig2 = px.bar(df2, x= month_list_copy, y=new_deaths_by_month, barmode="group",
					labels={
		                     "x": "Month",
		                     "y": "Number of deaths"
		            }, title = "Month vs Number of deaths")

	#manipulating dataframe for displaying day wise data for a single month
	else:
		new_cases_by_day = list(df2.loc[(df2.month == value),'new_cases'])
		day_list = [i for i in range(1,len(new_cases_by_day)+1)]
		fig1 = px.bar(df2, x= day_list, y=new_cases_by_day, barmode="group",
					labels={
				                     "x": "Day in the month",
				                     "y": "Number of cases"
				            }, title = "Day in the month vs Number of cases")

		new_deaths_by_day = list(df2.loc[(df2.month == value),'new_deaths'])
		day_list = [i for i in range(1,len(new_deaths_by_day)+1)]
		fig2 = px.bar(df2, x= day_list, y=new_deaths_by_day, barmode="group",
					labels={
				                     "x": "Day in the month",
				                     "y": "Number of death"
				            }, title = "Day in the month vs Number of deaths")

	return fig1,fig2


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=True)