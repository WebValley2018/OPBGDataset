from dicom_utilities import *

FIRST_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se001"
SECOND_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa001/st000/se002"
coregistration = CoRegistration(FIRST_IMAGE_DIR,
                                    SECOND_IMAGE_DIR,
                                    f"/Users/riccardobusetti/Desktop/nifti",
                                    f"/resampled_image_1.nii")
coregistration.start_coregistration()
