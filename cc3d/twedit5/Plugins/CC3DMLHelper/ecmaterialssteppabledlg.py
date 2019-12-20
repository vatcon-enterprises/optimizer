from copy import deepcopy
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from cc3d.twedit5.twedit.utils.global_imports import *
from . import ui_ecmaterialssteppable
from .ecmaterialsdlg import ECMaterialsDlg

MAC = "qt_mac_set_native_menubar" in dir()


class ECMaterialsSteppableDlg(QDialog, ui_ecmaterialssteppable.Ui_ECMaterialsSteppableDlg):
    def __init__(self, field_names: [], previous_info: {}):
        super(ECMaterialsSteppableDlg, self).__init__()
        self.setModal(True)
        self.setupUi(self)
        if not MAC:
            self.buttonBox.setFocusPolicy(Qt.NoFocus)

        # To prevent accept on Return key; also nice to have a custom key filter implemented for future dev
        self.key_event_detector = KeyEventDetector(parent=self)
        self.installEventFilter(self.key_event_detector)
        self.was_a_key_press = False

        self.user_res = False

        self.cell_types = None

        self.field_list = field_names

        self.keys_set_here = self.get_keys()

        self.cb_emitters = None

        self.ec_materials_dict = None
        self.load_previous_info(previous_info=deepcopy(previous_info))

        # Containers for interaction design
        self.mtl_interaction = None
        self.fld_interaction = None
        self.cell_interaction = None
        self.init_design_containers()
        self.cell_response_types = ['Proliferation', 'Death', 'Differentiation', 'Asymmetric Division']
        self.responses_new_types = ['Differentiation', 'Asymmetric Division']

        # Static connections
        self.comboBox_fldC.currentTextChanged.connect(self.on_fld_catalyst_select)
        self.comboBox_cellT.currentTextChanged.connect(self.update_combo_box_types_new)
        self.comboBox_cellR.currentTextChanged.connect(self.update_combo_box_types_new)

        # Connect dynamic connections
        self.connect_all_signals()

        self.update_ui()

        self.tabWidget.setCurrentIndex(0)

    @staticmethod
    def get_keys():
        return ["MaterialInteractions", "FieldInteractions", "CellInteractions", "MaterialDiffusion"]

    def init_design_containers(self) -> None:
        self.reset_mtl_interaction()
        self.reset_fld_interaction()
        self.reset_cell_interaction()

    def reset_mtl_interaction(self) -> None:
        self.mtl_interaction = {"Catalyst": '',
                                "Reactant": '',
                                "Coefficient": 0}

    def reset_fld_interaction(self) -> None:
        self.fld_interaction = {"Catalyst": '',
                                "Reactant": '',
                                "Coefficient": 0}

    def reset_cell_interaction(self) -> None:
        self.cell_interaction = {"ECMaterial": '',
                                 "CellType": '',
                                 "ResponseType": '',
                                 "Coefficient": 0,
                                 "CellTypeNew": ''}

    def load_previous_info(self, previous_info: dict) -> None:
        self.ec_materials_dict = previous_info

        # Get cell types from adhesion coefficients defined in plugin
        if self.ec_materials_dict["ECMaterials"]:
            self.cell_types = list(self.ec_materials_dict["Adhesion"][self.ec_materials_dict["ECMaterials"][0]].keys())
        else:
            self.cell_types = []

        # Perform checks on imported data
        for key, val in ECMaterialsDlg.get_default_data().items():
            if key not in self.ec_materials_dict.keys():
                self.ec_materials_dict[key] = val

        # Perform checks in case materials changed
        self.ec_materials_dict["CellInteractions"] = \
            [val for val in self.ec_materials_dict["CellInteractions"]
             if val["ECMaterial"] in self.ec_materials_dict["ECMaterials"]]
        self.ec_materials_dict["MaterialInteractions"] = \
            [val for val in self.ec_materials_dict["MaterialInteractions"]
             if len({val["Catalyst"], val["Reactant"]} & set(self.ec_materials_dict["ECMaterials"])) == 2]
        self.ec_materials_dict["FieldInteractions"] = \
            [val for val in self.ec_materials_dict["FieldInteractions"]
             if len({val["Catalyst"], val["Reactant"]} & set(self.ec_materials_dict["ECMaterials"])) == 1]
        self.ec_materials_dict["MaterialDiffusion"] = \
            {key: val for key, val in self.ec_materials_dict["MaterialDiffusion"].items()
             if key in self.ec_materials_dict["ECMaterials"]}
        for ec_material in self.ec_materials_dict["ECMaterials"] - self.ec_materials_dict["MaterialDiffusion"].keys():
            self.ec_materials_dict["MaterialDiffusion"][ec_material] = {"Diffuses": False,
                                                                        "Coefficient": 0}

        # Perform checks in case cell types changed
        self.ec_materials_dict["CellInteractions"] = \
            [val for val in self.ec_materials_dict["CellInteractions"] if val["CellType"] in self.cell_types]
        self.ec_materials_dict["CellInteractions"] = \
            [val for val in self.ec_materials_dict["CellInteractions"] if val["CellTypeNew"] in self.cell_types]

        # Perform checks in case fields changed
        self.ec_materials_dict["FieldInteractions"] = \
            [val for val in self.ec_materials_dict["FieldInteractions"]
             if len({val["Catalyst"], val["Reactant"]} & set(self.field_list)) == 1]

    def get_user_res(self):
        return self.user_res

    def extract_information(self) -> {}:

        return self.ec_materials_dict

    def connect_all_signals(self) -> None:
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.on_reject)

        # Tab: Material Interactions
        self.lineEdit_mtl.textChanged.connect(self.on_mtl_coefficient_edit)
        self.pushButton_mtlAdd.clicked.connect(self.on_mtl_add)
        self.pushButton__mtlDel.clicked.connect(self.on_mtl_del)
        self.pushButton__mtlClear.clicked.connect(self.on_mtl_clear)

        # Tab: Field Interactions
        self.lineEdit_fld.textChanged.connect(self.on_fld_coefficient_edit)
        self.pushButton_fldAdd.clicked.connect(self.on_fld_add)
        self.pushButton_fldDel.clicked.connect(self.on_fld_del)
        self.pushButton_fldClear.clicked.connect(self.on_fld_clear)

        # Tab: Cell Interactions
        self.lineEdit_cell.textChanged.connect(self.on_cell_coefficient_edit)
        self.pushButton_cellAdd.clicked.connect(self.on_cell_add)
        self.pushButton_cellDel.clicked.connect(self.on_cell_del)
        self.pushButton_cellClear.clicked.connect(self.on_cell_clear)

        # Tab: Material Diffusion
        self.tableWidget_diff.itemChanged.connect(self.on_diffusion_table_item_edit)
        self.tableWidget_diff.cellChanged.connect(self.on_diffusion_table_edit)

    def disconnect_all_signals(self) -> None:
        self.buttonBox.accepted.disconnect(self.on_accept)
        self.buttonBox.rejected.disconnect(self.on_reject)

        # Tab: Material Interactions
        self.lineEdit_mtl.textChanged.disconnect(self.on_mtl_coefficient_edit)
        self.pushButton_mtlAdd.clicked.disconnect(self.on_mtl_add)
        self.pushButton__mtlDel.clicked.disconnect(self.on_mtl_del)
        self.pushButton__mtlClear.clicked.disconnect(self.on_mtl_clear)

        # Tab: Field Interactions
        self.lineEdit_fld.textChanged.disconnect(self.on_fld_coefficient_edit)
        self.pushButton_fldAdd.clicked.disconnect(self.on_fld_add)
        self.pushButton_fldDel.clicked.disconnect(self.on_fld_del)
        self.pushButton_fldClear.clicked.disconnect(self.on_fld_clear)

        # Tab: Cell Interactions
        self.lineEdit_cell.textChanged.disconnect(self.on_cell_coefficient_edit)
        self.pushButton_cellAdd.clicked.disconnect(self.on_cell_add)
        self.pushButton_cellDel.clicked.disconnect(self.on_cell_del)
        self.pushButton_cellClear.clicked.disconnect(self.on_cell_clear)

        # Tab: Material Diffusion
        self.tableWidget_diff.itemChanged.disconnect(self.on_diffusion_table_item_edit)
        self.tableWidget_diff.cellChanged.disconnect(self.on_diffusion_table_edit)

    @staticmethod
    def template_table_item(text=None) -> QTableWidgetItem:
        twi = QTableWidgetItem()
        if text is None:
            text = ''
        twi.setText(str(text))
        twi.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        return twi

    def update_combo_box_field_reactants(self) -> None:
        current_field = self.comboBox_fldR.currentText()
        if self.comboBox_fldC.currentText() in self.ec_materials_dict["ECMaterials"]:
            new_list = self.field_list
        elif self.comboBox_fldC.currentText() in self.field_list:
            new_list = self.ec_materials_dict["ECMaterials"]
        else:
            new_list = [self.ec_materials_dict["ECMaterials"], self.field_list]

        self.comboBox_fldR.clear()
        self.comboBox_fldR.addItems(new_list)
        if current_field in new_list:
            self.comboBox_fldR.setCurrentText(current_field)

    def update_combo_box_types_new(self) -> None:
        if self.comboBox_cellR.currentText() not in self.responses_new_types:
            self.comboBox_cellT_New.clear()
            self.comboBox_cellT_New.setEnabled(False)
        else:
            current_type = self.comboBox_cellT_New.currentText()
            new_list = [cell_type for cell_type in self.cell_types if cell_type != self.comboBox_cellT.currentText()]
            self.comboBox_cellT_New.clear()
            self.comboBox_cellT_New.addItems(new_list)
            if current_type in new_list:
                self.comboBox_cellT_New.setCurrentText(current_type)

            self.comboBox_cellT_New.setEnabled(True)

    def update_ui(self) -> None:

        self.disconnect_all_signals()

        # Tab: Material Interactions
        self.comboBox_mtlC.clear()
        self.comboBox_mtlC.addItems(self.ec_materials_dict["ECMaterials"])
        self.comboBox_mtlC.setEditable(False)
        if self.mtl_interaction["Catalyst"].__len__() > 0:
            self.comboBox_mtlC.setCurrentText(self.mtl_interaction["Catalyst"])
        self.comboBox_mtlR.clear()
        self.comboBox_mtlR.addItems(self.ec_materials_dict["ECMaterials"])
        self.comboBox_mtlR.setEditable(False)
        if self.mtl_interaction["Reactant"].__len__() > 0:
            self.comboBox_mtlR.setCurrentText(self.mtl_interaction["Reactant"])
        self.lineEdit_mtl.setText(str(self.mtl_interaction["Coefficient"]))

        self.tableWidget_mtl.setRowCount(0)
        for interaction in self.ec_materials_dict["MaterialInteractions"]:
            row = self.tableWidget_mtl.rowCount()
            self.tableWidget_mtl.insertRow(row)
            self.tableWidget_mtl.setItem(row, 0, self.template_table_item(text=interaction["Catalyst"]))
            self.tableWidget_mtl.setItem(row, 1, self.template_table_item(text=interaction["Reactant"]))
            self.tableWidget_mtl.setItem(row, 2, self.template_table_item(text=interaction["Coefficient"]))

        if self.tableWidget_mtl.rowCount() == 0:
            self.tableWidget_mtl.setEnabled(False)
            self.pushButton__mtlDel.setEnabled(False)
            self.pushButton__mtlClear.setEnabled(False)
        else:
            self.tableWidget_mtl.setEnabled(True)
            self.pushButton__mtlDel.setEnabled(True)
            self.pushButton__mtlClear.setEnabled(True)

        # Tab: Field Interactions
        # mtl_fld_list = list(set(self.ec_materials_dict["ECMaterials"]).union(set(self.field_list)))
        mtl_fld_list = self.ec_materials_dict["ECMaterials"] + self.field_list
        self.comboBox_fldC.clear()
        self.comboBox_fldC.addItems(mtl_fld_list)
        if self.fld_interaction["Catalyst"].__len__() > 0:
            self.comboBox_fldC.setCurrentText(self.fld_interaction["Catalyst"])
        self.on_fld_catalyst_select(self.comboBox_fldC.currentText())
        self.lineEdit_fld.setText(str(self.fld_interaction["Coefficient"]))

        self.tableWidget_fld.setRowCount(0)
        for interaction in self.ec_materials_dict["FieldInteractions"]:
            row = self.tableWidget_fld.rowCount()
            self.tableWidget_fld.insertRow(row)
            self.tableWidget_fld.setItem(row, 0, self.template_table_item(text=interaction["Catalyst"]))
            self.tableWidget_fld.setItem(row, 1, self.template_table_item(text=interaction["Reactant"]))
            self.tableWidget_fld.setItem(row, 2, self.template_table_item(text=interaction["Coefficient"]))

        if self.tableWidget_fld.rowCount() == 0:
            self.tableWidget_fld.setEnabled(False)
            self.pushButton_fldDel.setEnabled(False)
            self.pushButton_fldClear.setEnabled(False)
        else:
            self.tableWidget_fld.setEnabled(True)
            self.pushButton_fldDel.setEnabled(True)
            self.pushButton_fldClear.setEnabled(True)

        # Tab: Cell Interactions
        self.comboBox_cellM.clear()
        self.comboBox_cellM.addItems(self.ec_materials_dict["ECMaterials"])
        self.comboBox_cellM.setEditable(False)
        if self.cell_interaction["ECMaterial"].__len__() > 0:
            self.comboBox_cellM.setCurrentText(self.cell_interaction["ECMaterial"])
        self.comboBox_cellT.clear()
        self.comboBox_cellT.addItems(self.cell_types)
        self.comboBox_cellT.setEditable(False)
        if self.cell_interaction["CellType"].__len__() > 0:
            self.comboBox_cellT.setCurrentText(self.cell_interaction["CellType"])
        self.comboBox_cellR.clear()
        self.comboBox_cellR.addItems(self.cell_response_types)
        self.comboBox_cellR.setEditable(False)
        if self.cell_interaction["ResponseType"].__len__() > 0:
            self.comboBox_cellR.setCurrentText(self.cell_interaction["ResponseType"])
        self.lineEdit_cell.setText(str(self.cell_interaction["Coefficient"]))
        self.update_combo_box_types_new()

        self.tableWidget_cell.setRowCount(0)
        for interaction in self.ec_materials_dict["CellInteractions"]:
            row = self.tableWidget_cell.rowCount()
            self.tableWidget_cell.insertRow(row)
            self.tableWidget_cell.setItem(row, 0, self.template_table_item(text=interaction["ECMaterial"]))
            self.tableWidget_cell.setItem(row, 1, self.template_table_item(text=interaction["CellType"]))
            self.tableWidget_cell.setItem(row, 2, self.template_table_item(text=interaction["ResponseType"]))
            self.tableWidget_cell.setItem(row, 3, self.template_table_item(text=interaction["Coefficient"]))
            self.tableWidget_cell.setItem(row, 4, self.template_table_item(text=interaction["CellTypeNew"]))

        if self.tableWidget_cell.rowCount() == 0:
            self.tableWidget_cell.setEnabled(False)
            self.pushButton_cellDel.setEnabled(False)
            self.pushButton_cellClear.setEnabled(False)
        else:
            self.tableWidget_cell.setEnabled(True)
            self.pushButton_cellDel.setEnabled(True)
            self.pushButton_cellClear.setEnabled(True)

        # Tab: Material Diffusion
        self.tableWidget_diff.setRowCount(0)
        self.cb_emitters = []
        for key, diffusion in self.ec_materials_dict["MaterialDiffusion"].items():
            row = self.tableWidget_diff.rowCount()
            self.tableWidget_diff.insertRow(row)
            self.tableWidget_diff.setItem(row, 0, self.template_table_item(text=key))
            cb = QCheckBox()
            cb.setChecked(diffusion["Diffuses"])
            cb.setCheckable(True)
            self.tableWidget_diff.setCellWidget(row, 1, cb)
            self.cb_emitters.append(QCBCallbackEmitter(parent=self,
                                                       cb=cb,
                                                       cb_row=row,
                                                       cb_col=1))
            twi = self.template_table_item(text=diffusion["Coefficient"])
            twi.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.tableWidget_diff.setItem(row, 2, twi)

        self.connect_all_signals()

    # Callbacks
    def on_mtl_coefficient_edit(self, text) -> None:
        try:
            float(text)
        except ValueError:
            self.lineEdit_mtl.textChanged.disconnect(self.on_mtl_coefficient_edit)
            self.lineEdit_mtl.clear()
            self.lineEdit_mtl.textChanged.connect(self.on_mtl_coefficient_edit)

    def on_mtl_add(self) -> None:
        # Assemble candidate entry
        try:
            val = float(self.lineEdit_mtl.text())
        except ValueError:
            return
        self.mtl_interaction = {"Catalyst": self.comboBox_mtlC.currentText(),
                                "Reactant": self.comboBox_mtlR.currentText(),
                                "Coefficient": val}

        # Check for completion
        for val in self.mtl_interaction.values():
            if val == '':
                return

        # Check for duplicates
        for interaction in self.ec_materials_dict["MaterialInteractions"]:
            is_different = False
            for key in interaction.keys() - "Coefficient":
                if interaction[key] != self.mtl_interaction[key]:
                    is_different = True

            if not is_different:
                return

        self.ec_materials_dict["MaterialInteractions"].append(self.mtl_interaction)
        self.reset_mtl_interaction()
        self.update_ui()

    def on_mtl_del(self) -> None:
        row = self.tableWidget_mtl.currentRow()
        if row < 0:
            return
        self.ec_materials_dict["MaterialInteractions"].pop(row)
        self.update_ui()

    def on_mtl_clear(self) -> None:
        self.ec_materials_dict["MaterialInteractions"].clear()
        self.update_ui()

    def on_fld_catalyst_select(self, text) -> None:
        current_fldR = None
        if text in self.ec_materials_dict["ECMaterials"]:
            if self.comboBox_fldR.currentText() in self.field_list:
                current_fldR = self.comboBox_fldR.currentText()
            new_list = self.field_list
        elif text in self.field_list:
            if self.comboBox_fldR.currentText() in self.ec_materials_dict["ECMaterials"]:
                current_fldR = self.comboBox_fldR.currentText()
            new_list = self.ec_materials_dict["ECMaterials"]
        else:
            new_list = self.ec_materials_dict["ECMaterials"] + self.field_list

        self.comboBox_fldR.clear()
        self.comboBox_fldR.addItems(new_list)
        if current_fldR is not None:
            self.comboBox_fldR.setCurrentText(current_fldR)

    def on_fld_coefficient_edit(self, text) -> None:
        try:
            float(text)
        except ValueError:
            self.lineEdit_fld.textChanged.disconnect(self.on_fld_coefficient_edit)
            self.lineEdit_fld.clear()
            self.lineEdit_fld.textChanged.connect(self.on_fld_coefficient_edit)

    def on_fld_add(self) -> None:
        # Assemble candidate entry
        try:
            val = float(self.lineEdit_fld.text())
        except ValueError:
            return
        self.fld_interaction = {"Catalyst": self.comboBox_fldC.currentText(),
                                "Reactant": self.comboBox_fldR.currentText(),
                                "Coefficient": val}

        # Check for completion
        for val in self.fld_interaction.values():
            if val == '':
                return

        # Check for duplicates
        for interaction in self.ec_materials_dict["FieldInteractions"]:
            is_different = False
            for key in interaction.keys() - "Coefficient":
                if interaction[key] != self.fld_interaction[key]:
                    is_different = True

            if not is_different:
                return

        self.ec_materials_dict["FieldInteractions"].append(self.fld_interaction)
        self.reset_fld_interaction()
        self.update_ui()

    def on_fld_del(self) -> None:
        row = self.tableWidget_fld.currentRow()
        if row < 0:
            return
        self.ec_materials_dict["FieldInteractions"].pop(row)
        self.update_ui()

    def on_fld_clear(self) -> None:
        self.ec_materials_dict["FieldInteractions"].clear()
        self.update_ui()

    def on_cell_coefficient_edit(self, text) -> None:
        try:
            val = float(text)
            self.cell_interaction["Coefficient"] = val
        except ValueError:
            self.lineEdit_cell.textChanged.disconnect(self.on_cell_coefficient_edit)
            self.lineEdit_cell.setText('0')
            self.lineEdit_cell.textChanged.connect(self.on_cell_coefficient_edit)

    def on_cell_add(self) -> None:
        # Assemble candidate entry
        try:
            val = float(self.lineEdit_cell.text())
        except ValueError:
            self.lineEdit_cell.textChanged.disconnect(self.on_cell_coefficient_edit)
            self.lineEdit_cell.setText('0')
            self.lineEdit_cell.textChanged.connect(self.on_cell_coefficient_edit)
            return
        self.cell_interaction = {"ECMaterial": self.comboBox_cellM.currentText(),
                                 "CellType": self.comboBox_cellT.currentText(),
                                 "ResponseType": self.comboBox_cellR.currentText(),
                                 "Coefficient": val,
                                 "CellTypeNew": self.comboBox_cellT_New.currentText()}

        # Check for completion
        for key in self.cell_interaction.keys():
            if self.cell_interaction[key] == '':
                if key == "CellTypeNew":
                    if self.cell_interaction["ResponseType"] in self.responses_new_types:
                        return
                else:
                    return

        # Check for duplicates
        for interaction in self.ec_materials_dict["CellInteractions"]:
            is_different = False
            for key in interaction.keys() - "Coefficient":
                if interaction[key] != self.cell_interaction[key]:
                    is_different = True

            if not is_different:
                return

        self.ec_materials_dict["CellInteractions"].append(self.cell_interaction)
        self.reset_cell_interaction()
        self.update_ui()

    def on_cell_del(self) -> None:
        row = self.tableWidget_cell.currentRow()
        if row < 0:
            return
        self.ec_materials_dict["CellInteractions"].pop(row)
        self.update_ui()

    def on_cell_clear(self) -> None:
        self.ec_materials_dict["CellInteractions"].clear()
        self.update_ui()

    def on_diffusion_table_item_edit(self, item) -> None:
        self.on_diffusion_table_edit(item.row(), item.column())

    def on_diffusion_table_edit(self, row, col) -> None:
        if row < 0 or col <= 0:
            return
        ec_material = self.tableWidget_diff.item(row, 0).text()
        cb: QCheckBox = self.tableWidget_diff.cellWidget(row, 1)
        self.ec_materials_dict["MaterialDiffusion"][ec_material]["Diffuses"] = cb.isChecked()
        twi = self.tableWidget_diff.item(row, 2)
        try:
            val = float(twi.text())
            self.ec_materials_dict["MaterialDiffusion"][ec_material]["Coefficient"] = val
        except ValueError:
            self.disconnect_all_signals()
            twi.setText(str(self.ec_materials_dict["MaterialDiffusion"][ec_material]["Coefficient"]))
            self.connect_all_signals()
        self.update_ui()

    def on_accept(self):
        if self.was_a_key_press:
            return
        self.user_res = True
        self.close()

    def on_reject(self):
        if self.was_a_key_press:
            return
        self.user_res = False
        self.close()

    def set_key_press_flag(self, key_press_flag):
        self.was_a_key_press = key_press_flag


class KeyEventDetector(QObject):
    def __init__(self, parent: ECMaterialsSteppableDlg):
        super(KeyEventDetector, self).__init__(parent)
        self.main_UI = parent

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        self.main_UI.set_key_press_flag(key_press_flag=a1.type() == a1.KeyPress)

        return super(KeyEventDetector, self).eventFilter(a0, a1)


class QCBCallbackEmitter(QObject):
    def __init__(self, parent: ECMaterialsSteppableDlg, cb: QCheckBox, cb_row: int, cb_col: int):
        super(QCBCallbackEmitter, self).__init__(parent)
        self.main_UI = parent
        self.cb = cb
        self.cb_row = cb_row
        self.cb_col = cb_col

        self.cb.stateChanged.connect(self.emit)

    def emit(self, state: int):
        self.main_UI.on_diffusion_table_edit(row=self.cb_row, col=self.cb_col)
