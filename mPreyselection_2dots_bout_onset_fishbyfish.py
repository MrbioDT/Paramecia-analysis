# THIS CODE WILL DETERMINE THE SELECTED PREY AND ITS LOCATION
# BASED ON THE ONSET OF THE CONTRA-LATERAL EYE CONVERGENCE
# The onset is defined as the point between the peak of eye velocity
# and the start of the tail bout.
# Last update: 23 AUG 2018, Ivan

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.signal import savgol_filter
from heapq import nsmallest

from csvfiles_reader import *
from extract_taileyebouts import *
from eye_movement_filters import *
from get_preylocation import *
import operator

plt.style.use(['dark_background'])

# ============================ MACRO FOR PREY SELECTION ANALYSIS =======================================================
# PARAMETERS FOR EXTRACTING THE BOUTS, AND PEAKS
Fs = 300
bout_thresh = 0.40  # 0.00 - 1.00 threshold value for extracting bouts, higher more bouts
tfactor = 0.3  # convert frames to ms
peakthres = 4  # 0.00 - 20.00 lower vale more peaks, for calculating tail beat frequency

# ========================= GENERATE ALL THE FILES =================================================================

dir_eye_80_R = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\RC right-center split\\80 deg\\eyes\\'
dir_tail_80_R = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\RC right-center split\\80 deg\\tail\\'
dir_output_80_R = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\RC right-center split\\80 deg\\All Analysis\\'

# Directories for 80 deg visual angle
dir_eye_80 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LC left-center split\\80 deg\\eyes\\'
dir_tail_80 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LC left-center split\\80 deg\\tail\\'
dir_output_80 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LC left-center split\\80 deg\\All Analysis\\'

dir_eye_70 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LC left-center split\\70 deg\\eyes\\'
dir_tail_70 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LC left-center split\\70 deg\\tail\\'
dir_output_70 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LC left-center split\\70 deg\\All Analysis\\'
'''
# Directories for 80 deg visual angle for LR
dir_eye_80 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LR left and right cross\\80 deg\\eyes\\'
dir_tail_80 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LR left and right cross\\80 deg\\tail\\'
dir_output_80 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LR left and right cross\\80 deg\\All Analysis\\'

dir_eye_70 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LR left and right cross\\70 deg\\eyes\\'
dir_tail_70 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LR left and right cross\\70 deg\\tail\\'
dir_output_70 = 'E:\\Semmelhack lab\\01 ANALYSIS\\Two dots\\LR left and right cross\\70 deg\\All Analysis\\'
'''
eye_files = list()
tail_files = list()

fishIDs = list()
fishIDs_dir = list()

fishIDs += [fish for fish in os.listdir(dir_eye_80_R)]  # store the fish filenames
fishIDs += [fish for fish in os.listdir(dir_eye_80)]  # store the fish filenames
fishIDs += [fish for fish in os.listdir(dir_eye_70)]  # store the fish filenames
fishIDs_dir += [{str(fish): [0, 0],
                 'wdb4_' + str(fish): [0, 0],
                 'afsplit_boutID' + str(fish): []} for fish in fishIDs] # for storing the right or left information for each fish


# fishID += [fish for fish in os.listdir(dir_eye_70)]
for (dirpath, dirnames, filenames) in os.walk(dir_eye_80_R):
    eye_files += [[os.path.join(dirpath, file), dir_output_80_R, 80, file, dirpath.replace(dir_eye_80_R,"")] for file in filenames]

for (dirpath, dirnames, filenames) in os.walk(dir_tail_80_R):
    tail_files += [[os.path.join(dirpath, file), dir_output_80_R, 80, file, dirpath.replace(dir_tail_80_R,"")] for file in filenames]

for (dirpath, dirnames, filenames) in os.walk(dir_eye_80):
    eye_files += [[os.path.join(dirpath, file), dir_output_80, -80, file, dirpath.replace(dir_eye_80,"")] for file in filenames]

for (dirpath, dirnames, filenames) in os.walk(dir_tail_80):
    tail_files += [[os.path.join(dirpath, file), dir_output_80, -80, file, dirpath.replace(dir_tail_80,"")] for file in filenames]

# Directory for 70 degrees visual angle
for (dirpath, dirnames, filenames) in os.walk(dir_eye_70):
    eye_files += [[os.path.join(dirpath, file), dir_output_70, -70, file, dirpath.replace(dir_eye_70,"")] for file in filenames]

