import os
import shutil
from collections import defaultdict

import pydicom

INPUT_DIR = '/Volumes/TOSHIBA EXT/OPBG-DEF/by_type/HEALTHY'
OUTPUT_DIR = '/Volumes/TOSHIBA EXT/OPBG-DEF/by_type/HEALTHY_PROC'

folders = defaultdict(lambda: defaultdict(list))

for patient_dir in os.scandir(INPUT_DIR):
    if not patient_dir.name.startswith('.'):
        for dicom_file in os.scandir(patient_dir):
            if not dicom_file.name.startswith('.')\
                    and not dicom_file.is_dir():
                dicom = pydicom.dcmread(dicom_file.path)

                folders[dicom.PatientName][dicom.SeriesNumber].append(dicom_file.path)
print("Finished mapping!")

for patient in folders:
    for series in folders[patient]:
        folder_path = os.path.join(OUTPUT_DIR, str(patient), str(series))
        os.makedirs(folder_path, exist_ok=True)
        print(f"Folder {folder_path} just created, insertion in progress...")
        for image in folders[patient][series]:
            shutil.copy(image, folder_path)
