import kivy
import random
from kivy.utils import rgba
import mysql.connector
from serial.tools import list_ports

kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.screenmanager import ScreenManager, Screen

Window.clearcolor = (0.95, 0.95, 0.95, 1)
Window.size = (1000, 800)

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Tuguldur#123",
  database="andorean",
)

mycursor = mydb.cursor()

print(mydb)

counter = 0

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.connection_status = False

    def add_anchor(self, *args):
        global counter
        main_layout = self.ids.main_layout
        counter = counter + 1
        button = Button(
            text='Anchor' + str(counter),
            size_hint=(.1, .1),
            pos_hint={'x': round(random.uniform(0.1, 0.9), 2), 'y': round(random.uniform(0.1, 0.9), 2)}
            )
        main_layout.add_widget(button)

    def get_selected_serial(self, name):
        print(name)

    def rst_anchor(self, *args):
        main_layout = self.ids.main_layout
        main_layout.clear_widgets()

    def showAvailablePorts(self):
        dropdown = DropDown()
        port_list = []
        for i, port in enumerate(list_ports.comports()):
            port_list.append(str(port.device))

        self.ids.port_status_unconnected.opacity = 0

        self.ids.select_port.values = port_list
        self.ids.select_port.text = "Please select a port"

    def serial_connection_status(self):
        if self.connection_status is True:
            self.ids.port_status_unconnected.opacity = 1
        else:
            self.ids.port_status_unconnected.opacity = 0

with open("Pages/main.kv", encoding='utf8') as f:
    mainPage = Builder.load_string(f.read())
    f.close()

class MyApp(App):

    def build(self):
        return mainPage

if __name__ == '__main__':
    MyApp().run()
