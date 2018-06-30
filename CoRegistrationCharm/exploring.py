import os
from operator import itemgetter

from dicom_utilities import CoRegistration

PATIENTS_DIR = 'tmp_processed'


def load_patients():
    return {
        patient_dir.name: {
            study_dir.name: {
                sequence_dir.name: sum(1 for _ in os.scandir(sequence_dir))
                for sequence_dir in os.scandir(study_dir) if not sequence_dir.name.startswith('.')
            }
            for study_dir in os.scandir(patient_dir) if not study_dir.name.startswith('.')
        }
        for patient_dir in os.scandir(PATIENTS_DIR) if not patient_dir.name.startswith('.')
    }


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
                    CoRegistration(
                        os.path.join(PATIENTS_DIR, patient, study, moving),
                        os.path.join(PATIENTS_DIR, patient, study, fixed),
                        out_study_dir,
                        f'/coreg_{moving}.nii'
                    ).start_coregistration()
                except RuntimeError:
                    pass

do_coreg(load_patients())
