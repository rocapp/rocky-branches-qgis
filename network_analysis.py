import sys

from qgis.core import *
from qgis.gui import *
from qgis.networkanalysis import *
import qgis.utils
from qgis.analysis import QgsGeometryAnalyzer

from PyQt4.QtCore import *
from PyQt4.QtGui import *

###################################
QgsApplication.setPrefixPath("C:\\OSGeo4W\\apps\\qgis", True)
qgs = QgsApplication([], True)
qgs.initQgis()

wae_crs = QgsCoordinateReferenceSystem()
wae_crs.createFromProj4("+proj=aeqd +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")

project = QgsProject.instance()

canvas = QgsMapCanvas() # Canvas
canvas.setCanvasColor(Qt.white)
canvas.enableAntiAliasing(True)
canvas.refresh()

bridge = QgsLayerTreeMapCanvasBridge( \
         QgsProject.instance().layerTreeRoot(), canvas)

project.read(QFileInfo("network_analysis.qgs"))

vl = QgsMapLayerRegistry.instance().mapLayers()[u'nodes_to_edges20160111174805104']
vl.setCrs(wae_crs)
vl_ = QgsMapCanvasLayer(vl)
vl_.setVisible(False)
canvas.refresh()

vl2 = QgsMapLayerRegistry.instance().mapLayers()[u'DQ_area_roads20160111140922177']
vl2_ = QgsMapCanvasLayer(vl2)
vl2_.setVisible(True)
canvas.refresh()

vl3 = QgsVectorLayer("Point", "marked_points", "memory")
QgsMapLayerRegistry.instance().addMapLayer(vl3)
pr = vl3.dataProvider()
vl3.startEditing()
vl3_ = QgsMapCanvasLayer(vl3)
vl3_.setVisible(True)
canvas.refresh()

# img = QImage(QSize(800, 600), QImage.Format_ARGB32_Premultiplied)
# color = QColor(255, 255, 255)
# img.fill(color.rgb())

mapRenderer = QgsMapRenderer()
mapRenderer.setProjectionsEnabled(True)

canvas.refresh()

# create painter
# p = QPainter(img)
# p.setRenderHint(QPainter.Antialiasing)

###################################

def distance():
  director = QgsLineVectorLayerDirector(vl, -1, '', '', '', 3)
  properter = QgsDistanceArcProperter()
  director.addProperter(properter)

  crs = mapRenderer.destinationCrs()
  builder = QgsGraphBuilder(crs)

  pStart = QgsPoint(-83.94216704, 34.53197821)
  print pStart
  delta = canvas.getCoordinateTransform().mapUnitsPerPixel() * 1

  all_pts = list()
  feats = list()
  all_pts.append((pStart.x(), pStart.y()))
  startPt = QgsGeometry.fromPoint(pStart)
  startF = QgsFeature()
  startF.setGeometry(startPt)
  feats.append(startF)

  tiedPoints = director.makeGraph(builder, [pStart])
  graph = builder.graph()
  tStart = tiedPoints[0]

  idStart = graph.findVertex(tStart)
  (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, idStart, 0)

  upperBound = []
  r = 40000.0
  # r = 40.0
  i = 0
  while i < len(cost):
    if cost[i] > r and tree[i] != -1:
      outVertexId = graph.arc(tree [i]).outVertex()
      if cost[outVertexId] < r:
        upperBound.append(i)
    i = i + 1

  for i in upperBound:
    centerPoint = graph.vertex(i).point()
    all_pts.append((centerPoint.x(), centerPoint.y()))
    # print centerPoint.x(), centerPoint.y()
    newPt = QgsGeometry.fromPoint(centerPoint)
    feature = QgsFeature()
    feature.setGeometry(newPt)
    feats.append(feature)
  pr.addFeatures(feats)
  vl3.updateExtents()
  QgsGeometryAnalyzer().centroids(vl3, "C:\\Users\\Robbie\\Desktop\\vl3_centroids.shp", False)
  vl3.commitChanges()
  canvas.refresh()
  return all_pts

all_pts = distance()

centroid_layer = QgsVectorLayer("C:\\Users\\Robbie\\Desktop\\vl3_centroids.shp",
                                  "centroid_layer", "ogr")
centroid_layer.updateExtents()
centroid_layer_ = QgsMapCanvasLayer(centroid_layer)
QgsMapLayerRegistry.instance().addMapLayer(centroid_layer)

# for pt in all_pts:
#   p.drawPoint(pt[0], pt[1])

canvas.setExtent(centroid_layer.extent())
canvas.setLayerSet([centroid_layer_, vl2_])
canvas.refresh()

# # set layer set
# layers = dict([(k, v) for (k, v) in QgsMapLayerRegistry.instance().mapLayers().items() if "nodes_to_edges20160111174805104" != k])
# lst = layers.keys()
# mapRenderer.setLayerSet(lst)

# # set extent
# rect = QgsRectangle(mapRenderer.fullExtent())
# rect.scale(1.1)
# mapRenderer.setExtent(rect)

# # set output size
# mapRenderer.setOutputSize(img.size(), img.logicalDpiX())

# # do the rendering
# mapRenderer.render(p)
# p.end()

settings = canvas.mapSettings()
settings.setLayers([l.id() for l in [centroid_layer, vl2]])
job = QgsMapRendererParallelJob(settings)
job.start()
job.waitForFinished()
image = job.renderedImage()
image.save("C:\\Users\\Robbie\\Desktop\\render.tif")

# save image
# img.save("C:\\Users\\Robbie\\Desktop\\render.png","png")

qgs.exitQgis()