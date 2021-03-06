# -*- coding: utf-8 -*-
#!/usr/bin/env python
##### System wide lib #####

##### Theory lib #####
from theory.gui import field
from theory.gui.form import SimpleGuiForm

##### Theory third-party lib #####

##### Local app #####
from . import BaseUIAdapter

##### Theory app #####

##### Misc #####

__all__ = ("TerminalAdapter",)

class TerminalForm(SimpleGuiForm):
  stdOut = field.TextField(label="Standard Output")
  #stdErr = field.TextField(label="Standard Error")

class TerminalAdapter(BaseUIAdapter):
  _stdOut = ""
  _stdErr = ""

  @property
  def stdOut(self):
    return self._stdOut
    #self.preStdOutPacker()
    #r = self.stdOutPacker()
    #return self.postStdOutPacker(r)

  def preStdOutPacker(self):
    if(self._stdOut=="" and self._stdRowOut!=[]):
      self._stdOut = self._stdOutLineBreak.join(self._stdRowOut)

  def stdOutPacker(self):
    return self._stdOut

  def postStdOutPacker(self, r):
    return r

  @stdOut.setter
  def stdOut(self, stdOut):
    self._stdOut = stdOut

  @property
  def stdErr(self):
    return self._stdErr

  @stdErr.setter
  def stdErr(self, stdErr):
    self._stdErr = stdErr

  def render(self, *args, **kwargs):
    super(TerminalAdapter, self).render(*args, **kwargs)
    bx = kwargs["uiParam"]["bx"]
    bx.clear()

    o = TerminalForm()
    o.fields["stdOut"].initData = self.stdOut
    #o.fields["stdErr"].initData = self.stdErr
    o.generateForm(**kwargs["uiParam"])
    self.terminalForm = o
    kwargs["stdOutAdjuster"](self.stdOut, "\n")
