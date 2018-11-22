# 2nd version for analyzing the paramecia's locations in prey capture frames
# Update: make the code for batch processing!
# CONTAINS THE FUNCTION FOR READING THE EYE MOVEMENTS
# PARAMECIA, and EYE COORDINATES STORED IN CSV FILE

import os
import csv
import pandas as pd
import math
from function_lib import *


def eye_reader(eyefile):
    # READ EYE POSITION

    LeftEye = []
    RightEye = []

    with open(eyefile) as csvfile:

        filename, file_extension = os.path.splitext(eyefile)
        readCSV = csv.reader(csvfile, delimiter=',')
        headers = readCSV.next()
        left = headers.index('left')
        right = headers.index('right')
        # leftv = headers1.index('Left Velocity')
        # rightv = headers1.index('Right Velocity')

        for row in readCSV:
            LeftEye.append(float(row[left]))
            RightEye.append(float(row[right]))
            # LeftVel.append(float(row[leftv]))
            # RightVel.append(float(row[rightv]))

        eyes = [{'LeftEye': LeftEye, 'RightEye': RightEye, 'filename': filename}]

    return eyes


def mideye_reader(mideyefile):

    Eye = []

    with open(mideyefile) as csvfile:

        filename, file_extension = os.path.splitext(mideyefile)
        readCSV = csv.reader(csvfile, delimiter=',')
        headers = readCSV.next()
        X = headers.index('X')
        Y = headers.index('Y')
        T = headers.index('T')

        for row in readCSV:
            Eye.append([float(row[X]), float(row[Y]), float(row[T])])

    return Eye


def para_reader(parafile):
    Para = []
    with open(parafile) as csvfile:
        filename, file_extension = os.path.splitext(parafile)
        readCSV = csv.reader(csvfile, delimiter=',')
        headers = readCSV.next()
        PosX = headers.index('X')  # x coord
        PosY = headers.index('Y')  # y coord
        PosT = headers.index('T')  # timepoint or frame
        trackID = headers.index('Track')  # which track
        for row in readCSV:
            Para.append([row[PosX], row[PosY], row[PosT], row[trackID]])
    return Para

