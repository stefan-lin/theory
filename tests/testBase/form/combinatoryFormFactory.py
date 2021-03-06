# -*- coding: utf-8 -*-
##### System wide lib #####
from copy import deepcopy
from datetime import datetime
import os

##### Theory lib #####
from theory.apps.model import Command
from theory.gui import field
from theory.gui.form import Form

##### Theory third-party lib #####

##### Local app #####

##### Theory app #####

##### Misc #####

__all__ = (
    'CombinatoryFormFactory',
    )

def getTestCaseFileAbsPath():
  return os.path.join(
      os.path.dirname(os.path.dirname(__file__)),
      "testsFile",
      "field"
  )

def getBinaryDefault():
  return bin(10)

def getImageDefault():
  return os.path.join(getTestCaseFileAbsPath(), "jpeg.jpg")

def getFileDefault():
  return getImageDefault()

def getBooleanDefault():
  return True

def getNullBooleanDefault():
  return None

#def getDateTimeDefault():
#  return datetime.now()
#
#def getComplexDateTimeDefault():
#  return datetime.now()

def getGeoPointDefault():
  return [1.0, 1.0]

def getDecimalDefault():
  return 1.0

def getFloatDefault():
  return 1.0

def getIntDefault():
  return 1

def getFilePathDefault():
  return os.path.join(getTestCaseFileAbsPath(), "jpeg.jpg")

def getDirPathDefault():
  return getTestCaseFileAbsPath()

def getStringDefault():
  return u"test"

def getEmailDefault():
  return u"test@test.com"

def getURLDefault():
  return u"http://google.com"

def getRegexDefault():
  return u"^.?"

def getAdapterDefault():
  return u"theory.adapter.terminal"

def getIPAddressDefault():
  return u"192.168.1.1"

def getGenericIPAddressDefault():
  return u"192.168.1.1"

def getSlugDefault():
  return u"theory-lab"

def getTypedChoiceDefault():
  return 1

def getTypedMultipleChoiceDefault():
  return [1, 2]

def getPythonModuleDefault():
  return "theory.core"

def getPythonClassDefault():
  return "theory.core.reactor.Reactor"

def getQuerysetDefault():
  return Command.objects.all()


def getChoiceSelection():
  return ((1, "1",), (2, "2",), (3, "3",),)

defaultValueSet1 = {
    "Binary": getBinaryDefault(),
    "Image": getImageDefault(),
    "File": getImageDefault(),
    "Dir": getDirPathDefault(),
    "Boolean": getBooleanDefault(),
    "NullBoolean": getNullBooleanDefault(),
    "DateTime": datetime.now(),
    "Time": datetime.now().time(),
    "GeoPoint": getGeoPointDefault(),
    "Decimal": getDecimalDefault(),
    "Float": getFloatDefault(),
    "Int": getIntDefault(),
    "String": getStringDefault(),
    "Email": getEmailDefault(),
    "URL": getURLDefault(),
    "Regex": getRegexDefault(),
    "Adapter": getAdapterDefault(),
    "IPAddress": getIPAddressDefault(),
    "GenericIPAddress": getGenericIPAddressDefault(),
    "FilePath": getFilePathDefault(),
    "Slug": getSlugDefault(),
    "Choice": 1,
    "MultipleChoice": [1, 2],
    "TypedChoice": getTypedChoiceDefault(),
    "TypedMultipleChoice": getTypedMultipleChoiceDefault(),
    "PythonModule": getPythonModuleDefault(),
    "PythonClass": getPythonClassDefault(),
    "Queryset": getQuerysetDefault(),
}

class CombinatoryFormWithDefaultValue(Form):
  textField = field.TextField(initData=defaultValueSet1["String"])
  integerField = field.IntegerField(initData=defaultValueSet1["Int"])
  regexField = field.RegexField(defaultValueSet1["Regex"], initData=defaultValueSet1["String"])
  emailField = field.EmailField(initData=defaultValueSet1["Email"])
  fileField = field.FileField(initData=defaultValueSet1["File"])
  imageField = field.ImageField(initData=defaultValueSet1["Image"])
  filePathField = field.FilePathField(initData=defaultValueSet1["File"])
  imagePathField = field.ImagePathField(initData=defaultValueSet1["File"])
  dirPathField = field.DirPathField(initData=defaultValueSet1["Dir"])

  uRLField = field.URLField(initData=defaultValueSet1["URL"])
  booleanField = field.BooleanField(initData=defaultValueSet1["Boolean"])
  nullBooleanField = field.NullBooleanField(initData=defaultValueSet1["Boolean"])

  choiceField = field.ChoiceField(initData=defaultValueSet1["Choice"], choices=getChoiceSelection())
  multipleChoiceField = field.MultipleChoiceField(initData=defaultValueSet1["MultipleChoice"], choices=getChoiceSelection())

  adapterField = field.AdapterField(initData=defaultValueSet1["Adapter"])
  floatField = field.FloatField(initData=defaultValueSet1["Float"])
  decimalField = field.DecimalField(initData=defaultValueSet1["Decimal"])
  iPAddressField = field.IPAddressField(initData=defaultValueSet1["IPAddress"])
  genericIPAddressField = field.GenericIPAddressField(initData=defaultValueSet1["GenericIPAddress"])
  filePathField = field.FilePathField(getTestCaseFileAbsPath(), initData=defaultValueSet1["FilePath"])
  slugField = field.SlugField(initData=defaultValueSet1["Slug"])

  typedChoiceField = field.TypedChoiceField(initData=defaultValueSet1["TypedChoice"], choices=getChoiceSelection())
  typedMultipleChoiceField = field.TypedMultipleChoiceField(initData=defaultValueSet1["TypedMultipleChoice"], choices=getChoiceSelection())

  pythonModuleField = field.PythonClassField(initData=defaultValueSet1["PythonModule"])
  pythonClassField = field.PythonClassField(initData=defaultValueSet1["PythonClass"])
  querysetField = field.QuerysetField(initData=defaultValueSet1["Queryset"])

  #binaryField = field.BinaryField(initData=defaultValueSet1["Binary"])
  dateField = field.DateField(initData=defaultValueSet1["DateTime"])
  dateTimeField = field.DateTimeField(initData=defaultValueSet1["DateTime"])
  timeField = field.TimeField(initData=defaultValueSet1["Time"])
  #geoPointField = field.GeoPointField(initData=defaultValueSet1["GeoPoint"])

  __name__ = "CombinatoryFormWithDefaultValueForm"

class CombinatoryFormFactory(object):
  def __init__(self, *args, **kwargs):
    super(CombinatoryFormFactory, self).__init__(*args, **kwargs)

  def getCombinatoryFormWithDefaultValue(self):
    return CombinatoryFormWithDefaultValue()

