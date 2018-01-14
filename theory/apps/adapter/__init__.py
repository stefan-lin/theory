# -*- coding: utf-8 -*-
#!/usr/bin/env python
##### System wide lib #####
from abc import ABCMeta, abstractmethod

##### Theory lib #####

##### Theory third-party lib #####

##### Local app #####

##### Theory app #####

##### Misc #####

class BaseAdapter(object):
  abstract = True

  def toDb(self):
    """This function is being used when the conversion needs to be
    separated and should be called after all properties were being assigned
    and before serialization.
    """
    return True

  def fromDb(self):
    """This function is being used when the conversion needs to be
    separated and should be called after serialization.
    """
    return True

  def run(self):
    """This function is being used when the conversion does not need to be
    separated and should be called after all properties were being assigned.
    """
    return self.toDb() and self.fromDb()

class BaseUIAdapter(BaseAdapter):
  abstract = True
  """Any adapter which interacted with UI should inheritage from this class.
  The render fxn must be a static method which will be called in the gui side.
  """

  @abstractmethod
  def toUi(self):
    pass

  @abstractmethod
  def fromUi(self):
    pass

  @staticmethod
  def render(data, uiParam, callReactor):
    raise NotImplementedError