for (dirpath, dirnames, filenames) in os.walk(dir_tail_70):
    tail_files += [[os.path.join(dirpath, file), dir_output_70, -70, file, dirpath.replace(dir_tail_70,"")] for file in filenames]

print len(eye_files), len(tail_files)
print len(fishIDs)
print fishIDs

no_match = 0
match = 0
prey_positions1 = []
eye_diffs = []
tails = []
rtime = []
one_bout = 0
multi_bout = 0
nbouts = 0
eye_onsets = []
fish_movements = []
right_prey = 0
left_prey = 0
aftersplit_prey_positions = []
aftersplit_rtime = []
reyepos_rightprey = []
leyepos_rightprey = []
reyepos_leftprey = []
leyepos_leftprey = []
wdb4split_left = 0
wdb4split_right = 0
wdb4split_rtime = []
eyediff_leftpc = []
eyediff_rightpc = []
LR = 0

for j in range(0, len(eye_files)):

    # ============ PREY LOCATION ==================
    dir_output = str(eye_files[j][1])
    # prey = prey_location_osci(40.0,70.0,-50.0,-10.0,'ccw',5) # with oscillation (speed,p1,p2,p3,dir,times)
    prey_loc = prey_location(40.0, float(eye_files[j][2]), -float(eye_files[j][2]), 0)  # without oscillation, (speed,p1,p2,times)
    print -eye_files[j][2]

    print 'PROCESSING: '
    print eye_files[j][0]
    print tail_files[j][0]

    # read the left and right eye tracks
    eyes = eye_reader(str(eye_files[j][0]))
    # =================== LOW PASS FILTER ========================
    order = 3
    fs = 300.0  # sample rate, Hz
    cutoff = 10  # desired cutoff frequency of the filter, Hz

    # print len(eyes[0]['LeftEye'])

    eyes[0]['LeftEye'] = butter_lowpass_filter(eyes[0]['LeftEye'], cutoff, fs, order)
    eyes[0]['RightEye'] = butter_lowpass_filter(eyes[0]['RightEye'], cutoff, fs, order)

    # print len(eyes[0]['LeftEye'])
    # compute the velocity

    LeftVel = savgol_filter(eyes[0]['LeftEye'], 3, 2, 1, mode = 'nearest')
    RightVel = savgol_filter(eyes[0]['RightEye'], 3, 2, 1, mode = 'nearest')
    eyes_vel = [{'LeftVel': LeftVel, 'RightVel': RightVel}]

    # print eyes[1]['RightVel']

    TailEye = extract_tail_eye_bout(eyes, eyes_vel, str(tail_files[j][0]), Fs, bout_thresh, peakthres)

    if not TailEye:
        print 'WARNING!! TailEye empty: ', eye_files[j]
        continue

    # stop
    if len(TailEye) == 1:
        one_bout += 1
    else:
        multi_bout += 1

    time = range(0, len(TailEye[0]['left']))
    time = [t / tfactor for t in time]

    count_afsplit_bout = 0
    afsplit_boutID = []

    for i in range(0, len(TailEye)):
        b4split_bout = 0 # initiate the variable to indicate if the bout is before split
        afsplit_bout = 0 # initiate the variable to check if the bout is after split
        print '============= BOUT #', i, '=================='
        if i == 0:
            rtime.append((TailEye[0]['frames'][0] / tfactor))

        print 'Mean binocular angle', np.mean(TailEye[i]['sum_eyeangles'])

        if np.mean(TailEye[i]['sum_eyeangles']) < 25:  # [(mid_list  - tenth):(mid_list + tenth)]) < 30:
            print 'Not converge enough, bout #: ', i, 'Sample: ', TailEye[i]['filename']
            continue

        if int(TailEye[i]['frames'][0]) < 20:
            continue

        right_eyebout = np.mean(TailEye[i]['right_eyeangles'])
        left_eyebout = np.mean(TailEye[i]['left_eyeangles'])

        right_v = (TailEye[i]['right_eyeangles'][-1] - TailEye[i]['right_eyeangles'][0]) / (
                len(TailEye[i]['right_eyeangles']) / tfactor)
        left_v = (TailEye[i]['left_eyeangles'][-1] - TailEye[i]['left_eyeangles'][0]) / (
                len(TailEye[i]['left_eyeangles']) / tfactor)

        if right_v < -0.005 and left_v < -0.005:
            print 'Diverging eyes'
            continue

        right_v = (TailEye[i]['right_eyeangles'][-1] - TailEye[i]['right_eyeangles'][0])# / (
                #len(TailEye[i]['right_eyeangles']) / tfactor)
        left_v = (TailEye[i]['left_eyeangles'][-1] - TailEye[i]['left_eyeangles'][0])# / (
                #len(TailEye[i]['left_eyeangles']) / tfactor)

        if right_v < -5 or left_v < -5:
            print 'Diverging eyes'
            continue


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
        lefteye_b4pc = np.mean(TailEye[i]['left'][t1 - 45 : t1-30])
        righteye_b4pc = np.mean(TailEye[i]['right'][t1 - 45 : t1-30])

        r_sac_on = int(math.ceil((r_maxpeak + r_minpeak)/2)) #tag. this is the onset of prey capture...
        l_sac_on = int(math.ceil((l_maxpeak + l_minpeak)/2))

        r_sac = TailEye[i]['right_vel_delay'][r_sac_on]
        l_sac = TailEye[i]['left_vel_delay'][l_sac_on]

        right_con = TailEye[i]['right_eyeangles_delay'][r_sac_on]
        left_con = TailEye[i]['left_eyeangles_delay'][l_sac_on]

        right_dir = TailEye[i]['right_eyeangles_delay'][-1] - TailEye[i]['right_eyeangles_delay'][r_sac_on]
        left_dir = TailEye[i]['left_eyeangles_delay'][-1] - TailEye[i]['left_eyeangles_delay'][l_sac_on]

        tail = np.mean(TailEye[i]['bout_angles'])

        EyeDiff = right_eyebout - left_eyebout
        VelDiff = right_v - left_v
        converge_thres = 2.0

        if EyeDiff > converge_thres:
            print 'Right eye converge more: ', 'R:', right_con, 'L:', left_con, \
                'Avg Velocities', right_v, left_v
        elif EyeDiff < -converge_thres:
            print 'Left eye converge more: ', 'L:', left_con, 'R:', right_con, \
                'Avg Velocities', left_v, right_v
        else:
            print 'Left and right eyes are equally converge: ', 'R:', right_con, 'L:', left_con, \
                'Avg Velocities', right_v, left_v

        delayed_prey = int(TailEye[i]['frames'][0]) - 30

        if delayed_prey < len(prey_loc) / 2.0: # if the bout correspond to before splitting
            b4split_bout = 1

        if delayed_prey > len(prey_loc) / 2.0: # if the bout correspond to before splitting
            afsplit_bout = 1
            count_afsplit_bout += 1 # to count the position of the bout after splitting

        if delayed_prey > len(prey_loc):
            print '========= WARNING ========= No prey location info available for the given bout frame. ' \
                  'The frame location of the bout is greater than the length of frames where prey is available'
            continue

        prey_pos1 = prey_loc[delayed_prey]  # delay the reaction time by 30 frames

        if -5.0 <= prey_pos1 <= 5.0:
            print 'COULD NOT DETECT, PREY IS AROUND THE CENTER'
            continue

        # set the onset and contra eye to none, default option
        first_onset = 'none'
        contra_eye = 'none'
        eye_convergence = 0
        if r_max < 0.1 and l_max < 0.1:
            print "======WARNING===== THE VELOCITY OF THE ONSET IS LESS THAN 150 deg/s"
            eye_convergence = 1

        # If there's a saccade, use it as the criteria else use eye convergence
        if eye_convergence == 0:

            if r_max < 0.1 <= l_max:
                first_onset = 'left'
            elif l_max < 0.1 <= r_max:
                first_onset = 'right'
            elif r_sac_on < l_sac_on:
                first_onset = 'right'
            elif l_sac_on < r_sac_on:
                first_onset = 'left'

            eye_onsets.append(first_onset)

        elif eye_convergence == 1:

            if abs(EyeDiff) <= 3.0:
                continue

            if right_eyebout > left_eyebout:
                contra_eye = 'right'
            elif left_eyebout > right_eyebout:
                contra_eye = 'left'

        if b4split_bout == 1 or LR == 1: # UNCOMMENT IF EXPERIMENT IS LEFT TO CENTER THEN SPLIT
            prey_pos2 = -prey_pos1
            # Assign which prey was selected based on the detected contra-lateral eye
            if first_onset == 'right' or contra_eye == 'right':
                if prey_pos1 < 0.0:
                    prey_pos = prey_pos1
                elif prey_pos2 < 0.0:
                    prey_pos = prey_pos2
            elif first_onset == 'left' or contra_eye == 'left':
                if prey_pos1 > 0.0:
                    prey_pos = prey_pos1
                elif prey_pos2 > 0.0:
                    prey_pos = prey_pos2
        else:  # UNCOMMENT IF EXPERIMENT IS LEFT TO CENTER THEN SPLIT
           prey_pos = prey_pos1

        # Is prey on the right, left or center?
        if prey_pos < 0.0:
            prey_rl = 'left'
        elif prey_pos > 0.0:
            prey_rl = 'right'

        prey_positions1.append(prey_pos)
        eye_diffs.append(EyeDiff)
        tails.append(tail)

        print 'Prey position', prey_pos
        print 'Eye Onset:', first_onset, 'R:', r_sac_on, 'L:', l_sac_on
        print 'right', right_con, right_dir
        print 'left', left_con, left_dir
        print 'tail angle', tail
        print 'tail beat frequency', TailEye[i]['tailfreq']

        # == EYE CHECK ==
        if first_onset == 'right' or contra_eye == 'right':
            fish_move = 'left'
            print 'Prey is @', prey_pos, 'and fish looks to left'
        elif first_onset == 'left' or contra_eye == 'left':
            fish_move = 'right'
            print 'Prey is @', prey_pos, 'and fish looks to right'

        if fish_move == prey_rl:
            match += 1
        elif fish_move != prey_rl:
            print "xxxxxxxxxxxxxxxxxx PREY DOESN'T MATCH xxxxxxxxxxxxxxxxxx"
            print 'fish', fish_move, 'prey', prey_rl
            no_match += 1

        fish_movements.append(fish_move)

        fi = fishIDs.index(eye_files[j][4])  # index of the current fish among all the fish samples in fishIDs
        print fi
        # store information
        if b4split_bout == 1 and afsplit_bout == 1 or LR == 1:
            if prey_pos > 0.0:
                wdb4split_right += 1
                fishIDs_dir[fi]['wdb4_' + fishIDs[fi]][1] += 1
                if count_afsplit_bout == 1:
                    wdb4split_rtime.append((TailEye[0]['frames'][0] / tfactor))
            elif prey_pos < 0.0:
                wdb4split_left += 1
                fishIDs_dir[fi]['wdb4_' + fishIDs[fi]][0] += 1
                if count_afsplit_bout == 1:
                    wdb4split_rtime.append((TailEye[0]['frames'][0] / tfactor))

        if afsplit_bout == 1 or LR == 1:
            if prey_pos > 0.0:
                right_prey += 1
                reyepos_rightprey.append(righteye_b4pc)
                leyepos_rightprey.append(lefteye_b4pc)
                eyediff_rightpc.append([(righteye_b4pc - lefteye_b4pc), prey_pos])
                fishIDs_dir[fi][fishIDs[fi]][1] += 1
                aftersplit_prey_positions.append(prey_pos)
                afsplit_boutID.append(1)  # directional ID for bouts after split
                if count_afsplit_bout:
                    aftersplit_rtime.append((TailEye[0]['frames'][0] / tfactor))
            elif prey_pos < 0.0:
                reyepos_leftprey.append(righteye_b4pc)
                leyepos_leftprey.append(lefteye_b4pc)
                eyediff_leftpc.append([(righteye_b4pc - lefteye_b4pc), prey_pos])
                left_prey += 1
                fishIDs_dir[fi][fishIDs[fi]][0] += 1
                aftersplit_prey_positions.append(prey_pos)
                afsplit_boutID.append(0)  # directional ID for bouts after split
                if count_afsplit_bout:
                    aftersplit_rtime.append((TailEye[0]['frames'][0] / tfactor))
        '''
        if afsplit_bout == 1:
            if prey_pos > 0.0:
                afsplit_boutID.append(1)  # directional ID for bouts after split
            elif prey_pos < 0.0:
                afsplit_boutID.append(0)  # directional ID for bouts after split
        '''

        nbouts += 1
        print 'r_sac', r_sac_on + t1
    fishIDs_dir[fi]['afsplit_boutID' + fishIDs[fi]].append(afsplit_boutID) # append the directional IDS per bout
    print fishIDs_dir[fi]['afsplit_boutID' + fishIDs[fi]]
    print TailEye[0]['filename']
    # plt.show()
    print 'done'

