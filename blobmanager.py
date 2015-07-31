# -*- coding: utf8 -*-

import pygame,  jsonpickle, uuid, math
from os import path
from random import choice, random, randint
from vector import Vector

class Blob:
  def __init__(self, pos, radius):
    self.id = str(uuid.uuid1())
    self.pos = Vector(pos)
    self.radius = radius
    self.state = 0

  def clone(self):
    result = Blob(self.pos, self.radius)
    result.id = self.id
    result.state = self.state
    return result

  def __getstate__(self):
    return [self.id, self.pos, self.radius, self.state]

  def __setstate__(self, stateData):
    self.id = stateData[0]
    self.pos = stateData[1]
    self.radius = stateData[2]
    self.state = stateData[3]

class BlobManager:
  def __init__(self, screenDim, mapData):
    self.mapData = mapData
    self.screenDim = screenDim

    self.blobs = []
    self.blobColor = (200, 200, 200)
    self.drawBlobs = True

    self.blobPersistenceInterval = 10000
    self.lastPersistence = 0

    self.blobMergeLimit = 10
    self.blobMergeRadiusFactor = 2.5
    self.spawnRate = 1000
    self.lastSpawn = 0

    self.blobFile = "blobs.json"
    if path.isfile(self.blobFile):
      print "loading existing blobs..."
      with open(self.blobFile, 'r') as f:
        content = f.read()
        self.blobs = jsonpickle.decode(content)
      print "done."

  def persistBlobs(self):
    print "persisting blobs..."
    blobData = jsonpickle.encode(self.blobs)
    with open(self.blobFile, 'w') as f:
      f.write(blobData)
    print "done."

  def isSet(self, pos):
    if not self.mapData:
      print "no mapData yet"
      return True

    if not isinstance(pos, Vector):
      pos = Vector(pos)

    if pos.x < 0 or pos.y < 0:
      return True
    if pos.x >= self.screenDim[0] or pos.y >= self.screenDim[1]:
      return True

    px = self.mapData.get_at(pos.toIntArr())
    return (px.r + px.g + px.b) < 600

  def mutateAt(self, index):
    result = False
    blob = self.blobs[index]
    newBlob = blob.clone()

    newBlob.radius += 1

    if not self.validate(newBlob):
      for i in range(5):
        offset = Vector.randomUnitCircle() * random()*i
        newBlob.pos += offset

        if self.validate(newBlob):
          result = True
          break
    else:
      result = True

    if not result and random() > 0.5:
      newBlob.radius -= 1
      for i in range(5):
        offset = Vector.randomUnitCircle() * random()*i

        if self.validate(newBlob):
          result = True


    if result:
      self.blobs[index] = newBlob

    return result

  def validate(self, blob, debug=False):
    result = True
    pos = blob.pos
    if self.isSet(pos):
      if debug:
        print "isset fail"
      result = False
    else:
      radius = blob.radius
      sqrRadius = radius**2
      for x in range(-radius, radius):
        for y in range(-radius, radius):
          if x*x + y*y <= sqrRadius:
            cPos = pos + [x, y]
            if self.isSet(cPos):
              if debug:
                print "wall collision fail"
              result = False
              break

        if not result:
          break

      for otherBlob in self.blobs:
        if otherBlob.id == blob.id:
          continue

        distance = Vector.distanceSqr(otherBlob.pos, blob.pos)
        if distance < (otherBlob.radius + blob.radius) ** 2:
          if debug:
            print "blob collision fail"
          result = False
          break


    return result

  def getCenter(self, posA, posB):
    return [
      int((posA[0] + posB[0]) / 2.0),
      int((posA[1] + posB[1]) / 2.0)
    ]

  def findCloseBlobs(self, blob, radius):
    result = []

    radiusSqr = radius * radius
    for otherBlob in self.blobs:
      if otherBlob.id == blob.id:
        continue

      if Vector.distanceSqr(blob.pos, otherBlob.pos) < radiusSqr:
        result.append(otherBlob)

    return result

  def tryMergeBlob(self, blob):
    otherBlobs = self.findCloseBlobs(blob, blob.radius * self.blobMergeRadiusFactor)

    for otherBlob in otherBlobs:
      center = ((otherBlob.pos + blob.pos) / 2.0).toIntArr()
      newBlob = Blob(center, blob.radius + otherBlob.radius)

      if self.validate(newBlob):
        print "mergedBlob at", blob.pos
        self.blobs.remove(blob)
        self.blobs.remove(otherBlob)
        self.blobs.append(newBlob)
        break

  def getLocationNextToRandomBlob(self):
    x = -1
    y = -1
    blob = self.blobs[randint(0, len(self.blobs)-1)]
    d = random() * math.pi
    dir = [
      math.cos(d) * choice([1, -1]),
      math.sin(d) * choice([1, -1])
    ]

    distance = blob.radius * (1 + random())

    x = int(math.floor(blob.pos.x + dir[0] + distance))
    y = int(math.floor(blob.pos.y + dir[1] + distance))

    return [x, y]

  def spawnAt(self, pos):
    blob = Blob(pos, 1)
    if self.validate(blob, True):
      print "blob spawned at", blob.pos
      self.blobs.append(blob)


  def spawn(self):
    randomBlob = choice(self.blobs)

    pos = randomBlob.pos + (Vector.randomUnitCircle() * randomBlob.radius * 2) * random()
    self.spawnAt(pos)

  def calculateScore(self):
    result = 0

    radiuses = 0.0
    for blob in self.blobs:
      radiuses = radiuses + blob.radius

    return radiuses/(float(len(self.blobs))+0.0001)

  def update(self, dt):
    blobsToTryMerge = []
    for i in range(len(self.blobs)):
      blob = self.blobs[i]
      if not self.mutateAt(i):
        blob.state = blob.state + 1

        if blob.radius < self.blobMergeLimit: # merging blobs
          blobsToTryMerge.append(blob)

    for blob in blobsToTryMerge:
      if blob in self.blobs:
        self.tryMergeBlob(blob)

    deadBlobs = []
    for blob in self.blobs:
      if not self.validate(blob): # removing dead blobs
        deadBlobs.append(blob)
    for blob in deadBlobs:
      print "removing dead blob at", blob.pos
      self.blobs.remove(blob)

    #time = pygame.time.get_ticks()
    #if self.lastSpawn + self.spawnRate > time:
    #  self.lastSpawn = time
    self.spawn()

    time = pygame.time.get_ticks()
    if self.lastPersistence + self.blobPersistenceInterval < time:
      self.lastPersistence = time
      self.persistBlobs()

  def draw(self, screen):
    if self.drawBlobs:
      for blob in self.blobs:
        pygame.draw.circle(screen, self.blobColor, blob.pos.toIntArr(), blob.radius)
