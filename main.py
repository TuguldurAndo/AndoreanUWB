import kivy
import random
from kivy.utils import rgba
import mysql.connector
import json
import time

kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup

from Popup.anchor_info_pp import AnchorInfoPopup

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
counter_1 = 0
tag_counter = 0

with open('static_data.json') as f:
    json_data = json.loads(f.read())
    f.close()

with open('tag_movement.json') as f:
    live_tag = json.loads(f.read())
    f.close()


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.connection_status = False

    def rst_anchor(self, *args):
        global counter_1, counter
        main_layout = self.ids.main_layout
        main_layout.clear_widgets()
        self.ids.tag_info_table.clear_widgets()
        self.ids.anchor_info_table.clear_widgets()
        counter = 0
        counter_1 = 0

    def connect_spi(self, *args):
        global json_data
        data = json_data
        for i in data[0]["ids"]:
            main_layout = self.ids.main_layout
            #------- Add anchor button ------
            if i["type"] == "anchor":
                uwb_btn_image = 'assets/anchor.png'
            elif i["type"] == "tag":
                uwb_btn_image = 'assets/tag.png'

            button = Button(
                text=i["id"],
                color=rgba(1,1,1,0),
                size_hint=(.1, .1),
                pos_hint={'x': int(i["x"])*.001, 'y': int(i["y"])*.001},
                background_normal=uwb_btn_image,
                background_down=""
                )
            button.bind(on_press=self.anchor_info)
            self.ids[str(i["id"])] = button

            #------- Add anchor ID label -------
            label_id = Label(
                text=i["id"],
                pos_hint={'x': (int(i["x"])*.001) - .45, 'y': (int(i["y"])*.001 + .025)},
                font_size=25,
                color=rgba('#555555'),
                bold=True,
                size_hint= (1, 0.17)
                )
            self.ids[str(i["id"] + str("text"))] = label_id
            #------- Add anchor x,y coordinates label -------
            label = Label(
                text=i["x"] + ',' + i["y"],
                pos_hint={'x': (int(i["x"])*.001) - .4475, 'y': (int(i["y"])*.001) - .1},
                font_size=25,
                color=rgba('#555555'),
                bold=True,
                size_hint= (1, 0.17)
                )
            self.ids[str(i["id"] + str("label"))] = label
            main_layout.add_widget(label_id)
            main_layout.add_widget(label)
            main_layout.add_widget(button)

            if i["type"] == "anchor":
                label = Label(
                    text=i["id"],
                    color= rgba("#000000")
                    )
                self.ids.anchor_info_table.add_widget(label)
                label = Label(
                    text=i["x"],
                    color= rgba("#000000")
                    )
                self.ids.anchor_info_table.add_widget(label)
                label = Label(
                    text=i["y"],
                    color= rgba("#000000")
                    )
                self.ids.anchor_info_table.add_widget(label)
                label = Label(
                    text=i["z"],
                    color= rgba("#000000")
                    )
                self.ids.anchor_info_table.add_widget(label)
            elif i["type"] == "tag":
                label = Label(
                    text=i["id"],
                    color= rgba("#000000")
                    )
                self.ids.tag_info_table.add_widget(label)
                label = Label(
                    text=i["x"],
                    color= rgba("#000000")
                    )
                self.ids.tag_info_table.add_widget(label)
                label = Label(
                    text=i["y"],
                    color= rgba("#000000")
                    )
                self.ids.tag_info_table.add_widget(label)
                label = Label(
                    text=i["z"],
                    color= rgba("#000000")
                    )
                self.ids.tag_info_table.add_widget(label)
                label = Label(
                    text=i["pwr"],
                    color= rgba("#000000")
                    )
                self.ids.tag_info_table.add_widget(label)

        Clock.schedule_interval(self.tag_tracking, 1)

    def anchor_info(self, instance):
        anchor_info_PP = AnchorInfoPopup(instance.text)
        anchor_info_PP.open()

    def tag_tracking(self, *args):
        global live_tag, counter_1, tag_counter
        main_layout = self.ids.main_layout
        tag_counter = tag_counter + 1

        button = Button(
            text=str(tag_counter),
            size_hint=(.03, .03),
            pos_hint=self.ids[live_tag[0]["ids"][counter_1]["id"]].pos_hint,
            background_normal='',
            background_color=rgba("#ff4242")
            )
        main_layout.add_widget(button)

        self.ids[live_tag[0]["ids"][counter_1]["id"]].pos_hint = {'x': int(live_tag[0]["ids"][counter_1]["x"])*.001, 'y': int(live_tag[0]["ids"][counter_1]["y"])*.001}
        self.ids[live_tag[0]["ids"][counter_1]["id"] + str("label")].pos_hint = {'x': int(live_tag[0]["ids"][counter_1]["x"])*.001 - .4525, 'y': int(live_tag[0]["ids"][counter_1]["y"])*.001  - .1}
        self.ids[live_tag[0]["ids"][counter_1]["id"] + str("text")].pos_hint = {'x': int(live_tag[0]["ids"][counter_1]["x"])*.001 - .45, 'y': int(live_tag[0]["ids"][counter_1]["y"])*.001  + .025}
        self.ids[live_tag[0]["ids"][counter_1]["id"] + str("label")].text = live_tag[0]["ids"][counter_1]["x"] + ',' + live_tag[0]["ids"][counter_1]["y"]

        counter_1 = counter_1 + 1
        if counter_1 == 5:
            Clock.unschedule(self.tag_tracking)

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
