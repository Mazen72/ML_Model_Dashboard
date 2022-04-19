import time
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input,Output,State,MATCH,ALL
import pandas as pd
import base64
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask
from dash.exceptions import PreventUpdate
from collections import OrderedDict
import dash_daq as daq
import configparser
import json
import os
#import RPi.GPIO as GPIO
#import dash_auth
import redis


redis_data = redis.Redis('localhost')
redis_data.set("power","")
redis_data.set("presoak","")
redis_data.set("soap","")
redis_data.set("degreaser","")
redis_data.set("rinse","")
redis_data.set("wax","")
redis_data.set("heater","")

data_dict={'power':False,'presoak':False,'soap':False,'degreaser':False,'rinse':False,'wax':False,'heater':False}


'''
power_relay_GBIO=17  # 11 on the board
presoak_relay_GBIO=18  # 12 on the board
soap_relay_GBIO=27  # 13 on the board
degreaser_relay_GBIO=22  # 15 on the board
rinse_relay_GBIO=23  # 16 on the board
wax_relay_GBIO=24  # 18 on the board
heater_relay_GBIO=10  # 19 on the board

GPIO.setmode(GPIO.BCM)
GPIO.setup(power_relay_GBIO,GPIO.OUT)
GPIO.setup(presoak_relay_GBIO,GPIO.OUT)
GPIO.setup(soap_relay_GBIO,GPIO.OUT)
GPIO.setup(degreaser_relay_GBIO,GPIO.OUT)
GPIO.setup(rinse_relay_GBIO,GPIO.OUT)
GPIO.setup(wax_relay_GBIO,GPIO.OUT)
GPIO.setup(heater_relay_GBIO,GPIO.OUT)
'''

myfolder=os.path.dirname(os.path.abspath(__file__))
contact_file=os.path.join(myfolder,'contact_info.json')
logo_file=os.path.join(myfolder,'logo.json')
csv_file=os.path.join(myfolder,'colors.csv')
config_file=os.path.join(myfolder,'config.txt')

with open(contact_file, 'r') as openfile:
    # Reading from json file
    contact_info_dict = json.load(openfile)


with open(logo_file, 'r') as openfile:
    # Reading from json file
    logo_content = json.load(openfile)

logo_content=logo_content['content']

config = configparser.ConfigParser()
config.read(config_file)

system_mode=config.get('system-mode', 'mode')
'''
data = {'Color': ['Current', 'Default'],'Main Background': ['#0f2937','#0f2937'],'Header Background': ['#20374c','#20374c']
    ,'Main Header Text': ['white','white'],'Containers Background': ['#20374c','#20374c'],
        'Containers Label': ['white','white'] , 'Buttons': ['#3d9be7','#3d9be7'], 'Buttons Text': ['white','white']
    , 'Leds Off State': ['#A9A9A9','#A9A9A9'] , 'Pre-Soak On State': ['#FD1C03','#FD1C03'] ,'Soap On State': ['#28E7FF','#28E7FF'] ,
      'Degreaser On State': ['#FF6700','#FF6700'] , 'Rinse On State': ['#FFFF33','#FFFF33'] ,'Wax On State': ['#16F529','#16F529'],
    'Heater On State': ['#FFFFFF', '#FFFFFF'], 'Pressure Washer On State': ['#39FF14', '#39FF14'],
    'Pressure Washer Off State': ['darkgrey', 'darkgrey'],
    'Timer Numbers': ['#42C4F7', '#42C4F7'], 'Timer Background': ['#0f2937', '#0f2937']
        }
'''
# Create DataFrame
#df = pd.DataFrame(data)
#df.to_csv(csv_file)
df_colors = pd.read_csv(csv_file)  # get coordinates data
components_colors = df_colors.to_dict('list')  # convert it to dictionery to be used easily
#print(components_colors)

server = Flask(__name__)

app = dash.Dash(
    __name__,server=server,
    meta_tags=[
        {
            'charset': 'utf-8',
        },
        {
            'name': 'viewport',
            'content': 'width=device-width, initial-scale=1.0, shrink-to-fit=no'
        }
    ] ,
)

#VALID_USERNAME_PASSWORD_PAIRS = {'user': 'pass'}
#auth = dash_auth.BasicAuth(app,VALID_USERNAME_PASSWORD_PAIRS)
app.title='Truck Washer Dashboard'
app.config.suppress_callback_exceptions = True
#app._favicon=('/home/mazen/PycharmProjects/Truck-Pressure-Washer/assets/favicon.ico')

text_font_size='1.6vh'
navbar_font_size='2vh'
header_font_size='2.2vh'
indicator_size=40

idle_state='idle'
washing_state='washing'
finished_washing_state='finished_washing'
system_state=idle_state
start_time=0
seconds=0
minutes=0
time_passed='00:00'

on='#39FF14'
off='red'

#encoded = base64.b64encode(open('demo.jpg', 'rb').read())
#'data:image/jpg;base64,{}'.format(encoded.decode())
logo_img=html.Img(src=logo_content, id='logo_img', height='',width='',className='mylogo',
                  style=dict(marginLeft=''))
logo_img_div=html.Div(logo_img,id='logo_img_div',style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))
# setting the size and spacing of logo_img using dash bootstrap
# more info on dash bootstrap layout : https://dash-bootstrap-components.opensource.faculty.ai/docs/components/layout/
db_logo_img=dbc.Col([ logo_img] ,
        xs=dict(size=2,offset=0), sm=dict(size=2,offset=0),
        md=dict(size=2,offset=0), lg=dict(size=3,offset=0), xl=dict(size=3,offset=0))

header_text=html.Div('Truck Pressure Washer System',id='main_header_text',style=dict(color=components_colors['Main Header Text'][0],
                     fontWeight='bold',fontSize='2.8vh',marginTop='',marginLeft='',width='100%',paddingTop='1vh',paddingBottom='1vh',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))




# setting the size and spacing of header_text using dash bootstrap
db_header_text=  dbc.Col([ header_text] ,
        xs=dict(size=10,offset=1), sm=dict(size=10,offset=1),
        md=dict(size=8,offset=2), lg=dict(size=6,offset=3), xl=dict(size=6,offset=3))

presoaking_text = html.Div(html.H1('Presoaking',className='card-header',
                                style=dict(fontWeight='bold', color='white',
                                           marginTop='')),
                        style=dict(display='inline-block', marginLeft='', textAlign="center"))

#        label=dict(label='PreSoaking',style=dict(color='white',fontSize=header_font_size,fontWeight='bold')),

leds_theme = {
    'dark': True,

    'secondary': components_colors['Leds Off State'][0]
}

