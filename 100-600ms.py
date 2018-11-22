# extract the paramecia tractory from -100ms to -600ms before strike

import os
import csv
import pandas as pd
import math

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

    folder = 'C:\DT files\Julie Semmelhack Lab\presentation\update report 20181109\para_location_strike 20181010 night'

    #Part-1. Read the 1st strike delay files
    # READ THE CSV FILES WITHIN THAT FOLDER AND GET THE STRKING FRAME, AND PARAMECIA'S LOCATION, X & Y
    # There should only be one csv in the folder
    filenames = os.listdir(folder)
    csv_list = [filename for filename in filenames if os.path.splitext(filename)[1] == '.csv']
    strike_files = folder + '\\' + csv_list[0]

    with open(strike_files) as s:
        strike_csv = csv.reader(s)
        strike_content = [] #X,Y,strike_frame,Filename
        for row in strike_csv:
            print row
            if row[1] != 'Y':
                if row[6][0] == 'p':
                   strike_content.append([float(row[0]),float(row[1]),row[6][10:43],float(row[9]),float(row[7]),float(row[8]),float(row[11])])
                else:
                   strike_content.append([float(row[0]), float(row[1]), row[6][0:32], float(row[9]),float(row[7]),float(row[8]),float(row[11])])

    # only look at the first strike frame in each files
    strike_filename = None
    new_strike_content = []
    for item in strike_content:
        if strike_filename != item[2]:
            new_strike_content.append(item)
            strike_filename = item[2]
    strike_content = new_strike_content

    #Part-2 Read all the paramecia trajectories
    para_folder = folder + '\\para'
    filenames = os.listdir(para_folder)
    csv_list = [filename for filename in filenames if os.path.splitext(filename)[1] == '.csv']

    csv_Track_dict = {}
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
        csv_Track_dict[each_csv] = Track_all

    #Part-3 Match and extract the corresponding points


    # First generate the big_x, big_y, big_t for output
    big_x = []
    big_y = []
    big_t = []
    big_sf = []
    big_midx = []
    big_midy = []
    big_mmpixel = []
    big_filename = []

    count_i = 0
    # 1st round match, find the right files
    for each_strike in strike_content:
        each_strike_file = each_strike[2]
        try:
            key = [file for file in csv_Track_dict.keys() if each_strike_file in file][0]
        except:
            try:
                key = [file for file in csv_Track_dict.keys() if each_strike_file[:22] in file][0]
            except:
                print 'no match for this one: ', each_strike_file, ', this frame: ', each_strike[3]
        print '@@@@@@@@@@@@@@@@@@@@@@'

        # 2nd round match, find the right track
        if key != None:

            i = 0 # for counting from f100 to f600
            for track in csv_Track_dict[key]:
                print 'enter track once'
                if each_strike[3] in track.keys():  # check if frame is right
                    if abs(each_strike[0] - track[each_strike[3]][0]) <= 0.00001:  # check if X is right

                        count_i += 1 #just for counting

                        # so far, we've found the right trajectory
                        # locate the corresponding frame range 33 frames(100ms) before strike to 200 frames(600ms)
                        strike_frame = each_strike[3]
                        try:
                            # try if there is 100ms before strike
                            f100 = track[strike_frame - 33]
                            f100 = strike_frame - 33
                        except:
                            print 'no f100 for ', each_strike[2], ' frame: ', each_strike[3]
                        else:
                            try:
                                # try if there is 600ms before strike
                                f600 = track[strike_frame - 200]
                                f600 = strike_frame - 200
                            except:
                                print 'no f600 for ', each_strike[2], ' frame: ', each_strike[3]
                                f600 = list(track.keys())[0]

                        print 'frame range for strike ', each_strike[3], ' is from ', f100, ' to ', f600

                        # access the frames, x, y in the right track
                        i = f100
                        while i >= f600:
                            big_x.append(track[i][0])
                            big_y.append(track[i][1])
                            big_t.append(i)
                            big_sf.append(each_strike[3])
                            big_midx.append(each_strike[4])
                            big_midy.append(each_strike[5])
                            big_mmpixel.append(each_strike[6])
                            big_filename.append(each_strike[2])
                            i -= 1.0


                        dataframe = pd.DataFrame({'X': big_x, 'Y': big_y, 'T': big_t, 'Strike_frame': big_sf, 'file_name': big_filename,
                                                  'mid_X':big_midx, 'mid_y':big_midy, 'onemm2pixel':big_mmpixel})
                        dataframe.to_csv(folder + "\\" + "summary_27.csv", index=False, sep=',')
                        print count_i
                        break  # once you got the right track just jump out

