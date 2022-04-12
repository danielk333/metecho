import numpy as np
from tqdm import tqdm
from matplotlib import pyplot as plt
from matplotlib import cm

F_vals_all, kx, ky = np.load('temp_grid_data.npy')
max_f_val_array, x_max_array, y_max_array = np.load('temp_multi_grid_data.npy')

print('max_f_val_array: ', max_f_val_array)
print('kx_max: ', kx[0,154])
print('ky_max: ', ky[72,0])
print('max_fals_index: ', np.where(F_vals_all == max_f_val_array))

# # plotting
# fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

# surf = ax.plot_surface(kx, ky, np.log10(np.abs(F_vals_all)), cmap=cm.coolwarm,
#                        linewidth=0, antialiased=False)

# ax.set_xlabel('kx')
# ax.set_ylabel('ky')
# ax.set_zlabel('F_vals_all')

# ax.grid()

# plt.show()



# # 2D plot
# plt.figure()

# plt.pcolormesh(kx[0,:], ky[:, 0], np.log10(np.abs(F_vals_all)))

# plt.show()



# # plot of multiple grids
# plt.figure()

# plt.pcolormesh(x_max_array, y_max_array, np.log10(np.abs(max_f_val_array)))

# plt.show()


# 2D plot
plt.figure()

plt.pcolormesh(kx[0,154], ky[72, 0], np.log10(np.abs(F_vals_all[[154],[72]])))

plt.show()
