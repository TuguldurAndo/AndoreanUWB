from kivy.uix.popup import Popup
import json

with open('static_data.json') as f:
    json_data = json.loads(f.read())
    f.close()

class AnchorInfoPopup(Popup):

    def __init__(self, id, **kwargs):
        super(AnchorInfoPopup, self).__init__(**kwargs)
        data = json.loads(json.dumps(json_data))
        print(id)
        for i in data[0]["ids"]:
          if i['id'] == id:
            self.ids.id_num.text = i["id"]
            self.ids.x_axis.text = i["x"] + ' (m)'
            self.ids.y_axis.text = i["y"] + ' (m)'
            self.ids.z_axis.text = i["z"] + ' (m)'
            self.ids.type.text = i["type"]
            self.ids.pwr.text = i["pwr"]