plt.rcParams['axes.linewidth'] = 5
plt.rcParams['xtick.major.width'] = 5
plt.rcParams['ytick.major.width'] = 5
plt.rcParams['xtick.major.size'] = 8
plt.rcParams['ytick.major.size'] = 8
plt.rcParams['xtick.labelsize'] = 25
plt.rcParams['ytick.labelsize'] = 30

if not os.path.exists(dir_output):  # create an output directory
    os.makedirs(dir_output)

f2, LR_bar = plt.subplots(1, 1, sharex=True, figsize=(20, 8))

left_fish = []
right_fish = []
nfish = []
fish_count = 0
count_ntrials = []
for i in range(len(fishIDs)):
    # Exclude the fish that only responded once after splitting
    total = fishIDs_dir[i][fishIDs[i]][0] + fishIDs_dir[i][fishIDs[i]][1]
    if total < 2:
        continue
    fish_count += 1
    nfish.append(fish_count)
    count_ntrials.append(total)
    left_fish.append((float(fishIDs_dir[i][fishIDs[i]][0])/total)*100.0)
    right_fish.append((float(fishIDs_dir[i][fishIDs[i]][1])/total)*100.0)

print 'TOTAL', fish_count, count_ntrials
b1 = LR_bar.bar(nfish, left_fish, color=[0, 1, 1])
b2 = LR_bar.bar(nfish, right_fish, color=[1, 0, 1], bottom=left_fish)
LR_bar.set_xticks([])
LR_bar.yaxis.set_major_locator(MaxNLocator(6))
LR_bar.set_ylabel('%', fontsize=40)
f2.savefig(dir_output + 'right_left_fish.png')

