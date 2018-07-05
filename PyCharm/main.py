from operator import itemgetter
import traceback

from dicom_utilities import *

PATIENTS_DIR = '/Users/riccardobusetti/Desktop/MB_PROC'


def do_registration(data):
    for patient in data:
        seqs = data[patient].items()

        fixed, _ = max(seqs, key=itemgetter(1))

        out_study_dir = os.path.join('/Users/riccardobusetti/Desktop/MB_COREG', patient)

        print(out_study_dir)

        if not os.path.exists(out_study_dir):
            os.makedirs(out_study_dir)

        for moving, _ in set(seqs):
            try:
                RegistrationHelper(
                    os.path.join(PATIENTS_DIR, patient, moving),
                    os.path.join(PATIENTS_DIR, patient, fixed),
                    out_study_dir,
                    f'{patient}_coreg_{moving}'
                ).start_coregistration(is_nifti=False,
                                       save_on_disk=True,
                                       file_extension=".nii")
            except RuntimeError as e:
                print(e)
                traceback.print_exc()
            print("Finished patient")

        print("\n----------\n")


helper = OPBGExplorer(PATIENTS_DIR)
do_registration(helper.load_patients())

'''helper = RegistrationHelper("/Volumes/LaCie/out/OPBG2001/5",
                            "/Volumes/LaCie/out/OPBG2001/6",
                            "/Users/riccardobusetti/Desktop/registration_nii",
                            "file_test").start_coregistration(is_nifti=False,
                                                              save_on_disk=True,
                                                              file_extension=".nii")'''
