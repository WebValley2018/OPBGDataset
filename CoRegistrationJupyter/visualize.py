import matplotlib.pyplot as plt
import numpy as np
#%%
def remove_keymap_conflicts(new_keys_set):
    for prop in plt.rcParams:
        if prop.startswith('keymap.'):
            keys = plt.rcParams[prop]
            remove_list = set(keys) & new_keys_set
            for key in remove_list:
                keys.remove(key)
                
def multi_slice_viewer(volume, mask=None):
    remove_keymap_conflicts({'j', 'k'})
    fig, ax = plt.subplots()
    
    if mask is not None:
        mask = mask*np.max(volume)/2

    ax.volume = volume + mask
        
    ax.index = volume.shape[2] // 2
    ax.imshow(volume[:,:,ax.index])
    
#    ax.imshow(mask[:,:,ax.index], alpha=0.5)
        
    fig.canvas.mpl_connect('key_press_event', process_key)

def process_key(event):
    fig = event.canvas.figure
    ax = fig.axes[0]
    if event.key == 'j':
        previous_slice(ax)
    elif event.key == 'k':
        next_slice(ax)
    fig.canvas.draw()

def previous_slice(ax):
    volume = ax.volume
#    mask = ax.mask
    ax.index = (ax.index - 1) % volume.shape[2]  # wrap around using %
    ax.images[0].set_array(volume[:,:, ax.index])
#    ax.images[1].set_array(mask[:,:, ax.index])

def next_slice(ax):
    volume = ax.volume
#    mask = ax.mask
    ax.index = (ax.index + 1) % volume.shape[2]
    ax.images[0].set_array(volume[:,:,ax.index])
#    ax.images[1].set_array(mask[:,:, ax.index])
