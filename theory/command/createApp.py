# -*- coding: utf-8 -*-
##### System wide lib #####
import os
from shutil import copytree

##### Theory lib #####
from theory.conf import settings

##### Theory third-party lib #####

##### Local app #####
from .baseCommand import BaseCommand

##### Theory app #####

##### Misc #####

class CreateApp(BaseCommand):
  """
  Start an Theory app
  """
  name = "createApp"
  verboseName = "createApp"
  params = ["name",]
  _notations = ["Command",]
  _gongs = ["Terminal", ]

  @property
  def name(self):
    return self._name

  @name.setter
  def name(self, name):
    self._name = name

  def run(self, *args, **kwargs):
    fromPath = os.path.join(os.path.dirname(os.path.dirname(__file__)),
        "conf", "app_template")
    toPath = os.path.join(settings.APPS_ROOT, self.name)
    self._stdOut += "Coping" + fromPath + " --> " + toPath + "<br/>"
    copytree(fromPath, toPath)
    self._stdOut += \
        "Don't forget to add the app name into the INSTALLED_APP within "\
        "your project's setting. To make your app recognized by theory, you "\
        "will also need to restart theory or run the probeModule command"



