import os
import pydicom as pd
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import SimpleITK as Sitk

from moviepy.editor import *


# Helper class that maps the folders of the OPBG dataset.
# author: Ettore Forigo.
class OPBGExplorer:

    # Initialization method of the class.
    def __init__(self, root_dir):
        self.root_dir = root_dir

    # Maps the folders as nested dictionaries that will be
    # used to feed the registration algorithm.
    def load_patients(self):
        return {
            patient_dir.name: {
                study_dir.name: {
                    sequence_dir.name: sum(1 for _ in os.scandir(sequence_dir))
                    for sequence_dir in os.scandir(study_dir) if not sequence_dir.name.startswith('.')
                }
                for study_dir in os.scandir(patient_dir) if not study_dir.name.startswith('.')
            }
            for patient_dir in os.scandir(self.root_dir) if not patient_dir.name.startswith('.')
        }


# Helper class to perform registration on images.
# author: Riccardo Busetti.
class RegistrationHelper:

    # Initialization method of the class.
    def __init__(self, moving_image_dir, fixed_image_dir, output_dir, output_name):
        self.moving_image_dir = moving_image_dir
        self.fixed_image_dir = fixed_image_dir
        self.output_dir = output_dir
        self.output_name = output_name

    # Creates the reader object, one for each sequence of
    # dicom images. This readers are then used to perform
    # operations on the dicom files.
    def read_dicom_files(self):
        # Reading meta data of the first sequence of images.
        reader_first = Sitk.ImageSeriesReader()
        reader_first.SetOutputPixelType(Sitk.sitkFloat64)
        dicom_first = reader_first.GetGDCMSeriesFileNames(self.moving_image_dir)
        reader_first.SetFileNames(dicom_first)

        # Reading meta data of the second sequence of images.
        reader_second = Sitk.ImageSeriesReader()
        reader_second.SetOutputPixelType(Sitk.sitkFloat64)
        dicom_second = reader_second.GetGDCMSeriesFileNames(self.fixed_image_dir)
        reader_second.SetFileNames(dicom_second)

        return reader_first, reader_second

    # Computes the dicom files from the reader and returns a "3D"
    # image, that will be then resampled.
    def compute_dicom_files(self, reader_first, reader_second):
        # Returns a tuple with images.
        return reader_first.Execute(), reader_second.Execute()

    # Resampling process of the two images.
    def resample(self, moving_image, fixed_image):
        # Returns the resampled image.
        return Sitk.Resample(moving_image, fixed_image)

    def final_resample(self, fixed_image, resampled_image, transformation):
        return Sitk.Resample(resampled_image,
                             fixed_image,
                             transformation,
                             Sitk.sitkLinear,
                             0.0,
                             resampled_image.GetPixelIDValue())

    # Getting the initial transform.
    def get_initial_transform(self, fixed_image, resampled_image):
        # Returns the centered transorm.
        return Sitk.CenteredTransformInitializer(fixed_image,
                                                 resampled_image,
                                                 Sitk.Euler3DTransform(),
                                                 Sitk.CenteredTransformInitializerFilter.GEOMETRY)

    # Getting the secondary transform.
    def get_secondary_transform(self, fixed_image, resampled_image, initial_transform):
        registration_method = Sitk.ImageRegistrationMethod()

        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.01)

        registration_method.SetInterpolator(Sitk.sitkLinear)

        registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=60)
        registration_method.SetOptimizerScalesFromPhysicalShift()

        registration_method.SetInitialTransform(initial_transform, inPlace=False)

        # Returns the coregistration trasformation.
        return registration_method.Execute(fixed_image, resampled_image)

    # Converts a specified image to numpy array.
    def image_to_nparray(self, image):
        # Returns the numpy array of a specific image.
        return Sitk.GetArrayFromImage(image)

    # Plot all the images.
    def plot_images(self, *images):
        # Loop throgh images and plot them.
        for image in images:
            print(str(image.shape))
            depth_level, _, _ = image.shape
            plt.imshow(image[int(depth_level / 2), :, :])
            plt.show()
        print("--------------------------------------")

    # Converts image as numpy array to nifti and saves it.
    def nparray_to_nifti(self, image, output_path):
        nifti_image = nib.Nifti1Image(image, affine=np.eye(4))
        nib.save(nifti_image, output_path)

    # Starts the coregistration.
    def start_coregistration(self, save_as_nifti=False):
        # Reading dicom files.
        reader_first, reader_second = self.read_dicom_files()

        # Computing dicom files.
        moving_image, fixed_image = self.compute_dicom_files(reader_first, reader_second)

        # Resampling images.
        resampled_image = self.resample(moving_image, fixed_image)

        # Second resampling process with the centered transformation.
        initial_transformation = self.get_initial_transform(fixed_image, resampled_image)
        resampled_image = self.final_resample(fixed_image, resampled_image, initial_transformation)

        # Third resampling process with the coregistration transformation.
        secondary_transformation = self.get_secondary_transform(fixed_image, resampled_image, initial_transformation)
        resampled_image = self.final_resample(fixed_image, resampled_image, secondary_transformation)

        # Converting images from image object to numpy array.
        moving_image_np = self.image_to_nparray(moving_image)
        fixed_image_np = self.image_to_nparray(fixed_image)
        resampled_image_np = self.image_to_nparray(resampled_image)

        # Plotting images.
        self.plot_images(moving_image_np,
                         fixed_image_np,
                         resampled_image_np)

        # Saving images as nifti to the disk.
        if save_as_nifti:
            self.nparray_to_nifti(resampled_image_np, self.output_dir + self.output_name)


# Helper class to help read dicom files.
# author: Riccardo Busetti.
class DicomHelper:

    # Initialization method of the class.
    def __init__(self):
        pass

    # Creates a gif from an array, in our case
    # it will convert a 3D nparray to a gid.
    def dicom_to_gif(self, output_dir, array, fps=10, scale=1.0):
        # Ensure that the file has the .gif extension.
        fname, _ = os.path.splitext(output_dir)
        output_dir = fname + '.gif'

        # Copy into the color dimension if the images are black and white.
        if array.ndim == 3:
            array = array[..., np.newaxis] * np.ones(3)

        # Make the moviepy clip.
        clip = ImageSequenceClip(list(array), fps=fps).resize(scale)
        clip.write_gif(output_dir, fps=fps)
        return clip

    # Returns a list with the meta data of a dicom file from
    # a given sequence.
    def read_dicom_meta_data(self, dicom_dir):
        dicom_files = list(filter(lambda it: not it.startswith(".") and it != "VERSION", os.listdir(dicom_dir)))

        if len(dicom_files) > 0:
            return pd.dcmread(os.path.join(dicom_dir, dicom_files[0]))
        else:
            return None