presoaking_indicator=html.Div(daq.Indicator(className='led',
        id='presoaking_indicator',
label=dict(label='Pre-Soak',style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')),
    color=components_colors['Pre-Soak On State'][0],value=False,size=indicator_size
    )  , style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center')
                              )
presoaking_indicator_div= html.Div(id='presoaking_indicator_div', children=[
    daq.DarkThemeProvider(theme=leds_theme, children=presoaking_indicator)],
                          style=dict(width='100%',display= 'flex', alignItems= 'center', justifyContent= 'center') )

#style={'font-size': '12px', 'width': '140px', 'display': 'inline-block',
# 'margin-bottom': '10px', 'margin-right': '5px', 'height':'37px', 'verticalAlign': 'top'}


presoaking_button=html.Div([dbc.Button("On/Off",size='lg',outline=False, color="", className="me-1", n_clicks=0,id="presoaking_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor=components_colors['Buttons'][0],
                                        color=components_colors['Buttons Text'][0]
                                        )
                            )],style=dict(display=''))



presoaking_buttons_div=html.Div([presoaking_button,],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))


soap_indicator=daq.Indicator(className='led',
        id='soap_indicator',
        label=dict(label='Soap',style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')),
    color=components_colors['Soap On State'][0],value=False,size=indicator_size
    )

soap_indicator_div= html.Div(id='soap_indicator_div', children=[
    daq.DarkThemeProvider(theme=leds_theme, children=soap_indicator)],
                          style=dict(width='100%',display= 'flex', alignItems= 'center', justifyContent= 'center') )

soap_button=html.Div([dbc.Button("On/Off",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="soap_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor=components_colors['Buttons'][0],
                                        color=components_colors['Buttons Text'][0]
                                        )
                            )],style=dict(display='inline-block'))



soap_buttons_div=html.Div([soap_button],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))


#D76428
degreaser_indicator=daq.Indicator(className='led',
        id='degreaser_indicator',
        label=dict(label='Degreaser',style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')),
    color=components_colors['Degreaser On State'][0],value=False,size=indicator_size
    )

degreaser_indicator_div= html.Div(id='degreaser_indicator_div', children=[
    daq.DarkThemeProvider(theme=leds_theme, children=degreaser_indicator)],
                          style=dict(width='100%',display= 'flex', alignItems= 'center', justifyContent= 'center') )


degreaser_button=html.Div([dbc.Button("On/Off",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="degreaser_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor=components_colors['Buttons'][0],
                                        color=components_colors['Buttons Text'][0]
                                        )
                            )],style=dict(display='inline-block'))



degreaser_buttons_div=html.Div([degreaser_button],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))



rinse_indicator=daq.Indicator(className='led',
        id='rinse_indicator',
        label=dict(label='Rinse',style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')),
    color=components_colors['Rinse On State'][0],value=False,size=indicator_size
    )

rinse_indicator_div= html.Div(id='rinse_indicator_div', children=[
    daq.DarkThemeProvider(theme=leds_theme, children=rinse_indicator)],
                          style=dict(width='100%',display= 'flex', alignItems= 'center', justifyContent= 'center') )

rinse_button=html.Div([dbc.Button("On/Off",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="rinse_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor=components_colors['Buttons'][0],
                                        color=components_colors['Buttons Text'][0]
                                        )
                            )],style=dict(display='inline-block'))


rinse_buttons_div=html.Div([rinse_button],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))


wax_indicator=daq.Indicator(className='led',
        id='wax_indicator',
        label=dict(label='Wax',style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')),
    color=components_colors['Wax On State'][0],value=False,size=indicator_size
    )

wax_indicator_div= html.Div(id='wax_indicator_div', children=[
    daq.DarkThemeProvider(theme=leds_theme, children=wax_indicator)],
                          style=dict(width='100%',display= 'flex', alignItems= 'center', justifyContent= 'center')
                          )

wax_button=html.Div([dbc.Button("On/Off",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="wax_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor=components_colors['Buttons'][0],
                                        color=components_colors['Buttons Text'][0]
                                        )
                            )],style=dict(display='inline-block'))


wax_buttons_div=html.Div([wax_button],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))



heater_indicator=daq.Indicator(className='led',
        id='heater_indicator',
        label=dict(label='Heater',style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')),
    color=components_colors['Heater On State'][0],value=False,size=indicator_size
    )

heater_indicator_div= html.Div(id='heater_indicator_div', children=[
    daq.DarkThemeProvider(theme=leds_theme, children=heater_indicator)],
                          style=dict(width='100%',display= 'flex', alignItems= 'center', justifyContent= 'center')
                          )

heater_button=html.Div([dbc.Button("On/Off",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="heater_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor=components_colors['Buttons'][0],
                                        color=components_colors['Buttons Text'][0]
                                        )
                            )],style=dict(display='inline-block'))


heater_buttons_div=html.Div([heater_button],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))


cycle_timer=daq.LEDDisplay(
    id='cycle_timer',className='timer',
    label=dict(label="Cycle Timer",style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')),
    value='00:00' , size=30 , color=components_colors['Timer Numbers'][0],backgroundColor=components_colors['Timer Background'][0]
#42C4F7"
#0f2937 #FF5E5E
)
cycle_timer_div=html.Div(cycle_timer,style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))

timer_update=dcc.Interval(id="timer_update",interval=1000,n_intervals=0)

emergency_stop=dbc.Button("Stop All",size='lg', color="danger",n_clicks=0,id="emergency_stop",className='stop'
                            ,style=dict(fontWeight='bold',border='1px solid red')
                            )
emergency_stop_div=html.Div(emergency_stop,style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))


power_button_theme = {
    'dark': True,
    'detail': 'darkgrey',
    'primary': 'darkgrey',
    'secondary': components_colors['Pressure Washer Off State'][0]
}


power_button= daq.PowerButton(on=False,color=components_colors['Pressure Washer On State'][0],className='power',size=100,id='power_button',
                             label=dict(label='Pressure Washer',style=dict(color=components_colors['Containers Label'][0],fontWeight='bold')))


power_button_div=html.Div(id='power_button_div', children=[
    daq.DarkThemeProvider(theme=power_button_theme, children=power_button)],
                          style=dict(width='100%',display= 'flex', alignItems= 'center', justifyContent= 'center')
                          )

color_picker=    daq.ColorPicker(id='color_picker', className='color_picker',size=190,
        label=dict(label='Color Picker',style=dict(color='white',fontWeight='bold')),
        value=dict(hex='#119DFF')
    )
color_picker_div=html.Div(color_picker,style=dict(display='inline-block'))

