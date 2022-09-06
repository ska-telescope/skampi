import os
import re
import sys
import json
import time
import numpy as np
from bokeh.plotting import figure, output_file, save
from bokeh.io import show, output_notebook, push_notebook
from bokeh.layouts import row

""" TELESCOPE RESOURCE ASSIGNMENT """
def telescope_onoff(telescope_power, monitor_frame, monitor_source, on_angle, on_colour, off_angle, off_colour):
    if telescope_power == 'on':
        monitor_source.data = dict(label_x = [0.5, 0.5, 0.5], label_y = [0.0, 0.5, 1.0],
                                           label_text = ['On/Off', 'Resources Assigned?', 'Other thing'],
                                           label_angle = [on_angle, off_angle, off_angle],
                                           label_color = [on_colour, off_colour, off_colour])
    elif telescope_power == 'off':
        monitor_source.data = dict(label_x = [0.5, 0.5, 0.5], label_y = [0.0, 0.5, 1.0],
                                           label_text = ['On/Off', 'Resources Assigned?', 'Other thing'],
                                           label_angle = [off_angle, off_angle, off_angle],
                                           label_color = [off_colour, off_colour, off_colour])

    push_notebook(handle=monitor_frame)


def assign_resources(file, monitor_frame, monitor_source, on_angle, on_colour, off_angle, off_colour):
    """ This is really basic and just reads in a JSON file """
    f = open(file)

    """ return JSON object as a dictionary """
    data = json.load(f)

    monitor_source.data = dict(label_x = [0.5, 0.5, 0.5], label_y = [0.0, 0.5, 1.0],
                                       label_text = ['On/Off', 'Resources Assigned?', 'Other thing'],
                                       label_angle = [off_angle, on_angle, off_angle],
                                       label_color = [off_colour, on_colour, off_colour])
    push_notebook(handle=monitor_frame)

    return data




def show_resources(data, resource_type: str = ''):
    """ basic func to print available resources """

    if resource_type =='':
        print("Currently assigned resources:\n")
        print(data)

    else:
        print("Currently assigned "+resource_type+" resource:\n")
        print(data[resource_type])


def generate_fake_amplitude(num_chans: int, cont_flux: float, profile: str):
    if profile == 'flat':
        fake_amplitude = cont_flux+(np.random.randn(1,num_chans)*0.5)
    elif profile == 'gaussian':
        chans = np.arange(0.0,float(num_chans))
        gauss = (20.0*cont_flux)*np.exp(-1.0*(((chans-(num_chans/2.0))**2.0)/(2.0*(5.0)**2.0)))
        fake_amplitude = cont_flux+(np.random.randn(1,num_chans)*0.5)+gauss



    return fake_amplitude


def observe_loop(simple_targets_json:str, num_chans: int, int_time: float, amp_avg, amp_time, amp_plots, total_time, num_loops: int = 2):
    """ loop through targets defined in JSON file one at a time for """
    """ the specified time """
    """ num_loops: how many times to loop the targets in the defined JSON """
    f = open(simple_targets_json)
    target_data = json.load(f)

    chans = np.arange(0,num_chans)
    colours = ['forestgreen','darkmagenta','goldenrod', 'coral', 'royalblue','mediumseagreen']

    for loop in range(0,num_loops):
        print('\nObserving loop '+str(loop+1)+' of '+str(num_loops)+':\n')


        ic = 0
        for key, value in target_data.items():
            cont_flux = float(target_data[key]['expect_flux'])
            source_avg_amps = generate_fake_amplitude(num_chans, cont_flux, 'flat')#np.zeros(num_chans)
            print('Observing '+target_data[key]['target_name']+' for '+target_data[key]['on_source']+'s')


            for obs_time in np.arange(0.0,float(target_data[key]['on_source']), int_time):


                this_amps = generate_fake_amplitude(num_chans, cont_flux,target_data[key]['profile'])
                source_avg_amps = np.concatenate((source_avg_amps,this_amps))
                mean_source_avg_amps =np.mean(source_avg_amps,0)

                line_amp_avg = amp_avg.line(chans, mean_source_avg_amps, line_width=1, color=colours[ic])
                circ_amp_time = amp_time.circle(total_time,np.mean(mean_source_avg_amps),color=colours[ic])

                push_notebook(handle=amp_plots)


#                 time.sleep(int_time/speed_up)
                line_amp_avg.visible=False
                total_time+=int_time
            ic+=1
        print('Finished current observing loop')

    return [total_time]