right = 0
left = 0
l_ratio = []
r_ratio = []
for i in range(len(fishIDs)):
    # Exclude the fish that only responded once after splitting
    total = fishIDs_dir[i][fishIDs[i]][0] + fishIDs_dir[i][fishIDs[i]][1]
    if total < 2:
        continue
    right += fishIDs_dir[i][fishIDs[i]][1]
    left += fishIDs_dir[i][fishIDs[i]][0]
    l_ratio.append((float(fishIDs_dir[i][fishIDs[i]][0]) / total)*100.0)
    r_ratio.append((float(fishIDs_dir[i][fishIDs[i]][1]) / total)*100.0)

# Average of LR ratio of each fish
f3, LR_avgratios = plt.subplots(1, 1, sharex=True, figsize=(20, 8))

LR_avgratios.set_xlim([0, 1])
LR_avgratios.set_xticks([])
LR_avgratios.yaxis.set_major_locator(MaxNLocator(6))
# LR_ratio.xaxis.set_major_locator(MaxNLocator(len(fishIDs)))
LR_avgratios.set_ylabel('%', fontsize=40)
# np.mean(l_ratio) np.mean(r_ratio)
LR_avgratios.bar(0.5, 48.67, 0.5, color=[0, 1, 1])
LR_avgratios.bar(0.5, 51.33, 0.5, color=[1, 0, 1], bottom=48.67)
f3.savefig(dir_output + 'average_ratios2.png')

