from logging import StringTemplateStyle
import kivy
import random
from kivy.utils import rgba
import mysql.connector
import json
import time
import serial
import RPi.GPIO as GPIO

kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.screenmanager import Screen

from Popup.anchor_info_pp import AnchorInfoPopup
from kivy.config import Config

Config.set('graphics','resizable',0)
Window.clearcolor = (0.95, 0.95, 0.95, 1)
Window.size = (800, 600)

serial_port = serial.Serial(
    port="/dev/ttyTHS0",
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

#mydb = mysql.connector.connect(
 # host="localhost",
 # user="root",
 # password="Tuguldur#123",
 # database="andorean",
#)

#mycursor = mydb.cursor()

#print(mydb)

counter = 0
counter_1 = 0
tag_counter = 0

addresses = []
objAddress = []
led_pin = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin, GPIO.OUT)

class anchors:
    def __init__(self, id, type, x, y, z, pwr):
        self.id = id
        self.type = type
        self.x = x
        self.y = y  
        self.z = z
        self.pwr = pwr

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.connection_status = False
        self.scale = 0.1
        self.in_danger = False
        self.filter_uwb = 0
        self.filter_counter = 0

    def rst_anchor(self, *args):
        global counter_1, counter
        main_layout = self.ids.main_layout
        main_layout.clear_widgets()
        self.ids.tag_info_table.clear_widgets()
        self.ids.anchor_info_table.clear_widgets()
        counter = 0
        counter_1 = 0
        objAddress.clear()
        addresses.clear()
        Clock.unschedule(self.get_uart_data)
        self.ids.connect_btn.text = "Connect"
        self.ids.connect_btn.disabled = False

    def connect_spi(self, *args):
        global live_tag, counter_1, tag_counter
        objAddress.append( anchors('00', "anchor", 0, 0, 0, 0))
        self.create_elements(objAddress[0])

        Clock.schedule_interval(self.get_uart_data, 0.01)
        Clock.schedule_interval(self.update_table, 5)

    def get_uart_data(self, *args):
        global counter_1, tag_counter
        main_layout = self.ids.main_layout
        if serial_port.inWaiting() > 0:
                data = serial_port.readline().decode('ascii')
                print(data)
                stm32Receiver = self.is_json(data)

                self.ids.connect_btn.text = "Connected"
                self.ids.connect_btn.disabled = True

                if stm32Receiver is not False:

                    if ((stm32Receiver["id"] in addresses) is False):

                        addresses.append(stm32Receiver["id"])

                        if stm32Receiver["error"] is False:

                            objAddress.append(anchors(stm32Receiver["id"], "tag", stm32Receiver["distance"], 0, 0, 0))
                            lastElement = objAddress[-1]

                            # --------------------------------------------------------------------
                            self.create_elements(lastElement)

                    else: 

                        for item in objAddress:

                            if item.id == stm32Receiver["id"]:

                                if stm32Receiver["error"] is False:

                                    self.filter_uwb = self.filter_uwb + float(stm32Receiver["distance"])
                                    self.filter_counter += 1

                                    if self.filter_counter == 10:
                                        print(self.filter_uwb/10)
                                        self.filter_counter = 0
                                        f = open('uwb.txt', 'a')
                                        f.write(f'{str(self.filter_uwb/10)}')
                                        f.write('\n')
                                        f.close()
                                        #------- Add table items ----------
                                        item.x = self.filter_uwb/10
                                        tag_counter = tag_counter + 1

                                        if tag_counter >= 10:
                                            main_layout.remove_widget(self.ids[str(tag_counter - 9)])

                                        lbl = Label(
                                            text = '.',
                                            size_hint=(.1, .15),
                                            pos_hint=self.ids[item.id].pos_hint,
                                            color=rgba("#ff4242"),
                                            font_size=50
                                            )
                                        self.ids[str(tag_counter)] = lbl
                                        main_layout.add_widget(lbl)

                                        if float(item.x) < 10:
                                            self.scale = 0.1
                                        else:
                                            self.scale = 0.05

                                        self.btn_animation({'x': (float(item.x)*self.scale), 'y': (int(item.y)*.1 + .01)}, str(item.id))
                                        self.btn_animation({'x': float(item.x)*self.scale - .460, 'y': int(item.y)*.001  - .1}, str(item.id) + str("label"))
                                        self.btn_animation({'x': float(item.x)*self.scale - .460, 'y': int(item.y)*.001  + .025}, str(item.id) + str("text"))
                                        self.ids[str(item.id) + str("label")].text = str(round(item.x,2)) + ',' + str(item.y)

                                        self.filter_uwb = 0

    def danger(self):
        global led_pin
        self.in_danger = True if self.in_danger is False else False
        self.ids.in_danger.text = "DANGER!" if self.in_danger is True else "DANGER"
        GPIO.output(led_pin, self.in_danger)

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
            text=str(i.id),
            size_hint=(0.075, 0.075),
            pos_hint={'x': (float(i.x)*.1), 'y': (int(i.y)*.1 + .01)},
            background_color=rgba(uwb_type_color),
            background_normal='',
            background_down=""
            )
        button.bind(on_press=self.anchor_info)
        self.ids[str(i.id)] = button
        main_layout.add_widget(button)
    
    def add_anchor_id_label(self, i, anchor_type, main_layout):
        label_id = Label(
            text=anchor_type,
            pos_hint={'x': (int(i.x)*.1) - .460, 'y': (int(i.y)*.001 + .025)},
            font_size=15,
            color=rgba('#555555'),
            bold=True,
            size_hint= (1, 0.17)
            )
        self.ids[str(i.id + str("text"))] = label_id
        main_layout.add_widget(label_id)

    def add_anchor_coordinates_label(self, i, main_layout):
        label = Label(
            text=str(i.x) + ',' + str(i.y),
            pos_hint={'x': (int(i.x)*.1) - .460, 'y': (int(i.y)*.1) - .103},
            font_size=15,
            color=rgba('#555555'),
            bold=True,
            size_hint= (1, 0.17)
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