if __name__ == '__main__':

    folder = 'D:\Data\Sep7th\demo'

    # Part-1. Read the para_track csv and sorting
    # READ ALL THE CSV FILES WITHIN THAT FOLDER AND STORES SORTED PARA TRACK INTO csv_Track_all
    para_folder = folder + '\\para\\results'
    filenames = os.listdir(para_folder)
    csv_list = [filename for filename in filenames if os.path.splitext(filename)[1] == '.csv']

    csv_Track_all = [] # list contains all the para track, each item should be dictionary, in each dict: keys are each csv's filename, values are Track_all
    for each_csv in csv_list:

        Para = para_reader(para_folder+'\\'+each_csv)
        print '[Para_track] Currently processing this file: ', each_csv

        # divide the Para into different Para_track based on the track number
        Para_track_allitem = [] # a list stores all the track number
        for item in Para:
            if float(item[3]) not in Para_track_allitem:
                Para_track_allitem.append(float(item[3]))

        # sorting the track based on time sequence first
        Para= sorted(Para, key=lambda x: float(x[2]))
        X = []; Y = []; T = []; Track = [];
        Track_all = []; #contains all the track in one csv

        # sorting the track based on track number and output to a csv
        i = 0
        for track_id in Para_track_allitem:
            Track_all.append({})
            for item in Para:
                if float(item[3]) == track_id:
                    Track_all[i][float(item[2])] = ([float(item[0]),float(item[1])]) #append each track to track all
                    X.append(float(item[0]))
                    Y.append(float(item[1]))
                    T.append(float(item[2]))
                    Track.append(float(item[3]))
            i = i+1
        dataframe = pd.DataFrame({'X': X, 'Y': Y, 'T': T, 'Track': Track})
        dataframe.to_csv(folder +"\\"+each_csv+"_sorted.csv", index=False, sep=',')
        para_dict = {each_csv:Track_all}
        csv_Track_all.append(para_dict)

    # Part-2. Mid point of two eyes: Read the csv and output the mid-point of two eyes
    # READ 1ST EYES_CSV AND CALCULATE THE MID-POINT, AND USE IT FOR THE REST

    eyes_folder = folder + '\\eyes\\results'
    eyes_filenames = os.listdir(eyes_folder)
    eyes_csv_list = [eyes_filename for eyes_filename in eyes_filenames if
                     os.path.splitext(eyes_filename)[1] == '.csv']
    eyes_files = eyes_folder + '\\' + eyes_csv_list[0]
    print '[Eyes] Currently processing this file: ', eyes_csv_list[0]

    with open(eyes_files) as e:
        eyes_csv = csv.reader(e)
        header = next(eyes_csv)
        eyes_list = [];
        r = None;
        l = None;
        count = 0;

        # determin left eyes based on smallest x value, right eyes based on biggest x value
        for row in eyes_csv:
            eyes_list.append((float(row[0]), float(row[1])))

            if count == 0:
                r = (float(row[0]), float(row[1]))
                l = (float(row[0]), float(row[1]))
            else:
                if float(row[0]) < l[0]:
                    l = (float(row[0]), float(row[1]))
                if float(row[0]) > r[0]:
                    r = (float(row[0]), float(row[1]))
            count += 1
    mid_point = ((r[0] + l[0]) / 2, (r[1] + l[1]) / 2)
    print 'eyes_list is: ', eyes_list
    print 'mid_point of two eyes for this batch is: ', mid_point

    # Part-3. Frame: Read the csv and output the striking frame as well as onset of prey capture
    # READ ALL THE CSV FILES WITHIN THAT FOLDER
    pc_folder = folder + '\\original_plot'
    # pc_folder = 'C:\Users\DT-JLS Lab\Desktop\original_plot'
    csv_pc_all = pc_onset(pc_folder)
    print 'csv_pc_all are: ', csv_pc_all
    print '++++++++++++++++++++++++++++PC FINISH++++++++++++++++++++++++++++++++'


    #Part-4. Selection: select the right track, output the relative location of paramecia

    file_list = []
    t_list = []
    x_list = []
    y_list = []
    mid_x_list = []
    mid_y_list = []

    if len(csv_pc_all) != len(csv_Track_all):
        print 'WARNING! len(csv_Sf_all) != len(csv_Track_all)'
    else:
        for i in range(len(csv_pc_all)):
            print i, 'th counting ++++++++++++++++++++++++++++++++++++++++=++++++++++++++++++'
            for pc_key, f_list in csv_pc_all[i].items():
                print 'pppppppppppppp ', pc_key
                for t_key, item_list in csv_Track_all[i].items():
                    print 'tttttttttttttttttttt ', t_key

                    for f in f_list:
                    # select track and location for each strike frame
                        min_distance = 10000000000000000000
                        para_track = None
                        para_location = None
                        for item in item_list:
                            # each item is dictionary with frame range as keys, para location in each frame as value
                            if float(f) in item.keys(): # judge if this frame is in the track first
                                p1 = mid_point
                                p2 = item[float(f)]
                                distance = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))
                                if distance < min_distance:
                                    min_distance = distance
                                    para_location = p2
                        print 'Paramecia location for ', f, ' frame is ', para_location, ', corresponding track is '

                        if para_location != None:
                            x_list.append(para_location[0])
                            y_list.append(para_location[1])
                            t_list.append(f)
                            file_list.append(pc_key)
                            mid_x_list.append(mid_point[0])
                            mid_y_list.append(mid_point[1])

    dataframe = pd.DataFrame({'X': x_list, 'Y': y_list, 'pc_frame': t_list, 'file_name': file_list,'mid_point_X':mid_x_list,'mid_point_Y':mid_y_list})
    dataframe.to_csv(folder + "\\" + "pc_para_location.csv", index=False, sep=',')


            #Select the strike and pc frame in track and output the figure!