import cc3d.CompuCellSetup as CompuCellSetup

from FocalPointPlasticityCustomSteppables import FocalPointPlasticityCustomSteppable

CompuCellSetup.register_steppable(steppable=FocalPointPlasticityCustomSteppable(frequency=1))

CompuCellSetup.run()

