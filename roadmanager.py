# -*- coding: utf8 -*-
import pygame, uuid, math

class RoadManager:
  def __init__(self, screenDim, mapData, blobManager):
    self.screenDim = screenDim
    self.mapData = mapData
    self.blobManager = blobManager

    self.roads = []
    self.roadColor = (0, 255, 0)

    self.roadDict = {}

    self.roadBlobLimitFactor = 3
    self.roadLimit = 3

  def getRoadId(self):
    return str(uuid.uuid1())

  def validate(self, road):
    result = True

    start = road[0]
    end = road[1]

    x0 = start[0]
    x1 = end[0]
    y0 = start[1]
    y1 = end[1]

    deltaX = x1 - x0
    if deltaX == 0:
      deltaX = 0.000001
    deltaY = y1 - y0
    error = 0.0
    deltaErr = abs(deltaY / float(deltaX))
    y = y0
    points = []
    for x in range(x0, x1):
      pos = [int(x), int(y)]
      points.append(pos)
      error = error + deltaErr
      while error >= 0.5:
        if not pos in points:
          points.append(pos)

        y = y + math.copysign(1, y1 - y0)
        error = error - 1.0

        pos = [int(x), int(y)]

    for p in points:
      if self.blobManager.isSet(p):
        result = False
        break

    return result

  def update(self, dt):
    deadRoads = []
    for road in self.roads:
      if not self.validate(road):
        deadRoads.append(road)

    for road in deadRoads:
      print "removing road at", road[0], road[1]
      self.roads.remove(road)

  def draw(self, screen):
    for road in self.roads:
      #pygame.draw.line(screen, self.roadColor, road[0], road[1], int((road[2] + road[3])/2.0))
      pygame.draw.line(screen, self.roadColor, road[0], road[1], 1)

  def regenerate(self):
    print "regenerating roads (for " + str(len(self.blobManager.blobs)) + " blobs)..."

    for blob in self.blobManager.blobs:
      if not self.roadDict.has_key(blob.id):
        self.roadDict[blob.id] = []

      if len(self.roadDict[blob.id]) > self.roadLimit:
        continue # already too many roads

      roadBlobLimit = blob.radius * self.roadBlobLimitFactor
      otherBlobs = self.blobManager.findCloseBlobs(blob, roadBlobLimit)

      for otherBlob in otherBlobs:
        if not self.roadDict.has_key(otherBlob.id):
          self.roadDict[otherBlob.id] = []

        if otherBlob.id == blob.id:
          continue

        if otherBlob.id in self.roadDict[blob.id]:
          continue # already has a road to that blob

        if blob.id in self.roadDict[otherBlob.id]:
          continue # already has a road from that blob

        if len(self.roadDict[otherBlob.id]) > self.roadLimit:
          continue # already too many roads

        newRoad = [blob.pos, otherBlob.pos, blob.radius, otherBlob.radius, self.getRoadId()]
        if self.validate(newRoad):
          self.roadDict[blob.id].append(otherBlob.id)
          self.roadDict[otherBlob.id].append(blob.id)

          self.roads.append(newRoad)

    print "done."