# PREY CAPTURE EVENTS AFTER SPLIT THAT ALSO HAS PC BEFORE SPLIT
f4, LR_bar_wdb4 = plt.subplots(1, 1, sharex=True, figsize=(20, 8))

left_fish_wdb4 = []
right_fish_wdb4 = []
nfish = []
fish_count = 0
fish_wdb4 = []
for i in range(len(fishIDs)):
    # Exclude the fish that only responded once after splitting
    total = fishIDs_dir[i]['wdb4_' + fishIDs[i]][0] + fishIDs_dir[i]['wdb4_' + fishIDs[i]][1]
    if total < 2:
        continue
    fish_wdb4.append(fishIDs[i])
    fish_count += 1
    nfish.append(fish_count)
    left_fish_wdb4.append((float(fishIDs_dir[i]['wdb4_' + fishIDs[i]][0])/total)*100.0)
    right_fish_wdb4.append((float(fishIDs_dir[i]['wdb4_' + fishIDs[i]][1])/total)*100.0)

print 'fishwdb4', fish_wdb4
print 'left_fish_wdb4', left_fish_wdb4
print 'right_fish_wdb4', right_fish_wdb4

b1 = LR_bar_wdb4.bar(nfish, left_fish_wdb4, color=[0, 1, 1])
b2 = LR_bar_wdb4.bar(nfish, right_fish_wdb4, color=[1, 0, 1], bottom=left_fish_wdb4)
LR_bar_wdb4.set_xticks([])
LR_bar_wdb4.yaxis.set_major_locator(MaxNLocator(6))
LR_bar_wdb4.set_ylabel('%', fontsize=40)
f4.savefig(dir_output + 'wdb4_right_left_fish.png')

