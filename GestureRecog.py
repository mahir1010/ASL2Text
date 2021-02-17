#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 23:16:00 2021

@author: even
"""
import cv2
import numpy as np
import sys, os
import glob
# import imutils


#Skin Detection using HSV color space
# Returns the detected skin frame
def skinDetectionHSV(img):
    '''
    Parameters
    ----------
    img: color image
    '''
    image = np.array(img)
    imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    skinMaskHSV = cv2.bitwise_or((cv2.inRange(imageHSV, (0, 25, 80), (50, 255, 255))),(cv2.inRange(imageHSV, (150, 25, 80), (255, 255, 255))))
    skinHSV = cv2.bitwise_and(image, image, mask = skinMaskHSV)
    return skinHSV

def matchTemplate(img, templates, titles,method=cv2.TM_CCORR_NORMED):
    ''' 
    Parameters
    ----------
    img : grayscale image
    template : grayscale image
    method: matching method, an integer, 
            'cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
            'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED'

    Returns
    -------
    bounding box.

    '''
    img2 = img.copy()
    found = None
    maxMatch = None
    box = None
    matchName = None
    # loop over the scales of the image
    for scale in np.linspace(0.2, 1.0, 20)[::-1]:
        resized = cv2.resize(img, (int(img.shape[1] * scale),int(img.shape[0] * scale)))
        r = img.shape[1] / float(resized.shape[1])
        # edged = cv2.Canny(resized, 40, 90)
        edged=resized
#         cv2.imshow('frame', edged)
        for template,t in zip(templates,titles):
            tH, tW = template.shape[:2]
            if resized.shape[0] < tH or resized.shape[1] < tW:
                break
#             cv2.imshow("Template", template)
            result = cv2.matchTemplate(edged, template, method)
            (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
            # if we have found a new maximum correlation value, then update
            # the bookkeeping variable
            if found is None or maxVal > found[0]:
                found = (maxVal, maxLoc, r,t)
            
 	# unpack the bookkeeping variable and compute the (x, y) coordinates
 	# of the bounding box based on the resized ratio
    (maxVal, maxLoc, r,t) = found
    (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
    (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
    
    return maxVal,t,startX, startY, endX, endY
    




if __name__ == "__main__":
    
    # read templates from folder
    templates = glob.glob("templates/*.png")

    # templates_gray = [ cv2.Canny(cv2.imread(template,0), 40,90) for template in templates ]
    templates_gray = [cv2.imread(template, 0) for template in templates]
    names = [(name.split("/")[-1]).split(".")[0] for name in templates]
    # for n,t in zip(names,templates_gray):
    #     cv2.imshow(n,t)

    cap = cv2.VideoCapture(0)
    # if not successful, exit program
    if not cap.isOpened():
        print("Cannot open the video cam")
        sys.exit()
    
    # create a window called "MyVideo0"
    cv2.namedWindow("MyVideo", cv2.WINDOW_AUTOSIZE)
    fgbg = cv2.createBackgroundSubtractorKNN()
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc,30.0, (640, 480))
    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Cannot read a frame from video stream")
            break
        fgmask = fgbg.apply(frame)
        fgmask = cv2.medianBlur(fgmask, 3)
        fgmask = cv2.blur(fgmask,(3,3))
        fgmask = cv2.dilate(fgmask,np.ones((7,7)))
        fgmask = ((fgmask>0)*255).astype(np.uint8)
        skinMatching = skinDetectionHSV(frame)
        skinMatching= cv2.medianBlur(skinMatching,5)
        skinMatching=cv2.cvtColor(skinMatching, cv2.COLOR_BGR2GRAY)
        skinMatching = ((skinMatching>0)*255).astype(np.uint8)
        fgmask = cv2.bitwise_and(skinMatching,fgmask)
        # fgmask = cv2.blur(fgmask,(5,5))
        contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours)!=0:
            maxCont = max(contours, key=cv2.contourArea)
            blankImage=np.zeros_like(fgmask)
            cv2.drawContours(blankImage,[maxCont],-1,(255,255,255),thickness=cv2.FILLED)
            maxVal,name,startX,startY,endX,endY = matchTemplate(blankImage,templates_gray,names)
            print(maxVal,name,startX,startY,endX,endY)
            if maxVal > 0.7:
                box = [(startX, startY), (endX, endY)]
                cv2.putText(frame,name,(40,40),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)
                cv2.rectangle(frame,box[0],box[1],(255,255,255),2)
                cv2.imshow("mask", blankImage)
        # cv2.imshow("skinDetection",skinMatching)
        # cv2.imshow('merged', fgmask)
        cv2.imshow("MyVideo", frame)
        out.write(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.imwrite('skinDetection.png', blankImage)
            break
    

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
