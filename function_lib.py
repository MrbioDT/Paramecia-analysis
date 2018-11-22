import os
import csv
from scipy.signal import savgol_filter
import shelve
import peakdetector
from operator import add
import numpy as np
import operator
from bouts import *
from framemetrics import *
from scipy.signal import butter, filtfilt


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y


def extract_tail_eye_bout(eyes,vel, tailfits, Fs, bout_thresh, peakthres):

    # --------------------- READ TAILFITS -----------------------------------
    shv = shelve.open(tailfits)
    print shv

    if shv:
        tailfit = shv[shv.keys()[0]].tailfit
        shv.close()

        tailfit = normalizetailfit(tailfit)
        tailangle = -(tail2angles(tailfit))
        boutedges, var = extractbouts(tailangle, bout_thresh)

        # --------------------- READ EYE ANGLES -----------------------------------
        LeftEye = eyes[0]['LeftEye']
        RightEye = eyes[0]['RightEye']
        LeftVel = vel[0]['LeftVel']
        RightVel = vel[0]['RightVel']
        filename = eyes[0]['filename']
        # --------------------- EXTRACT TAIL BOUTS -----------------------------------
        bouts = []
        for bout in boutedges:
            # if boutacceptable(tailfit[bout[0]:bout[1]]):  # tag
            bouts += [{'tail': tailfit[bout[0]:bout[1]],
                       'frames': [bout[0], bout[1]]}]
        '''
        bout_angles = []
        left_eyeangles = []
        right_eyeangles = []
        tailfreq = []
        peaks=[]
        '''
        sum_eyes = map(add, LeftEye, RightEye)
        taileye = []
        '''
        if not bouts:
            taileye += [{'tail': tailangle, 'left': LeftEye, 'right': RightEye, 'sum_eyes': sum_eyes,
                         'LeftVel': LeftVel, 'RightVel': RightVel, 'filename': filename, 'no_bouts': [1]}]
        '''
        # else:
        for i in range(len(bouts)):
            nFrames = len(bouts[i]['tail'])
            # frames = bouts[i]['tail']
            # print bouts[i]['frames'][0]

            left_eyeangle = LeftEye[bouts[i]['frames'][0]:bouts[i]['frames'][1]]
            right_eyeangle = RightEye[bouts[i]['frames'][0]:bouts[i]['frames'][1]]
            left_vel = LeftVel[bouts[i]['frames'][0]:bouts[i]['frames'][1]]
            right_vel = RightVel[bouts[i]['frames'][0]:bouts[i]['frames'][1]]

            bout_value = 0
            if bouts[i]['frames'][0] - 50 < 0:
                left_eyeangle_delay = LeftEye[0:bouts[i]['frames'][1]]
                right_eyeangle_delay = RightEye[0:bouts[i]['frames'][1]]
                left_vel_delay = LeftVel[0:bouts[i]['frames'][1]]
                right_vel_delay = RightVel[0:bouts[i]['frames'][1]]
                bout_value = bouts[i]['frames'][0] - 50
            else:
                left_eyeangle_delay = LeftEye[(bouts[i]['frames'][0] - 50):bouts[i]['frames'][1]]
                right_eyeangle_delay = RightEye[(bouts[i]['frames'][0] - 50):bouts[i]['frames'][1]]
                left_vel_delay = LeftVel[(bouts[i]['frames'][0] - 50):bouts[i]['frames'][1]]
                right_vel_delay = RightVel[(bouts[i]['frames'][0] - 50):bouts[i]['frames'][1]]

            sum_eyeangles = map(add, left_eyeangle, right_eyeangle)

            boutangle = tail2angles(bouts[i]['tail'])  # extract the tailfits of the bout frames
            boutangle = [-1*a for a in boutangle]
            peak = peakdetector.peakdetold(
                boutangle, peakthres)  # get the number of peaks which tells us about how many tail beats for the bout

            peak_new = []
            # print 'Length of peak: ', len(peak[0])
            # print 'Length of frames: ', nFrames
            # print 'Length of tail: ', len(bouts[i]['tail'])
            # print 'Length of tail: ', len(bouts[i]['tail'])
            for item in peak[0]:
                peak_new.append([boutedges[i][0] + item[0], item[1]])
            '''
            left_eyeangles.append(left_eyeangle)
            right_eyeangles.append(right_eyeangle)
            tailfreq.append(len(peak[0]) / float((Fs * nFrames)))
            bout_angles.append(boutangle)
            peaks.append(peak_new)
            '''
            # left_eyeangles = eye angles during bouts
            # left_eyeangles_delay = eye angles during bouts with delay
            # sum_eyeangles = sum of eye angles during bouts
            # sum_eyes = summation of eye angles during the whole trial
            # left_v = eye velocity during the bout
            # left_vel_delay = eye velocity during the bout with delay
            # LeftVel - eye velocity during the whole trial
            # frames = the initial and last frame of the bout
            # filename = the filename of the eye files

            taileye += [{'tail': tailangle, 'bout_angles': boutangle, 'tailfreq': len(peak[0])/(0.0033*nFrames),
                         'left_eyeangles': left_eyeangle, 'right_eyeangles': right_eyeangle,
                         'left_eyeangles_delay': left_eyeangle_delay, 'right_eyeangles_delay': right_eyeangle_delay,
                         'sum_eyeangles': sum_eyeangles, 'left': LeftEye, 'right': RightEye, 'sum_eyes': sum_eyes,
                         'left_v': left_vel, 'right_v': right_vel, 'LeftVel': LeftVel, 'RightVel': RightVel,
                         'frames': bouts[i]['frames'], 'filename': filename, 'left_vel_delay':
                             left_vel_delay, 'right_vel_delay': right_vel_delay, 'no_bouts': [0],'bout_value':bout_value}]

    else:
        print "Tailfit empty"
        taileye = []

    return taileye  # bout_angles,tailfreq, left_eyeangles, right_eyeangles



