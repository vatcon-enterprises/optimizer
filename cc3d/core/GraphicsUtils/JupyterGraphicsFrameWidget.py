"""
Defines features for interactive visualization for use with CC3D simservice applications in a Jupyter notebook
"""

from typing import Optional, Union, Tuple, List
import warnings
from weakref import ref

from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor, vtkRenderWindow

import cc3d.CompuCellSetup
from cc3d.core.GraphicsOffScreen.GenericDrawer import GenericDrawer
from cc3d.core.GraphicsUtils.GraphicsFrame import GraphicsFrame
from cc3d.core.GraphicsUtils.CC3DPyGraphicsFrame import (
    CC3DPyGraphicsFrameClientBase, CC3DPyInteractorStyle, np_img_data, save_img
)


# Test for IPython
try:
    get_ipython
    __has_interactive__ = True
    from ipyvtklink.viewer import ViewInteractiveWidget
    from IPython.display import display
    from ipywidgets import HBox, Layout, VBox
except NameError:
    __has_interactive__ = False
    ViewInteractiveWidget = object


class JupyterGraphicsFrame(GraphicsFrame):
    """
    Interactive graphics in a Jupyter notebook
    """

    def __init__(self, *args, **kwargs):

        if not __has_interactive__:
            raise RuntimeError('Interactive frame launched outside of an interactive environment.')

        # Validate current simulation state
        pg = cc3d.CompuCellSetup.persistent_globals
        if pg.simulator is None:
            raise RuntimeError('Simulator not set')
        elif pg.screenshot_manager is None:
            raise RuntimeError('Screenshot manager not set')
        try:
            field_extractor = pg.persistent_holder['field_extractor']
        except KeyError:
            raise RuntimeError('Field extractor not set')

        self.style: Optional[CC3DPyInteractorStyle] = None

        generic_drawer = GenericDrawer(boundary_strategy=pg.simulator.getBoundaryStrategy())
        generic_drawer.set_pixelized_cartesian_scene(pg.configuration.getSetting("PixelizedCartesianFields"))
        generic_drawer.set_field_extractor(field_extractor=field_extractor)

        super().__init__(generic_drawer=generic_drawer, current_bsd=pg.screenshot_manager.bsd, *args, **kwargs)

        # Initialize options
        self.bounding_box_on = self.config.getSetting('BoundingBoxOn')
        self.cell_borders_on = self.config.getSetting('CellBordersOn')
        self.cell_glyphs_on = self.config.getSetting('CellGlyphsOn')
        self.cells_on = self.config.getSetting('CellsOn')
        self.cluster_borders_on = self.config.getSetting('ClusterBordersOn')
        self.fpp_links_on = self.config.getSetting('FPPLinksOn')
        self.lattice_axes_labels_on = self.config.getSetting('ShowAxes')
        self.lattice_axes_on = self.config.getSetting('ShowHorizontalAxesLabels') or self.config.getSetting(
            'ShowVerticalAxesLabels')

        # Initialize initial rendered state

        # noinspection PyUnresolvedReferences
        self.style.SetCurrentRenderer(self.gd.get_renderer())
        self.draw()
        self.reset_camera()
        self.init_field_types()
        self.Render()

    def get_vtk_window(self):
        """
        Get an initialized vtk window and window interactor.

        Implementation of :class:`GraphicsFrame` interface.
        """

        # noinspection PyArgumentList
        interactor = vtkRenderWindowInteractor()

        renWin = vtkRenderWindow()
        renWin.SetOffScreenRendering(1)
        renWin.SetSize(600, 600)

        interactor.SetRenderWindow(renWin)
        renWin.SetInteractor(interactor)

        self.style = CC3DPyInteractorStyle()
        interactor.SetInteractorStyle(self.style)

        interactor.Initialize()

        return renWin, interactor

    def store_gui_vis_config(self, scr_data):
        """
        Save current internal data.

        Implementation of :class:`GraphicsFrame` interface.
        """

        scr_data.bounding_box_on = self.bounding_box_on
        scr_data.cell_borders_on = self.cell_borders_on
        scr_data.cell_glyphs_on = self.cell_glyphs_on
        scr_data.cells_on = self.cells_on
        scr_data.cluster_borders_on = self.cluster_borders_on
        scr_data.fpp_links_on = self.fpp_links_on
        scr_data.lattice_axes_labels_on = self.lattice_axes_labels_on
        scr_data.lattice_axes_on = self.lattice_axes_on

    def set_drawing_style(self, _style):
        """
        Function that wires-up the widget to behave according tpo the dimension of the visualization.

        Override of :class:`GraphicsFrame` interface.

        :param _style:{str} '2D' or '3D'
        :return: None
        """
        super().set_drawing_style(_style)

        self.style.can_rotate = _style == '3D'


