import numpy as np
from skimage.draw import polygon
from scipy.ndimage.interpolation import zoom

def flatten(lst):
    return sum(([x] if not isinstance(x, list) else flatten(x) for x in lst), [])

def generate_mask(scan, roi):
    scan_image = scan['image']
    X,Y,Z = scan['coords']
    
    mask = np.zeros_like(scan_image)
    for zslice in roi:
        curr_z = zslice[0][2]
        idx_z = np.argmin(abs(Z - curr_z))
        
        x_ = []
        y_ = []
        for points in zslice:
            curr_x = points[0]
            curr_y = points[1]
            idx_x = np.argmin(abs(X - curr_x))
            idx_y = np.argmin(abs(Y - curr_y))
            x_.append(idx_x)
            y_.append(idx_y)
        
        rr, cc = polygon(np.array(y_), np.array(x_))
        mask[rr,cc,idx_z] = 1
    
    return({'image':mask, 'coords':[X,Y,Z]})

def interpolate_scan(scan, pixel_size=None, pixel_number=None):
    assert pixel_size is not None or pixel_number is not None, "Either pixel_size or pixel_number should be defined, not both"
    assert not (pixel_size is not None and pixel_number is not None), "Either pixel_size or pixel_number should be defined, not both"
    x,y,z = scan['coords']
    
    if pixel_size is not None:
        ratiox = (max(x) - min(x))/(pixel_size*len(x))
        ratioy = (max(y) - min(y))/(pixel_size*len(y))
        ratioz = (max(z) - min(z))/(pixel_size*len(z))
    if pixel_number is not None:
        ratiox = pixel_number/len(x)
        ratioy = pixel_number/len(y)
        ratioz = pixel_number/len(z)
        
    out = zoom(scan['image'], (ratiox, ratioy, ratioz))
    x = np.linspace(min(x), max(x), out.shape[0])
    y = np.linspace(min(y), max(y), out.shape[1])
    z = np.linspace(min(z), max(z), out.shape[2])
    return({'image':out, 'coords':[x,y,z], 'modality':scan['modality']})

def get_volume(scan, box, margin):
    x,y,z = scan['coords']
    [max_x, min_x, max_y, min_y, max_z, min_z] = box
    max_x = max_x+margin
    min_x = min_x-margin
    
    max_y = max_y+margin
    min_y = min_y-margin
    
    max_z = max_z+margin
    min_z = min_z-margin
    
    x0 = x[0]
    dx = x[1] - x[0]
    idx_x_st = int(np.floor((min_x - x0)/dx))
    idx_x_sp = int(np.ceil((max_x - x0)/dx))
    
    y0 = y[0]
    dy = y[1] - y[0]
    idx_y_st = int(np.floor((min_y - y0)/dy))
    idx_y_sp = int(np.ceil((max_y - y0)/dy))
    
    z0 = z[0]
    dz = z[1] - z[0]
    idx_z_st = int(np.floor((min_z - z0)/dz))
    idx_z_sp = int(np.ceil((max_z - z0)/dz))
    
    volume_image = scan['image'][idx_x_st:idx_x_sp+1, idx_y_st:idx_y_sp+1, idx_z_st:idx_z_sp+1]
    volume_x = x[idx_x_st:idx_x_sp+1]
    volume_y = y[idx_y_st:idx_y_sp+1]
    volume_z = z[idx_z_st:idx_z_sp+1]
    
    return({'image':volume_image, 'coords':[volume_x, volume_y, volume_z], 'modality':scan['modality']})
    
def get_ROI_volume(PATIENT_DIR, name='GTV', margin = 5, interpolate=True, pixel_size=1):

    ct_dir, pt_dir, rt_ct_dir, rt_pt_dir = get_directories(PATIENT_DIR)

    scan_ct = read_SCAN(ct_dir, return_ref=False)
    box_ct = get_ROI_box(rt_ct_dir, name)
    
    scan_pt = read_SCAN(pt_dir, return_ref=False)
    box_pt = get_ROI_box(rt_pt_dir, name)
    
    scan_ct = get_volume(scan_ct, box_ct, margin)
    scan_pt = get_volume(scan_pt, box_pt, margin)
    
    if interpolate:
        scan_ct = interpolate_scan(scan_ct, pixel_size)
        scan_pt = interpolate_scan(scan_pt, pixel_size)
    return(scan_ct, scan_pt)