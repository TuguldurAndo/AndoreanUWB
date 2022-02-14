from kivy.uix.popup import Popup
import json

class AnchorInfoPopup(Popup):

    def __init__(self, id, obj, **kwargs):
        super(AnchorInfoPopup, self).__init__(**kwargs)

        for i in obj:
          if i.id == id:
            self.ids.id_num.text = i.id
            self.ids.x_axis.text = str(i.x) + ' (m)'
            self.ids.y_axis.text = str(i.y) + ' (m)'
            self.ids.z_axis.text = str(i.z) + ' (m)'
            self.ids.type.text = i.type
            self.ids.pwr.text = str(i.pwr)