class CC3DViewInteractiveWidget(ViewInteractiveWidget):
    """:class:`ViewInteractiveWidget` that shares interactions"""

    def __init__(self, frame: JupyterGraphicsFrame, *args, **kwargs):

        self._frame = ref(frame)
        self._camera = None
        self._forwarding = False
        self._partners: List[CC3DViewInteractiveWidget] = []

        super().__init__(*args, **kwargs)

    def update_canvas(self, force_render=True, quality=75):
        if self._forwarding:
            return
        self._forwarding = True

        for p in self._partners:
            p.update_canvas(force_render, quality)

        self._forwarding = False
        super().update_canvas(force_render, quality)

    def sync_cameras(self, interactor):
        """Synchronize all cameras"""

        interactor: CC3DViewInteractiveWidget

        if interactor in self._partners or interactor is self:
            return

        if self._forwarding:
            return
        self._forwarding = True

        frame = self._frame()
        frame_p = interactor._frame()
        if frame is None or frame_p is None:
            warnings.warn('Could not synchronize cameras')
            return

        frame: JupyterGraphicsFrame
        frame_p: JupyterGraphicsFrame

        if self._camera is None:
            self._camera = frame.gd.get_active_camera()
        frame.gd.get_renderer().SetActiveCamera(frame_p.gd.get_active_camera())

        for p in self._partners:
            p.sync_cameras(interactor)

        interactor._partners.append(self)
        self._partners.append(interactor)

        self._forwarding = False

    def unsync_camera(self):
        """Unsynchronize all cameras"""

        for p in self._partners:
            p._partners.remove(self)
        self._partners.clear()

        if self._camera is None:
            return

        frame = self._frame()
        if frame is None:
            warnings.warn('Could not unsychronize camera')
        frame: JupyterGraphicsFrame

        frame.gd.get_renderer().SetActiveCamera(self._camera)
        self._camera = None


class JupyterGraphicsFrameClient(CC3DPyGraphicsFrameClientBase):
    """Client for a Jupyter grpahics frame"""

    def __init__(self,
                 name: str = None,
                 config_fp: str = None):

        self.frame: Optional[JupyterGraphicsFrame] = None
        self.widget: Optional[CC3DViewInteractiveWidget] = None

        super().__init__(name=name, config_fp=config_fp)

    def launch(self, timeout: float = None):
        """
        Launches the graphics frame process and blocks until startup completes.

        Implementation of :class:`CC3DPyGraphicsFrameClientBase` interface.

        :param timeout: permissible duration of launch attempt
        :type timeout: float
        :return: interface object on success, or None on failure
        :rtype: Any or None
        """

        self.frame = JupyterGraphicsFrame()
        self.frame.gd.get_renderer().ResetCamera()

        self.widget = CC3DViewInteractiveWidget(frame=self.frame,
                                                render_window=self.frame.renWin)
        return self

    def show(self):
        display(self.widget)

    def draw(self, blocking: bool = False):
        """
        Update visualization data in rendering process.

        Implementation of :class:`CC3DPyGraphicsFrameClientBase` interface.

        :param blocking: flag to block until update is complete
        :type blocking: bool
        :return: True on success
        :rtype: bool
        """

        self.frame.draw()
        self.widget: CC3DViewInteractiveWidget
        self.widget.update_canvas()

    def close(self):
        """
        Close the frame. Does nothing.

        Implementation of :class:`CC3DPyGraphicsFrameClientBase` interface.

        :return: True on success
        :rtype: bool
        """

        return True

    def np_img_data(self, scale: Union[int, Tuple[int, int]] = None, transparent_background: bool = False):
        """
        Get image data as numpy data.

        Implementation of :class:`CC3DPyGraphicsFrameClientBase` interface.

        :param scale: image scale
        :type scale: int or (int, int) or None
        :param transparent_background: flag to generate with a transparent background
        :type transparent_background: bool
        :return: image array data
        :rtype: numpy.array
        """

        return np_img_data(ren_win=self.frame.renWin, scale=scale, transparent_background=transparent_background)

    def save_img(self,
                 file_path: str,
                 scale: Union[int, Tuple[int, int]] = None,
                 transparent_background: bool = False):
        """
        Save a window to file.

        Supported image types are .eps, .jpg, .jpeg, .pdf, .png, .svg.

        Implementation of :class:`CC3DPyGraphicsFrameClientBase` interface.

        :param file_path: absolute path to save the image
        :type file_path: str
        :param scale: image scale
        :type scale: int or (int, int) or None
        :param transparent_background: flag to generate with a transparent background
        :type transparent_background: bool
        :return: None
        """

        return save_img(ren_win=self.frame.renWin,
                        file_path=file_path,
                        scale=scale,
                        transparent_background=transparent_background)

    def set_drawing_style(self, _style):
        """
        Function that wires-up the widget to behave according tpo the dimension of the visualization

        :param _style:{str} '2D' or '3D'
        :return: None
        """

        self.frame.set_drawing_style(_style)

        self._update()

    def set_plane(self, plane, pos=0):
        """Set the plane and position"""

        self.frame.currentProjection = plane
        self.frame.projection_position = pos

        if self.frame.currentProjection == 'xy':
            if pos > self.frame.xyMaxPlane:
                pos = self.frame.xyMaxPlane
            self.frame.xyPlane = pos

        elif self.frame.currentProjection == 'xz':
            if pos > self.frame.xzMaxPlane:
                pos = self.frame.xzMaxPlane
            self.frame.xzPlane = pos

        elif self.frame.currentProjection == 'yz':
            if pos > self.frame.yzMaxPlane:
                pos = self.frame.yzMaxPlane
            self.frame.yzPlane = pos

        self.frame.set_plane(self.frame.currentProjection, pos)
        self._update()

    def _update(self):
        self.frame.reset_camera()
        self.frame.current_screenshot_data = self.frame.compute_current_screenshot_data()
        self.frame.draw()
        self.widget.update_canvas()

    @property
    def field_names(self) -> List[str]:
        """Current available field names"""

        if self.frame is None or self.frame.fieldTypes is None:
            return []
        return list(self.frame.fieldTypes.keys())

    def set_field_name(self, _field_name: str):
        """Set the name of the field to render"""

        field_names = self.field_names

        if not field_names:
            warnings.warn('Field names not available', RuntimeWarning)
            return

        if _field_name not in field_names:
            warnings.warn(f'Field name not known: {_field_name}. Available field names are' + ','.join(field_names),
                          RuntimeWarning)
            return

        super().set_field_name(_field_name)
        self.frame.field_name = _field_name
        self._update()

    def sync_cameras(self, frame):
        """Synchronize all cameras"""

        return self.widget.sync_cameras(frame.widget)

    def unsync_camera(self):
        """Unsynchronize all cameras"""

        return self.widget.unsync_camera()