component_text= html.Div(html.H1('Choose a Component',
                                    style=dict(fontSize=text_font_size, fontWeight='bold', color='white',
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

components_menu = dcc.Dropdown(className="custom-dropdown",
                 id='components_menu',
                 options=[{'label': 'Main Background', 'value': 'Main Background'},{'label': 'Header Background', 'value': 'Header Background'},
                 {'label': 'Main Header Text', 'value': 'Main Header Text'},{'label': 'Containers Background', 'value': 'Containers Background'},
                 {'label': 'Containers Label', 'value': 'Containers Label'},{'label': 'Buttons', 'value': 'Buttons'},
                 {'label': 'Buttons Text', 'value': 'Buttons Text'},{'label': 'Leds Off State', 'value': 'Leds Off State'},
                 {'label': 'Pre-Soak On State', 'value': 'Pre-Soak On State'},{'label': 'Soap On State', 'value': 'Soap On State'},
                 {'label': 'Degreaser On State', 'value': 'Degreaser On State'},{'label': 'Rinse On State', 'value': 'Rinse On State'},
                 {'label': 'Wax On State', 'value': 'Wax On State'},{'label': 'Heater On State', 'value': 'Heater On State'},
                 {'label': 'Pressure Washer On State', 'value': 'Pressure Washer On State'},
                 {'label': 'Pressure Washer Off State', 'value': 'Pressure Washer Off State'},
                 {'label': 'Timer Numbers', 'value': 'Timer Numbers'},{'label': 'Timer Background', 'value': 'Timer Background'},
                 {'label': 'Contact Info Text', 'value': 'Contact Info Text'}
                              ]
                            # get all countries from countries list
                            ,
                            value='Main Background',
                            style=dict(color='#0f2537', fontWeight='bold', textAlign='center',
                                       width='23vh', backgroundColor='#0f2537', border='')
                            )

upload_img_text= html.Div(html.H1('Change Logo',
                                    style=dict(fontSize=text_font_size, fontWeight='bold', color='white',
                                               marginTop='')),
                            style=dict(display='', textAlign="", width='100%'))

upload_img =dcc.Upload(id='upload_img',children=dbc.Button("Upload Logo", color="primary", size='lg', outline=True,
                                       n_clicks=0,id="upload_img_button",style=dict(fontSize=text_font_size,color='white') ) )

change_logo_div=html.Div([upload_img_text,upload_img],
                            style=dict(fontSize=text_font_size,display='inline-block',marginLeft='2vw',textAlign="center",
                                       verticalAlign='top'))

components_menu_div = html.Div([change_logo_div,html.Br(),html.Br(),html.Br(),component_text,components_menu],
                            style=dict(fontSize=text_font_size,display='inline-block',marginLeft='2vw',textAlign="center",marginBottom='10vh',
                                       verticalAlign='top'))

apply_button=html.Div([dbc.Button("Apply",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="apply_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor='#3d9be7',
                                        color='white'
                                        )
                            )],style=dict(display='inline-block'))

default_button=html.Div([dbc.Button("Default",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="default_button"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor='#3d9be7',
                                        color='white'
                                        )
                            )],style=dict(display='inline-block',marginLeft='2vw'))

coloring_buttons_div=html.Div([apply_button,default_button],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))

contact_info=html.Div(html.H1(contact_info_dict['text'],className='mytext',
                                    style=dict(fontSize='', fontWeight='bold', color=contact_info_dict['color'],
                                               marginTop='') ,id='contact_info_text' ),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

edit_text=html.Div(html.H1('Edit Contact Info Text',className='mytext2',
                                    style=dict(fontSize='', fontWeight='bold', color='white',
                                               marginTop='')),
                            style=dict(display='', marginLeft='', textAlign="center", width='100%'))

edit_contact_info=dbc.Textarea( size="lg", placeholder="Please enter your text here",className='my-textera',id='textera'
        )

apply_text=html.Div([dbc.Button("Apply",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="apply_button2"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor='#3d9be7',
                                        color='white'
                                        )
                            )],style=dict(display='inline-block'))

default_text=html.Div([dbc.Button("Default",size='lg',outline=False, color="primary", className="me-1", n_clicks=0,id="default_button2"
                            ,style=dict(fontWeight='bold',border='1px solid transparent',
                                        backgroundColor='#3d9be7',
                                        color='white'
                                        )
                            )],style=dict(display='inline-block',marginLeft='2vw'))

editing_buttons_div=html.Div([apply_text,default_text],
                                style=dict(width='100%',
                     display= 'flex', alignItems= 'center', justifyContent= 'center'))

