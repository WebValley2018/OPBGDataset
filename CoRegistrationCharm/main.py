import nibabel as nib

from registration_utilities import *

# Helper class to perform coregistration on images.
class CoRegistration():

    # Initialization method of the class.
    def __init__(self, first_dir, second_dir, output_dir, output_name):
        self.first_dir = first_dir
        self.second_dir = second_dir
        self.output_dir = output_dir
        self.output_name = output_name

    # Creates the reader object, one for each sequence of
    # dicom images. This readers are then used to perform
    # operations on the dicom files.
    def read_dicom_files(self):
        # Reading meta data of the first sequence of images.
        reader_first = sitk.ImageSeriesReader()
        reader_first.SetOutputPixelType(sitk.sitkFloat32)
        dicom_first = reader_first.GetGDCMSeriesFileNames(self.first_dir)
        reader_first.SetFileNames(dicom_first)

        # Reading meta data of the second sequence of images.
        reader_second = sitk.ImageSeriesReader()
        reader_second.SetOutputPixelType(sitk.sitkFloat32)
        dicom_second = reader_second.GetGDCMSeriesFileNames(self.second_dir)
        reader_second.SetFileNames(dicom_second)
        return (reader_first, reader_second)

    # Computes the dicom files from the reader and returns a "3D"
    # image, that will be then resampled.
    def compute_dicom_files(self, reader_first, reader_second):
        # Returning a tuple with images.
        return (reader_first.Execute(),
                reader_second.Execute())

    # Resampling process of the two images, that will use
    # the centered transform algorithm.
    def center_resample(self, moving_image, fixed_image):
        # Initiate the center transformation.
        initial_transform = sitk.CenteredTransformInitializer(fixed_image,
                                                              moving_image,
                                                              sitk.Euler3DTransform(),
                                                              sitk.CenteredTransformInitializerFilter.GEOMETRY)

        # Returning the resampled image.
        return (sitk.Resample(moving_image,
                             fixed_image,
                             initial_transform,
                             sitk.sitkLinear,
                             0.0,
                             moving_image.GetPixelID()), initial_transform)

    # Converts a specified image to numpy array.
    def image_to_nparray(self, image):
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

    # Coregistration of the images.
    def coregister(self, moving_image, fixed_image, initial_transform):
        registration_method = sitk.ImageRegistrationMethod()

        # Similarity metric settings.
        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.01)

        registration_method.SetInterpolator(sitk.sitkLinear)

        # Optimizer settings.
        registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100,
                                                          convergenceMinimumValue=1e-6, convergenceWindowSize=10)
        registration_method.SetOptimizerScalesFromPhysicalShift()

        # Setup for the multi-resolution framework.
        registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
        registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
        registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

        # Don't optimize in-place, we would possibly like to run this cell multiple times.
        registration_method.SetInitialTransform(initial_transform, inPlace=False)

        # Execute the final transformation.
        final_transform = registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),
                                                      sitk.Cast(moving_image, sitk.sitkFloat32))

        # Resample the final image.
        return sitk.Resample(moving_image,
                             fixed_image,
                             final_transform,
                             sitk.sitkLinear,
                             0.0,
                             moving_image.GetPixelID())

    # Starts the coregistration.
    def start_coregistration(self):
        # Reading dicom files.
        reader_first, reader_second = self.read_dicom_files()

        # Computing dicom files.
        moving_image, fixed_image = self.compute_dicom_files(reader_first, reader_second)

        # Resampling images.
        resampled_image, initial_transform = self.center_resample(moving_image, fixed_image)

        # Final resample.
        final_resampled_image = self.coregister(moving_image, fixed_image, initial_transform)

        # Converting images from <Image> object to numpy array.
        moving_image_np = self.image_to_nparray(moving_image)
        fixed_image_np = self.image_to_nparray(fixed_image)
        resampled_image_np = self.image_to_nparray(resampled_image)
        final_resampled_image_np = self.image_to_nparray(final_resampled_image)

        # Plotting images.
        self.plot_images(moving_image_np,
                         fixed_image_np,
                         resampled_image_np,
                         final_resampled_image_np)

        # Saving images as nifti to the disk.
        self.nparray_to_nifti(final_resampled_image_np, self.output_dir + self.output_name)


for i in range(0, 6, 2):
    FIRST_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa002/st000/se00{i}"
    SECOND_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa002/st000/se00{i+1}"
    coregistration = CoRegistration(FIRST_IMAGE_DIR,
                                    SECOND_IMAGE_DIR,
                                    f"/Users/riccardobusetti/Desktop",
                                    f"/resampled_image_{i}.nii")
    coregistration.start_coregistration()
