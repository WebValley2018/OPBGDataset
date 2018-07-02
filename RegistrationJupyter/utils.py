import pydicom
import os
import numpy as np

def isDCMLeaf(directory):
    '''
    Return true if the directory contains only dcm file
    '''
    subdirs = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    if len(subdirs)>0:
        return(False)
    fileslist = os.listdir(directory)
    dcmCollection = np.array(['.dcm' in x for x in fileslist]).all()
    return(dcmCollection) 

def isRTSTRUCT(folder):
    if not isDCMLeaf(folder): return(False)
    
    files = os.listdir(folder)
    if len(files)!=1: return(False)
    
    dataset = pydicom.dcmread(os.path.join(folder, files[0]))
    if dataset.Modality != 'RTSTRUCT': return(False)
    
    return(True)

def get_DCMLeaf_info(directory):
    '''
    Return number of files and modality of a DCMLeaf directory
    '''
    assert isDCMLeaf(directory), 'directory should be a DCMLeaf'
    files = os.listdir(directory)
    try:
        RefDs = pydicom.dcmread(os.path.join(directory, files[0]))
        modality = RefDs.Modality
    except:
        modality = ''
    return(len(files), modality )

def get_dataset_info(dcm_dataset):
    '''
    Read and print all string metadata
    '''
    tags = dcm_dataset.dir()
    for TAG in tags:
        value = dcm_dataset.get(TAG)
        if isinstance(value, str) or isinstance(value, float) or isinstance(value, int):
            print(TAG, '\t\t\t', str(value))
            
def iterativeScan(directory):
    '''
    Iteratively scan all folders and sub-folders and report info about the DCMLeaf folders
    '''
    if isDCMLeaf(directory):
        leaf_info = get_DCMLeaf_info(directory)
        return(directory, leaf_info[0], leaf_info[1])
    else:
        directories = []
        n_slices = []
        modalities = []
        subdirs = [os.path.join(directory, name) for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
        for SUB in subdirs:
            subdir, n_slice, modality = iterativeScan(SUB)
            directories.append(np.array(subdir))
            n_slices.append(np.array(n_slice))
            modalities.append(np.array(modality))
        return(directories, n_slices, modalities)

def get_rois_names(folder):
    '''
    Load a DCM file (RTSTRUCT modality) containing volume ROIs and return the names of the ROIs
    '''
    assert isRTSTRUCT(folder), "Input folder is not a valid RTSTRUCT folder"
    files = os.listdir(folder)
    dataset = pydicom.dcmread(os.path.join(folder, files[0]))
    
    structure_set = dataset.StructureSetROISequence
    rois = dataset.ROIContourSequence
    
    roi_name = []
    for i, (STRUCT, ROI)  in enumerate(zip(structure_set,rois)):
        roi_name.append(STRUCT.ROIName)
    
    return(roi_name)
    
#%%
def get_directories(patient_dir, roi_name='GTV'):
    '''
    Select candidate CT, PT and RTSTRUCT (with given roi_name) folders.
    DISCLAIMER: Developed for Head-Neck dataset
    '''
    patient_dir = os.path.join(patient_dir)
    dirs, slices, modalities = iterativeScan(patient_dir)
    dirs = np.array(flatten(dirs))
    slices = np.array(flatten(slices))
    modalities = np.array(flatten(modalities))
    
    errors = []
    #candidate PT
    dir_PT = ''
    hasPT =  'PT' in modalities
    if hasPT:
        idx_PT = np.where(np.array(modalities)=='PT')[0]
        if len(idx_PT)>1:
            errors.append('Multiple PT scans')
            
        idx_PT = idx_PT[0]
        n_slices_PT = slices[idx_PT]
        dir_PT = dirs[idx_PT]
    else:
        errors.append('No PT scans')
    
    
    #candidate CT        
    dir_CT = ''
    hasCT =  'CT' in modalities
    if hasCT and hasPT:
        idx_CT = np.where(np.array(modalities)=='CT')[0]
        n_slices_CT = slices[idx_CT]
        
        if len(idx_CT)>1: #multiple CT found
            # search set with same number of slices as PT
            idx_OK = np.where(n_slices_CT==n_slices_PT)[0]
            if len(idx_OK) == 0 : #no same number 
                errors.append('Multiple CT scans, none with same slices number as PT, picking the set with more slices')
                idx_CT = idx_CT[np.argmax(n_slices_CT)]
            else:
                idx_CT = idx_CT[idx_OK[0]]
        else:
            idx_CT = idx_CT[0]
            n_slices_CT = slices[idx_CT]
            if n_slices_CT != n_slices_PT:
                errors.append('One CT scan set found. With different slices number as PT')
            
        dir_CT = dirs[idx_CT]
    else:
        errors.append('No CT scans')
    
    #candidate RT struct is the one with GTV
    hasRTSTRUCT = 'RTSTRUCT' in modalities
    dir_RT = ''
    if hasRTSTRUCT and hasCT and hasPT:
        idx_RTSTRUCT = np.where(modalities == 'RTSTRUCT')[0]
        dirs_RT = dirs[idx_RTSTRUCT]
        dirs_RT_ok = []
        for D in dirs_RT:
            roi_names = get_RTSTRUCT_names(D)
            for NAME in roi_names:
                if roi_name in NAME:
                    dirs_RT_ok.append(D)
                
                
        if len(dirs_RT_ok)==0:
            errors.append('RTSTRUCT found but none with requested ROI')
        elif len(dirs_RT_ok)>1:
            errors.append('Multiple RT scans, searching petpet')
            done = False
            for D in dirs_RT_ok:
                if 'petpet' in D.lower(): 
                    dir_RT = D
                    done = True
            
            if not done:
                errors.append('petpet not found using the first valid')
                dir_RT = dirs_RT_ok[0]
        else:
            dir_RT = dirs_RT_ok[0]
    else:
        errors.append('No RTSTRUCT')
    
    return([dir_CT, dir_PT, dir_RT], errors)