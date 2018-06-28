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
        return sitk.Resample(moving_image,
                             fixed_image,
                             initial_transform,
                             sitk.sitkLinear,
                             0.0,
                             moving_image.GetPixelID())

    # Converts all the images to numpy array.
    def images_to_np_array(self, moving_image, fixed_image, resampled_image):
        # Returning a tuple with images converted to numpy arrays
        return (sitk.GetArrayFromImage(moving_image),
                sitk.GetArrayFromImage(fixed_image),
                sitk.GetArrayFromImage(resampled_image))

    # Plot all the images.
    def plot_images(self, moving_image_np, fixed_image_np, resampled_image_np):
        # Plots moving image.
        print(str(moving_image_np.shape))
        depth_level, _, _ = moving_image_np.shape
        plt.imshow(moving_image_np[int(depth_level / 2), :, :])
        plt.show()

        # Plots fixed image.
        print(str(fixed_image_np.shape))
        depth_level, _, _ = fixed_image_np.shape
        plt.imshow(fixed_image_np[int(depth_level / 2), :, :])
        plt.show()

        # Plots resampled image.
        print(str(resampled_image_np.shape))
        depth_level, _, _ = resampled_image_np.shape
        plt.imshow(resampled_image_np[int(depth_level / 2), :, :])
        plt.show()
        print("--------------------------------------")

    # Converts image as numpy array to nifti and saves it.
    def nparray_to_nifti(self, image, output_path):
        nifti_image = nib.Nifti1Image(image, affine=np.eye(4))
        nib.save(nifti_image, output_path)

    # TODO: this method needs to be rewritten and understood
    def coregister(self, fixed_image, resampled_image, initial_transform):
        registration_method = sitk.ImageRegistrationMethod()

        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.01)

        registration_method.SetInterpolator(sitk.sitkLinear)

        registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=60)
        registration_method.SetOptimizerScalesFromPhysicalShift()

        registration_method.SetInitialTransform(initial_transform, inPlace=False)

        return registration_method.Execute(fixed_image, resampled_image)

    def start_coregistration(self):
        # Reading dicom files.
        reader_first, reader_second = self.read_dicom_files()

        # Computing dicom files.
        moving_image, fixed_image = self.compute_dicom_files(reader_first, reader_second)

        # Resampling images.
        resampled_image = self.center_resample(moving_image, fixed_image)

        # Converting images from <Image> object to numpy array.
        moving_image_np, fixed_image_np, resampled_image_np = self.images_to_np_array(moving_image,
                                                                                      fixed_image,
                                                                                      resampled_image)

        # Plotting images.
        self.plot_images(moving_image_np, fixed_image_np, resampled_image_np)

        # Saving images as nifti to the disk.
        self.nparray_to_nifti(resampled_image, "")


for i in range(0, 8):
    FIRST_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se00{i}"
    SECOND_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se00{i+1}"
    coregistration = CoRegistration(FIRST_IMAGE_DIR,
                                    SECOND_IMAGE_DIR,
                                    "/Users/riccardobusetti/Desktop",
                                    f"resampled_image_{i}")
    coregistration.start_coregistration()

'''FIRST_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se000"
SECOND_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se001"
coregistration = CoRegistration(FIRST_IMAGE_DIR, SECOND_IMAGE_DIR)
coregistration.start_coregistration()'''
