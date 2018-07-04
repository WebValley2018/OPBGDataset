import os
import shutil
from collections import defaultdict

import pydicom

INPUT_DIR = '/Users/riccardobusetti/Desktop/DIPG'
OUTPUT_DIR = '/Users/riccardobusetti/Desktop/DIPG_REG'

folders = defaultdict(lambda: defaultdict(list))

for patient_dir in os.scandir(INPUT_DIR):
    if not patient_dir.name.startswith('.'):
        for dicom_file in os.scandir(patient_dir):
            if not dicom_file.name.startswith('.'):
                dicom = pydicom.dcmread(dicom_file.path)

                folders[dicom.PatientName][dicom.SeriesNumber].append(dicom_file.path)


for patient in folders:
    for series in folders[patient]:
        folder_path = os.path.join(OUTPUT_DIR, str(patient), str(series))
        os.makedirs(folder_path, exist_ok=True)

        for image in folders[patient][series]:
            shutil.copy(image, folder_path)