# AFTER SPLIT MULTI-BOUTS, CHANGE PREY OR NOT?
changeprey = 0
sameprey = 0
count_fishbouts = [] # count how many fish did multibout
count_trials = 0  # count how many trials with multi bouts
nthfish = 0 # initialize the fish counter value
for i in range(len(fishIDs)): # loop over each fish
    # print fishIDs_dir[i]['afsplit_boutID' + fishIDs[i]]
    for j in range(len(fishIDs_dir[i]['afsplit_boutID' + fishIDs[i]])): # loop over each trial in the fish i
        if len(fishIDs_dir[i]['afsplit_boutID' + fishIDs[i]][j]) < 2: # consider only multibouts
            continue
        count_trials += 1

        count_fishbouts.append(i)

        c = [] # list to store the ID of comparison per bout, 0 if same, 1 if change
        for k in range(len(fishIDs_dir[i]['afsplit_boutID' + fishIDs[i]][j])): # loop over each bout in the trial j
            if fishIDs_dir[i]['afsplit_boutID' + fishIDs[i]][j][0] !=\
                    fishIDs_dir[i]['afsplit_boutID' + fishIDs[i]][j][k]: # if the
                c.append(1)
            else:
                c.append(0)
        if any(c):
            changeprey += 1
        else:
            sameprey += 1

print 'Change of prey', count_fishbouts, changeprey, sameprey
total = float(sameprey + changeprey)
sameprey = (sameprey/total) * 100.0
changeprey = (changeprey/total) * 100.0

f5, changeprey_bar = plt.subplots(1, 1, sharex=True, figsize=(20, 8))
b1 = changeprey_bar.bar(0.5, sameprey, 0.5, color=[0, 1, 0])
b2 = changeprey_bar.bar(0.5, changeprey, 0.5, color=[0, 0, 1], bottom=sameprey)
changeprey_bar.set_xlim([0, 1])
changeprey_bar.set_xticks([])
changeprey_bar.yaxis.set_major_locator(MaxNLocator(6))
changeprey_bar.set_ylabel('%', fontsize=40)
f5.savefig(dir_output + 'changeORsame_prey.png')

f6, (rightprey, leftprey) = plt.subplots(2,1, sharex=True, figsize=(20, 8))
f6.subplots_adjust(hspace=0)
binwidth = 1
n1, bins1, patches1 = rightprey.hist(reyepos_rightprey,edgecolor=[1, 0, 1], linewidth = 5, facecolor = 'none',
                           bins=np.arange(min(reyepos_rightprey), max(reyepos_rightprey) + binwidth, binwidth))

n1, bins1, patches1 = rightprey.hist(leyepos_rightprey,edgecolor=[0, 1, 1], linewidth = 5, facecolor = 'none',
                           bins=np.arange(min(leyepos_rightprey), max(leyepos_rightprey) + binwidth, binwidth))
rightprey.yaxis.set_tick_params(width=5)
rightprey.yaxis.set_tick_params(length=8)
rightprey.tick_params('y', labelsize=20)
rightprey.yaxis.set_major_locator(MaxNLocator(6))
rightprey.set_ylabel('Count (Right PC)', fontsize=15)

n1, bins1, patches1 = leftprey.hist(reyepos_leftprey,edgecolor=[1, 0, 1], linewidth = 5, facecolor = 'none',
                           bins=np.arange(min(reyepos_leftprey), max(reyepos_leftprey) + binwidth, binwidth))

n1, bins1, patches1 = leftprey.hist(leyepos_leftprey,edgecolor=[0, 1, 1], linewidth = 5, facecolor = 'none',
                           bins=np.arange(min(leyepos_leftprey), max(leyepos_leftprey) + binwidth, binwidth))
