import threading
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def plot_sine_wave(x, y,name,dpi=300):
    fig,ax = plt.subplots(1,1,figsize=(6,2))
    ax.plot(x, y)
    fig.tight_layout()
    fig.subplots_adjust(left=None, bottom=None, top=None, hspace=None)
    fig.savefig(name,dpi=dpi)
    
x = np.linspace(0, 2*np.pi, 100)
threads = []
for i in range(4):
    t = threading.Thread(target=plot_sine_wave, args=(np.arange(10), np.arange(10),f'{i}.png'))
    threads.append(t)

for t in threads:
    t.start()
for t in threads:
    t.join()