import os
import shutil
def delete_pycache_folders(folder):
    for root, dirs, files in os.walk(folder):
        for dir in dirs:
            if dir == "__pycache__":
                folder_path = os.path.join(root, dir)
                print("Deleting folder:", folder_path)
                shutil.rmtree(folder_path)

# 指定要遍历的文件夹路径
folder_path = os.getcwd()

# 调用函数删除__pycache__文件夹
delete_pycache_folders(folder_path)

# import threading
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib
# matplotlib.use('Agg')


# def plot_sine_wave(x, y,name,dpi=300):
#     fig,ax = plt.subplots(1,1,figsize=(6,2))
#     ax.plot(x, y)
#     fig.tight_layout()
#     fig.subplots_adjust(left=None, bottom=None, top=None, hspace=None)
#     fig.savefig(name,dpi=dpi)
    
# x = np.linspace(0, 2*np.pi, 100)
# threads = []
# for i in range(4):
#     t = threading.Thread(target=plot_sine_wave, args=(np.arange(10), np.arange(10),f'{i}.png'))
#     threads.append(t)

# for t in threads:
#     t.start()
# for t in threads:
#     t.join()