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
import numpy as np
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
#----------------------------------------------------------------------

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

mu_0 = np.array([0, 0])
Sigma_0 = np.array([[0.1, 0],
                     [0, 0.1]])
u_t = np.array([1, 1]) # we assume constant control input

A = np.array([[0.9, 0],
              [0, 0.9]])
B = np.array([[0.26, 0],
              [0, 0.5]])
Q = np.array([[0.3, 0],
              [0, 0.3]])
H = np.array([[0.9, 0],
              [0, 0.7]])
R = np.array([[1, 0],
              [0, 1]])

# Initialize empty lists to store the filtered states and measurements for plotting
measurement_states = []
filtered_states = []

# state = [x_pos, y_pos]
num_steps = 10
ground_truth_xs = np.linspace(0, 10, num=num_steps + 1) # [0, 1, ..., 10]
ground_truth_ys = ground_truth_xs.copy() # x = y
ground_truth_states = np.stack((ground_truth_xs,ground_truth_ys), axis=1) # ground_truth_states is [[0,0], [1,1], ..., [10,10]]

# Run KF for each time step
mu_current = mu_0.copy()
Sigma_current = Sigma_0.copy()

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
        self.filter_x = 0
        self.filter_y = 0
        self.filter_counter = 0
        self.sensor_noise = 0
        self.previous_x = 1
        self.previous_y = 1
        self.error = 1
        self.kalman_gain = 0
        self.current_x = 0
        self.current_y = 0
        self.q = 0.15
        self.p = self.error + self.q
        self.r = 0.1

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

                        objAddress.append(anchors(stm32Receiver["id"], "tag", stm32Receiver["x"], stm32Receiver["y"], 0, 0))
                        lastElement = objAddress[-1]

                        # --------------------------------------------------------------------
                        self.create_elements(lastElement)

                    else: 

                        for item in objAddress:

                            if item.id == stm32Receiver["id"]:

                                self.filter_x = self.filter_x + float(stm32Receiver["x"])
                                self.filter_y = self.filter_y + float(stm32Receiver["y"])

                                self.filter_counter += 1

                                #if self.filter_counter == 5:
                                    #print(self.filter_x/5)
                                    #print(self.filter_y/5)
                                    #self.filter_counter = 0
                                    #f = open('uwb.txt', 'a')
                                    #f.write(f'{str(self.filter_uwb/10)}')
                                    #f.write('\n')
                                    #f.close()
                                    #------- Add table items ----------
                                    #item.x = self.filter_x/5
                                    #item.y = self.filter_y/5
                                item.x = float(stm32Receiver["x"])
                                item.y = float(stm32Receiver["y"])
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

                                global predicted_mu, predicted_Sigma, mu_current, Sigma_current
                                # Predict step
                                predicted_mu, predicted_Sigma = predict(A, B, Q, u_t, mu_current, Sigma_current)
                                
                                # Get measurement (in real life, we get this from our sensor)    
                                measurement_noise = [item.x, item.y]
                                new_measurement = H @ measurement_noise # this is z_t
                                
                                # The rest of update step
                                mu_current, Sigma_current = update(H, R, new_measurement, predicted_mu, predicted_Sigma)
                                
                                # Store measurements and mu_current so we can plot it later
                                measurement_states.append(new_measurement)
                                filtered_states.append(mu_current)

                                print(mu_current)


                                #------------------------------------ Kalman ----------------------------------------------
                                # #---------------update-----------------------
                                # self.kalman_gain = self.p / (self.p) + self.r
                                # self.current_x = self.previous_x + self.kalman_gain * (item.x - self.previous_x)
                                # self.current_y = self.previous_y + self.kalman_gain * (item.y - self.previous_y)
                                # self.p = (1 - self.kalman_gain) * self.p
                                # #---------------predict---------------------
                                # self.previous_x = self.current_x
                                # self.previous_x = self.current_y
                                # self.p = self.p + self.q
                                # print(self.kalman_gain)
                                #------------------------------------------------------------------------------------------
                                # print(self.current_x)
                                # print(self.current_y)
                                f = open('uwb.txt', 'a')
                                f.write(f'{str(mu_current[0]) + "," +str(mu_current[1])}')
                                f.write('\n')
                                f.close()
                                f = open('uwb_1.txt', 'a')
                                f.write(f'{str(item.x) + "," +str(item.y)}')
                                f.write('\n')
                                f.close()
                                self.btn_animation({'x': (float(mu_current[0])*self.scale), 'y': (int(mu_current[1])*.1)}, str(item.id))
                                self.btn_animation({'x': float(mu_current[0])*self.scale - .460, 'y': int(mu_current[1])*.1  - .11}, str(item.id) + str("label"))
                                self.btn_animation({'x': float(mu_current[0])*self.scale - .460, 'y': int(mu_current[1])*.1  + .026}, str(item.id) + str("text"))
                                self.ids[str(item.id) + str("label")].text = str(round(mu_current[0],2)) + ',' + str(round(mu_current[1],2))

                                self.filter_x = 0
                                self.filter_y = 0

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


def predict(A, B, Q, u_t, mu_t, Sigma_t):
    predicted_mu = A @ mu_t + B @ u_t
    predicted_Sigma = A @ Sigma_t @ A.T + Q
    return predicted_mu, predicted_Sigma

def update(H, R, z, predicted_mu, predicted_Sigma):
    residual_mean = z - H @ predicted_mu
    residual_covariance = H @ predicted_Sigma @ H.T + R
    kalman_gain = predicted_Sigma @ H.T @ np.linalg.inv(residual_covariance)
    updated_mu = predicted_mu + kalman_gain @ residual_mean
    updated_Sigma = predicted_Sigma - kalman_gain @ H @ predicted_Sigma
    return updated_mu, updated_Sigma

class MyApp(App):

    def build(self):
        return mainPage

if __name__ == '__main__':
    MyApp().run()
