from dicom_utilities import *

for i in range(0, 6, 2):
    FIRST_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa002/st000/se00{i}"
    SECOND_IMAGE_DIR = f"/Users/riccardobusetti/Desktop/tmp_processed/pa002/st000/se00{i+1}"
    coregistration = CoRegistration(FIRST_IMAGE_DIR,
                                    SECOND_IMAGE_DIR,
                                    f"/Users/riccardobusetti/Desktop/nifti",
                                    f"/resampled_image_{i}.nii")
    coregistration.start_coregistration()
