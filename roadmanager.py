# -*- coding: utf8 -*-
import pygame, uuid, math

class RoadManager:
  def __init__(self, screenDim, blobManager):
    self.screenDim = screenDim
    self.blobManager = blobManager

    self.roads = []
    self.roadColor = (200, 200, 200)
    self.roadLineColor = (255, 255, 255)

    self.roadDict = {}

    self.roadBlobLimitFactor = 3
    self.roadLimit = 4

    self.drawRoad = True
    self.drawLine = True

  def getRoadId(self):
    return str(uuid.uuid1())

  def validate(self, road):
    result = True

    start = road[0]
    end = road[1]

    delta = end - start
    if delta.x == 0:
      delta.x = 0.000001
    error = 0.0
    deltaErr = abs(delta.y / float(delta.x))
    y = int(end.y)
    points = []
    for x in range(int(start.x), int(end.x)):
      pos = [x, y]
      points.append(pos)
      error = error + deltaErr
      while error >= 0.5:
        if not pos in points:
          points.append(pos)

        y += int(math.copysign(1, end.y - start.y))
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
      print "removing road at", road[0], road[1]
      self.roads.remove(road)

  def draw_dashed_line(self, surf, color, origin, target, width=1, dash_length=10):
    displacement = target - origin
    length = len(displacement)
    slope = displacement/length

    for index in range(0, length/dash_length, 2):
        start = origin + (slope *    index    * dash_length)
        end   = origin + (slope * (index + 1) * dash_length)
        pygame.draw.line(surf, color, start.toIntArr(), end.toIntArr(), width)

  def draw(self, screen):
    for road in self.roads:
      if self.drawRoad:
        direction = (road[1] - road[0]).getNormalized()
        leftDir = direction.getLeftPerpendicular()
        rightDir = direction.getRightPerpendicular()
        p1 = road[0] + leftDir * road[2]
        p2 = road[0] + rightDir * road[2]
        p3 = road[1] + rightDir * road[3]
        p4 = road[1] + leftDir * road[3]
        pygame.draw.polygon(screen, self.roadColor, [p1.toIntArr(), p2.toIntArr(), p3.toIntArr(), p4.toIntArr()])
      else:
        pygame.draw.line(screen, (255,0,0), road[0].toIntArr(), road[1].toIntArr(), 1)

    if self.drawRoad and self.drawLine:
      for road in self.roads:
        pygame.draw.line(screen, self.roadLineColor, road[0].toIntArr(), road[1].toIntArr(), 1)
        #self.draw_dashed_line(screen, self.roadLineColor, road[0], road[1])

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
