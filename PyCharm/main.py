from dicom_utilities import *
from operator import itemgetter

PATIENTS_DIR = '/Users/riccardobusetti/Desktop/tmp_processed'

def do_registration(data):
    for patient in data:
        for study in data[patient]:
            seqs = data[patient][study].items()

            fixed, _ = origin_fixed = max(seqs, key=itemgetter(1))

            out_study_dir = os.path.join('/Users/riccardobusetti/Desktop/tmp_processed_mha', patient, study)

            if not os.path.exists(out_study_dir):
                os.makedirs(out_study_dir)

            for moving, _ in set(seqs) - {origin_fixed}:
                try:
                    RegistrationHelper(
                        os.path.join(PATIENTS_DIR, patient, study, moving),
                        os.path.join(PATIENTS_DIR, patient, study, fixed),
                        out_study_dir,
                        f'coreg_{moving}'
                    ).start_coregistration(save_on_disk=True)
                except RuntimeError:
                    pass

            print("\n----------")


helper = OPBGExplorer(PATIENTS_DIR)
do_registration(helper.load_patients())

'''helper = RegistrationHelper("/Users/riccardobusetti/Desktop/tmp_processed/pa015/st000/se000",
                            "/Users/riccardobusetti/Desktop/tmp_processed/pa015/st000/se001",
                            "/Users/riccardobusetti/Desktop/mha_processed/pa015/st000/se01",
                            "file_test").start_coregistration(save_as_nifti=True)'''
