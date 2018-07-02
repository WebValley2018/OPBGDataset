import numpy as np
import matplotlib.pyplot as plt
import SimpleITK as sitk
import os
import pydicom
from registration_utilities import *

# %%
def remove_keymap_conflicts(new_keys_set):
    for prop in plt.rcParams:
        if prop.startswith('keymap.'):
            keys = plt.rcParams[prop]
            remove_list = set(keys) & new_keys_set
            for key in remove_list:
                keys.remove(key)


def multi_slice_viewer(volume, mask=None):
    remove_keymap_conflicts({'j', 'k'})
    fig, ax = plt.subplots()

    if mask is not None:
        mask = mask * np.max(volume) / 2
        volume = volume + mask

    ax.volume = volume

    ax.index = volume.shape[2] // 2
    ax.imshow(volume[:, :, ax.index])

    #    ax.imshow(mask[:,:,ax.index], alpha=0.5)

    fig.canvas.mpl_connect('key_press_event', process_key)


def process_key(event):
    fig = event.canvas.figure
    ax = fig.axes[0]
    if event.key == 'j':
        previous_slice(ax)
    elif event.key == 'k':
        next_slice(ax)
    fig.canvas.draw()


def previous_slice(ax):
    volume = ax.volume
    #    mask = ax.mask
    ax.index = (ax.index - 1) % volume.shape[2]  # wrap around using %
    ax.images[0].set_array(volume[:, :, ax.index])


#    ax.images[1].set_array(mask[:,:, ax.index])

def next_slice(ax):
    volume = ax.volume
    #    mask = ax.mask
    ax.index = (ax.index + 1) % volume.shape[2]
    ax.images[0].set_array(volume[:, :, ax.index])


#    ax.images[1].set_array(mask[:,:, ax.index])

DATADIR_1 = '/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se000'
DATADIR_2 = '/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se001'

reader_1 = sitk.ImageSeriesReader()
reader_1.SetOutputPixelType(sitk.sitkFloat32)
dicom_names_1 = reader_1.GetGDCMSeriesFileNames(DATADIR_1)
reader_1.SetFileNames(dicom_names_1)

reader_2 = sitk.ImageSeriesReader()
reader_2.SetOutputPixelType(sitk.sitkFloat32)
dicom_names_2 = reader_2.GetGDCMSeriesFileNames(DATADIR_2)
reader_2.SetFileNames(dicom_names_2)

fixed_image = reader_1.Execute()
moving_image = reader_2.Execute()

moving_to_fixed = sitk.Resample(moving_image, fixed_image)
moving_to_fixed_np = sitk.GetArrayFromImage(moving_to_fixed)
moving_image_np = sitk.GetArrayFromImage(moving_image)
fixed_image_np = sitk.GetArrayFromImage(fixed_image)

multi_slice_viewer(moving_image_np)

initial_transform = sitk.CenteredTransformInitializer(fixed_image, 
                                                      moving_to_fixed, 
                                                      sitk.Euler3DTransform(), 
                                                      sitk.CenteredTransformInitializerFilter.GEOMETRY)

display_registration_results(fixed_image, moving_to_fixed, initial_transform)

print(initial_transform)

registration_method = sitk.ImageRegistrationMethod()

registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
registration_method.SetMetricSamplingPercentage(0.01)

registration_method.SetInterpolator(sitk.sitkLinear)

registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=60)
registration_method.SetOptimizerScalesFromPhysicalShift() 

registration_method.SetInitialTransform(initial_transform, inPlace=False)

registration_method.AddCommand(sitk.sitkStartEvent, metric_start_plot)
registration_method.AddCommand(sitk.sitkEndEvent, metric_end_plot)
registration_method.AddCommand(sitk.sitkIterationEvent, 
                               lambda: metric_plot_values(registration_method))

final_transform_v1 = registration_method.Execute(fixed_image, moving_to_fixed)

print(final_transform_v1)

display_registration_results(fixed_image, moving_to_fixed, final_transform_v1)