leftprey.xaxis.set_tick_params(width =5)
leftprey.yaxis.set_tick_params(width=5)
leftprey.xaxis.set_tick_params(length=8)
leftprey.yaxis.set_tick_params(length=8)
leftprey.tick_params('y', labelsize=20)
leftprey.tick_params('x', labelsize=20)
leftprey.yaxis.set_major_locator(MaxNLocator(6))
leftprey.xaxis.set_major_locator(MaxNLocator(10))
leftprey.set_ylabel('Count (Left PC)', fontsize=15)
leftprey.set_xlabel('Eye position ($^\circ$)', fontsize=30)

f6.savefig(dir_output + 'Eye positions before PC.png')

f7, (rightprey2, leftprey2) = plt.subplots(2,1, sharex=True, figsize=(20, 8))
f7.subplots_adjust(hspace=0)

rightprey2.scatter(reyepos_rightprey, leyepos_rightprey, c = [1, 0, 1])
rightprey2.yaxis.set_tick_params(width=5)
rightprey2.yaxis.set_tick_params(length=8)
rightprey2.tick_params('y', labelsize=20)
rightprey2.yaxis.set_major_locator(MaxNLocator(6))
rightprey2.set_ylabel('Left Eye ($^\circ$)', fontsize=30)
rightprey2.set_ylim([-5, 40])
rightprey2.set_xlim([-5, 40])
leftprey2.scatter(reyepos_leftprey, leyepos_leftprey, c = [0, 1, 1])
leftprey2.xaxis.set_tick_params(width =5)
leftprey2.yaxis.set_tick_params(width=5)
leftprey2.xaxis.set_tick_params(length=8)
leftprey2.yaxis.set_tick_params(length=8)
leftprey2.tick_params('y', labelsize=20)
leftprey2.tick_params('x', labelsize=20)
leftprey2.yaxis.set_major_locator(MaxNLocator(6))
leftprey2.xaxis.set_major_locator(MaxNLocator(6))
leftprey2.set_ylabel('Left Eye ($^\circ$)', fontsize=30)
leftprey2.set_xlabel('Right Eye ($^\circ$)', fontsize=30)
leftprey2.set_ylim([-5, 40])
leftprey2.set_xlim([-5, 40])

reg_leftpc = stats.linregress(reyepos_leftprey, leyepos_leftprey)
reg_rightpc = stats.linregress(reyepos_rightprey, leyepos_rightprey)


rpc = lambda x: (reg_rightpc[0] * x) + reg_rightpc[1]
x = np.array([0, 35])
rightprey2.plot(x, rpc(x), lw=2.5, c="w")

lpc = lambda x2: (reg_leftpc[0] * x2) + reg_leftpc[1]
x2 = np.array([0, 35])
leftprey2.plot(x2, lpc(x2), lw=2.5, c="w")

f7.savefig(dir_output + 'Eye positions before PC_scatter.png')

f8, eyediff_b4pc = plt.subplots(1,1, sharex=True, figsize=(20, 8))

eyediff_b4pc.scatter(np.array(eyediff_rightpc)[:, 1], np.array(eyediff_rightpc)[:, 0], c = [1, 0, 1])
eyediff_b4pc.scatter(np.array(eyediff_leftpc)[:, 1], np.array(eyediff_leftpc)[:, 0], c = [0, 1, 1])
eyediff_b4pc.xaxis.set_tick_params(width =5)
eyediff_b4pc.yaxis.set_tick_params(width=5)
eyediff_b4pc.xaxis.set_tick_params(length=8)
eyediff_b4pc.yaxis.set_tick_params(length=8)
eyediff_b4pc.tick_params('y', labelsize=20)
eyediff_b4pc.tick_params('x', labelsize=20)
eyediff_b4pc.yaxis.set_major_locator(MaxNLocator(6))
eyediff_b4pc.xaxis.set_major_locator(MaxNLocator(6))
eyediff_b4pc.set_ylabel('Eye diff ($^\circ$)', fontsize=30)
eyediff_b4pc.set_xlabel('Prey pos ($^\circ$)', fontsize=30)

f8.savefig(dir_output + 'Eye positions before PC_scatter2.png')

print 'Saved to ', dir_output
print 'Left after split', left
print 'Right after split', right
print 'Average Left ratio', np.mean(l_ratio)
print 'Average Right ratio', np.mean(r_ratio)
print 'One bout', one_bout
print 'Multi bout', multi_bout
print 'Total # of bouts', nbouts
print '# of files', len(eye_files)
print changeprey, sameprey, count_trials
print 'Right PC Regression', reg_rightpc
print 'Left PC Regression', reg_leftpc

