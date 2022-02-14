import json
import time
import serial
import random
import numpy as np
from math import sin
from ctypes import windll
import matplotlib.pyplot as plt
from win32api import GetSystemMetrics
#import RPi.GPIO as GPIO
from kivy.app import App
from kivy.utils import rgba
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen
from Popup.anchor_info_pp import AnchorInfoPopup
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

w0 = GetSystemMetrics(0)
h0 = GetSystemMetrics(1)
windll.user32.SetProcessDPIAware()
w1 = GetSystemMetrics(0)
h1 = GetSystemMetrics(1)
sf_w = w1/w0
sf_h = h1/h0

#----------------------------------------------------------------------
Window.clearcolor = (0.95, 0.95, 0.95, 1)
Config.set('graphics', 'resizable', 0)
Window.borderless = False
Window.resizable = False
Window.size = (1100, 800)

tag_counter = 0

addresses = []
objAddress = []
led_pin = 18

serial_port = serial.Serial(
    port="COM3",
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(led_pin, GPIO.OUT)
class anchors:
    def __init__(self, id, type, x, y, z, pwr):
        self.x = x
        self.y = y  
        self.z = z
        self.id = id
        self.pwr = pwr
        self.type = type

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.plt = 0
        self.scale = 0.1
        self.sensor_noise = 0
        self.is_write_txt = False
        self.in_danger = False
        self.filter_counter = 0
        self.graph_viewer = True
        self.connection_status = False

        open("filtered_value.txt", "w").close()
        open("initial_value.txt", "w").close()

    def rst_anchor(self, *args):
        main_layout = self.ids.main_layout 
        main_layout.clear_widgets()
        self.ids.boxlayout.clear_widgets()
        self.ids.tag_info_table.clear_widgets()
        self.ids.anchor_info_table.clear_widgets()
        self.ids.console_print.text = ""
        self.ids.plot_view.disabled = False
        self.ids.dynamic_view.disabled = True
        Clock.unschedule(self.get_uart_data)
        self.ids.connect_btn.text = "Connect"
        self.ids.connect_btn.disabled = False
        self.graph_viewer = True
        self.is_write_txt = False
        objAddress.clear()
        addresses.clear()
        plt.clf()

    def connect_spi(self, *args):
        global live_tag, tag_counter
        # objAddress.append( anchors('00', "anchor", 0, 0, 0, 0))
        # self.create_elements(objAddress[0])
        Clock.schedule_interval(self.get_uart_data, 0.01)
        Clock.schedule_interval(self.update_table, 0.01)

    def get_uart_data(self, *args):
        global tag_counter
        if serial_port.inWaiting() > 0:
                data = serial_port.readline().decode('utf-8')
                # print(data)
                self.ids.console_print.text += str(data)
                stm32Receiver = self.is_json(data)
                main_layout = self.ids.main_layout
                self.ids.connect_btn.text = "Connected"
                self.ids.connect_btn.disabled = True

                if stm32Receiver is not False:

                    if ((stm32Receiver["id"] in addresses) is False):

                        addresses.append(stm32Receiver["id"])

                        objAddress.append(anchors(stm32Receiver["id"], "tag", stm32Receiver["x"], stm32Receiver["y"], 0, 0))
                        lastElement = objAddress[-1]

                        # --------------------------------------------------------------------
                        self.create_elements(lastElement)

                    else: 

                        for item in objAddress:

                            if item.id == stm32Receiver["id"]:

                                item.x = float(stm32Receiver["x"])
                                item.y = float(stm32Receiver["y"])
                                
                                if self.is_write_txt is True:
                                    #------------------------------------ Kalman ----------------------------------------------
                                    f = open('initial_value.txt', 'a')
                                    f.write(f'{str(float(stm32Receiver["a"])) + "," +str(float(stm32Receiver["b"]))}')
                                    f.write('\n')
                                    f.close()
                                    f = open('filtered_value.txt', 'a')
                                    f.write(f'{str(item.x) + "," +str(item.y)}')
                                    f.write('\n')
                                    f.close()

                                if self.graph_viewer is True:
                                    tag_counter = tag_counter + 1

                                    # if tag_counter >= 10:
                                    #     main_layout.remove_widget(self.ids[str(tag_counter - 9)])

                                    lbl = Label(
                                        text = '.',
                                        size_hint=(.1, .15),
                                        pos_hint=self.ids[item.id].pos_hint,
                                        color=rgba("#ff4242"),
                                        font_size=50
                                        )
                                    self.ids[str(tag_counter)] = lbl 
                                    main_layout.add_widget(lbl)

                                    self.scale = 0.1

                                    mu_current = [item.x, item.y]

                                    self.btn_animation({'x': (float(mu_current[0])*self.scale), 'y': (int(mu_current[1])*self.scale)}, str(item.id))
                                    self.btn_animation({'x': float(mu_current[0])*self.scale - .460, 'y': int(mu_current[1])*self.scale  - .11}, str(item.id) + str("label"))
                                    self.btn_animation({'x': float(mu_current[0])*self.scale - .460, 'y': int(mu_current[1])*self.scale  + .026}, str(item.id) + str("text"))
                                    self.ids[str(item.id) + str("label")].text = str(round(mu_current[0],2)) + ',' + str(round(mu_current[1],2))
                                
                                else:
                                    self.ids.boxlayout.clear_widgets()
                                    plt.scatter(item.x, item.y, color="black")
                                    plt.xlabel("X Label")
                                    plt.ylabel("Y Label")
                                    self.ids.boxlayout.add_widget(FigureCanvasKivyAgg(plt.gcf()))

    def change_graph_viewer(self, value):
        if value == 0:
            self.ids.boxlayout.clear_widgets()
            self.ids.plot_view.disabled = False
            self.ids.dynamic_view.disabled = True
            self.graph_viewer = True
            Clock.unschedule(self.get_uart_data)
            Clock.unschedule(self.update_table)
            self.connect_spi()
        else:
            self.ids.plot_view.disabled = True
            self.ids.dynamic_view.disabled = False
            self.graph_viewer = False
            main_layout = self.ids.main_layout 
            main_layout.clear_widgets()
            objAddress.clear()
            addresses.clear()


    def write_value_to_file(self):
        self.is_write_txt = True if self.is_write_txt is False else False
        self.ids.write_txt_btn.text = "WRITING" if self.is_write_txt is True else "WRITE"

    def danger(self):
        global led_pin
        self.in_danger = True if self.in_danger is False else False
        self.ids.in_danger.text = "DANGER!" if self.in_danger is True else "DANGER"
        #GPIO.output(led_pin, self.in_danger)


    def update_table(self, *args):
        self.ids.tag_info_table.clear_widgets()
        self.ids.anchor_info_table.clear_widgets()
        for item in objAddress:
            self.add_table_items(item)


    def anchor_info(self, instance):
        anchor_info_PP = AnchorInfoPopup(instance.text, objAddress)
        anchor_info_PP.open()


    def create_elements(self, object):
        main_layout = self.ids.main_layout
        #------- Add anchor button ------
        if object.type == "anchor":

            anchor_type = "Anchor"
            uwb_type_color = "#fcba03"

        elif object.type == "tag":

            anchor_type = "Tag"
            uwb_type_color = "#217a6b"

        #------- Button create -------------
        self.add_btn(object, uwb_type_color, main_layout)                 

        #------- Add anchor ID label --------
        self.add_anchor_id_label(object, anchor_type, main_layout)

        #------- Add anchor x,y coordinates label -------
        self.add_anchor_coordinates_label(object, main_layout)

        #------- Add table items ----------
        self.add_table_items(object)


    def is_json(self, myjson):
        try:
            data = json.loads(myjson)
            return data
        except ValueError as e:
            return False
        
    def add_btn(self, i, uwb_type_color, main_layout):

        button = Button(
            pos_hint={'x': (float(i.x)*.1), 'y': (int(i.y)*.1 + .01)},
            background_color=rgba(uwb_type_color),
            size_hint=(0.075, 0.075),
            background_normal='',
            background_down="",
            text=str(i.id)
            )
        button.bind(on_press=self.anchor_info)
        self.ids[str(i.id)] = button
        main_layout.add_widget(button)

    
    def add_anchor_id_label(self, i, anchor_type, main_layout):

        label_id = Label(
            pos_hint={'x': (int(i.x)*.1) - .460, 'y': (int(i.y)*.001 + .025)},
            color=rgba('#555555'),
            size_hint= (1, 0.17),
            text=anchor_type,
            font_size=15,
            bold=True
            )
        self.ids[str(i.id + str("text"))] = label_id
        main_layout.add_widget(label_id)


    def add_anchor_coordinates_label(self, i, main_layout):

        label = Label(
            pos_hint={'x': (int(i.x)*.1) - .460, 'y': (int(i.y)*.1) - .103},
            text=str(i.x) + ',' + str(i.y),
            color=rgba('#555555'),
            size_hint= (1, 0.17),
            font_size=15,
            bold=True
            )
        self.ids[str(i.id + str("label"))] = label
        main_layout.add_widget(label)


    def add_table_items(self, i):

        if i.type == "anchor":

            self.add_anchor_label(i.id)
            self.add_anchor_label(round(i.x,2))
            self.add_anchor_label(round(i.y,2))
            self.add_anchor_label(round(i.z,2))

        elif i.type == "tag":

            self.add_tag_label(i.id)
            self.add_tag_label(round(i.x,2))
            self.add_tag_label(round(i.y,2))
            self.add_tag_label(round(i.z,2))
            self.add_tag_label(i.pwr)

    
    def add_anchor_label(self, i):

        label = Label(
                    text=str(i),
                    color= rgba("#000000")
                )
        self.ids.anchor_info_table.add_widget(label)


    def add_tag_label(self, i):

        label = Label(
                    text=str(i),
                    color= rgba("#000000")
                )
        self.ids.tag_info_table.add_widget(label)


    def btn_animation(self, position, id):
        ani=Animation(pos_hint=position)
        ani.start(self.ids[id])
        

with open("Popup/kv/anchor_info_popup.kv", encoding='utf8') as f:
    Builder.load_string(f.read())
    f.close()

with open("Pages/main.kv", encoding='utf8') as f:
    mainPage = Builder.load_string(f.read())
    f.close()  

class MyApp(App):

    def build(self):
        return mainPage

if __name__ == '__main__':
    MyApp().run()
