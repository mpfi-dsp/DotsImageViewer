import sys
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QRectF, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QIcon, QCursor, QPainterPath, QBrush, QColor, QPolygon, \
    QPen
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
    qApp, QFileDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QToolButton, QLineEdit, QWidget, QVBoxLayout, \
    QHBoxLayout, QFrame, QToolBar, QPushButton, QApplication


""" DISPLAYS IMAGE IN DRAGGABLE AND ZOOMABLE INTERFACE """
class QPhotoViewer(QGraphicsView):
    photoClicked = pyqtSignal(QPoint)

    def __init__(self):
        super(QPhotoViewer, self).__init__()
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.draw_mode = False
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        self.setFrameShape(QFrame.NoFrame)

        # self._photo.mousePressEvent = self.get_click_pos
        self.points = []


    # def get_click_pos(self, event):
    #     if not self.draw_mode:
    #         self.mousePressEvent(event)
    #     elif self.draw_mode:
    #         x = event.pos().x()
    #         y = event.pos().y()
    #         print(x, y)
    #         self.points.append((x, y))


    def has_photo(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.has_photo():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def set_photo(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
            self.pix = pixmap
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.has_photo():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def toggle_drag_mode(self):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setDragMode(QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse() and not self.draw_mode:
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        elif self._photo.isUnderMouse() and self.draw_mode:
            """ DO THINGS WITH COORDINATES HERE """
            x = event.pos().x()
            y = event.pos().y()
            print(x, y)
            self.points.append((x, y))
        super(QPhotoViewer, self).mousePressEvent(event)

    def toggle_draw_mode(self):
        if self.draw_mode:
            self.draw_mode = False
        else:
            self.draw_mode = True

    def increment_zoom(self):
        self._zoom += 1
        self.scale(1.25, 1.25)

    def decrement_zoom(self):
        self._zoom -= 1
        self.scale(0.8, 0.8)


""" WRAPPER FOR PHOTO VIEWER WITH MENU TOOLBAR AND VARIOUS FUNCTIONS """
class QImageViewer(QMainWindow):
    def __init__(self, img):
        super(QImageViewer, self).__init__()

        self.setWindowTitle("Image Viewer")
        self.setWindowIcon(QIcon('./assets/logo.png'))
        self.resize(800, 800)
        self.printer = QPrinter()

        self.img = img
        self.viewer = QPhotoViewer()
        self.pix = QPixmap(img)
        self.viewer.set_photo(self.pix)
        self.setCentralWidget(self.viewer)

        self.menu = self.menuBar()
        self.create_actions()
        self.create_menus()

        self.viewer.fitInView(True)
        # self.setWindowFlags(Qt.FramelessWindowHint)

    def save(self):
        print("save file")
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "output_file.tif", "All Files(*);;", options=options)
        print(path)
        if path:
            self.img.save(path)

    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self._photo.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self._photo.pixmap().rect())
            painter.drawPixmap(0, 0, self._photo.pixmap())

    def zoom_in(self):
        self.viewer.increment_zoom()

    def zoom_out(self):
        self.viewer.decrement_zoom()


    def create_actions(self):
        self.save_act = QAction("&Save...", self, shortcut="Ctrl+S", triggered=self.save)
        self.print_act = QAction("&Print...", self, shortcut="Ctrl+P", enabled=True, triggered=self.print_)
        self.exit_act = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoom_in_act = QAction("Zoom &In (25%)", self, shortcut="Ctrl++", enabled=True, triggered=self.zoom_in)
        self.zoom_out_act = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=True, triggered=self.zoom_out)
        self.normal_size_act = QAction("&Normal Size", self, shortcut="Ctrl+S", enabled=True, triggered=self.viewer.fitInView)
        self.toggle_draw_act = QAction("&Toggle Draw Mode", self, shortcut="Ctrl+D", enabled=True, triggered=self.viewer.toggle_draw_mode)

    def create_menus(self):
        file_menu = self.menu.addMenu("&File")
        file_menu.addAction(self.save_act)
        file_menu.addAction(self.print_act)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_act)

        view_menu = self.menu.addMenu("&View")
        view_menu.addAction(self.zoom_in_act)
        view_menu.addAction(self.zoom_out_act)
        view_menu.addAction(self.normal_size_act)
        view_menu.addSeparator()

        draw_menu = self.menu.addMenu("&Draw")
        draw_menu.addAction(self.toggle_draw_act)
        draw_menu.addSeparator()

""" INITIALIZATION """
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setStyleSheet(styles)
    app.setStyle("fusion")
    fileName, dummy = QFileDialog.getOpenFileName(None, "Open image file...")
    image = QImage(fileName)
    w = QImageViewer(image)
    w.show()
    sys.exit(app.exec_())
