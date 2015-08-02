# -*- coding: utf8 -*-
import pygame, uuid, math

class Road:
  def __init__(self, startBlob, endBlob):
    self.id = str(uuid.uuid1())

    self.startId = startBlob.id
    self.start = startBlob.pos
    self.startRadius = startBlob.radius

    self.endId = endBlob.id
    self.end = endBlob.pos
    self.endRadius = endBlob.radius

    self.roadColor = (200, 200, 200)
    self.roadLineColor = (255, 255, 255)

  def update(self, dt):
    pass

  def drawRoad(self, screen):
    direction = (self.end - self.start).getNormalized()
    leftDir = direction.getLeftPerpendicular()
    rightDir = direction.getRightPerpendicular()
    p1 = self.start + leftDir * self.startRadius
    p2 = self.start + rightDir * self.startRadius
    p3 = self.end + rightDir * self.endRadius
    p4 = self.end + leftDir * self.endRadius
    pygame.draw.polygon(screen, self.roadColor, [p1.toIntArr(), p2.toIntArr(), p3.toIntArr(), p4.toIntArr()])

  def drawDebugLine(self, screen):
    pygame.draw.line(screen, (255,0,0), self.start.toIntArr(), self.end.toIntArr(), 1)

  def drawLine(self, screen):
    pygame.draw.line(screen, self.roadLineColor, self.start.toIntArr(), self.end.toIntArr(), 1)
    #self.draw_dashed_line(screen, self.roadLineColor, road.start.toIntArr(), road.end.toIntArr())

  def draw_dashed_line(self, surf, color, origin, target, width=1, dash_length=10):
    displacement = target - origin
    length = len(displacement)
    slope = displacement/length

    for index in range(0, length/dash_length, 2):
        start = origin + (slope *    index    * dash_length)
        end   = origin + (slope * (index + 1) * dash_length)
        pygame.draw.line(surf, color, start.toIntArr(), end.toIntArr(), width)

class RoadManager:
  def __init__(self, screenDim, blobManager):
    self.screenDim = screenDim
    self.blobManager = blobManager

    self.roads = []

    self.roadDict = {}

    self.roadBlobLimitFactor = 3
    self.roadLimit = 2

    self.drawRoad = True
    self.drawLine = True

  def validate(self, road):
    result = True

    delta = road.end - road.start
    if delta.x == 0:
      delta.x = 0.000001
    error = 0.0
    deltaErr = abs(delta.y / float(delta.x))
    y = int(road.end.y)
    points = []
    for x in range(int(road.start.x), int(road.end.x)):
      pos = [x, y]
      points.append(pos)
      error = error + deltaErr
      while error >= 0.5:
        if not pos in points:
          points.append(pos)

        y += int(math.copysign(1, road.end.y - road.start.y))
        error = error - 1.0

        pos = [x, y]

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
      print "removing road at", road.start, road.end
      self.roads.remove(road)

  def draw(self, screen):
    for road in self.roads:
      if self.drawRoad:
        road.drawRoad(screen)
      else:
        road.drawDebugLine(screen)

    if self.drawRoad and self.drawLine:
      for road in self.roads:
        road.drawLine(screen)

  def regenerate(self):
    print "regenerating roads (for " + str(len(self.blobManager.blobs)) + " blobs)..."

    for blob in self.blobManager.blobs:
      if not self.roadDict.has_key(blob.id):
        self.roadDict[blob.id] = []

      if len(blob.roads) > self.roadLimit:
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

        if len(otherBlob.roads) > self.roadLimit:
          continue # already too many roads

        newRoad = Road(blob, otherBlob)
        if self.validate(newRoad):
          self.roadDict[blob.id].append(otherBlob.id)
          self.roadDict[otherBlob.id].append(blob.id)

          self.roads.append(newRoad)
          blob.roads.append(newRoad)
          otherBlob.roads.append(newRoad)

    print "done."
