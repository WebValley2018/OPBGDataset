from dicom_utilities import *
from operator import itemgetter

PATIENTS_DIR = 'tmp_processed'


def do_coreg(data):
    for patient in data:
        for study in data[patient]:
            seqs = data[patient][study].items()

            fixed, _ = max(seqs, key=itemgetter(1))

            out_study_dir = os.path.join('coreg', patient, study)

            if not os.path.exists(out_study_dir):
                os.makedirs(out_study_dir)

            for moving, _ in set(seqs) - {fixed}:
                try:
                    RegistrationHelper(
                        os.path.join(PATIENTS_DIR, patient, study, moving),
                        os.path.join(PATIENTS_DIR, patient, study, fixed),
                        out_study_dir,
                        f'/coreg_{moving}.nii'
                    ).start_coregistration()
                except RuntimeError:
                    pass


helper = DicomHelper()
print(helper.read_dicom_meta_data("/Users/riccardobusetti/Desktop/DICOM-DATA/tmp/0dd5f745-7f03-4cc6-b701-c74d3fbcee33/OPBG0016_20180622_113709428"))
