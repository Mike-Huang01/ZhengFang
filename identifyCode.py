# -*- coding: utf-8 -*-

__author__ = 'West'

import os
from PIL import Image, ImageDraw
from collections import namedtuple

# 巧妙的使用namedtuple，定义一种tuple类型，包含'Image','Charact'
ImageMap = namedtuple('ImageMap', ['Image', 'Charact'])
# 四个文件保存的路径
srcPath = os.path.join(os.path.abspath('./resources'), 'src')
truePath = os.path.join(os.path.abspath('./resources'), 'true')
trainPath = os.path.join(os.path.abspath('./resources'), 'data')
testPath = os.path.join(os.path.abspath('./resources'), 'test')
# 保存单字符图片和字符的映射
trainMap = None


# 判断像素点是否为蓝色
def isBlue(color):
    if (color[0] + color[1] + color[2]) == 153:
        return 1
    return 0


# 判断像素点是否为黑色
def isBlack(color):
    if (color[0] + color[1] + color[2]) <= 100:
        return 1
    return 0


# 黑白化
def removeBackground(picName):
    img = Image.open(picName)
    img = img.crop((5, 1, 55, img.size[1] - 1))
    img = img.convert('RGB')
    width, height = img.size
    for x in range(width):
        for y in range(height):
            if isBlue(img.getpixel((x, y))) == 1:
                img.putpixel((x, y), (0, 0, 0))
            else:
                img.putpixel((x, y), (255, 255, 255))
    return img


# 复制图片的局部区域
def copyImage(img, beginPoint):
    width, height = img.size
    width = int(width / 4)
    tempImg = Image.new('RGB', (width, height))
    for x in range(width):
        for y in range(height):
            tempImg.putpixel((x, y), img.getpixel((beginPoint[0] + x, beginPoint[1] + y)))
    return tempImg


# 将图片分割为4份
def spliteImage(img):
    subImgList = []
    width, height = img.size
    width = int(width / 4)
    subImgList.append(copyImage(img, (0, 0)))
    subImgList.append(copyImage(img, (width, 0)))
    subImgList.append(copyImage(img, (width * 2, 0)))
    subImgList.append(copyImage(img, (width * 3, 0)))
    return subImgList


# 打开图片，并将其分割为4部分
def spliteImageFile(filename):
    img = Image.open(filename)
    return spliteImage(img)


# 从true文件夹中导出黑白图片到train文件夹中	
def srcToTrain():
    for filename in os.listdir(srcPath):
        abspath = srcPath + '\\' + filename
        img = removeBackground(abspath)
        # print(os.path.split(filename)[0])
        abspath = trainPath + '\\' + filename[0:4] + '.jpg'
        img.save(abspath)


# 加载训练的数据，存放到映射表trainMap中
def loadTrainData():
    map = []
    for filename in os.listdir(trainPath):
        abspath = trainPath + '/' + filename
        images = spliteImageFile(abspath)
        i = 0
        for img in images:
            # 保存单个字符
            name = truePath + '/' + filename[0:4] + '-' + str(i) + '-' + filename[i] + '.jpg'
            namelist = os.listdir(truePath)
            if name not in namelist:
                img.save(name)
            IM = ImageMap(img, filename[i])
            map.append(IM)
            i += 1
    global trainMap
    trainMap = map
    print('len of trainMap is', len(trainMap))


# 识别一个单一字符
# img：一张带有一个字符的待识别图片
# map: Image为图片数据，Charact为图片中的对应字符 
def getSingleCharOcr(img, map):
    result = '#'
    width, height = img.size
    minDiffPixelNum = width * height
    for IM in map:
        image = IM.Image
        charact = IM.Charact
        count = 0
        if abs(width - image.size[0]) > 2:
            continue
        widthmin = min(width, image.size[0])
        heightmin = min(height, image.size[1])
        for x in range(widthmin):
            for y in range(heightmin):
                if isBlack(image.getpixel((x, y))) != isBlack(img.getpixel((x, y))):
                    if count >= minDiffPixelNum:
                        break
                    count += 1
                # else:
                # if count >= minDiffPixelNum:
                # break
        if count < minDiffPixelNum:
            minDiffPixelNum = count
            result = charact
    return result


# 等到图片的验证码，共四个字符
def getAllOcr(absname):
    filename = os.path.basename(absname)
    img = removeBackground(filename)
    listImg = spliteImage(img)
    global trainMap
    map = trainMap
    result = ''
    for image in listImg:
        result += getSingleCharOcr(image, map)
    return result


if __name__ == '__main__':
    # 测试
    loadTrainData()
    test_images = os.listdir('./test_images')
    os.chdir('./test_images')
    hit = 0
    total = 0
    for filename in test_images:
        string = getAllOcr(filename)
        truestring = os.path.splitext(filename)[0]
        if (string == truestring):
            hit += 1
        total += 1
        print 'origin: ' + truestring + '\n' + 'predict: ' + string
    print str(hit), '/' + str(total)
