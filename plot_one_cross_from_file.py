#!/usr/bin/env python

import argparse
import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--f_start', default=200, type=float)
    parser.add_argument('--f_stop',  default=300, type=float)
    parser.add_argument('--d', type=str)
    parser.add_argument('--annotate', type=float, default=None)
    args = parser.parse_args()

    sig = np.load('{d}/0x1.npy'.format(d = args.d))
    sig = np.log10(np.abs(sig))
    plt.plot(np.linspace(0, 400, len(sig), endpoint=False), sig)
    plt.title("Magnitude spectrum of 0x1 at XXXX")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Magnitude (arbitrary units) [log]")
    plt.xlim(left = args.f_start, right = args.f_stop)

    if args.annotate is not None:
        xy = (args.annotate, sig[int(round(1024*(args.annotate/400.0)))])
        xytext = (xy[0] - 22, xy[1] + 0.5)
        plt.annotate('{f}'.format(f = args.annotate),
                     xy = xy, 
                     xytext = xytext,
                     color='red',
                     arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=6)
                     )

    plt.show()