class CC3DJupyterGraphicsFrameGrid:

    def __init__(self, rows: int = 1, cols: int = 1):
        if rows <= 0 or cols <= 0:
            raise ValueError('Must have positive rows and columns')

        self._items: List[List[Optional[JupyterGraphicsFrameClient]]] = []
        for r in range(rows):
            self._items.append([None for _ in range(cols)])

        self.grid_box: Optional[VBox] = None

    @property
    def rows(self) -> int:
        """Current number of rows"""

        return len(self._items)

    @property
    def cols(self) -> int:
        """Current number of columns"""

        return len(self._items[0])

    def _prep_grid(self, row: int, col: int):
        while row >= self.rows:
            self._items.append([None for _ in range(self.cols)])
        if col > self.cols:
            for c in range(self.cols, col):
                [r.append(None) for r in self._items]

    def set_frame(self, frame: JupyterGraphicsFrameClient, row: int, col: int):
        """Set the frame at a position"""

        if row < 0 or col < 0:
            raise ValueError('Indices must be non-negative')

        self._prep_grid(row, col)
        self._items[row][col] = frame

    def sync_cameras(self):
        """Synchronize all cameras"""

        for rows_i in range(self.rows):
            for cols_i in range(self.cols):
                item_i = self._items[rows_i][cols_i]
                if item_i is not None:
                    for rows_j in range(self.rows):
                        for cols_j in range(self.cols):
                            item_j = self._items[rows_j][cols_j]
                            if item_j is not None and item_i is not item_j:
                                item_i.sync_cameras(item_j)

    def unsync_cameras(self):
        """Unsynchronize all cameras"""

        for rows in range(self.rows):
            for cols in range(self.cols):
                item = self._items[rows][cols]
                if item is not None:
                    item.unsync_camera()

    def show(self):
        """Show the grid"""

        to_show = []

        for r in range(self.rows):
            to_show_r = [item for item in self._items[r] if item is not None]
            if to_show_r:
                to_show.append(to_show_r)

        hboxes = []
        for to_show_r in to_show:
            if to_show_r:
                hboxes.append(HBox([to_show_rc.widget for to_show_rc in to_show_r]))

        if hboxes:
            self.grid_box = VBox(hboxes)
            display(self.grid_box)
