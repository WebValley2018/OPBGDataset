import nibabel as nib

from registration_utilities import *

# Helper class to perform coregistration on images.
class CoRegistration():

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
        reader_first = sitk.ImageSeriesReader()
        reader_first.SetOutputPixelType(sitk.sitkFloat64)
        dicom_first = reader_first.GetGDCMSeriesFileNames(self.moving_image_dir)
        reader_first.SetFileNames(dicom_first)

        # Reading meta data of the second sequence of images.
        reader_second = sitk.ImageSeriesReader()
        reader_second.SetOutputPixelType(sitk.sitkFloat64)
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
        return sitk.Resample(moving_image, fixed_image)

    def final_resample(self, fixed_image, resampled_image, transformation):
        return sitk.Resample(resampled_image,
                             fixed_image,
                             transformation,
                             sitk.sitkLinear,
                             0.0,
                             resampled_image.GetPixelIDValue())

    # Getting the initial transform.
    def get_initial_transform(self, fixed_image, resampled_image):
        # Returns the centered transorm.
        return sitk.CenteredTransformInitializer(fixed_image,
                                            resampled_image,
                                            sitk.Euler3DTransform(),
                                            sitk.CenteredTransformInitializerFilter.GEOMETRY)

    # Getting the secondary transform.
    def get_secondary_transform(self, fixed_image, resampled_image, initial_transform):
        registration_method = sitk.ImageRegistrationMethod()

        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.01)

        registration_method.SetInterpolator(sitk.sitkLinear)

        registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=60)
        registration_method.SetOptimizerScalesFromPhysicalShift()

        registration_method.SetInitialTransform(initial_transform, inPlace=False)

        # Returns the coregistration trasformation.
        return registration_method.Execute(fixed_image, resampled_image)

    # Converts a specified image to numpy array.
    def image_to_nparray(self, image):
        # Returns the numpy array of a specific image.
        return sitk.GetArrayFromImage(image)

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
    def start_coregistration(self):
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
        self.nparray_to_nifti(resampled_image_np, self.output_dir + self.output_name)