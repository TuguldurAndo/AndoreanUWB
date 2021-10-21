import kivy
kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.button import Button
import random
import mysql.connector
from kivy.uix.screenmanager import ScreenManager, Screen

Window.clearcolor = (0.95, 0.95, 0.95, 1)
Window.size = (1000, 800)

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="admin",
  database="andorean"
)

mycursor = mydb.cursor()

print(mydb)

class MainScreen(Screen):
    def add_anchor(self, *args):
        main_layout = self.ids.main_layout
        button = Button(
            text='Hello world', 
            size_hint=(.1, .1),
            pos_hint={'x': round(random.uniform(0.1, 0.9), 2), 'y': round(random.uniform(0.1, 0.9), 2)}
            )
        main_layout.add_widget(button)
    
    def rst_anchor(self, *args):
        main_layout = self.ids.main_layout
        main_layout.clear_widgets()



with open("Pages/main.kv", encoding='utf8') as f:
    mainPage = Builder.load_string(f.read())
    f.close()

class MyApp(App):

    def build(self):
        return mainPage

if __name__ == '__main__':
    MyApp().run()