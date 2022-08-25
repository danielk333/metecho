import metecho
import pathlib 
import numpy as np
from matplotlib import pyplot as plt

doa_example_data = pathlib.Path().home() / 'clones' / 'metecho_clone' / 'metecho' / 'src' / 'metecho' / 'data' /'doa_data_example.npy'

sample_range = np.load(doa_example_data)

# plotting
fig = plt.figure()

ax = fig.add_subplot(projection='3d')

#plt.pcolormesh(kx[0,:], ky[:, 0], np.log10(np.abs(max_f_val_array)))
ax.scatter(sample_range[0, :], sample_range[1, :], sample_range[2, :])

plt.show()