def eye_reader(eyefile):
    # READ EYE POSITION
    # eyefile should be the csv files including the directory path

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


def pc_onset(folder):
# input folder should be the folder that contain all the csv output of swimbladder program, with eye plotting data inside

    #READ ALL CSV FILES IN ONE FOLDERS
    filenames = os.listdir(folder)
    csv_list = [filename for filename in filenames if os.path.splitext(filename)[1] == '.csv']
    shv_list = [filename for filename in filenames if os.path.splitext(filename)[1] == '.shv']

    onset_list_all = []

    for index in range(len(csv_list)):
        eyes = eye_reader(folder+'\\'+csv_list[index])
        tail_files = folder + '\\' +shv_list[index] #temp!!!
        print 'Currently process csv of this video: ', csv_list[index]
        print 'Currently process shv of this video: ', shv_list[index]

        # PARAMETERS FOR EXTRACTING THE BOUTS, AND PEAKS
        Fs = 300
        bout_thresh = 0.40  # 0.00 - 1.00 threshold value for extracting bouts, higher more bouts
        tfactor = 0.3  # convert frames to ms
        peakthres = 4  # 0.00 - 20.00 lower vale more peaks, for calculating tail beat frequency

        # =================== LOW PASS FILTER ========================
        order = 3
        fs = 300.0  # sample rate, Hz
        cutoff = 10  # desired cutoff frequency of the filter, Hz

        eyes[0]['LeftEye'] = butter_lowpass_filter(eyes[0]['LeftEye'], cutoff, fs, order)
        eyes[0]['RightEye'] = butter_lowpass_filter(eyes[0]['RightEye'], cutoff, fs, order)

        # compute the velocity
        LeftVel = savgol_filter(eyes[0]['LeftEye'], 3, 2, 1, mode='nearest')
        RightVel = savgol_filter(eyes[0]['RightEye'], 3, 2, 1, mode='nearest')
        eyes_vel = [{'LeftVel': LeftVel, 'RightVel': RightVel}]
        TailEye = extract_tail_eye_bout(eyes, eyes_vel, tail_files, Fs, bout_thresh, peakthres)

        # TailEye might contains multiple bouts in one video
        # regardless of amplitude, just include all the frames in any bouts

        # DETERMINE THE ONSET
        onset_list = []
        for i in range(0, len(TailEye)):  ###########tag
            #Analyze bout by bout

            # ======SACCADEONSET======
            # get the index, and value of the saccade onset based on velocity
            # Get the velocity maximum peak

            r_maxpeak, r_max = max(enumerate(TailEye[i]['right_vel_delay']), key=operator.itemgetter(1))
            l_maxpeak, l_max = max(enumerate(TailEye[i]['left_vel_delay']), key=operator.itemgetter(1))

            # Get the minimum peak between the start of the bout to the peak velocity
            # You only want the minimum peak BEFORE the maximum peak
            # There are cases when the maximum peak is found within the first two points
            # one reason is the starting point of the detected tail bout is greatly delayed compared to
            # its corresponding eye movement

            if r_maxpeak == 0:
                r_min = TailEye[i]['right_vel_delay'][0]
                r_minpeak = 0
            else:
                r_minpeak, r_min = min(enumerate(TailEye[i]['right_vel_delay'][0:r_maxpeak]), key=operator.itemgetter(1))

            if l_maxpeak == 0:
                l_min = TailEye[i]['left_vel_delay'][0]
                l_minpeak = 0
            else:
                l_minpeak, l_min = min(enumerate(TailEye[i]['left_vel_delay'][0:l_maxpeak]), key=operator.itemgetter(1))

            # SACCADE ONSET END
            t1 = TailEye[i]['frames'][0]
            t2 = TailEye[i]['frames'][1]

            # Eye orientation before prey capture
            lefteye_b4pc = np.mean(TailEye[i]['left'][t1 - 45: t1 - 30])
            righteye_b4pc = np.mean(TailEye[i]['right'][t1 - 45: t1 - 30])

            r_sac_on = int(math.ceil((r_maxpeak + r_minpeak) / 2))  # tag. this is the onset of prey capture...
            l_sac_on = int(math.ceil((l_maxpeak + l_minpeak) / 2))

            r = r_sac_on + t1 - 50 - TailEye[i]['bout_value']
            l = l_sac_on + t1 - 50 - TailEye[i]['bout_value']
            onset = min(r,l)
            onset_list.append(onset)

        pc_dict = {csv_list[index]:onset_list}
        onset_list_all.append(pc_dict)

    return onset_list_all



if __name__ == '__main__':

    folder = 'F:\DT-data\\2018\May\May 28_low density\\20180528_1st\single paramecia\good eye plotting  group\\demo'
    pc_onset(folder)