main_layout=html.Div([
    dbc.Row([db_header_text],style=dict(backgroundColor=components_colors['Header Background'][0]),id='main_header' )
                        ,html.Br(),
       dbc.Row([

           dbc.Col([dbc.Card(dbc.CardBody(
        [html.Div([presoaking_indicator_div ,html.Br(),presoaking_buttons_div,html.Br()

                   ], style=dict(height=''))])
        , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card1',className='mycard'), html.Br()
    ], xl=dict(size=2,offset=1),lg=dict(size=2,offset=1),
                     md=dict(size=3,offset=0),sm=dict(size=6,offset=0),xs=dict(size=6,offset=0)),

                      dbc.Col([dbc.Card(dbc.CardBody(
                          [html.Div([soap_indicator_div, html.Br(),soap_buttons_div,html.Br()

                                     ], style=dict(height=''))])
                          , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card2',className='mycard'), html.Br()
                      ], xl=dict(size=2, offset=0), lg=dict(size=2, offset=0),
                          md=dict(size=3, offset=0), sm=dict(size=6, offset=0), xs=dict(size=6, offset=0)),

           dbc.Col([dbc.Card(dbc.CardBody(
               [html.Div([degreaser_indicator_div, html.Br(), degreaser_buttons_div,html.Br()

                          ], style=dict(height=''))])
               , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card3',className='mycard'), html.Br()
           ], xl=dict(size=2, offset=0), lg=dict(size=2, offset=0),
               md=dict(size=3, offset=0), sm=dict(size=6, offset=0), xs=dict(size=6, offset=0)),

           dbc.Col([dbc.Card(dbc.CardBody(
               [html.Div([rinse_indicator_div, html.Br(), rinse_buttons_div,html.Br()

                          ], style=dict(height=''))])
               , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card4',className='mycard'), html.Br()
           ], xl=dict(size=2, offset=0), lg=dict(size=2, offset=0),
               md=dict(size=3, offset=0), sm=dict(size=6, offset=0), xs=dict(size=6, offset=0)) ,

           dbc.Col([dbc.Card(dbc.CardBody(
               [html.Div([wax_indicator_div, html.Br(), wax_buttons_div, html.Br()

                          ], style=dict(height=''))])
               , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card5',className='mycard'), html.Br()
           ], xl=dict(size=2, offset=0), lg=dict(size=2, offset=0),
               md=dict(size=3, offset=0), sm=dict(size=6, offset=0), xs=dict(size=6, offset=0)),

           dbc.Col([dbc.Card(dbc.CardBody(
               [html.Div([power_button_div,html.Br()

                          ], style=dict(height=''))])
               , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card6',className='mycard'), html.Br()
           ], xl=dict(size=2, offset=1), lg=dict(size=2, offset=1),
               md=dict(size=3, offset=0), sm=dict(size=6, offset=0), xs=dict(size=6, offset=0)) ,

           dbc.Col([dbc.Card(dbc.CardBody(
               [html.Div([heater_indicator_div, html.Br(), heater_buttons_div, html.Br()

                          ], style=dict())])
               , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card7',className='mycard'), html.Br()
           ], xl=dict(size=2, offset=0), lg=dict(size=2, offset=0),
               md=dict(size=3, offset=0), sm=dict(size=6, offset=0), xs=dict(size=6, offset=0),style=dict()
           ),

           dbc.Col([dbc.Card(dbc.CardBody(
               [html.Div([ cycle_timer_div

                          ], style=dict())])
               , style=dict(backgroundColor=components_colors['Containers Background'][0]),id='card8',className='mycard'), html.Br()
           ], xl=dict(size=2, offset=0), lg=dict(size=2, offset=0),
               md=dict(size=3, offset=0), sm=dict(size=6, offset=0), xs=dict(size=6, offset=0),style=dict()
           )
         ,

           dbc.Col([
               html.Div([html.Br(), logo_img_div

                         ], style=dict())
               , html.Br()
           ], xl=dict(size=3, offset=0), lg=dict(size=4, offset=0),
               md=dict(size=6, offset=3), sm=dict(size=10, offset=1), xs=dict(size=10, offset=1),
               style=dict()
           )
                ,html.Br()
          , contact_info

            ,timer_update

])
])

if system_mode=='editing':
    app.layout=html.Div([  main_layout,html.Br(), dbc.Row([
        dbc.Col([dbc.Card(dbc.CardBody(
            [html.Div([color_picker_div, components_menu_div], style=dict(width='100%',
                                                                          display='flex', alignItems='center',
                                                                          justifyContent='center'))
             , html.Br(),coloring_buttons_div
             ])
            , style=dict(backgroundColor='#20374c'), id='card9',
            className='my-color-picker'), html.Br()
        ], xl=dict(size=4, offset=2), lg=dict(size=6, offset=1),
            md=dict(size=8, offset=0), sm=dict(size=10, offset=1), xs=dict(size=10, offset=1), style=dict()
        )
    ,
        dbc.Col([dbc.Card(dbc.CardBody(
            [edit_text,html.Br(),edit_contact_info , html.Br(),editing_buttons_div
             ])
            , style=dict(backgroundColor='#20374c'), id='card10',
            className='my-textera-container'), html.Br()
        ], xl=dict(size=4, offset=0), lg=dict(size=4, offset=0),
            md=dict(size=4, offset=0), sm=dict(size=10, offset=1), xs=dict(size=10, offset=1), style=dict()
        )

    ])

       ],style=dict(backgroundColor=components_colors['Main Background'][0]),className='main',id='main_div')

else :
    app.layout=html.Div([main_layout,dcc.Store(id='data_updated',data='updated'),dcc.Store(id='database',data=data_dict),
                         dcc.Interval(id='server_interval',n_intervals=200),


    ],style=dict(backgroundColor=components_colors['Main Background'][0]),className='main',id='main_div')

'''
[ Output('presoaking_indicator', 'value'), Output('soap_indicator', 'value'),
                   Output('degreaser_indicator', 'value'), Output('rinse_indicator', 'value'),
                   Output('wax_indicator', 'value'), Output('power_button', 'on'), Output('heater_indicator', 'value') ]
'''
if system_mode!='editing':

    @app.callback([Output('presoaking_indicator', 'value'), Output('soap_indicator', 'value'),
                   Output('degreaser_indicator', 'value'), Output('rinse_indicator', 'value'),
                   Output('wax_indicator', 'value'), Output('power_button', 'on'), Output('heater_indicator', 'value'),
                   Output('cycle_timer','value')]
                   ,
                  [Input('presoaking_button', 'n_clicks'), Input('soap_button', 'n_clicks'),
                   Input('degreaser_button', 'n_clicks'), Input('rinse_button', 'n_clicks'),
                   Input('wax_button', 'n_clicks'),
                   Input('power_button', 'on'), Input('heater_button', 'n_clicks'),Input('server_interval','n_intervals')
                   ],
                  [State('presoaking_indicator', 'value'), State('soap_indicator', 'value'),
                   State('degreaser_indicator', 'value'), State('rinse_indicator', 'value'),
                   State('wax_indicator', 'value'),
                   State('power_button', 'on'), State('heater_indicator', 'value')

                   ], prevent_initial_call=True)
    def cycle_control(presoaking_button, soap_button, degreaser_button,
                      rinse_button, wax_button, pressure_washer_button, heater_button,server_interval
                      , presoaking_state, soap_state, degreaser_state, rinse_state, wax_state, pressure_washer_state,
                      heater_state
                      ):
        global idle_state, washing_state, system_state, start_time, seconds , time_passed
        ctx = dash.callback_context
        button_pressed = ctx.triggered[0]['prop_id'].split('.')[0]




        if system_state == idle_state:
            if button_pressed == 'power_button':
                if pressure_washer_state == True:
                    system_state = washing_state
                    start_time = time.time()
                    # pressure_washer pin on
                    #GPIO.output(power_relay_GBIO, GPIO.HIGH)
                    redis_data.set("power","on")
                    return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True,
                            dash.no_update,time_passed)
                else:
                    raise PreventUpdate

            else:
                raise PreventUpdate



        elif system_state == washing_state:
            seconds = int(time.time() - start_time)
            min,sec=divmod(seconds,60)
            if len(str(min))==1:
                min='0{}'.format(min)

            if len(str(sec))==1:
                sec='0{}'.format(sec)

            time_passed='{}:{}'.format(min,sec)
            if button_pressed == 'power_button':
                if pressure_washer_state == False:
                    system_state = finished_washing_state
                    '''
                    GPIO.output(power_relay_GBIO, GPIO.LOW)
                    GPIO.output(presoak_relay_GBIO, GPIO.LOW)
                    GPIO.output(soap_relay_GBIO, GPIO.LOW)
                    GPIO.output(degreaser_relay_GBIO, GPIO.LOW)
                    GPIO.output(rinse_relay_GBIO, GPIO.LOW)
                    GPIO.output(wax_relay_GBIO, GPIO.LOW)
                    GPIO.output(heater_relay_GBIO, GPIO.LOW)
                    '''
                    # all pins off
                    redis_data.set("power", "")
                    redis_data.set("presoak", "")
                    redis_data.set("soap", "")
                    redis_data.set("degreaser", "")
                    redis_data.set("rinse", "")
                    redis_data.set("wax", "")
                    redis_data.set("heater", "")

                    return (False, False, False, False, False, False, False,time_passed)

            elif button_pressed == 'presoaking_button':

                if presoaking_state == True:
                    # presoaking pin off
                   # GPIO.output(presoak_relay_GBIO, GPIO.LOW)
                    redis_data.set("presoak", "")
                    return (False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,time_passed)

                elif presoaking_state == False:
                # presoaking pin on and the other 4 pins on top off
                    '''
                    GPIO.output(presoak_relay_GBIO, GPIO.HIGH)
                    GPIO.output(soap_relay_GBIO, GPIO.LOW)
                    GPIO.output(degreaser_relay_GBIO, GPIO.LOW)
                    GPIO.output(rinse_relay_GBIO, GPIO.LOW)
                    GPIO.output(wax_relay_GBIO, GPIO.LOW)
                    '''
                    redis_data.set("presoak", "on")
                    redis_data.set("soap", "")
                    redis_data.set("degreaser", "")
                    redis_data.set("rinse", "")
                    redis_data.set("wax", "")
                    return (True, False, False, False, False, dash.no_update, dash.no_update,time_passed)


            elif button_pressed == 'soap_button':

                if soap_state == True:
                    # soap pin off
                  #  GPIO.output(soap_relay_GBIO, GPIO.LOW)
                    redis_data.set("soap", "")
                    return (dash.no_update, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,time_passed)

                elif soap_state == False:
                # soap pin on and the other 4 pins on top off
                    '''
                    GPIO.output(presoak_relay_GBIO, GPIO.LOW)
                    GPIO.output(soap_relay_GBIO, GPIO.HIGH)
                    GPIO.output(degreaser_relay_GBIO, GPIO.LOW)
                    GPIO.output(rinse_relay_GBIO, GPIO.LOW)
                    GPIO.output(wax_relay_GBIO, GPIO.LOW)
                    '''
                    redis_data.set("presoak", "")
                    redis_data.set("soap", "on")
                    redis_data.set("degreaser", "")
                    redis_data.set("rinse", "")
                    redis_data.set("wax", "")
                    return (False, True, False, False, False, dash.no_update, dash.no_update,time_passed)


            elif button_pressed == 'degreaser_button':

                if degreaser_state == True:
                    # degreaser pin off
                  #  GPIO.output(degreaser_relay_GBIO, GPIO.LOW)
                    redis_data.set("degreaser", "")
                    return (dash.no_update, dash.no_update, False, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,time_passed)

                elif degreaser_state == False:
                    # degreaser pin on and the other 3 pins on top off
                    '''
                    GPIO.output(presoak_relay_GBIO, GPIO.LOW)
                    GPIO.output(soap_relay_GBIO, GPIO.LOW)
                    GPIO.output(degreaser_relay_GBIO, GPIO.HIGH)
                    GPIO.output(rinse_relay_GBIO, GPIO.LOW)
                    GPIO.output(wax_relay_GBIO, GPIO.LOW)
                    '''
                    redis_data.set("presoak", "")
                    redis_data.set("soap", "")
                    redis_data.set("degreaser", "on")
                    redis_data.set("rinse", "")
                    redis_data.set("wax", "")
                    return (False, False, True, False, False, dash.no_update, dash.no_update,time_passed)



            elif button_pressed == 'rinse_button':

                if rinse_state == True:
                    # rinse pin off
                  #  GPIO.output(rinse_relay_GBIO, GPIO.LOW)
                    redis_data.set("rinse", "")
                    return (dash.no_update, dash.no_update, dash.no_update, False, dash.no_update, dash.no_update,
                            dash.no_update,time_passed)

                elif rinse_state == False:
                    # rinse pin on and the other 3 pins on top off
                    '''
                    GPIO.output(presoak_relay_GBIO, GPIO.LOW)
                    GPIO.output(soap_relay_GBIO, GPIO.LOW)
                    GPIO.output(degreaser_relay_GBIO, GPIO.LOW)
                    GPIO.output(rinse_relay_GBIO, GPIO.HIGH)
                    GPIO.output(wax_relay_GBIO, GPIO.LOW)
                    '''
                    redis_data.set("presoak", "")
                    redis_data.set("soap", "")
                    redis_data.set("degreaser", "")
                    redis_data.set("rinse", "on")
                    redis_data.set("wax", "")
                    return (False, False, False, True, False, dash.no_update, dash.no_update,time_passed)

            elif button_pressed == 'wax_button':

                if wax_state == True:
                    # wax pin off
               #     GPIO.output(wax_relay_GBIO, GPIO.LOW)
                    redis_data.set("wax", "")
                    return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, dash.no_update,
                            dash.no_update,time_passed)

                elif wax_state == False:
                    # wax pin on and the other 3 pins on top off
                    '''
                    GPIO.output(presoak_relay_GBIO, GPIO.LOW)
                    GPIO.output(soap_relay_GBIO, GPIO.LOW)
                    GPIO.output(degreaser_relay_GBIO, GPIO.LOW)
                    GPIO.output(rinse_relay_GBIO, GPIO.LOW)
                    GPIO.output(wax_relay_GBIO, GPIO.HIGH)
                    '''
                    redis_data.set("presoak", "")
                    redis_data.set("soap", "")
                    redis_data.set("degreaser", "")
                    redis_data.set("rinse", "")
                    redis_data.set("wax", "on")
                    return (False, False, False, False, True, dash.no_update, dash.no_update,time_passed)

            elif button_pressed == 'heater_button':

                if heater_state == True:
                    # heater pin off
                #    GPIO.output(heater_relay_GBIO, GPIO.LOW)
                    redis_data.set("heater", "")
                    return (
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        False,time_passed)

                elif heater_state == False:
                    # heater pin on
                #    GPIO.output(heater_relay_GBIO, GPIO.HIGH)
                    redis_data.set("heater", "on")
                    return (
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        True,time_passed)

            elif button_pressed == 'server_interval':
                return (bool(redis_data.get('presoak')), bool(redis_data.get('soap')), bool(redis_data.get('degreaser'))
                        , bool(redis_data.get('rinse')), bool(redis_data.get('wax')), bool(redis_data.get('power')),
                        bool(redis_data.get('heater')),time_passed
                        )

            else:
                raise PreventUpdate

        elif system_state == finished_washing_state:
            if button_pressed == 'power_button':
                system_state = washing_state
                start_time = time.time()
                # pressure_washer pin on
              #  GPIO.output(power_relay_GBIO, GPIO.HIGH)
                redis_data.set("power", "on")
                return (
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True,
                    dash.no_update,time_passed)

            return (bool(redis_data.get('presoak')), bool(redis_data.get('soap')), bool(redis_data.get('degreaser'))
                    , bool(redis_data.get('rinse')), bool(redis_data.get('wax')), bool(redis_data.get('power')),
                    bool(redis_data.get('heater')),time_passed
                    )

        else:
            raise PreventUpdate

else:

    @app.callback([Output('presoaking_indicator', 'value'), Output('soap_indicator', 'value'),
                   Output('degreaser_indicator', 'value'), Output('rinse_indicator', 'value'),
                   Output('wax_indicator', 'value'), Output('power_button', 'on'), Output('heater_indicator', 'value'),
                   Output('presoaking_indicator', 'color'), Output('soap_indicator', 'color'),
                   Output('degreaser_indicator', 'color'), Output('rinse_indicator', 'color'),
                   Output('wax_indicator', 'color'), Output('heater_indicator', 'color'),Output('power_button', 'color'),
                   Output('presoaking_indicator', 'label'), Output('soap_indicator', 'label'),
                   Output('degreaser_indicator', 'label'), Output('rinse_indicator', 'label'),
                   Output('wax_indicator', 'label'), Output('heater_indicator', 'label'),
                   Output('power_button', 'label')
                   ],
                  [Input('presoaking_button', 'n_clicks'), Input('soap_button', 'n_clicks'),
                   Input('degreaser_button', 'n_clicks'), Input('rinse_button', 'n_clicks'),
                   Input('wax_button', 'n_clicks'),Input('power_button', 'on'), Input('heater_button', 'n_clicks'),
                   Input('apply_button', 'n_clicks')
                   ],
                  [State('presoaking_indicator', 'value'), State('soap_indicator', 'value'),
                   State('degreaser_indicator', 'value'), State('rinse_indicator', 'value'),
                   State('wax_indicator', 'value'),
                   State('power_button', 'on'), State('heater_indicator', 'value'),
                   State('components_menu','value'),State('color_picker','value')

                   ])
    def update_indicators(presoaking_button, soap_button, degreaser_button,
                      rinse_button, wax_button, pressure_washer_button, heater_button,apply_button
                      , presoaking_state, soap_state, degreaser_state, rinse_state, wax_state, pressure_washer_state,
                      heater_state , component,color_picked
                      ):
        global idle_state, washing_state, system_state, start_time, seconds , df , components_colors
        ctx = dash.callback_context



        if not ctx.triggered:
            df_colors = pd.read_csv(csv_file)
            colors_dict = df_colors.to_dict('list')

            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update,colors_dict['Pre-Soak On State'][0],colors_dict['Soap On State'][0],
                    colors_dict['Degreaser On State'][0],colors_dict['Rinse On State'][0],colors_dict['Wax On State'][0],
                    colors_dict['Heater On State'][0],colors_dict['Pressure Washer On State'][0],
                    dict(label='Pre-Soak',style=dict(color=colors_dict['Containers Label'][0], fontWeight='bold'))
                    ,dict(label='Soap',style=dict(color=colors_dict['Containers Label'][0], fontWeight='bold'))
                    ,dict(label='Degreaser',style=dict(color=colors_dict['Containers Label'][0], fontWeight='bold')),
                    dict(label='Rinse',style=dict(color=colors_dict['Containers Label'][0], fontWeight='bold')),
                    dict(label='Wax',style=dict(color=colors_dict['Containers Label'][0], fontWeight='bold')),
                    dict(label='Heater',style=dict(color=colors_dict['Containers Label'][0], fontWeight='bold')),
                    dict(label='Pressure Washer',style=dict(color=colors_dict['Containers Label'][0], fontWeight='bold'))
                    )

        button_pressed = ctx.triggered[0]['prop_id'].split('.')[0]



        if button_pressed=='apply_button':
            if component=='Pre-Soak On State':
                components_colors['Pre-Soak On State'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,color_picked['hex'],dash.no_update, dash.no_update, dash.no_update
                        , dash.no_update, dash.no_update,dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update
                        )

            elif component=='Soap On State':
                components_colors['Soap On State'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update,color_picked['hex'], dash.no_update, dash.no_update
                        , dash.no_update, dash.no_update,dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update
                        )

            elif component=='Degreaser On State':
                components_colors['Degreaser On State'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update,dash.no_update, color_picked['hex'], dash.no_update
                        , dash.no_update, dash.no_update,dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update
                        )

            elif component=='Rinse On State':
                components_colors['Rinse On State'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update,dash.no_update, dash.no_update, color_picked['hex']
                        , dash.no_update, dash.no_update,dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update
                        )

            elif component=='Wax On State':
                components_colors['Wax On State'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update,dash.no_update, dash.no_update, dash.no_update
                        , color_picked['hex'], dash.no_update,dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update
                        )

            elif component=='Heater On State':
                components_colors['Heater On State'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update,dash.no_update, dash.no_update, dash.no_update
                        , dash.no_update, color_picked['hex'],dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update
                        )

            elif component=='Pressure Washer On State':
                components_colors['Pressure Washer On State'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update,dash.no_update, dash.no_update, dash.no_update
                        , dash.no_update, dash.no_update,color_picked['hex'],dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

            elif component=='Containers Label':
                components_colors['Containers Label'][0]=color_picked['hex']
                df=pd.DataFrame(components_colors)
                df.to_csv(csv_file,index=False)
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update,dash.no_update, dash.no_update, dash.no_update
                        , dash.no_update, dash.no_update,dash.no_update,
                        dict(label='Pre-Soak', style=dict(color=color_picked['hex'], fontWeight='bold'))
                        , dict(label='Soap', style=dict(color=color_picked['hex'], fontWeight='bold'))
                        , dict(label='Degreaser',style=dict(color=color_picked['hex'], fontWeight='bold')),
                        dict(label='Rinse', style=dict(color=color_picked['hex'], fontWeight='bold')),
                        dict(label='Wax', style=dict(color=color_picked['hex'], fontWeight='bold')),
                        dict(label='Heater', style=dict(color=color_picked['hex'], fontWeight='bold')),
                        dict(label='Pressure Washer',style=dict(color=color_picked['hex'], fontWeight='bold'))
                        )
            else:
                raise PreventUpdate




        if button_pressed == 'power_button':

            if pressure_washer_state == False:
                    # all pins off
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update
                            )

            elif pressure_washer_state == True:

                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, dash.no_update,
                            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,
                            components_colors['Pressure Washer On State'][0],dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update
                            )

        elif button_pressed == 'presoaking_button':

            if presoaking_state == True:
                    # presoaking pin off
                return (False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

            elif presoaking_state == False:
                # presoaking pin on and the other 3 pins on top off
                return (True, False, False, False, False, dash.no_update, dash.no_update,
                            components_colors['Pre-Soak On State'][0], dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update
                            )


        elif button_pressed == 'soap_button':

            if soap_state == True:
                    # soap pin off
                return (dash.no_update, False, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

            elif soap_state == False:
                # soap pin on and the other 3 pins on top off
                return (False, True, False, False, False, dash.no_update, dash.no_update,
                            dash.no_update, components_colors['Soap On State'][0], dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update
                            )


        elif button_pressed == 'degreaser_button':

            if degreaser_state == True:
                    # degreaser pin off
                return (dash.no_update, dash.no_update, False, dash.no_update, dash.no_update, dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

            elif degreaser_state == False:
                    # degreaser pin on and the other 3 pins on top off
                return (False, False, True, False, False, dash.no_update, dash.no_update,
                            dash.no_update, dash.no_update, components_colors['Degreaser On State'][0], dash.no_update, dash.no_update,
                            dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update
                            )



        elif button_pressed == 'rinse_button':

            if rinse_state == True:
                    # rinse pin off
                return (dash.no_update, dash.no_update, dash.no_update, False, dash.no_update, dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

            elif rinse_state == False:
                    # rinse pin on and the other 3 pins on top off
                return (False, False, False, True, False, dash.no_update, dash.no_update,
                            dash.no_update, dash.no_update, dash.no_update,components_colors['Rinse On State'][0], dash.no_update,
                            dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update
                            )

        elif button_pressed == 'wax_button':

            if wax_state == True:
                    # wax pin off
                return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

            elif wax_state == False:
                    # wax pin on and the other 3 pins on top off
                return (False, False, False, False, True, dash.no_update, dash.no_update,
                            dash.no_update, dash.no_update, dash.no_update, dash.no_update, components_colors['Wax On State'][0],
                            dash.no_update,
                            dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update
                            )

        elif button_pressed == 'heater_button':

            if heater_state == True:
                    # heater pin off
                return (
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    False,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

            elif heater_state == False:
                    # heater pin on
                return (
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    True,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, components_colors['Heater On State'][0],
                        dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update)

        else:
            raise PreventUpdate


#,Input('power_button','on')
'''
if system_mode!='editing':
    @app.callback(Output('cycle_timer','value'),
              [Input('timer_update','n_intervals'),Input('power_button', 'on')]
              )
    def update_timer(time_update,power_button):
        global seconds , time_passed
        if system_state== washing_state:
            seconds = int(time.time() - start_time)
            min,sec=divmod(seconds,60)
            if len(str(min))==1:
                min='0{}'.format(min)

            if len(str(sec))==1:
                sec='0{}'.format(sec)

            time_passed='{}:{}'.format(min,sec)
            return time_passed
        else:
            return time_passed
'''
if system_mode =='editing':

    @app.callback([Output('main_div', 'style'),Output('main_header', 'style'),Output('main_header_text','style'),Output('card1', 'style'),
               Output('card2', 'style'),Output('card3', 'style'),Output('card4', 'style'),Output('card5', 'style'),
               Output('card6', 'style'),Output('card7', 'style'),Output('card8', 'style'),
               ],
                  Input('apply_button', 'n_clicks'),
                  [State('main_div','style'),State('main_header','style'),State('main_header_text','style'),State('card1', 'style'),
                   State('card2', 'style'),State('card3', 'style'),State('card4', 'style'),State('card5', 'style'),
                   State('card6', 'style'),State('card7', 'style'),State('card8', 'style'),

                   State('components_menu','value'),State('color_picker','value')]
            )
    def update_background_colors(clicks,main_div,main_header,main_header_text,card1,card2,card3,card4,card5,card6,card7,
                             card8,component,color_picked):
        global  df , components_colors
        ctx = dash.callback_context
        if not ctx.triggered:
            df_colors = pd.read_csv(csv_file)
            colors_dict = df_colors.to_dict('list')
            main_div['backgroundColor']=colors_dict['Main Background'][0]
            main_header['backgroundColor']=colors_dict['Header Background'][0]
            main_header_text['color']=colors_dict['Main Header Text'][0]
            card1['backgroundColor']=colors_dict['Containers Background'][0]
            card2['backgroundColor']=colors_dict['Containers Background'][0]
            card3['backgroundColor']=colors_dict['Containers Background'][0]
            card4['backgroundColor']=colors_dict['Containers Background'][0]
            card5['backgroundColor']=colors_dict['Containers Background'][0]
            card6['backgroundColor']=colors_dict['Containers Background'][0]
            card7['backgroundColor']=colors_dict['Containers Background'][0]
            card8['backgroundColor']=colors_dict['Containers Background'][0]
            return (main_div,main_header,main_header_text,card1,card2,card3,card4,card5,card6,card7,card8)

        if component=='Main Background':
            components_colors['Main Background'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file,index=False)
            main_div['backgroundColor']=color_picked['hex']
            return (main_div,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update)

        elif component=='Header Background':
            components_colors['Header Background'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file,index=False)
            main_header['backgroundColor']=color_picked['hex']
            return (dash.no_update,main_header,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update)

        elif component=='Main Header Text':
            components_colors['Main Header Text'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file,index=False)
            main_header_text['color']=color_picked['hex']
            return (dash.no_update,dash.no_update,main_header_text,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update)

        elif component=='Containers Background':
            components_colors['Containers Background'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file,index=False)
            card1['backgroundColor']=color_picked['hex']
            card2['backgroundColor']=color_picked['hex']
            card3['backgroundColor']=color_picked['hex']
            card4['backgroundColor']=color_picked['hex']
            card5['backgroundColor']=color_picked['hex']
            card6['backgroundColor']=color_picked['hex']
            card7['backgroundColor']=color_picked['hex']
            card8['backgroundColor']=color_picked['hex']
            return ( dash.no_update,dash.no_update,dash.no_update,card1,card2,card3,card4,card5,card6,card7,card8 )

        else:
            raise PreventUpdate

    @app.callback(Output('color_picker', 'value'),
                  Input('default_button','n_clicks'),
                  [State('components_menu','value')]
                  ,prevent_initial_call=True)
    def default_color(default_button,component):
        if component=='Contact Info Text':
            with open('contact_info.json', 'r') as openfile:
                # Reading from json file
                contact_info_dict = json.load(openfile)
            return dict(hex=contact_info_dict['default_color'])

        df_colors=pd.read_csv(csv_file)
        colors_dict=df_colors.to_dict('list')
        colors_dict[component][0]=colors_dict[component][1]
        df_colors=pd.DataFrame(colors_dict)
        df_colors.to_csv(csv_file,index=False)
        return dict(hex=colors_dict[component][1])

# presoaking_indicator_div soap_indicator_div degreaser_indicator_div  rinse_indicator_div wax_indicator_div heater_indicator_div power_button_div

    @app.callback([Output('presoaking_indicator_div', 'children'), Output('soap_indicator_div', 'children'),
               Output('degreaser_indicator_div', 'children'),Output('rinse_indicator_div', 'children'),
               Output('wax_indicator_div', 'children'),Output('heater_indicator_div', 'children'),
               Output('power_button_div', 'children'),
               ],
                  Input('apply_button', 'n_clicks'),
                  [State('components_menu','value'),State('color_picker','value')]
                    )
    def update_themes(clicks,component,color_picked):
        global leds_theme ,df , components_colors , power_button_theme

        ctx = dash.callback_context
        if not ctx.triggered:
            df_colors = pd.read_csv(csv_file)
            colors_dict = df_colors.to_dict('list')
            leds_theme['secondary']=colors_dict['Leds Off State'][0]
            power_button_theme['secondary']=colors_dict['Pressure Washer Off State'][0]
            return (daq.DarkThemeProvider(theme=leds_theme, children=presoaking_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=soap_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=degreaser_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=rinse_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=wax_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=heater_indicator),
                daq.DarkThemeProvider(theme=power_button_theme, children=power_button)
                )

        if component=='Leds Off State':
            leds_theme['secondary']=color_picked['hex']
            components_colors['Leds Off State'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file,index=False)
            return (daq.DarkThemeProvider(theme=leds_theme, children=presoaking_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=soap_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=degreaser_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=rinse_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=wax_indicator),
                daq.DarkThemeProvider(theme=leds_theme, children=heater_indicator),
                dash.no_update
                )

        elif component=='Pressure Washer Off State':
            power_button_theme['secondary']=color_picked['hex']
            components_colors['Pressure Washer Off State'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file,index=False)
            return (dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                daq.DarkThemeProvider(theme=power_button_theme, children=power_button)
                )

        else:
            raise PreventUpdate

    @app.callback([Output('presoaking_button', 'style'),Output('soap_button', 'style'),Output('degreaser_button', 'style'),
               Output('rinse_button', 'style'),Output('wax_button', 'style'),Output('heater_button', 'style')
               ],
                  Input('apply_button', 'n_clicks'),
                  [State('presoaking_button', 'style'),State('soap_button', 'style'),State('degreaser_button', 'style'),
               State('rinse_button', 'style'),State('wax_button', 'style'),State('heater_button', 'style'),
                   State('components_menu','value'),State('color_picker','value')]
            )
    def update_buttons(clicks,presoaking_button,soap_button,degreaser_button,rinse_button,wax_button,heater_button,component,color_picked):
        global df, components_colors
        ctx = dash.callback_context
        if not ctx.triggered:
            df_colors = pd.read_csv(csv_file)
            colors_dict = df_colors.to_dict('list')
            presoaking_button['backgroundColor'] = colors_dict['Buttons'][0]
            soap_button['backgroundColor'] = colors_dict['Buttons'][0]
            degreaser_button['backgroundColor'] = colors_dict['Buttons'][0]
            rinse_button['backgroundColor'] = colors_dict['Buttons'][0]
            wax_button['backgroundColor'] = colors_dict['Buttons'][0]
            heater_button['backgroundColor'] = colors_dict['Buttons'][0]
            presoaking_button['color'] = colors_dict['Buttons Text'][0]
            soap_button['color'] = colors_dict['Buttons Text'][0]
            degreaser_button['color'] = colors_dict['Buttons Text'][0]
            rinse_button['color'] = colors_dict['Buttons Text'][0]
            wax_button['color'] = colors_dict['Buttons Text'][0]
            heater_button['color'] = colors_dict['Buttons Text'][0]
            return (presoaking_button, soap_button, degreaser_button, rinse_button, wax_button, heater_button)

        if component == 'Buttons':
            components_colors['Buttons'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file, index=False)
            presoaking_button['backgroundColor'] = color_picked['hex']
            soap_button['backgroundColor'] = color_picked['hex']
            degreaser_button['backgroundColor'] =color_picked['hex']
            rinse_button['backgroundColor'] = color_picked['hex']
            wax_button['backgroundColor'] = color_picked['hex']
            heater_button['backgroundColor'] = color_picked['hex']
            return (presoaking_button, soap_button, degreaser_button, rinse_button, wax_button, heater_button)

        elif component == 'Buttons Text':
            components_colors['Buttons Text'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file, index=False)
            presoaking_button['color'] = color_picked['hex']
            soap_button['color'] = color_picked['hex']
            degreaser_button['color'] = color_picked['hex']
            rinse_button['color'] = color_picked['hex']
            wax_button['color'] = color_picked['hex']
            heater_button['color'] = color_picked['hex']
            return (presoaking_button, soap_button, degreaser_button, rinse_button, wax_button, heater_button)

        else:
            raise PreventUpdate

# cycle_timer color backgroundColor label
# dict(label="Cycle Timer",style=dict(color=components_colors['Containers Label'][0],fontWeight='bold'))
    @app.callback([Output('cycle_timer','color'),Output('cycle_timer','backgroundColor'),Output('cycle_timer','label')],
              Input('apply_button', 'n_clicks'),
              [State('components_menu','value'),State('color_picker','value')]

              )
    def update_timer(clicks,component,color_picked):
        global df, components_colors
        df_colors = pd.read_csv(csv_file)
        colors_dict = df_colors.to_dict('list')
        ctx = dash.callback_context
        if not ctx.triggered:
            return (colors_dict['Timer Numbers'][0],colors_dict['Timer Background'][0],
                dict(label="Cycle Timer",style=dict(color=colors_dict['Containers Label'][0],fontWeight='bold')))

        if component=='Timer Numbers':
            components_colors['Timer Numbers'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file, index=False)
            return (color_picked['hex'],dash.no_update,dash.no_update)

        elif component=='Timer Background':
            components_colors['Timer Background'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file, index=False)
            return (dash.no_update,color_picked['hex'],dash.no_update)

        elif component=='Containers Label':
            components_colors['Containers Label'][0] = color_picked['hex']
            df = pd.DataFrame(components_colors)
            df.to_csv(csv_file, index=False)
            return (dash.no_update,dash.no_update,
                dict(label="Cycle Timer",style=dict(color=color_picked['hex'],fontWeight='bold')))

        else:
            raise PreventUpdate


    # html.Img(src='data:image/jpg;base64,{}'.format(encoded.decode()), id='logo_img', height='',width='',className='mylogo',
    #                   style=dict(marginLeft='')) logo_img_div
    @app.callback(Output('logo_img_div', 'children'),
                  Input('upload_img', 'contents'),
                  State('upload_img', 'filename'),
                  prevent_initial_call=True)
    def update_logo(list_of_contents, filename):
        logo=''

        try:
            if ('jbg' in filename) or ('jpeg' in filename ) or ('png' in filename) or ('svg' in filename):
                logo=  html.Img(src=list_of_contents, id='logo_img',className='mylogo',
                       )
                img_dict={'content':list_of_contents}
                with open(logo_file, "w") as outfile:
                    json.dump(img_dict, outfile)
        except :
            return (html.Div([
                'There was an error processing this file.',
            ],style=dict(fontSize='2vh',fontWeight='bold',color='red',textAlign='center')) )

        return logo


    # apply_button2 default_button2 contact_info_text textera

    @app.callback([Output('contact_info_text','children'),Output('contact_info_text','style')],
                  [Input('apply_button', 'n_clicks'),Input('apply_button2', 'n_clicks') ],
                  [State('textera','value'),State('contact_info_text','style'),State('contact_info_text','children'),
                   State('components_menu','value'),State('color_picker','value')]
                  )
    def update_contact_info(apply_button,apply_button2,textera,contact_info_style,contact_info_text,component,color_picked):
        global contact_info_dict
        ctx = dash.callback_context
        if not ctx.triggered:
            contact_info_style['color']=contact_info_dict['color']
            return (contact_info_dict['text'],contact_info_style)

        button_pressed = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_pressed == 'apply_button':
            if component=='Contact Info Text':
                contact_info_dict['color']=color_picked['hex']
                with open(contact_file, "w") as outfile:
                    json.dump(contact_info_dict, outfile)

                contact_info_style['color']=color_picked['hex']
                return (dash.no_update,contact_info_style)

            else:
                raise PreventUpdate

        elif button_pressed=='apply_button2':
            contact_info_dict['text']=textera
            with open(contact_file, "w") as outfile:
                json.dump(contact_info_dict, outfile)

            return (textera, dash.no_update)


    @app.callback(Output('textera','value'),
                  Input('default_button2', 'n_clicks')
                  ,prevent_initial_call=True)
    def default_contact_text(default_button2):
        with open(contact_file, 'r') as openfile:
            # Reading from json file
            contact_info_dict = json.load(openfile)
        return contact_info_dict['default_text']


'''
contact_dict = {'text': 'Custom Pressure Wash System by Bruce contact for information or support, email bruce@knevitt.com',
                'color':'indianred'}
with open("contact_info.json", "w") as outfile:
    json.dump(contact_dict, outfile)
'''
if __name__ == '__main__':
    app.run_server(host='localhost',port=8050,debug=True,dev_tools_silence_routes_logging=True)










