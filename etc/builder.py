from iocbuilder import AutoSubstitution, SetSimulation, Device, Architecture, ModuleBase
from iocbuilder.arginfo import *

from iocbuilder.modules.motor import basic_asyn_motor, MotorRecord
from iocbuilder.modules.tpmac import DeltaTau, DeltaTauCommsPort
from iocbuilder.modules.asyn import AsynPort
from iocbuilder.modules.calc import Calc
from iocbuilder.modules.busy import Busy
from iocbuilder.modules.seq import Seq
from iocbuilder.modules.genSub import GenSub
from iocbuilder.modules.streamDevice import AutoProtocol

import os, sys

class PmacUtil(Device):
    Dependencies = (GenSub,Seq)
    LibFileList = ["pmacUtil"]
    DbdFileList = ["pmacUtilSupport"]
    AutoInstantiate = True

class autohome(AutoSubstitution):
    TemplateFile = 'autohome.template'
autohome.ArgInfo.descriptions["PORT"] = Ident("Delta tau motor controller comms port", DeltaTauCommsPort)

def add_basic(cls):
    """Convenience function to add basic_asyn_motor attributes to a class that
    includes it via an msi include statement rather than verbatim"""
    cls.Arguments += basic_asyn_motor.Arguments + [x for x in cls.Arguments if x not in basic_asyn_motor.Arguments]
    cls.ArgInfo = basic_asyn_motor.ArgInfo + cls.ArgInfo.filtered(without=basic_asyn_motor.ArgInfo.Names())
    cls.Defaults.update(basic_asyn_motor.Defaults)
    return cls

try:
    from iocbuilder.modules.pmacCoord import PmacCoord, CS

    @add_basic
    class dls_pmac_asyn_motor(AutoSubstitution, AutoProtocol, MotorRecord):
        WarnMacros = False
        TemplateFile = 'dls_pmac_asyn_motor.template'
        ProtocolFiles = ['pmac.proto']
        Dependencies = (Busy,PmacCoord)
    dls_pmac_asyn_motor.ArgInfo.descriptions["PORT"] = Ident("Delta tau motor controller", DeltaTau)
    dls_pmac_asyn_motor.ArgInfo.descriptions["SPORT"] = Ident("Delta tau motor controller comms port", DeltaTauCommsPort)

    @add_basic
    class dls_pmac_cs_asyn_motor(AutoSubstitution):
        WarnMacros = False
        TemplateFile = 'dls_pmac_cs_asyn_motor.template'
        Dependencies = (Busy,)
    dls_pmac_cs_asyn_motor.ArgInfo.descriptions["PORT"] = Ident("Delta tau motor CS", CS)
        
except ImportError:
    print "# pmacCoord not found, dls_pmac_asyn_motor will not be available"

class _pmacStatusAxis(AutoSubstitution, AutoProtocol):
    ProtocolFiles = ['pmac.proto']
    TemplateFile = 'pmacStatusAxis.template'

class pmacStatus(AutoSubstitution, AutoProtocol):
    Dependencies = (PmacUtil,)
    ProtocolFiles = ['pmac.proto']
    TemplateFile = 'pmacStatus.template'

    def __init__(self, **args):
        # init the super class
        self.__super.__init__(**args)
        self.axes = []
        NAXES = int(args["NAXES"])
        assert NAXES in range(1,33), "Number of axes (%d) must be in range 1..32" % NAXES
        # for each axis
        for i in range(1, NAXES + 1):
            args["AXIS"] = i
            # make a _pmacStatusAxis instance
            self.axes.append(
                _pmacStatusAxis(
                    **filter_dict(args, _pmacStatusAxis.ArgInfo.Names())))
pmacStatus.ArgInfo.descriptions["PORT"] = Ident("Delta tau motor controller comms port", DeltaTauCommsPort)

class gather(AutoSubstitution, Device):
    '''Setup PMAC or Geobrick gathering template'''

    Dependencies = (PmacUtil,)

    def PostIocInitialise(self):
        if Architecture() == "linux-x86":
            print 'seq(gather,"P=%(P)s,M=%(M)s")' % self.args
        else:
            print 'seq &gather,"P=%(P)s,M=%(M)s"' % self.args

    # Substitution attributes
    TemplateFile = 'gather.template'

class positionCompare(AutoSubstitution, AutoProtocol):
    '''Setup position compare on a delta tau. Needs PLC_PMAC_position_compare
    or PLC_BRICK_position_compare'''
    Dependencies = (Calc,)
    ProtocolFiles = ['pmac.proto']
    TemplateFile = 'positionCompare.template'
