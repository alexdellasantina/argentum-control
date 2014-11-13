#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Argentum Control PrintView

author: Trent Waddington
"""

import sys
import os
from PyQt4 import QtGui, QtCore, QtSvg

printPlateDesignScale = [1.0757, 1.2256] # * printArea
imageScale            = [ 23.52,  23.29] # * print = pixels

# A kind of annoying Rect
# Note: (0,0) is the bottom left corner of the printer
# All measurements are in millimeters
class PrintRect:
    def __init__(self, left, bottom, width, height):
        self.left   = float(left)
        self.bottom = float(bottom)
        self.width  = float(width)
        self.height = float(height)

class PrintImage(PrintRect):
    def __init__(self, pixmap, filename):
        self.pixmap = pixmap
        self.filename = filename
        self.left = 0.0
        self.bottom = 0.0
        self.width = pixmap.width() / imageScale[0]
        self.height = pixmap.height() / imageScale[1]
        self.screenRect = None

        filename = os.path.basename(filename)
        if filename.find('.') != -1:
            filename = filename[:filename.find('.')]
        self.hexFilename = filename + ".hex"

    def pixmapRect(self):
        return QtCore.QRectF(self.pixmap.rect())

class PrintView(QtGui.QWidget):
    def __init__(self, argentum):
        super(PrintView, self).__init__()
        self.argentum = argentum
        self.lastRect = QtCore.QRect()

        self.printPlateArea = PrintRect(0, 0, 285, 255)
        self.printArea = PrintRect(24, 73, 247, 127)
        self.printPlateDesign = QtSvg.QSvgRenderer("printPlateDesign.svg")
        height = self.printArea.height * printPlateDesignScale[1]
        self.printPlateDesignArea = PrintRect(12, 
                    50,
                    self.printArea.width * printPlateDesignScale[0],
                    height)
        self.images = []
        self.dragging = None
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

    def calcScreenRects(self):
        if self.lastRect == self.rect():
            for image in self.images:
                if image.screenRect == None:
                    image.screenRect = self.printAreaToScreen(image)
            return
        self.lastRect = self.rect()

        # Ensure correct aspect ratio
        aspectRect = QtCore.QRectF(self.rect())
        aspectRatio = aspectRect.width() / aspectRect.height()
        desiredAspectRatio = (self.printPlateArea.width / 
                              self.printPlateArea.height)
        #print("window {} x {}".format(aspectRect.width(), aspectRect.height()))
        #print("aspect ratio {}".format(aspectRatio))
        #print("desired aspect ratio {}".format(desiredAspectRatio))

        if aspectRatio < desiredAspectRatio:
            height = aspectRect.height() * (aspectRatio / desiredAspectRatio)
            #print("calculated height {}".format(height))
            #print("calculated aspect ratio {}".format(aspectRect.width() / height))
            aspectRect.setTop((aspectRect.height() - height) / 2)
            aspectRect.setHeight(height)
        else:
            width = aspectRect.width() / (aspectRatio / desiredAspectRatio)
            #print("calculated width {}".format(width))
            #print("calculated aspect ratio {}".format(width / aspectRect.height()))
            aspectRect.setLeft((aspectRect.width() - width) / 2)
            aspectRect.setWidth(width)

        #print("printPlateRect is {}, {} {} x {}".format(aspectRect.left(), 
        #                                             aspectRect.top(),
        #                                             aspectRect.width(),
        #                                             aspectRect.height()))
        self.printPlateRect = aspectRect

        # Now we can make the screen rects
        self.printPlateDesignRect = self.printToScreen(self.printPlateDesignArea)
        for image in self.images:
            image.screenRect = self.printAreaToScreen(image)

    def printToScreen(self, printRect):
        #print("printRect {}, {} {} x {}".format(printRect.left,
        #                                        printRect.bottom,
        #                                        printRect.width,
        #                                        printRect.height))
        #print("printPlateArea {} x {}".format(self.printPlateArea.width,
        #                                      self.printPlateArea.height))
        left   = (self.printPlateRect.left() + 
                  printRect.left / self.printPlateArea.width
                               * self.printPlateRect.width())
        top    = (self.printPlateRect.top() + self.printPlateRect.height() -
                  (printRect.bottom + printRect.height) 
                                 / self.printPlateArea.height
                               * self.printPlateRect.height())
        width  = (printRect.width / self.printPlateArea.width
                               * self.printPlateRect.width())
        height = (printRect.height / self.printPlateArea.height
                               * self.printPlateRect.height())

        #print("on screen {}, {} {} x {}".format(left, top, width, height))

        return QtCore.QRectF(left, top, width, height)

    def printAreaToScreen(self, printRect):
        p = PrintRect(self.printArea.left + printRect.left,
                      self.printArea.bottom + printRect.bottom,
                      printRect.width, printRect.height)
        return self.printToScreen(p)

    def screenToPrintArea(self, x, y):
        r = self.printToScreen(self.printArea)
        if x < r.left():
            x = r.left()
        if x > r.left() + r.width():
            x = r.left() + r.width()
        if y < r.top():
            y = r.top()
        if y > r.top() + r.height():
            y = r.top() + r.height()

        dx = x - r.left()
        dy = y - r.top()

        return (dx * self.printArea.width / r.width(),
                self.printArea.height - dy * self.printArea.height / r.height())

    def paintEvent(self, event):
        self.calcScreenRects()

        qp = QtGui.QPainter()
        qp.begin(self)
        qp.fillRect(self.rect(), QtGui.QColor(0,0,0))
        self.printPlateDesign.render(qp, self.printPlateDesignRect)
        for image in self.images:
            qp.drawPixmap(image.screenRect, image.pixmap, image.pixmapRect())
        qp.end()

    def addImageFile(self, inputFileName):
        pixmap = QtGui.QPixmap(inputFileName)
        if pixmap.isNull():
            print("Can't load image " + inputFileName)
            return None
        pi = PrintImage(pixmap, inputFileName)
        self.images.append(pi)
        self.update()
        return pi

    def isImageProcessed(self, image):
        hexFilename = os.path.join(self.argentum.filesDir, image.hexFilename)
        if not os.path.exists(hexFilename):
            return False
        imgModified = os.path.getmtime(image.filename)
        hexModified = os.path.getmtime(hexFilename)
        if imgModified < hexModified:
            return True
        return False

    def processImage(self, image):
        ip = self.argentum.getImageProcessor()
        hexFilename = os.path.join(self.argentum.filesDir, image.hexFilename)
        print("processing " + image.filename)
        ip.sliceImage(image.filename, hexFilename)

    def startPrint(self):
        if not self.argentum.printer.connected:
            print("Printer isn't connected.")
            return
        if len(self.images) == 0:
            self.argentum.statusBar().showMessage('Add some images to print.')
            return

        self.progress = QtGui.QProgressDialog(self)
        self.progress.setWindowTitle("Printing")
        self.progress.setLabelText("Setting up...")
        self.progress.show()

        if self.argentum.printer.isHomed():
            self.progress.setValue(10)
        else:
            self.argentum.printer.home()

        self.progress.setLabelText("Processing images...")
        perImage = 40 / len(self.images)
        for image in self.images:
            if not self.isImageProcessed(image):
                self.progress.setText("Processing image {}.".format(os.path.basename(image.filename)))
                self.processImage(image)
            self.progress.setValue(self.progress.value() + perImage)
        hexfiles = [image.hexFilename for image in self.images]
        missing = self.argentum.printer.missingFiles(hexfiles)
        for filename in missing:
            # I swear on Poseidon's trident, one day I shall remove the need 
            # for this Sneaker Net bullshit
            msgbox = QtGui.QMessageBox()
            msgbox.setWindowTitle("Sneaker Net Required.")
            msgbox.setText("One or more files are missing from the printer.")
            msgbox.setDetailedText('\n'.join(missing))
            msgbox.exec_()
            self.argentum.printer.disconnect()
            self.argentum.printer.connect()
            missing = self.argentum.printer.missingFiles(hexfiles)
            if len(missing) != 0:
                self.progress.cancel()
                return

        if not self.argentum.printer.isHomed():
            self.progress.cancel()
            self.argentum.statusBar().showMessage('Print canceled. Printer head needs homing.')
            return

        self.progress.setValue(50)

        perImage = 50 / len(self.images)
        for image in self.images:
            self.argentum.printer.move(image.left + image.width, image.bottom)
            #self.argentum.printer.print(image.hexFilename, wait=True)
            self.progress.setValue(self.progress.value() + perImage)

        self.progress.close()
        self.argentum.statusBar().showMessage('Print complete.')

    def mouseReleaseEvent(self, event):
        self.dragging = None
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def ensureImageInPrintArea(self, image):
        if image.left < 0:
            image.left = 0
        if image.bottom < 0:
            image.bottom = 0
        if image.left + image.width > self.printArea.width:
            image.left = self.printArea.width - image.width
        if image.bottom + image.height > self.printArea.height:
            image.bottom = self.printArea.height - image.height

    def mouseMoveEvent(self, event):
        pressed = event.buttons() & QtCore.Qt.LeftButton
        p = self.screenToPrintArea(event.pos().x(), event.pos().y())
        if p == None:
            if self.dragging == None:
                self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            return

        px = p[0]
        py = p[1]
        #print("{}, {}".format(px, py))

        if pressed and self.dragging != None:
            image = self.dragging
            image.left = px - self.dragStart[0] + self.dragImageStart[0]
            image.bottom = py - self.dragStart[1] + self.dragImageStart[1]
            self.ensureImageInPrintArea(image)
            image.screenRect = None
            self.update()
        elif self.dragging == None:
            hit = False
            for image in self.images:
                if px >= image.left and px < image.left + image.width:
                    if py >= image.bottom and py < image.bottom + image.height:
                        hit = True
                        if pressed:
                            self.dragging = image
                            self.dragImageStart = (image.left, image.bottom)
                            self.dragStart = (px, py)
                            self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
                        else:
                            self.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
                        break
            if not hit:
                self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def dragEnterEvent(self, e):
        self.argentum.raise_()
        self.argentum.activateWindow()
        e.accept()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            url = str(e.mimeData().urls()[0].path())
            pi = self.addImageFile(url)
            if pi == None:
                return
            p = self.screenToPrintArea(e.pos().x(), e.pos().y())
            if p != None:
                pi.left = p[0] - pi.width / 2
                pi.bottom = p[1] - pi.height / 2
                self.ensureImageInPrintArea(pi)
