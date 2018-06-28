import nibabel as nib

from registration_utilities import *


class CoRegistration():

    def __init__(self, first_dir, second_dir):
        self.first_dir = first_dir
        self.second_dir = second_dir

    def get_meta_data(self):
        # Reading meta data of the first images
        reader_first = sitk.ImageSeriesReader()
        reader_first.SetOutputPixelType(sitk.sitkFloat32)
        dicom_first = reader_first.GetGDCMSeriesFileNames(self.first_dir)
        reader_first.SetFileNames(dicom_first)
        # Reading meta data of the second images
        reader_second = sitk.ImageSeriesReader()
        reader_second.SetOutputPixelType(sitk.sitkFloat32)
        dicom_second = reader_second.GetGDCMSeriesFileNames(self.second_dir)
        reader_second.SetFileNames(dicom_second)
        return (reader_first, reader_second)

    def execute(self, reader_first, reader_second):
        # Returning a tuple with images
        return (reader_first.Execute(),
                reader_second.Execute())

    def resample(self, moving_image, fixed_image):
        # Returning the resampled image
        return sitk.Resample(moving_image, fixed_image)

    def images_to_np_array(self, moving_image, fixed_image, resampled_image):
        # Returning a tuple with images converted to numpy arrays
        return (sitk.GetArrayFromImage(moving_image),
                sitk.GetArrayFromImage(fixed_image),
                sitk.GetArrayFromImage(resampled_image))

    def plot_images(self, moving_image_np, fixed_image_np, resampled_image_np):
        print(str(moving_image_np.shape))
        depth_level, _, _ = moving_image_np.shape
        plt.imshow(moving_image_np[int(depth_level / 2), :, :])
        plt.show()
        print(str(fixed_image_np.shape))
        depth_level, _, _ = fixed_image_np.shape
        plt.imshow(fixed_image_np[int(depth_level / 2), :, :])
        plt.show()
        print(str(resampled_image_np.shape))
        depth_level, _, _ = resampled_image_np.shape
        plt.imshow(resampled_image_np[int(depth_level / 2), :, :])
        plt.show()
        print("--------------------------------------")

    def convert_resampled_np_to_nifti(self, resampled_image_np):
        # Returns the numpy array converted to nifti format
        return nib.Nifti1Image(resampled_image_np, affine=np.eye(4))

    def transform(self, fixed_image, resampled_image):
        # Returns the centered images
        return sitk.CenteredTransformInitializer(fixed_image,
                                          resampled_image,
                                          sitk.Euler3DTransform(),
                                          sitk.CenteredTransformInitializerFilter.GEOMETRY)

    def coregister(self, fixed_image, resampled_image, initial_transform):
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
        return registration_method.Execute(fixed_image, resampled_image)

    def start_coregistration(self):
        reader_first, reader_second = self.get_meta_data()
        moving_image, fixed_image = self.execute(reader_first, reader_second)
        resampled_image = self.resample(moving_image, fixed_image)
        moving_image_np, fixed_image_np, resampled_image_np = self.images_to_np_array(moving_image,
                                                                                      fixed_image,
                                                                                      resampled_image)
        transform = self.transform(fixed_image, resampled_image)
        final_transform = self.coregister(fixed_image, resampled_image, transform)
        # self.plot_images(moving_image_np, fixed_image_np, resampled_image_np)
        # nifti_resampled_image = self.convert_resampled_np_to_nifti(resampled_image_np)
        # nib.save(nifti_resampled_image, "/Users/riccardobusetti/Desktop/resampled_image.nii")


for i in range(0, 8):
    FIRST_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se00{i}"
    SECOND_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se00{i+1}"
    coregistration = CoRegistration(FIRST_IMAGE_DIR, SECOND_IMAGE_DIR)
    moving_image, fixed_image, resampled_image = coregistration.start_coregistration()
