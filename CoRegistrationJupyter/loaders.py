import pydicom
import os
import numpy as np
from .utils import isDCMLeaf as _isDCMLeaf, isRTSTRUCT as _isRTSTRUCT, get_dataset_info as _get_info

def load_series(folder, return_ref=True):
    '''
    Load a series of DCM slices from the folder.
    Return a dictionary: 
        'image': numpy array of the 3D image; 
        'coords': sampling of the positions on the 3 axis; 
        'reference': reference dicom dataset with metadata (if return_ref=True).
    '''
    assert _isDCMLeaf(folder), "The folder is not a DCMLeaf"
    
    files = os.listdir(folder)
    RefDs = pydicom.dcmread(os.path.join(folder, files[0]))
    
    # Load dimensions info
    nx = int(RefDs.Rows)
    ny = int(RefDs.Columns)
    nz=len(files)
    dx = float(RefDs.PixelSpacing[0])
    dy = float(RefDs.PixelSpacing[0])
#    dz = float(RefDs.SliceThickness)
    # create 3d numpy array of the scan
    ArrayDicom = np.zeros((nx, ny, nz))
    z = []
    # loop through all the DICOM files
    for i, filenameDCM in enumerate(files):
        # read the file
        ds = pydicom.dcmread(os.path.join(folder, filenameDCM))
        # store the raw image data
        ArrayDicom[:, :, i] = ds.pixel_array
        print(ds.SOPInstanceUID)
        z.append(float(ds.ImagePositionPatient[2]))
    
    indexes_sort = np.argsort(z)
    x0,y0,_ = np.array(ds.ImagePositionPatient).astype(float)
    
    # create mesh of physical coordinates
    
    x = np.arange(nx)*dx + x0
    y = np.arange(ny)*dy + y0
    z = np.array(z)[indexes_sort]
    
    ArrayDicom = ArrayDicom[:,:,indexes_sort]
    if return_ref:
        return({'image':ArrayDicom, 'coords':[x,y,z], 'modality':RefDs.Modality, 'reference':RefDs})
    else:
        return({'image':ArrayDicom, 'coords':[x,y,z], 'modality':RefDs.Modality})

    
def load_roi(folder, name=None, return_ref=True):
    '''
    Load a DCM file (RTSTRUCT modality) containing volume ROIs.
    Return a dictionary for the selected roi names (all rois if name=None):
        'name': names of the ROIs; 
        'coords': coordinates of the ROIs;
        'box': coordinate of the bounding box of each ROI;
        'reference': reference dicom dataset with metadata (if return_ref=True).
    '''
    assert _isRTSTRUCT(folder), "Input folder is not a valid RTSTRUCT folder"
    files = os.listdir(folder)
    dataset = pydicom.dcmread(os.path.join(folder, files[0]))
    
    structure_set = dataset.StructureSetROISequence
    
    rois = dataset.ROIContourSequence
    
    roi_names = []
    roi_coords = []
    roi_boxs = []
    for i, (STRUCT, ROI)  in enumerate(zip(structure_set, rois)):
        ROI_NAME = STRUCT.ROIName
        if ROI_NAME in name:
            roi_names.append(ROI_NAME)
        
            coords = []
            max_x = -np.Inf
            min_x = np.Inf
            max_y = -np.Inf
            min_y = np.Inf
            max_z = -np.Inf
            min_z = np.Inf
            contours = ROI.ContourSequence
            for Z_CONT in contours:
                z_data = np.array([float(x) for x in Z_CONT.ContourData])
                z_data = np.reshape(z_data, (int(len(z_data)/3), 3))
                max_x = np.max([max_x, np.max(z_data[:,0])])
                min_x = np.min([min_x, np.min(z_data[:,0])])
                max_y = np.max([max_y, np.max(z_data[:,1])])
                min_y = np.min([min_y, np.min(z_data[:,1])])
                max_z = np.max([max_z, np.max(z_data[:,2])])
                min_z = np.min([min_z, np.min(z_data[:,2])])
                coords.append(z_data)
        
            roi_coords.append(coords)
            roi_boxs.append([max_x, min_x, max_y, min_y, max_z, min_z])

    # TODO coord to indexes
    if return_ref:
        return({'name':roi_names, 'coords':roi_coords, 'box': roi_boxs, 'reference': dataset})
    else:
        return({'name':roi_names, 'coords':roi_coords,'box': roi_boxs})