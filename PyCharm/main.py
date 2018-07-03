from dicom_utilities import *
from operator import itemgetter

PATIENTS_DIR = '/Users/riccardobusetti/Desktop/tmp_processed'


def do_registration(data):
    for patient in data:
        for study in data[patient]:
            seqs = data[patient][study].items()

            fixed, _ = max(seqs, key=itemgetter(1))

            out_study_dir = os.path.join('/Users/riccardobusetti/Desktop/tmp_processed_nifti', patient, study)
            print(out_study_dir)

            if not os.path.exists(out_study_dir):
                os.makedirs(out_study_dir)

            for moving, _ in set(seqs) - {fixed}:
                try:
                    RegistrationHelper(
                        os.path.join(PATIENTS_DIR, patient, study, moving),
                        os.path.join(PATIENTS_DIR, patient, study, fixed),
                        out_study_dir,
                        f'/coreg_{moving}.nii'
                    ).start_coregistration(save_as_nifti=True)
                except RuntimeError:
                    pass


helper = OPBGExplorer(PATIENTS_DIR)
do_registration(helper.load_patients())
